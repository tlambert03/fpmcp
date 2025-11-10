import requests

from fpmcp.europmc_models import Model as SearchResponse


def get_fulltext_from_europmc(pmid: str) -> str | None:
    """Retrieve the full-text XML of an article from Europe PMC using its PubMed ID."""
    # https://www.ebi.ac.uk/europepmc/webservices/api/swagger.json

    # Check availability
    search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": f"ext_id:{pmid} src:med", "format": "json", "resultType": "core"}
    response = requests.get(search_url, params=params)
    data = SearchResponse.model_validate_json(response.text)

    if not (result := data.resultList.result):
        return None

    article = result[0]

    # Check if full text available
    if article.inEPMC == "Y" and article.pmcid:
        # Retrieve full-text XML
        pmcid = article.pmcid
        fulltext_url = (
            f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        )
        xml_response = requests.get(fulltext_url)

        if xml_response.status_code == 200:
            return xml_response.text

    return None


if __name__ == "__main__":
    test_pmid = "35468954"  # staygold
    fulltext_xml = get_fulltext_from_europmc(test_pmid)
    if fulltext_xml:
        print("Full-text XML retrieved successfully.")
    else:
        print("Full-text XML not available.")
