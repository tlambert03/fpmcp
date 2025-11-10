import sys

from fpmcp.europmc import get_fulltext_from_europmc
from fpmcp.util import iter_tables


def test_fetch_full_text(pmid: str = "35468954"):
    fulltext_xml = get_fulltext_from_europmc(pmid)
    assert fulltext_xml is not None
    assert "<article" in fulltext_xml


def test_parse_tables(pmid: str = "35468954"):
    fulltext_xml = get_fulltext_from_europmc(pmid)
    assert fulltext_xml is not None
    tables = list(iter_tables(fulltext_xml))
    assert len(tables) > 0

    if "-s" in sys.argv:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        for table in tables:
            console.print(Markdown(table))
