"""Test PDF fallback for articles without XML."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest
from fpmcp.fulltext import extract_tables, get_fulltext


def test_pdf_fallback():
    """Test that PDF fallback works when XML is unavailable.

    We'll mock the Europe PMC call to fail and verify PDF sources work.
    """
    # Use a DOI that might not be in Europe PMC but should have PDF access
    # For testing, we'll force PDF by mocking the XML fetch to return None

    with patch("fpmcp.fulltext._try_europmc", return_value=None):
        result = get_fulltext("10.1038/s41592-023-02085-6")

        if result is None:
            import pytest

            pytest.skip("No PDF source available for this article")

        assert result is not None
        assert result.format == "pdf"
        assert result.source in ("unpaywall", "crossref")

        # Try extracting tables from PDF
        tables = extract_tables(result)

        if "-s" in sys.argv:
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            console.print(f"\n[bold]PDF Source: {result.source}[/bold]")
            console.print(f"Extracted {len(tables)} tables\n")
            for idx, table in enumerate(tables, 1):
                console.print(f"[bold cyan]Table {idx}:[/bold cyan]")
                console.print(Markdown(table))
                console.print()


def test_compare_xml_vs_pdf():
    """Direct comparison of XML vs PDF table extraction for the same article."""
    # Get XML version
    xml_result = get_fulltext("10.1038/s41592-023-02085-6")
    assert xml_result is not None

    if xml_result.format == "xml":
        xml_tables = extract_tables(xml_result)

        # Force PDF
        with patch("fpmcp.fulltext._try_europmc", return_value=None):
            pdf_result = get_fulltext("10.1038/s41592-023-02085-6")

            if pdf_result is None:
                pytest.skip("No PDF source available")
                return

            pdf_tables = extract_tables(pdf_result)

            if "-s" in sys.argv:
                from rich.console import Console

                console = Console()
                console.print("\n[bold green]XML SOURCE:[/bold green]")
                console.print(f"Tables: {len(xml_tables)}")
                console.print(f"Total chars: {sum(len(t) for t in xml_tables):,}")

                console.print("\n[bold blue]PDF SOURCE:[/bold blue]")
                console.print(f"Tables: {len(pdf_tables)}")
                console.print(f"Total chars: {sum(len(t) for t in pdf_tables):,}")

                console.print("\n[bold yellow]COMPARISON:[/bold yellow]")
                console.print(
                    f"XML has {len(xml_tables) - len(pdf_tables)} more tables"
                )
                console.print(
                    f"Quality ratio: {len(pdf_tables) / max(len(xml_tables), 1):.1%}"
                )
