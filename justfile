serve:
    fastmcp run  # uses config at fastmcp.json

test:
    uv run pytest

genmodel-europepmc-search:
    #!/usr/bin/env bash
    set -euo pipefail
    # Generate models from diverse sample
    curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=cancer%20OR%20malaria%20OR%20covid&format=json&resultType=core&pageSize=100" | \
    uv run datamodel-codegen \
        --input-file-type json \
        --output fpmcp/europmc_models.py \
        --output-model-type pydantic_v2.BaseModel \
        --use-standard-collections \
        --use-union-operator \
        --target-python-version 3.12 \
        --field-constraints \
        --allow-population-by-field-name \
        --use-default
    # Fix pagination fields that should be optional
    sed -i '' 's/nextCursorMark: str$/nextCursorMark: str | None = None/' fpmcp/europmc_models.py
    sed -i '' 's/nextPageUrl: str$/nextPageUrl: str | None = None/' fpmcp/europmc_models.py
    ruff format fpmcp/europmc_models.py
