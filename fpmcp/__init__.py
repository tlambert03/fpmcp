"""MCP server for fpbase research."""

from importlib.metadata import PackageNotFoundError, version

from fpmcp.fulltext import extract_tables, extract_text, get_fulltext

try:
    __version__ = version("fpmcp")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["extract_tables", "extract_text", "get_fulltext"]
