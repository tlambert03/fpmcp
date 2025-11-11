"""MCP server for fpbase research."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fpmcp")
except PackageNotFoundError:
    __version__ = "uninstalled"


from fpmcp.article_id import ArticleIdentifier
from fpmcp.fulltext import extract_tables, extract_text, get_fulltext

__all__ = ["ArticleIdentifier", "extract_tables", "extract_text", "get_fulltext"]
