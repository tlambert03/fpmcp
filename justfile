serve:
    fastmcp run  # uses config at fastmcp.json

test:
    uv run pytest

genmodel-europepmc-search:
    #!/usr/bin/env bash
    set -euo pipefail
    # Generate models from diverse sample
    DEST=fpmcp/europmc/models.py
    curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=cancer%20OR%20malaria%20OR%20covid&format=json&resultType=core&pageSize=100" | \
    uv run datamodel-codegen \
        --input-file-type json \
        --output $DEST \
        --output-model-type pydantic_v2.BaseModel \
        --target-python-version 3.12 
    # Fix pagination fields that should be optional
    sed -i '' 's/nextCursorMark: str$/nextCursorMark: str | None = None/' $DEST
    sed -i '' 's/nextPageUrl: str$/nextPageUrl: str | None = None/' $DEST
    ruff format $DEST
    ruff check --fix-only $DEST
