from __future__ import annotations

from functools import cache

from fpmcp.http import get_session

EMAIL = "talley@hms.harvard.edu"


@cache
def get_unpaywall_data(doi: str) -> dict:
    """Check Unpaywall for OA availability.

    Parameters
    ----------
    doi : str
        The DOI of the article to check.

    Returns
    -------
    DOISchema
        The Unpaywall response containing OA location and metadata.
    """
    url = f"https://api.unpaywall.org/v2/{doi}"
    response = get_session().get(url, params={"email": EMAIL})
    response.raise_for_status()
    return response.json()
