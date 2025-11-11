# An mcp server for doing research on fluorescent proteins

This repo contains code for an mcp server that can assist FPbase
curators and moderators in verifying the data in FPbase.  It can:

- associate a protein name with literature references
- look up full text articles from literature references
- extract tables from full text articles
- search for specific terms in full text articles

## Bash commands for development

- `uv sync` - setup the repo for development
- `uv run pytest` - run the tests
- `prek -a` - run linting and formatting checks (will fix some issues automatically)
- `uv run fastmcp run` - run the mcp server locally
