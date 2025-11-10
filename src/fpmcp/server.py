"""Main server module for FastMCP."""

from fastmcp import FastMCP

mcp = FastMCP("FP Research Server")


@mcp.tool
def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"
