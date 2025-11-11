"""Script to find a test article that has PDF available."""

from __future__ import annotations

from fpmcp.fulltext import get_fulltext_sources

# Try various DOIs
test_dois = [
    "10.1038/s41592-023-02085-6",
    "10.1371/journal.pbio.3001700",  # PLOS paper
    "10.1371/journal.pone.0123456",  # Another PLOS
    "10.1016/j.cell.2020.01.001",  # Cell paper
    "10.7554/eLife.12345",  # eLife paper
]

for doi in test_dois:
    print(f"\nTrying {doi}:")
    sources = get_fulltext_sources(doi)
    print(f"  Available sources: {[s.name for s in sources]}")

    for source in sources:
        if source.name == "europmc":
            continue  # Skip XML source
        print(f"  Testing {source.name}...")
        result = source()
        if result and result.format == "pdf":
            print(f"    ✓ Found PDF from {source.name}!")
            print(f"    Size: {len(result.content) / 1024 / 1024:.2f} MB")
            print(f"\nUse this DOI for testing: {doi}")
            break
    else:
        print(f"  No PDF available for {doi}")
