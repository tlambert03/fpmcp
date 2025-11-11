from typing import Final

from fpmcp.europmc.models import Model as SearchResponse
from fpmcp.http import get_session

# https://europepmc.org/RestfulWebService
ROOT: Final = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def _search(query: str) -> SearchResponse:
    # https://europepmc.org/RestfulWebService#!/Europe32PMC32Articles32RESTful32API/search
    response = get_session().get(
        f"{ROOT}/search",
        params={"query": query, "format": "json", "resultType": "core"},
    )
    response.raise_for_status()
    return SearchResponse.model_validate_json(response.text)


def _fulltext_xml(pmcid: str) -> str | None:
    # https://europepmc.org/RestfulWebService#!/Europe32PMC32Articles32RESTful32API/fullTextXML
    xml_response = get_session().get(f"{ROOT}/{pmcid}/fullTextXML")
    if xml_response.status_code == 200:
        return xml_response.text
    return None


def get_fulltext_from_europmc(pmid: str) -> str | None:
    """Retrieve the full-text XML of an article from Europe PMC using its PubMed ID."""
    data = _search(f"ext_id:{pmid} src:med")
    if not (result := data.resultList.result):
        return None

    # Check if full text available
    article = result[0]
    if article.inEPMC == "Y" and (pmcid := article.pmcid):
        return _fulltext_xml(pmcid)

    return None
