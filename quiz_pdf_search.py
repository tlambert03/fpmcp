"""Quiz the PDF search implementation with realistic research questions.

This script demonstrates the real-world utility of the PDF search functionality
by answering specific questions about fluorescent proteins from scientific papers.
"""

from __future__ import annotations

import re

from fpmcp.fulltext import extract_text, get_fulltext
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def ask_question(doi: str, question: str, pattern: str) -> list[str]:
    """Ask a research question about an article using regex search.

    Parameters
    ----------
    doi : str
        Article DOI
    question : str
        The research question to answer
    pattern : str
        Regex pattern to search for

    Returns
    -------
    list[str]
        List of answer snippets found
    """
    console.print(f"\n[bold cyan]Q: {question}[/bold cyan]")
    console.print(f"   DOI: {doi}")
    console.print(f"   Search pattern: [yellow]{pattern}[/yellow]")

    # Get full text
    result = get_fulltext(doi)
    if not result:
        console.print("   [red]✗ Could not fetch article[/red]")
        return []

    console.print(f"   ✓ Using {result.source} ({result.format})")

    # Extract text
    text = extract_text(result)

    # Search
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if not matches:
        console.print("   [red]✗ No matches found[/red]")
        return []

    console.print(f"   [green]✓ Found {len(matches)} matches[/green]\n")

    # Show snippets
    answers = []
    for i, match in enumerate(matches[:3], 1):  # Show first 3 matches
        start = max(0, match.start() - 150)
        end = min(len(text), match.end() + 150)
        snippet = text[start:end].replace("\n", " ")

        # Clean up excessive whitespace
        snippet = re.sub(r"\s+", " ", snippet)

        answers.append(snippet)
        console.print(f"   [bold]Match {i}:[/bold]")
        console.print(f"   ...{snippet}...\n")

    return answers


def main():
    """Run the quiz."""
    console.print(
        Panel.fit(
            "[bold magenta]PDF Search Quiz[/bold magenta]\n"
            "Testing real-world research questions on fluorescent proteins",
            border_style="magenta",
        )
    )

    # Quiz questions
    questions = [
        (
            "10.1038/s41592-023-02085-6",
            "What is the quantum yield of StayGold variants?",
            r"(?:quantum\s+yield|QY)[:\s]+([0-9.]+)",
        ),
        (
            "10.1038/s41592-023-02085-6",
            "What is the excitation maximum wavelength?",
            r"(?:excitation|absorption)[^.]{0,50}?(\d{3})\s*nm",
        ),
        (
            "10.1038/s41592-023-02085-6",
            "What is the emission maximum wavelength?",
            r"emission[^.]{0,50}?(\d{3})\s*nm",
        ),
        (
            "10.1038/s41592-023-02085-6",
            "What is the extinction coefficient?",
            r"(?:extinction\s+coefficient|molar\s+extinction)[^.]{0,100}?([\d,]+)\s*M",
        ),
        (
            "10.1038/s41592-023-02085-6",
            "What is the maturation time?",
            r"matur(?:ation|ing)[^.]{0,100}?(\d+\.?\d*)\s*(?:h|hr|hour)",
        ),
        (
            "10.1038/s41592-023-02085-6",
            "What is the oligomerization state?",
            r"(?:obligate\s+)?(monomer|dimer|tetramer|oligomer)",
        ),
    ]

    # Summary table
    results_table = Table(
        title="Quiz Results Summary", show_header=True, header_style="bold magenta"
    )
    results_table.add_column("Question", style="cyan")
    results_table.add_column("Matches Found", justify="center")
    results_table.add_column("Status", justify="center")

    results = []
    for doi, question, pattern in questions:
        answers = ask_question(doi, question, pattern)
        results.append((question, len(answers)))

        status = "✓" if answers else "✗"
        status_style = "green" if answers else "red"
        results_table.add_row(
            question[:50] + "..." if len(question) > 50 else question,
            str(len(answers)),
            f"[{status_style}]{status}[/{status_style}]",
        )

    # Display summary
    console.print("\n")
    console.print(results_table)

    # Overall results
    total_questions = len(questions)
    successful = sum(1 for _, count in results if count > 0)

    console.print(
        f"\n[bold]Overall: {successful}/{total_questions} questions answered[/bold]"
    )

    if successful == total_questions:
        console.print(
            "\n[bold green]🎉 Perfect score! "
            "PDF search is working excellently.[/bold green]"
        )
    elif successful >= total_questions * 0.7:
        console.print(
            "\n[bold yellow]✓ Good performance! Most questions answered.[/bold yellow]"
        )
    else:
        console.print(
            "\n[bold red]⚠ Some issues detected. Review the results above.[/bold red]"
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Quiz interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
