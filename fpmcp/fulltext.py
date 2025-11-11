"""Ultimate any-ID to full-text fetcher with multiple source fallbacks.

This module provides a unified interface for fetching full-text content from
scientific articles using any common identifier (DOI, PMID, PMCID).

The fetching strategy uses a waterfall approach:
1. Try Europe PMC for structured JATS XML (best for tables/structured data)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from fpmcp.article_id import ArticleIdentifier
from fpmcp.crossref.utils import get_fulltext_urls_from_crossref
from fpmcp.europmc.utils import _fulltext_xml, _search
from fpmcp.http import get_session
from fpmcp.unpaywall.utils import get_unpaywall_data

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


@dataclass
class FullTextResult:
    """Result of fetching full-text content.

    Attributes
    ----------
    source : str
        Where the content came from: "europmc", "unpaywall", "crossref"
    format : str
        Content format: "xml" or "pdf"
    content : str | bytes
        Raw content (str for XML, bytes for PDF)
    article_id : ArticleIdentifier
        Normalized article identifiers
    url : str
        URL where the full-text can be accessed
    """

    source: Literal["europmc", "unpaywall", "crossref"]
    format: Literal["xml", "pdf"]
    content: str | bytes
    article_id: ArticleIdentifier
    url: str


@dataclass
class FullTextSource:
    """A lazy source for full-text content.

    This is a callable object that fetches content only when invoked,
    allowing inspection of available sources without immediately downloading.

    Attributes
    ----------
    name : str
        Source name: "europmc", "unpaywall", or "crossref"
    article_id : ArticleIdentifier
        The article to fetch
    _fetch_fn : Callable
        Function to call to fetch the content
    """

    name: Literal["europmc", "unpaywall", "crossref"]
    article_id: ArticleIdentifier
    _fetch_fn: Callable[[], FullTextResult | None]

    def __call__(self) -> FullTextResult | None:
        """Fetch the full-text content from this source.

        Returns
        -------
        FullTextResult | None
            The fetched content, or None if unavailable
        """
        return self._fetch_fn()


def get_fulltext_sources(any_id: str | ArticleIdentifier) -> list[FullTextSource]:
    """Get all potential sources for full-text without fetching content.

    This allows inspection of available sources and lazy fetching only
    when needed. Each source is a callable that fetches when invoked.

    Parameters
    ----------
    any_id : str | ArticleIdentifier
        Any article identifier: DOI, PMID, or PMCID

    Returns
    -------
    list[FullTextSource]
        List of available sources, ordered by preference (XML > PDF)

    Examples
    --------
    >>> sources = get_fulltext_sources("10.1038/s41592-023-02085-6")
    >>> for source in sources:
    ...     print(f"Available: {source.name}")
    ...     result = source()  # Fetch only when needed
    ...     if result:
    ...         break
    """
    # Normalize the identifier
    article_id = (
        any_id if isinstance(any_id, ArticleIdentifier) else ArticleIdentifier(any_id)
    )

    sources = []

    # Strategy 1: Europe PMC for structured XML
    if article_id.pmid:
        sources.append(
            FullTextSource(
                name="europmc",
                article_id=article_id,
                _fetch_fn=lambda aid=article_id: _try_europmc(aid),
            )
        )

    # Strategy 2: Unpaywall for PDF
    if article_id.doi:
        sources.append(
            FullTextSource(
                name="unpaywall",
                article_id=article_id,
                _fetch_fn=lambda aid=article_id: _try_unpaywall(aid),
            )
        )

    # Strategy 3: CrossRef for PDF
    if article_id.doi:
        sources.append(
            FullTextSource(
                name="crossref",
                article_id=article_id,
                _fetch_fn=lambda aid=article_id: _try_crossref(aid),
            )
        )

    return sources


def get_fulltext(any_id: str | ArticleIdentifier) -> FullTextResult | None:
    """Fetch full-text content from any article identifier.

    This is the main entry point for fetching full-text content. It tries
    multiple sources in order of quality, preferring structured XML over PDF.

    Parameters
    ----------
    any_id : str | ArticleIdentifier
        Any article identifier: DOI, PMID, or PMCID

    Returns
    -------
    FullTextResult | None
        Full-text content with metadata, or None if not found

    Examples
    --------
    >>> result = get_fulltext("10.1038/s41592-023-02085-6")
    >>> if result:
    ...     print(f"Found {result.format} from {result.source}")
    ...     tables = extract_tables(result)
    """
    # Get all available sources and try each in order
    for source in get_fulltext_sources(any_id):
        logger.debug("Trying source: %s", source.name)
        if result := source():
            return result

    return None


def _try_europmc(article_id: ArticleIdentifier) -> FullTextResult | None:
    """Try to fetch JATS XML from Europe PMC."""
    # Need PMID to search Europe PMC
    if not article_id.pmid:
        return None

    try:
        # Check if full text is available
        data = _search(f"ext_id:{article_id.pmid} src:med")
        if not (result := data.resultList.result):
            return None

        article = result[0]
        if article.inEPMC == "Y" and (pmcid := article.pmcid):
            if xml_content := _fulltext_xml(pmcid):
                return FullTextResult(
                    source="europmc",
                    format="xml",
                    content=xml_content,
                    article_id=article_id,
                    url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
                )
    except Exception:
        pass

    return None


def _try_unpaywall(article_id: ArticleIdentifier) -> FullTextResult | None:
    """Try to fetch PDF from Unpaywall."""
    if not article_id.doi:
        return None

    try:
        data = get_unpaywall_data(article_id.doi)

        # Prioritize best_oa_location
        if best_loc := data.get("best_oa_location"):
            if pdf_url := best_loc.get("url_for_pdf"):
                if pdf_content := _download_pdf(pdf_url):
                    # Use landing page URL if available, otherwise PDF URL
                    url = (
                        best_loc.get("url_for_landing_page")
                        or best_loc.get("url")
                        or pdf_url
                    )
                    return FullTextResult(
                        source="unpaywall",
                        format="pdf",
                        content=pdf_content,
                        article_id=article_id,
                        url=url,
                    )
    except Exception:
        pass

    return None


def _try_crossref(article_id: ArticleIdentifier) -> FullTextResult | None:
    """Try to fetch PDF from CrossRef."""
    if not article_id.doi:
        return None

    try:
        data = get_fulltext_urls_from_crossref(article_id.doi)

        # Try PDF first
        if pdf_url := data.get("pdf_url"):
            if pdf_content := _download_pdf(pdf_url):
                return FullTextResult(
                    source="crossref",
                    format="pdf",
                    content=pdf_content,
                    article_id=article_id,
                    url=pdf_url,
                )
    except Exception:
        pass

    return None


def _download_pdf(url: str, timeout: int = 30) -> bytes | None:
    """Download PDF from a URL with timing debug info."""
    start = time.time()
    try:
        logger.debug("Starting PDF download from: %s", url)

        # Use shared session for connection pooling
        session = get_session()

        # Time the request
        req_start = time.time()
        response = session.get(url, timeout=timeout, stream=False)
        req_time = time.time() - req_start
        logger.debug("Request took %.2fs, status: %d", req_time, response.status_code)

        response.raise_for_status()

        # Verify it's actually a PDF
        if response.content[:4] == b"%PDF":
            total_time = time.time() - start
            size_mb = len(response.content) / (1024 * 1024)
            logger.debug(
                "Downloaded %.2fMB PDF in %.2fs (%.2fMB/s)",
                size_mb,
                total_time,
                size_mb / total_time,
            )
            return response.content
        else:
            logger.debug("Not a PDF, first 4 bytes: %s", response.content[:4])
    except Exception as e:
        elapsed = time.time() - start
        logger.debug("Failed after %.2fs: %s: %s", elapsed, type(e).__name__, e)
        pass

    return None


def extract_tables(fulltext: FullTextResult) -> list[str]:
    """Extract tables from full-text content as markdown.

    Parameters
    ----------
    fulltext : FullTextResult
        Full-text content from get_fulltext()

    Returns
    -------
    list[str]
        List of tables in markdown format

    Examples
    --------
    >>> result = get_fulltext("10.1038/s41592-023-02085-6")
    >>> tables = extract_tables(result)
    >>> print(tables[0])
    """
    if fulltext.format == "xml":
        assert isinstance(fulltext.content, str)
        return _extract_tables_from_xml(fulltext.content)
    else:  # PDF
        raise NotImplementedError("PDF table extraction not yet implemented")


def _extract_tables_from_xml(xml_content: str) -> list[str]:
    """Extract tables from JATS XML using existing iter_tables utility."""
    from fpmcp.util import iter_tables

    return list(iter_tables(xml_content))


def extract_text(fulltext: FullTextResult) -> str:
    """Extract plain text from full-text content.

    Parameters
    ----------
    fulltext : FullTextResult
        Full-text content from get_fulltext()

    Returns
    -------
    str
        Plain text content

    Examples
    --------
    >>> result = get_fulltext("10.1038/s41592-023-02085-6")
    >>> text = extract_text(result)
    """
    if fulltext.format == "xml":
        assert isinstance(fulltext.content, str)
        return _extract_text_from_xml(fulltext.content)
    else:  # PDF
        assert isinstance(fulltext.content, bytes)
        return _extract_text_from_pdf(fulltext.content)


def _extract_text_from_xml(xml_content: str) -> str:
    """Extract plain text from JATS XML."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_content)
        # Get all text content, preserving some structure
        return "".join(root.itertext())
    except Exception:
        return ""


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF using pypdfium2.

    This function efficiently extracts text from PDF content using pypdfium2,
    which is fast, has low memory usage, and uses a permissive Apache-2.0 license.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw PDF content

    Returns
    -------
    str
        Extracted plain text from all pages
    """
    try:
        import pypdfium2 as pdfium

        # Open PDF from bytes (no file I/O needed)
        doc = pdfium.PdfDocument(pdf_bytes)

        # Extract text from all pages using a generator for memory efficiency
        # This avoids loading all text into memory at once for large PDFs
        text_parts = []
        for page in doc:
            textpage = page.get_textpage()
            text_parts.append(textpage.get_text_range())

        # Close the document to free resources
        doc.close()

        # Join all page text
        return "".join(text_parts)

    except Exception as e:
        logger.debug("Failed to extract text from PDF: %s", e)
        return ""
