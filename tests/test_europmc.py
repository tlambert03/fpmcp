import sys

import pytest
from fpmcp.europmc import get_fulltext_from_europmc
from fpmcp.util import iter_tables


def test_fetch_full_text(pmid: str = "35468954"):
    fulltext_xml = get_fulltext_from_europmc(pmid)
    assert fulltext_xml is not None
    assert "<article" in fulltext_xml


@pytest.mark.parametrize(
    "pmid",
    [
        ("35468954", ["- b: Emission maximum"]),
        (
            "40671276",
            [
                "| Protein | λ _ex,max (nm) | λ _em,max (nm) | ε (M^−1 cm^−1) | QY | Bright. (×10^3) | pKa |"  # noqa: RUF001, E501
            ],
        ),
        "36344833",
        (
            "38036853",
            [
                "| tdoxStayGold | 496/504 | NT | NT | NT | NT | NT | NT | 58.3 | 75.5 | 64.5 |",  # noqa: E501
                "- b: Emission maximum",
            ],
        ),
        (
            "35715437",
            [
                "| Ex max (nm) | 402 | 383 | 399 | 402 | 403 |",
                "| Relative brightness in HEK cells a | 21 | 69 | 100 | 91 | 97 |",
                "- b: Refers to mean fluorescence half-time",
            ],
        ),
    ],
    ids=lambda x: x if isinstance(x, str) else x[0],
)
def test_parse_tables(pmid: str | tuple[str, list[str]]) -> None:
    expect = None
    if isinstance(pmid, tuple):
        pmid, expect = pmid
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

    if expect is not None:
        t = tables[0]
        for e in expect:
            assert e in t.splitlines()
