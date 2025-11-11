# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "fpmcp",
# ]
#
# [tool.uv.sources]
# fpmcp = { path = "." }
# ///

from fpmcp.server import mcp

mcp.run()
