"""MCP server for fpbase research."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fpmcp")
except PackageNotFoundError:
    __version__ = "uninstalled"
