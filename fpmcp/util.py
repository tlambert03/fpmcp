from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def iter_tables(xml: str) -> Iterator[str]:
    """Parse JATS XML tables to markdown, handling rowspan/colspan.

    This function parses JATS XML tables and handles multi-level headers with
    rowspan and colspan attributes, converting them into readable markdown tables.

    PMC and Europe PMC normalize to JATS.  Elsevier, Springer, and Wiley might not.
    """
    root = ET.fromstring(xml)
    for table_wrap in root.findall(".//table-wrap"):
        elem = table_wrap.find(".//caption")
        caption = "".join(elem.itertext()).strip() if elem is not None else ""

        if (table := table_wrap.find(".//table")) is None:
            continue

        thead = table.find(".//thead")
        headers = _parse_thead(thead) if thead is not None else []
        tbody = table.find(".//tbody")
        rows = _parse_tbody(tbody) if tbody is not None else []

        yield _to_markdown(caption, headers, rows)


def _parse_thead(thead: ET.Element) -> list[str]:
    """Parse table header with rowspan/colspan into flattened list."""
    if not (header_rows := thead.findall(".//tr")):
        return []

    num_rows = len(header_rows)
    grid: list[list[str | None]] = [[] for _ in range(num_rows)]

    for row_idx, tr in enumerate(header_rows):
        col_idx = 0
        for th in tr.findall(".//th"):
            while col_idx < len(grid[row_idx]) and grid[row_idx][col_idx] is not None:
                col_idx += 1

            cell_text = "".join(th.itertext()).strip()
            rowspan = int(th.get("rowspan", "1"))
            colspan = int(th.get("colspan", "1"))

            for r_offset in range(rowspan):
                if (r := row_idx + r_offset) >= num_rows:
                    break
                for c_offset in range(colspan):
                    target_col = col_idx + c_offset
                    while len(grid[r]) <= target_col:
                        grid[r].append(None)
                    grid[r][target_col] = cell_text if c_offset == 0 else ""

            col_idx += colspan

    num_cols = max(len(row) for row in grid) if grid else 0
    for row in grid:
        while len(row) < num_cols:
            row.append("")

    final_headers = []
    for col_idx in range(num_cols):
        header_parts = []
        prev_value = None
        for row in grid:
            cell = row[col_idx]
            if cell == "":
                for left_col in range(col_idx - 1, -1, -1):
                    if (left_cell := row[left_col]) and left_cell.strip():
                        cell = left_cell
                        break
            if cell and cell.strip() and cell != prev_value:
                header_parts.append(cell)
                prev_value = cell
        final_headers.append(" > ".join(header_parts) if header_parts else "")

    return final_headers


def _parse_tbody(tbody: ET.Element) -> list[list[str]]:
    """Parse table body rows."""
    return [
        ["".join(td.itertext()).strip() for td in tr.findall(".//td")]
        for tr in tbody.findall(".//tr")
    ]


def _to_markdown(caption: str, headers: list[str], rows: list[list[str]]) -> str:
    """Convert table data to markdown format."""
    lines = [f"**{caption}**\n"] if caption else []

    if headers:
        lines.extend(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
            ]
        )

    for row in rows:
        row.extend([""] * (len(headers) - len(row)))
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
