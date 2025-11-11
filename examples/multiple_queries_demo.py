"""Demo showing multiple scientific queries from the same article.

Demonstrates:
1. What is the quantum yield of StayGold? → 0.93
2. What is the absorption maximum of mEGFP? → 488 nm
"""

from fpmcp.fulltext import extract_tables, get_fulltext

doi = "10.1038/s41592-023-02085-6"

print("=" * 70)
print("Fetching article and extracting tables...")
print("=" * 70)

result = get_fulltext(doi)
if result is None:
    print("Could not fetch article")
    exit(1)

assert result is not None  # Type narrowing for type checker
tables = extract_tables(result)
print(f"✓ Found {len(tables)} table(s) from {result.source} ({result.format})\n")

# Query 1: Quantum yield of StayGold
print("=" * 70)
print("Query 1: What is the quantum yield of StayGold?")
print("=" * 70)

lines = tables[0].split("\n")
staygold_lines = [
    line for line in lines if "StayGold" in line and "|" in line and line.count("|") > 2
]

# Find the exact StayGold entry (not variants)
for line in staygold_lines:
    parts = [p.strip() for p in line.split("|")]
    if len(parts) > 1 and parts[1] == "StayGold":
        print("Found StayGold row:")
        print(f"  {line}")
        if "0.93" in line:
            print("\n✓ Answer: Quantum yield (QY) = 0.93\n")
        break

# Query 2: Absorption maximum of mEGFP
print("=" * 70)
print("Query 2: What is the absorption maximum of mEGFP?")
print("=" * 70)

megfp_lines = [line for line in lines if "mEGFP" in line and "|" in line]

if megfp_lines:
    print("Found mEGFP row:")
    print(f"  {megfp_lines[0]}")
    if "488" in megfp_lines[0]:
        print("\n✓ Answer: Absorption maximum (λab) = 488 nm\n")

# Bonus: Show all proteins in the table
print("=" * 70)
print("Bonus: All fluorescent proteins in this table")
print("=" * 70)

proteins = []
for line in lines:
    if "|" in line and line.count("|") > 2 and not line.startswith("| ---"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 1 and parts[1] and "λ" not in parts[1] and parts[1] != "":
            proteins.append(parts[1])

print(f"Found {len(proteins)} proteins:")
for protein in proteins:
    if protein:
        print(f"  • {protein}")

print("\n" + "=" * 70)
print("Demo complete!")
print("=" * 70)
