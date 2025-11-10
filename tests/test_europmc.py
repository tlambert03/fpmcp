from fpmcp.europmc import get_fulltext_from_europmc


def test_fetch_full_text(pmid: str = "35468954"):
    fulltext_xml = get_fulltext_from_europmc(pmid)
    assert fulltext_xml is not None
    assert "<article" in fulltext_xml
