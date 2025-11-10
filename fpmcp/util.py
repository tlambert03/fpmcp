from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Normalize multiple whitespace characters (spaces, newlines, tabs) into single space
_WHITESPACE_RE = re.compile(r"\s+")

# Match inline legend format: "aText for a.bText for b" where each marker is
# lowercase letter followed by uppercase text, separated by periods
_INLINE_LEGEND_RE = re.compile(r"([a-z])([A-Z].*?)(?=\.\s*[a-z][A-Z]|$)")

# Match legend marker at start: 1-2 lowercase letters followed by text
_LEGEND_MARKER_RE = re.compile(r"^([a-z]{1,2})(.+)$")


def iter_tables(xml: str) -> Iterator[str]:
    """Parse JATS XML tables to markdown, handling rowspan/colspan.

    This function parses JATS XML tables and handles multi-level headers with
    rowspan and colspan attributes, converting them into readable markdown tables.

    PMC and Europe PMC normalize to JATS.  Elsevier, Springer, and Wiley might not.
    """
    root = ET.fromstring(xml)
    for table_wrap in root.findall(".//table-wrap"):
        elem = table_wrap.find(".//label")
        label = "".join(elem.itertext()).strip() if elem is not None else ""

        elem = table_wrap.find(".//caption")
        caption = "".join(elem.itertext()).strip() if elem is not None else ""

        elem = table_wrap.find(".//table-wrap-foot")
        legend = "".join(elem.itertext()).strip() if elem is not None else ""

        if (table := table_wrap.find(".//table")) is None:
            continue

        thead = table.find(".//thead")
        headers = _parse_thead(thead) if thead is not None else []
        tbody = table.find(".//tbody")
        rows = _parse_tbody(tbody) if tbody is not None else []

        yield _to_markdown(label, caption, legend, headers, rows)


def _get_cell_text(elem: ET.Element) -> str:
    """Extract text from cell using semantic XML structure.

    Based on XML structure, not heuristics:
    - <sup><xref>...</xref></sup> → citation reference, REMOVE
    - <sup>a</sup> → footnote marker, add SPACE before
    - <sup>3</sup>, <sup>-1</sup> → exponent, convert to ^ notation
    - <sub>f</sub> → subscript, keep inline (or could use _ notation)
    """
    parts = []
    if elem.text:
        parts.append(elem.text)

    for child in elem:
        if child.tag == "xref":
            if child.tail:
                parts.append(child.tail)
            continue

        if child.tag in ("sup", "sub"):
            if child.find(".//xref") is not None:
                if child.tail:
                    parts.append(child.tail)
                continue

            child_text = "".join(child.itertext()).strip()
            if child_text.isalpha() and len(child_text) <= 2:
                parts.append(f" {child_text}")
            elif child_text:
                prefix = "^" if child.tag == "sup" else "_"
                parts.append(f"{prefix}{child_text}")
            if child.tail:
                parts.append(child.tail)
            continue

        parts.append(_get_cell_text(child))
        if child.tail:
            parts.append(child.tail)

    return _WHITESPACE_RE.sub(" ", "".join(parts)).strip()


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

            cell_text = _get_cell_text(th)
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
        [_get_cell_text(td) for td in tr.findall(".//td")]
        for tr in tbody.findall(".//tr")
    ]


def _format_legend(legend: str) -> str:
    """Format legend as bulleted list."""
    inline_matches = _INLINE_LEGEND_RE.findall(legend)
    if inline_matches and len(inline_matches) > 2:
        items = [
            f"- {m}: {t.strip().rstrip('.')}"
            for m, t in inline_matches
            if t.strip().rstrip(".")
        ]
        if items:
            return "\n".join(items)

    parts = [p.strip() for p in legend.split(";") if p.strip()]
    items = []
    for part in parts:
        if match := _LEGEND_MARKER_RE.match(part):
            items.append(f"- {match[1]}: {match[2].strip()}")
        else:
            items.append(f"- {part}")
    return "\n".join(items) if items else legend


def _replace_common_unicode(text: str) -> str:
    """Replace common Unicode characters with ASCII equivalents."""
    replacements = {
        "\u2009": " "  # Thin space
    }
    for uni_char, ascii_equiv in replacements.items():
        text = text.replace(uni_char, ascii_equiv)
    return text


def _to_markdown(
    label: str, caption: str, legend: str, headers: list[str], rows: list[list[str]]
) -> str:
    """Convert table data to markdown format."""
    lines = []

    # Add label and caption as title
    if label and caption:
        lines.append(f"**{label}: {caption}**\n")
    elif caption:
        lines.append(f"**{caption}**\n")
    elif label:
        lines.append(f"**{label}**\n")

    # Add table headers and data
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

    # Add legend/footnotes at the end
    if legend:
        lines.append("\n**Legend:**")
        lines.append(_format_legend(legend))

    return "\n".join(map(_replace_common_unicode, lines))
