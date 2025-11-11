"""Main server module for FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from fpmcp.fulltext import extract_tables, extract_text, get_fulltext

mcp = FastMCP("FP Research Server")


@mcp.tool
def get_article_tables(article_id: str) -> list[str]:
    """Get all tables from a scientific article as markdown.

    Fetches full-text from any article identifier (DOI, PMID, PMCID) and
    extracts all tables in markdown format. Tables can then be searched or
    analyzed to find specific data points.

    Parameters
    ----------
    article_id : str
        Any article identifier: DOI (e.g., "10.1038/..."), PMID (e.g., "12345"),
        or PMCID (e.g., "PMC12345")

    Returns
    -------
    list[str]
        List of tables in markdown format. Each table includes title, headers,
        data rows, and legends/footnotes.

    Examples
    --------
    To find the quantum yield of StayGold in a paper:
    1. Call get_article_tables("10.1038/s41592-023-02085-6")
    2. Search the returned tables for "StayGold" and "QY" or "quantum yield"
    3. Extract the corresponding value from the table
    """
    result = get_fulltext(article_id)
    if result is None:
        return []

    return extract_tables(result)


@mcp.tool
def get_article_text(article_id: str) -> str:
    """Get full text content from a scientific article.

    Fetches the complete text content of an article from any identifier.
    Useful for reading abstracts, methods, results, and discussion sections.

    Parameters
    ----------
    article_id : str
        Any article identifier: DOI, PMID, or PMCID

    Returns
    -------
    str
        Full text content of the article
    """
    result = get_fulltext(article_id)
    if result is None:
        return ""

    return extract_text(result)


@mcp.tool
def get_article_info(article_id: str) -> dict[str, str]:
    """Get metadata about an article and its full-text availability.

    Parameters
    ----------
    article_id : str
        Any article identifier: DOI, PMID, or PMCID

    Returns
    -------
    dict
        Dictionary with keys:
        - source: Where full-text was found (europmc, unpaywall, crossref)
        - format: Content format (xml or pdf)
        - doi: Article DOI
        - pmid: PubMed ID (if available)
        - pmcid: PubMed Central ID (if available)
    """
    result = get_fulltext(article_id)
    if result is None:
        return {"error": "Full-text not found"}

    return {
        "source": result.source,
        "format": result.format,
        "doi": result.article_id.doi or "",
        "pmid": result.article_id.pmid or "",
        "pmcid": result.article_id.pmcid or "",
    }
