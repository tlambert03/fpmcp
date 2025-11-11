"""Graphql queries for fpbase."""

from collections import defaultdict
from collections.abc import Mapping
from functools import cache

import requests

URL = "https://www.fpbase.org/graphql/"
GET_REFS = """{
  references {
    doi
    pmid
    proteins { edges { node { id name } } }
  }
}
"""


@cache
def get_references() -> list[dict]:
    """Fetch all PMIDs from FPbase GraphQL API, and their associated proteins"""
    requests_session = requests.Session()
    response = requests_session.post(URL, json={"query": GET_REFS})
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL query failed: {data['errors']}")
    return data["data"]["references"]


def pmids() -> Mapping[str, list[str]]:
    """Get mapping of PMIDs to associated protein IDs."""
    refs = get_references()
    pmid_map: dict[str, list[str]] = {}
    for ref in refs:
        pmid = ref.get("pmid")
        if not pmid:
            continue
        proteins = [edge["node"] for edge in ref["proteins"]["edges"]]
        pmid_map[pmid] = proteins
    return pmid_map


def dois() -> Mapping[str, list[str]]:
    """Get mapping of DOIs to associated protein IDs."""
    refs = get_references()
    doi_map: dict[str, list[str]] = {}
    for ref in refs:
        doi = ref.get("doi")
        if not doi:
            continue
        proteins = [edge["node"] for edge in ref["proteins"]["edges"]]
        doi_map[doi] = proteins
    return doi_map


def get_protein_references() -> Mapping[str, list[dict]]:
    """Get mapping of protein names to associated references (with DOI/PMID)."""
    refs = get_references()
    protein_map: dict[str, list[dict]] = defaultdict(list)
    for ref in refs:
        for edge in ref["proteins"]["edges"]:
            protein_name = edge["node"]["name"]
            ref_no_prots = {k: v for k, v in ref.items() if k != "proteins"}
            protein_map[protein_name].append(ref_no_prots)
    return protein_map
