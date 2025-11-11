"""Ultimate any-ID to full-text fetcher with multiple source fallbacks.

This module provides a unified interface for fetching full-text content from
scientific articles using any common identifier (DOI, PMID, PMCID).

The fetching strategy uses a waterfall approach:
1. Try Europe PMC for structured JATS XML (best for tables/structured data)
2. Fall back to PDF from Unpaywall (open access priority)
3. Fall back to PDF from CrossRef
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Literal

import requests

from fpmcp.article_id import ArticleIdentifier
from fpmcp.crossref.utils import get_fulltext_urls_from_crossref
from fpmcp.europmc.utils import _fulltext_xml, _search
from fpmcp.unpaywall.utils import check_unpaywall


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
    """

    source: Literal["europmc", "unpaywall", "crossref"]
    format: Literal["xml", "pdf"]
    content: str | bytes
    article_id: ArticleIdentifier


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
    # Normalize the identifier
    article_id = (
        any_id if isinstance(any_id, ArticleIdentifier) else ArticleIdentifier(any_id)
    )

    # Strategy 1: Try Europe PMC for structured XML
    if result := _try_europmc(article_id):
        return result

    # Strategy 2: Try Unpaywall for PDF
    if result := _try_unpaywall(article_id):
        return result

    # Strategy 3: Try CrossRef for PDF
    if result := _try_crossref(article_id):
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
                )
    except Exception:
        pass

    return None


def _try_unpaywall(article_id: ArticleIdentifier) -> FullTextResult | None:
    """Try to fetch PDF from Unpaywall."""
    if not article_id.doi:
        return None

    try:
        data = check_unpaywall(article_id.doi)

        # Prioritize best_oa_location
        if best_loc := data.get("best_oa_location"):
            if pdf_url := best_loc.get("url_for_pdf"):
                if pdf_content := _download_pdf(pdf_url):
                    return FullTextResult(
                        source="unpaywall",
                        format="pdf",
                        content=pdf_content,
                        article_id=article_id,
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
                )
    except Exception:
        pass

    return None


def _download_pdf(url: str, timeout: int = 30) -> bytes | None:
    """Download PDF from a URL."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Verify it's actually a PDF
        if response.content[:4] == b"%PDF":
            return response.content
    except Exception:
        pass

    return None


def extract_tables(fulltext: FullTextResult) -> list[str]:
    """Extract tables from full-text content as markdown.

    Works with both XML and PDF sources. XML provides better structured
    tables via JATS parsing, while PDF uses heuristic table detection.

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
        assert isinstance(fulltext.content, bytes)
        return _extract_tables_from_pdf(fulltext.content)


def _extract_tables_from_xml(xml_content: str) -> list[str]:
    """Extract tables from JATS XML using existing iter_tables utility."""
    from fpmcp.util import iter_tables

    return list(iter_tables(xml_content))


def _extract_tables_from_pdf(pdf_content: bytes) -> list[str]:
    """Extract tables from PDF using pdfplumber.

    Parameters
    ----------
    pdf_content : bytes
        Raw PDF bytes

    Returns
    -------
    list[str]
        List of tables in markdown format
    """
    import pdfplumber

    tables = []

    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                for table_idx, table in enumerate(page.extract_tables()):
                    if table:
                        md_table = _pdf_table_to_markdown(table, page_num, table_idx)
                        if md_table:
                            tables.append(md_table)
    except Exception:
        pass

    return tables


def _pdf_table_to_markdown(
    table: list[list[str | None]], page_num: int, table_idx: int
) -> str | None:
    """Convert pdfplumber table to markdown format.

    Parameters
    ----------
    table : list[list[str | None]]
        Table data from pdfplumber
    page_num : int
        Page number for reference
    table_idx : int
        Table index on the page

    Returns
    -------
    str | None
        Markdown formatted table
    """
    if not table or len(table) < 2:
        return None

    # Clean up None values and empty strings
    cleaned_table = []
    for row in table:
        cleaned_row = [(cell or "").strip().replace("\n", " ") for cell in row]
        # Skip completely empty rows
        if any(cleaned_row):
            cleaned_table.append(cleaned_row)

    if len(cleaned_table) < 2:
        return None

    # Assume first row is header
    headers = cleaned_table[0]
    rows = cleaned_table[1:]

    # Build markdown
    lines = [f"**Table from page {page_num} (#{table_idx + 1})**\n"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        # Pad row to match header length
        row.extend([""] * (len(headers) - len(row)))
        lines.append("| " + " | ".join(row[: len(headers)]) + " |")

    return "\n".join(lines)


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


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract plain text from PDF."""
    import pdfplumber

    text_parts = []

    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                if page_text := page.extract_text():
                    text_parts.append(page_text)
    except Exception:
        pass

    return "\n\n".join(text_parts)
