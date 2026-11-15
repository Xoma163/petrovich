#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

requirements_file="$(mktemp)"
trap 'rm -f "$requirements_file"' EXIT

# Export the committed lock, including the default dev group, without resolving new versions.
uv export --locked --no-emit-project --output-file "$requirements_file" --quiet

# These packages require source builds on supported Linux hosts. Keep the exception list explicit;
# all other dependencies must have wheels, and every artifact must match a hash from uv.lock.
uv pip sync --python .venv/bin/python --require-hashes \
  --only-binary :all: --no-binary crontab,yandex-music,psycopg2 \
  "$requirements_file"
