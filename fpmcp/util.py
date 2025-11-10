from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def iter_tables(xml: str) -> Iterator[str]:
    """Yield each table found in the XML document as a nicely formatted markdown string.

    This function parses JATS XML tables and handles multi-level headers with
    rowspan and colspan attributes, converting them into readable markdown tables.

    PMC and Europe PMC normalize to JATS.  Elsevier, Springer, and Wiley might not.

    Parameters
    ----------
    xml : str
        The full-text XML document from Europe PMC

    Yields
    ------
    str
        Markdown-formatted table string
    """
    root = ET.fromstring(xml)

    # Find all table-wrap elements (JATS XML format)
    for table_wrap in root.findall(".//table-wrap"):
        # Get table caption if available
        caption_elem = table_wrap.find(".//caption")
        caption = ""
        if caption_elem is not None:
            caption = "".join(caption_elem.itertext()).strip()

        # Get the actual table element
        table = table_wrap.find(".//table")
        if table is None:
            continue

        # Parse headers
        thead = table.find(".//thead")
        headers = _parse_thead(thead) if thead is not None else []

        # Parse body
        tbody = table.find(".//tbody")
        rows = _parse_tbody(tbody) if tbody is not None else []

        # Convert to markdown
        markdown = _to_markdown(caption, headers, rows)
        yield markdown


def _parse_thead(thead: ET.Element) -> list[str]:
    """Parse table header, handling multi-level headers with rowspan/colspan."""
    header_rows = thead.findall(".//tr")
    if not header_rows:
        return []

    # Build a grid to handle rowspan and colspan
    num_rows = len(header_rows)
    # Initialize grid with None values
    grid: list[list[str | None]] = [[] for _ in range(num_rows)]

    for row_idx, tr in enumerate(header_rows):
        col_idx = 0
        for th in tr.findall(".//th"):
            # Find next available column (skip cells occupied by previous rowspans)
            while col_idx < len(grid[row_idx]) and grid[row_idx][col_idx] is not None:
                col_idx += 1

            # Get cell text and clean it
            cell_text = "".join(th.itertext()).strip()

            # Get span attributes
            rowspan = int(th.get("rowspan", "1"))
            colspan = int(th.get("colspan", "1"))

            # Fill the grid accounting for rowspan and colspan
            for r_offset in range(rowspan):
                r = row_idx + r_offset
                if r >= num_rows:
                    break

                for c_offset in range(colspan):
                    target_col = col_idx + c_offset

                    # Extend row if needed
                    while len(grid[r]) <= target_col:
                        grid[r].append(None)

                    # Set the cell value
                    # For multi-row spans, replicate the text (it applies to all rows)
                    # For multi-col spans, only put text in first column,
                    # mark others as "" so they're treated as sub-columns
                    if c_offset == 0:
                        grid[r][target_col] = cell_text
                    else:
                        # Mark as empty string (not None) to indicate it's a
                        # continuation of a colspan
                        grid[r][target_col] = ""

            col_idx += colspan

    # Determine number of columns (final number of actual columns)
    num_cols = max(len(row) for row in grid) if grid else 0

    # Pad all rows to same length
    for row in grid:
        while len(row) < num_cols:
            row.append("")

    # Combine multi-row headers into single header row
    # For each column, concatenate unique non-empty values from all rows
    final_headers = []
    for col_idx in range(num_cols):
        header_parts = []
        prev_value = None
        for row in grid:
            cell = row[col_idx]

            # If cell is empty string (from colspan), look left to find parent header
            if cell == "":
                # Look for the most recent non-empty value to the left in this row
                for left_col in range(col_idx - 1, -1, -1):
                    left_cell = row[left_col]
                    if left_cell and left_cell.strip():
                        cell = left_cell
                        break

            # Only add if non-empty and different from previous value
            # (to avoid repeating the same value multiple times)
            if cell is not None and cell.strip() and cell != prev_value:
                header_parts.append(cell)
                prev_value = cell

        # Join with a separator for better LLM readability
        final_header = " > ".join(header_parts) if header_parts else ""
        final_headers.append(final_header)

    return final_headers


def _parse_tbody(tbody: ET.Element) -> list[list[str]]:
    """Parse table body rows."""
    rows = []
    for tr in tbody.findall(".//tr"):
        row = []
        for td in tr.findall(".//td"):
            cell_text = "".join(td.itertext()).strip()
            row.append(cell_text)
        rows.append(row)
    return rows


def _to_markdown(caption: str, headers: list[str], rows: list[list[str]]) -> str:
    """Convert table data to markdown format."""
    lines = []

    # Add caption if available
    if caption:
        lines.append(f"**{caption}**\n")

    # Create header row
    if headers:
        lines.append("| " + " | ".join(headers) + " |")
        # Add separator row
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Add data rows
    for row in rows:
        # Pad row to match header length if needed
        while len(row) < len(headers):
            row.append("")
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
