from __future__ import annotations

import re
from typing import TYPE_CHECKING

import requests

from fpmcp.http import get_session

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any


class ArticleIdentifier:
    """Hybrid identifier system that normalizes to DOI but preserves other IDs

    Detection order:
        1. PMCID (most specific - has 'PMC' prefix)
        2. DOI (specific - has '10.' prefix and '/')
        3. PMID (least specific - bare digits, validated via API)
    """

    def __init__(self, identifier: Any) -> None:
        self.doi = self.pmid = self.pmcid = None
        self.source_id = identifier = str(identifier)

        if _is_pmcid(identifier):
            self.pmcid = identifier
        elif _is_doi(identifier):
            self.doi = identifier
        elif _is_pmid(identifier):
            self.pmid = identifier

        if self.pmcid or self.doi or self.pmid:
            self._complete_identifiers()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ArticleIdentifier):
            return NotImplemented
        return (
            self.doi == value.doi
            and self.pmid == value.pmid
            and self.pmcid == value.pmcid
        )

    def __repr__(self) -> str:
        return (
            f"ArticleIdentifier(doi={self.doi!r}, pmid={self.pmid!r}, "
            f"pmcid={self.pmcid!r})"
        )

    def __rich_repr__(self) -> Iterable[tuple[str, str | list[str] | None]]:
        return self.__iter__()

    def __iter__(self) -> Iterable[tuple[str, str | list[str] | None]]:
        yield ("doi", self.doi)
        yield ("pmid", self.pmid)
        yield ("pmcid", self.pmcid)
        yield ("source_id", self.source_id)
        if upd := self.unpaywall_data():
            if locations := upd.get("oa_locations", []):
                yield (
                    "urls_for_pdf",
                    sorted(
                        {url for loc in locations if (url := loc.get("url_for_pdf"))}
                    ),
                )
                yield (
                    "url_for_landing_pages",
                    sorted(
                        {
                            url
                            for loc in locations
                            if (url := loc.get("url_for_landing_page"))
                        }
                    ),
                )

    def unpaywall_data(self) -> dict[str, Any]:
        """Fetch Unpaywall metadata for this article, if DOI is available."""
        if not self.doi:
            return {}
        from fpmcp.unpaywall.utils import get_unpaywall_data

        return get_unpaywall_data(self.doi)

    def _complete_identifiers(self) -> bool:
        """Fill in missing identifiers via API calls."""
        if not (id_value := self.doi or self.pmid or self.pmcid):
            return False

        idtype = "doi" if self.doi else "pmid" if self.pmid else "pmcid"
        return self._try_pmc_converter(id_value, idtype) or self._try_europe_pmc(
            id_value, idtype
        )

    def _try_pmc_converter(self, id_value: str, idtype: str) -> bool:
        try:
            response = get_session().get(
                "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/",
                params={
                    "ids": id_value,
                    "idtype": idtype,
                    "format": "json",
                    "tool": "fpmcp",
                    "email": "research@example.com",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok" and data.get("records"):
                record = data["records"][0]
                if record.get("status") == "error":
                    return False

                if not self.doi and record.get("doi"):
                    self.doi = record["doi"]
                if not self.pmid and record.get("pmid"):
                    self.pmid = str(record["pmid"])
                if not self.pmcid and record.get("pmcid"):
                    self.pmcid = record["pmcid"]
                return True

        except (requests.RequestException, KeyError, ValueError):
            pass
        return False

    def _try_europe_pmc(self, id_value: str, idtype: str) -> bool:
        query = (
            id_value
            if idtype in ("doi", "pmcid")
            else f"ext_id:{id_value}"
            if idtype == "pmid"
            else None
        )
        if not query:
            return False

        try:
            response = get_session().get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={"query": query, "format": "json"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("hitCount", 0) > 0 and data.get("resultList", {}).get("result"):
                result = data["resultList"]["result"][0]
                if not self.doi and result.get("doi"):
                    self.doi = result["doi"]
                if not self.pmid and result.get("pmid"):
                    self.pmid = result["pmid"]
                if not self.pmcid and result.get("pmcid"):
                    self.pmcid = result["pmcid"]
                return True

        except (requests.RequestException, KeyError, ValueError):
            pass
        return False


def _is_doi(identifier: str) -> bool:
    """Check if identifier is a DOI.

    DOIs must start with '10.' followed by a number, then '/', then a suffix.
    Based on ISO 26324 standard for DOI format.

    Sources
    -------
    - DataCite DOI Basics: https://support.datacite.org/docs/doi-basics
    """
    id_clean = identifier.strip()
    for prefix in ("doi:", "https://doi.org/", "http://doi.org/"):
        if id_clean.startswith(prefix):
            id_clean = id_clean[len(prefix) :].strip()
            break
    return bool(re.match(r"^10\.\d+/.+", id_clean))


def _is_pmid(identifier: str) -> bool:
    """Check if identifier is a PMID.

    PMIDs are numeric identifiers with no leading zeros.
    Officially 1-8 digits historically, but may be longer now.

    Sources
    -------
    - NLM Technical Bulletin: https://www.nlm.nih.gov/pubs/techbull/so08/so08_skill_kit_pmcid.html
    - PMID Wikipedia: https://en.wikipedia.org/wiki/PMID_(identifier)
    """
    id_clean = identifier.strip()
    return id_clean.isdigit() and (len(id_clean) == 1 or id_clean[0] != "0")


def _is_pmcid(identifier: str) -> bool:
    r"""Check if identifier is a PMCID.

    PMCIDs start with 'PMC' followed by digits, optionally with a version
    number.
    Format: PMC\d+(\.\d+)?

    Sources
    -------
    - NLM Technical Bulletin: https://www.nlm.nih.gov/pubs/techbull/so08/so08_skill_kit_pmcid.html
    - PMC ID Converter: https://pmc.ncbi.nlm.nih.gov/tools/idconv/
    - Bioregistry PMCID: https://bioregistry.io/pmc
    """
    # PMCID format: PMC followed by digits, optionally .digits for version
    return bool(re.match(r"^PMC\d+(?:\.\d+)?$", identifier.strip()))
