import requests


def get_fulltext_urls_from_crossref(doi: str) -> dict:
    """Use CrossRef to find full-text links for any DOI

    Returns: dict with PDF/XML URLs and license info
    """
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()["message"]

        # Extract full-text links
        links = data.get("link", [])
        fulltext_urls = {link["content-type"]: link["URL"] for link in links}

        # Extract license
        licenses = data.get("license", [])

        return {
            "pdf_url": fulltext_urls.get("application/pdf"),
            "xml_url": fulltext_urls.get("application/xml"),
            "html_url": fulltext_urls.get("text/html"),
            "licenses": [lic["URL"] for lic in licenses],
        }

    return {}
