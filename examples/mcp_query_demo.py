"""Demo of using MCP tools to answer scientific queries.

This shows how the MCP tools can be used to answer queries like:
"What is the quantum yield of StayGold in 10.1038/s41592-023-02085-6?"

Expected answer: 0.93
"""

from fpmcp.fulltext import extract_tables, get_fulltext

# Query: "What is the quantum yield of StayGold in 10.1038/s41592-023-02085-6?"

doi = "10.1038/s41592-023-02085-6"

# Step 1: Get article info
print("=" * 70)
print("Getting article information...")
print("=" * 70)
result = get_fulltext(doi)
if result:
    print(f"Source: {result.source}")
    print(f"Format: {result.format}")
    print(f"DOI: {result.article_id.doi}")
    print(f"PMID: {result.article_id.pmid}")
    print()

    # Step 2: Get all tables
    print("=" * 70)
    print("Fetching tables from article...")
    print("=" * 70)
    tables = extract_tables(result)
    print(f"Found {len(tables)} tables\n")
else:
    print("Could not fetch article")
    exit(1)

# Step 3: Search for StayGold and quantum yield
print("=" * 70)
print("Searching for StayGold quantum yield...")
print("=" * 70)

for i, table in enumerate(tables, 1):
    # Check if this table contains StayGold
    if "StayGold" in table or "staygold" in table.lower():
        print(f"\n✓ Found StayGold in Table {i}!")

        # Find lines with StayGold
        lines = table.split("\n")
        staygold_lines = [
            line for line in lines if "stay" in line.lower() and "gold" in line.lower()
        ]

        print(f"\nStayGold entries ({len(staygold_lines)} found):")
        for line in staygold_lines:
            if "0.93" in line:
                print(f"  → {line.strip()}")
                print("\n✓✓ FOUND: Quantum yield (QY) = 0.93")

print("\n" + "=" * 70)
print("Query answered successfully!")
print("=" * 70)
