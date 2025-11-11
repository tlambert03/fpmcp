"""Main server module for FastMCP."""

from __future__ import annotations

import re

from fastmcp import FastMCP

from fpmcp.fpbase.query import get_protein_references
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
        - url: URL where the full-text can be accessed
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
        "url": result.url,
    }


@mcp.tool
def search_article_text(
    article_id: str, pattern: str, context_chars: int = 500
) -> list[dict[str, str | int]]:
    """Search article text for a pattern and return matching snippets.

    This tool searches the full text of an article without loading the entire
    text into the agent's context. Only matching snippets with surrounding
    context are returned, making it efficient for finding specific information
    in large articles.

    Parameters
    ----------
    article_id : str
        Any article identifier: DOI, PMID, or PMCID
    pattern : str
        Regular expression pattern to search for. Use raw strings for complex
        patterns (e.g., r"\\d+ amino acids?" to find sequence lengths)
    context_chars : int, optional
        Number of characters to include before and after each match for context.
        Default is 500 characters.

    Returns
    -------
    list[dict]
        List of matches, where each match is a dictionary with:
        - text: The matched text plus surrounding context
        - position: Character position of match in full text
        - match: The exact text that matched the pattern

    Examples
    --------
    Find sequence length mentions:
    >>> matches = search_article_text(
    ...     "10.1038/s41587-022-01278-2", r"(\\d+)\\s+amino\\s+acids?"
    ... )

    Find aggregation state mentions:
    >>> matches = search_article_text(
    ...     "10.1038/nmeth.4074", r"(monomer|dimer|tetramer|oligomer)"
    ... )

    Find quantum yield values:
    >>> matches = search_article_text(
    ...     "10.1038/s41587-022-01278-2", r"quantum\\s+yield[:\\s]+([0-9.]+)"
    ... )

    Find extinction coefficient (handles multiple formats):
    >>> matches = search_article_text(
    ...     "10.1038/s41587-022-01278-2",
    ...     r"(extinction\\s+coefficient|ε|molar\\s+extinction).*?[\\d,]+\\s*M",
    ... )

    Find maturation time:
    >>> matches = search_article_text(
    ...     "10.1038/s41587-022-01278-2",
    ...     r"matur(ation|ing).*?(\\d+\\.?\\d*)\\s*(h|hr|hour|min|minute)",
    ... )

    Notes
    -----
    Common search patterns for fluorescent protein properties:
    - Oligomerization: "(monomer|dimer|tetramer|oligomer)"
    - Extinction (ε): "(extinction\\s+coefficient|ε|molar\\s+extinction)"
    - Quantum yield: "(quantum\\s+yield|QY|Φ)"
    - Maturation: "matur(ation|ing).*?\\d+.*?(hour|min)"
    - pKa: "pKa.*?\\d+\\.?\\d*"
    - Photostability: "(photostab|bleach|half.?life)"

    Regex tips:
    - Use \\s+ for flexible whitespace (matches spaces, newlines)
    - Use .*? for optional connecting text between terms
    - Use alternation (|) to catch synonyms and abbreviations
    - Numbers may have commas: use [\\d,]+ to match "159,000"
    - Greek letters work: ε (epsilon), Φ (phi for quantum yield)

    Limitations:
    - Requires full-text availability (returns [] if article not accessible)
    - All searches are case-insensitive
    - Default 500-char context may not capture complete paragraphs
    - Very complex patterns may miss edge cases
    """
    result = get_fulltext(article_id)
    if result is None:
        return []

    text = extract_text(result)
    if not text:
        return []

    matches = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)

        # Add ellipsis if we're not at the start/end
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        matches.append(
            {"text": snippet, "position": match.start(), "match": match.group()}
        )

    return matches


@mcp.tool
def get_protein_article_ids(protein_name: str) -> list[str]:
    """Get article identifiers (DOI/PMID) for a fluorescent protein.

    Searches the FPbase database for references associated with a specific
    protein. Returns article identifiers that can be used with other tools
    like get_article_tables() and get_article_text() to extract data.

    Parameters
    ----------
    protein_name : str
        Name of the fluorescent protein (e.g., "StayGold", "mCherry", "EGFP")

    Returns
    -------
    list[str]
        List of article identifiers, prioritizing DOI over PMID. Each entry
        is either a DOI (e.g., "10.1038/...") or PMID (e.g., "12345678").
        Returns empty list if protein not found.

    Examples
    --------
    To find the quantum yield of StayGold:
    1. Call get_protein_article_ids("StayGold") to get article identifiers
    2. For each identifier, call get_article_tables(identifier)
    3. Search the tables for "quantum yield" or "QY"
    4. If not found in tables, call get_article_text(identifier) and search
    """
    protein_refs = get_protein_references()
    article_ids = []
    for ref in protein_refs.get(protein_name.lower(), []):
        # Prioritize DOI, fallback to PMID
        if ref.get("doi"):
            article_ids.append(ref["doi"])
        elif ref.get("pmid"):
            article_ids.append(ref["pmid"])

    return article_ids
