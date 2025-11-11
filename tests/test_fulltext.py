"""Tests for the ultimate fulltext fetcher."""

from __future__ import annotations

import sys

from fpmcp.fulltext import extract_tables, get_fulltext


def test_get_fulltext_from_doi():
    """Test fetching fulltext from a DOI."""
    # This paper should have full text in Europe PMC
    result = get_fulltext("10.1038/s41592-023-02085-6")
    assert result is not None
    assert result.source in ("europmc", "unpaywall", "crossref")
    assert result.format in ("xml", "pdf")
    assert len(result.content) > 0

    # Verify we got identifiers
    assert result.article_id.doi == "10.1038/s41592-023-02085-6"


def test_extract_tables_from_doi():
    """Test extracting tables from the example DOI.

    This paper (PMID 38036853) is known to have useful tables.
    """
    result = get_fulltext("10.1038/s41592-023-02085-6")
    assert result is not None

    tables = extract_tables(result)
    assert len(tables) > 0

    # Should find the table mentioned in the issue
    # (has data about tdoxStayGold and emission maxima)
    table_text = "\n".join(tables)
    assert len(table_text) > 100  # Should have substantial content

    if "-s" in sys.argv:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        console.print(f"\n[bold]Source: {result.source} ({result.format})[/bold]\n")
        for idx, table in enumerate(tables, 1):
            console.print(f"[bold cyan]Table {idx}:[/bold cyan]")
            console.print(Markdown(table))
            console.print()


def test_get_fulltext_from_pmid():
    """Test fetching fulltext from a PMID."""
    result = get_fulltext("38036853")  # Same paper as the DOI above
    assert result is not None
    assert result.article_id.pmid == "38036853"
    assert result.article_id.doi == "10.1038/s41592-023-02085-6"


def test_compare_xml_vs_pdf_tables():
    """Compare table extraction quality between XML and PDF sources.

    This test will help verify that our PDF fallback produces similar
    quality results to the XML source.
    """
    result = get_fulltext("10.1038/s41592-023-02085-6")
    assert result is not None

    tables = extract_tables(result)
    assert len(tables) > 0

    # Basic quality checks
    for table in tables:
        # Tables should have markdown headers
        assert "|" in table
        # Should have header separator
        assert "---" in table or "Table" in table

    if "-s" in sys.argv:
        from rich.console import Console

        console = Console()
        msg = f"✓ Extracted {len(tables)} tables from {result.source} ({result.format})"
        console.print(f"\n[bold green]{msg}[/bold green]")
        content_type = "bytes" if result.format == "pdf" else "chars"
        console.print(f"Total content length: {len(result.content):,} {content_type}")
