# fpmcp

[![License](https://img.shields.io/pypi/l/fpmcp.svg?color=green)](https://github.com/tlambert03/fpmcp/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fpmcp.svg?color=green)](https://pypi.org/project/fpmcp)
[![Python Version](https://img.shields.io/pypi/pyversions/fpmcp.svg?color=green)](https://python.org)
[![CI](https://github.com/tlambert03/fpmcp/actions/workflows/ci.yml/badge.svg)](https://github.com/tlambert03/fpmcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tlambert03/fpmcp/branch/main/graph/badge.svg)](https://codecov.io/gh/tlambert03/fpmcp)

MCP server for fpbase research

## Development

The easiest way to get started is to use the [github cli](https://cli.github.com)
and [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
gh repo fork tlambert03/fpmcp --clone
# or just
# gh repo clone tlambert03/fpmcp
cd fpmcp
uv sync
```

Run tests:

```sh
uv run pytest
```

Lint files:

```sh
uv run pre-commit run --all-files
```
