"""Demo of the ultimate any-ID to full-text fetcher."""

from fpmcp.fulltext import extract_tables, extract_text, get_fulltext

# Example 1: Get full-text from any identifier
doi = "10.1038/s41592-023-02085-6"
result = get_fulltext(doi)

if result:
    print(f"✓ Found full-text from {result.source} ({result.format})")
    print(f"  DOI: {result.article_id.doi}")
    print(f"  PMID: {result.article_id.pmid}")
    print(f"  PMCID: {result.article_id.pmcid}")
    print()

    # Example 2: Extract tables
    tables = extract_tables(result)
    print(f"✓ Extracted {len(tables)} tables")
    print()
    print("First table preview:")
    print(tables[0][:500] + "...")
    print()

    # Example 3: Extract plain text
    text = extract_text(result)
    print(f"✓ Extracted {len(text):,} characters of text")
    print()
    print("Text preview:")
    print(text[:200] + "...")
else:
    print("✗ No full-text found")


# Example 4: You can also use PMID or PMCID
print("\n" + "=" * 60)
print("Using PMID instead of DOI:")
print("=" * 60 + "\n")

result2 = get_fulltext("38036853")  # Same paper as above
if result2:
    print(f"✓ Found full-text from {result2.source} ({result2.format})")
    print(f"  Normalized to DOI: {result2.article_id.doi}")
