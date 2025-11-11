#!/usr/bin/env python
"""Quick test of ArticleIdentifier with a specific DOI."""

import pytest
from fpmcp.article_id import ArticleIdentifier


@pytest.mark.parametrize(
    "identifier", ["10.1038/s41592-023-02085-6", "38036853", "PMC11009113"]
)
def test_article_identifier(identifier: str) -> None:
    article = ArticleIdentifier(identifier)
    assert article.source_id == identifier
    assert article.doi == "10.1038/s41592-023-02085-6"
    assert article.pmid == "38036853"
    assert article.pmcid == "PMC11009113"
