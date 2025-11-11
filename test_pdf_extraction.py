"""Test script to verify PDF text extraction and search functionality."""

from __future__ import annotations

import re

from fpmcp.fulltext import extract_text, get_fulltext, get_fulltext_sources


def test_pdf_text_extraction():
    """Test that PDF text extraction works correctly."""
    print("\n=== Testing PDF Text Extraction ===\n")

    # Use a DOI that we know has a PDF available
    doi = "10.1038/s41592-023-02085-6"
    print(f"Testing with DOI: {doi}")

    # Get PDF source specifically - try all non-XML sources
    sources = get_fulltext_sources(doi)
    result = None

    for pdf_source in sources:
        if pdf_source.name == "europmc":  # Skip XML source
            continue

        print(f"  Trying source: {pdf_source.name}")
        result = pdf_source()
        if result and result.format == "pdf":
            print(
                f"  ✓ Fetched PDF from {pdf_source.name} "
                f"({len(result.content) / 1024 / 1024:.2f} MB)"
            )
            break
        else:
            print(f"    (no PDF from {pdf_source.name})")

    if not result or result.format != "pdf":
        print("  ✗ Failed to fetch PDF from any source")
        return False

    # Extract text
    text = extract_text(result)
    print(f"  ✓ Extracted text ({len(text):,} characters)")

    # Verify text content (should contain expected terms)
    expected_terms = ["StayGold", "fluorescent", "protein"]
    for term in expected_terms:
        if term in text:
            print(f"  ✓ Found expected term: '{term}'")
        else:
            print(f"  ✗ Missing expected term: '{term}'")
            return False

    print("\n✓ PDF text extraction working correctly!\n")
    return True


def test_pdf_search_functionality():
    """Test that search_article_text works with PDFs."""
    print("=== Testing PDF Search Functionality ===\n")

    # Use a DOI that should have PDF
    doi = "10.1038/s41592-023-02085-6"
    print(f"Testing with DOI: {doi}")

    # Get the full text first
    result = get_fulltext(doi)
    if not result:
        print("  ✗ Could not fetch article")
        return False

    text = extract_text(result)
    print(f"  ✓ Extracted text from {result.format} ({len(text):,} chars)")

    # Test various search patterns
    test_patterns = [
        (r"StayGold", "StayGold protein name"),
        (r"quantum\s+yield", "quantum yield"),
        (r"fluorescent\s+protein", "fluorescent protein"),
        (r"\d+\s*nm", "wavelength measurements"),
        (r"matur(?:ation|ing)", "maturation mentions"),
    ]

    all_passed = True
    for pattern, description in test_patterns:
        print(f"\n  Testing pattern: {description}")
        print(f"    Pattern: {pattern}")

        # Search using regex (same as search_article_text tool)
        matches = list(re.finditer(pattern, text, re.IGNORECASE))

        if matches:
            print(f"    ✓ Found {len(matches)} matches")
            # Show first match
            if matches:
                match = matches[0]
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                snippet = text[start:end].replace("\n", " ")
                print(f"    Preview: ...{snippet}...")
        else:
            print("    ✗ No matches found")
            all_passed = False

    if all_passed:
        print("\n✓ PDF search functionality working correctly!\n")
    else:
        print("\n✗ Some searches failed\n")

    return all_passed


def test_pdf_vs_xml_comparison():
    """Compare text extraction quality between PDF and XML."""
    print("=== Comparing PDF vs XML Text Extraction ===\n")

    doi = "10.1038/s41592-023-02085-6"

    # Get both XML and PDF versions
    sources = get_fulltext_sources(doi)

    xml_text = None
    pdf_text = None

    for source in sources:
        result = source()
        if result:
            if result.format == "xml":
                xml_text = extract_text(result)
                print(
                    f"  XML text length: {len(xml_text):,} chars (from {source.name})"
                )
            elif result.format == "pdf":
                pdf_text = extract_text(result)
                print(
                    f"  PDF text length: {len(pdf_text):,} chars (from {source.name})"
                )

    if not xml_text or not pdf_text:
        print("  ✗ Could not get both XML and PDF versions")
        return False

    # Compare lengths (should be similar, within 20%)
    length_ratio = min(len(xml_text), len(pdf_text)) / max(len(xml_text), len(pdf_text))
    print(f"\n  Length similarity: {length_ratio:.1%}")

    if length_ratio > 0.8:
        print("  ✓ Text lengths are comparable")
    else:
        print("  ! Text lengths differ significantly")

    # Check that both contain key terms
    key_terms = ["StayGold", "fluorescent", "protein", "emission", "excitation"]
    print("\n  Checking for key terms:")

    for term in key_terms:
        in_xml = term in xml_text
        in_pdf = term in pdf_text
        status = "✓" if (in_xml and in_pdf) else "!"
        print(f"    {status} '{term}': XML={in_xml}, PDF={in_pdf}")

    print("\n✓ Comparison complete!\n")
    return True


if __name__ == "__main__":
    success = True

    try:
        success &= test_pdf_text_extraction()
    except Exception as e:
        print(f"✗ PDF text extraction test failed: {e}")
        import traceback

        traceback.print_exc()
        success = False

    try:
        success &= test_pdf_search_functionality()
    except Exception as e:
        print(f"✗ PDF search test failed: {e}")
        import traceback

        traceback.print_exc()
        success = False

    try:
        success &= test_pdf_vs_xml_comparison()
    except Exception as e:
        print(f"✗ PDF vs XML comparison test failed: {e}")
        import traceback

        traceback.print_exc()
        success = False

    if success:
        print("\n" + "=" * 60)
        print("🎉 All tests passed! PDF text extraction is working correctly.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Please review the output above.")
        print("=" * 60)
        exit(1)
