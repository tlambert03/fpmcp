"""Benchmark script to compare PDF text extraction libraries.

This script compares pypdfium2, pypdf, and PyMuPDF for:
- Extraction speed
- Text quality (length, readability)
- Memory usage

Run with: uv run python benchmark_pdf_libs.py
"""

from __future__ import annotations

import gc
import sys
import time
import tracemalloc

# Test DOIs for scientific papers (should have PDFs available)
TEST_ARTICLES = [
    "10.1038/s41592-023-02085-6",  # Nature Methods paper (14.29 MB)
    "10.7554/eLife.12345",  # eLife paper (3.50 MB)
]


def download_test_pdf(article_id: str) -> bytes | None:
    """Download a test PDF from our fulltext fetcher."""
    from fpmcp.fulltext import get_fulltext_sources

    # Try all sources, prefer PDF
    for source in get_fulltext_sources(article_id):
        if source.name == "europmc":  # Skip XML source
            continue
        result = source()
        if result and result.format == "pdf":
            assert isinstance(result.content, bytes)
            return result.content
    return None


def benchmark_pypdfium2(pdf_bytes: bytes) -> dict:
    """Benchmark pypdfium2."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return {"error": "pypdfium2 not installed"}

    # Warm up
    doc = pdfium.PdfDocument(pdf_bytes)
    _ = "".join(page.get_textpage().get_text_range() for page in doc)
    doc.close()
    gc.collect()

    # Benchmark
    tracemalloc.start()
    start = time.perf_counter()

    doc = pdfium.PdfDocument(pdf_bytes)
    text = "".join(page.get_textpage().get_text_range() for page in doc)
    doc.close()

    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "time": elapsed,
        "memory_peak_mb": peak / 1024 / 1024,
        "text_length": len(text),
        "text_preview": text[:200],
    }


def benchmark_pypdf(pdf_bytes: bytes) -> dict:
    """Benchmark pypdf."""
    try:
        import io

        from pypdf import PdfReader  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "pypdf not installed"}

    # Warm up
    reader = PdfReader(io.BytesIO(pdf_bytes))
    _ = "".join(page.extract_text() for page in reader.pages)
    gc.collect()

    # Benchmark
    tracemalloc.start()
    start = time.perf_counter()

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)

    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "time": elapsed,
        "memory_peak_mb": peak / 1024 / 1024,
        "text_length": len(text),
        "text_preview": text[:200],
    }


def benchmark_pymupdf(pdf_bytes: bytes) -> dict:
    """Benchmark PyMuPDF (fitz)."""
    try:
        import fitz  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "PyMuPDF not installed"}

    # Warm up
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    _ = "".join(page.get_text() for page in doc)
    doc.close()
    gc.collect()

    # Benchmark
    tracemalloc.start()
    start = time.perf_counter()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()

    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "time": elapsed,
        "memory_peak_mb": peak / 1024 / 1024,
        "text_length": len(text),
        "text_preview": text[:200],
    }


def run_benchmarks():
    """Run all benchmarks and display results."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Download test PDFs
    console.print("\n[bold cyan]Downloading test PDFs...[/bold cyan]")
    test_pdfs = []
    for article_id in TEST_ARTICLES:
        console.print(f"  Fetching {article_id}...")
        pdf_bytes = download_test_pdf(article_id)
        if pdf_bytes:
            size_mb = len(pdf_bytes) / 1024 / 1024
            console.print(f"    ✓ Downloaded ({size_mb:.2f} MB)")
            test_pdfs.append((article_id, pdf_bytes))
        else:
            console.print("    ✗ Failed to download")

    if not test_pdfs:
        console.print("[red]No PDFs available for testing[/red]")
        return

    # Run benchmarks
    console.print("\n[bold cyan]Running benchmarks...[/bold cyan]")
    results = {}
    for lib_name, benchmark_fn in [
        ("pypdfium2", benchmark_pypdfium2),
        ("pypdf", benchmark_pypdf),
        ("PyMuPDF", benchmark_pymupdf),
    ]:
        console.print(f"\n[bold yellow]{lib_name}:[/bold yellow]")
        results[lib_name] = []
        for article_id, pdf_bytes in test_pdfs:
            console.print(f"  Testing {article_id}...")
            result = benchmark_fn(pdf_bytes)
            results[lib_name].append((article_id, result))
            if "error" in result:
                console.print(f"    [red]✗ {result['error']}[/red]")
            else:
                console.print(
                    f"    ✓ Time: {result['time']:.4f}s, "
                    f"Memory: {result['memory_peak_mb']:.2f}MB, "
                    f"Text: {result['text_length']:,} chars"
                )

    # Display summary table
    console.print("\n[bold cyan]Summary:[/bold cyan]\n")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Library", style="cyan")
    table.add_column("Avg Time (s)", justify="right")
    table.add_column("Avg Memory (MB)", justify="right")
    table.add_column("Avg Text Length", justify="right")
    table.add_column("License", style="yellow")
    table.add_column("Status", style="green")

    for lib_name, lib_results in results.items():
        valid_results = [r for _, r in lib_results if "error" not in r]
        if not valid_results:
            table.add_row(lib_name, "—", "—", "—", "—", "[red]Not installed[/red]")
            continue

        avg_time = sum(r["time"] for r in valid_results) / len(valid_results)
        avg_memory = sum(r["memory_peak_mb"] for r in valid_results) / len(
            valid_results
        )
        avg_length = sum(r["text_length"] for r in valid_results) / len(valid_results)

        license_info = {
            "pypdfium2": "Apache-2.0",
            "pypdf": "BSD-3-Clause",
            "PyMuPDF": "AGPL/Commercial",
        }
        status = {"pypdfium2": "✓ Active", "pypdf": "✓ Active", "PyMuPDF": "✓ Active"}

        table.add_row(
            lib_name,
            f"{avg_time:.4f}",
            f"{avg_memory:.2f}",
            f"{avg_length:,.0f}",
            license_info[lib_name],
            status[lib_name],
        )

    console.print(table)

    # Display text quality samples
    console.print("\n[bold cyan]Text Quality Samples:[/bold cyan]")
    for lib_name, lib_results in results.items():
        console.print(f"\n[bold yellow]{lib_name}:[/bold yellow]")
        for article_id, result in lib_results:
            if "error" not in result:
                preview = result["text_preview"].replace("\n", " ")
                console.print(f"  {article_id[:20]}...: {preview}...")
                break  # Just show first article preview

    # Recommendations
    console.print("\n[bold cyan]Recommendations:[/bold cyan]")
    console.print(
        "• [bold]pypdfium2[/bold]: Fastest, permissive license (Apache-2.0), "
        "good for general use"
    )
    console.print(
        "• [bold]pypdf[/bold]: Pure Python, BSD license, good balance of speed "
        "and portability"
    )
    console.print(
        "• [bold]PyMuPDF[/bold]: Excellent quality, but AGPL license requires "
        "consideration"
    )


if __name__ == "__main__":
    # Check if required packages are available
    missing = []
    for pkg in ["rich"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print("Install with: uv add {' '.join(missing)}")
        sys.exit(1)

    run_benchmarks()
