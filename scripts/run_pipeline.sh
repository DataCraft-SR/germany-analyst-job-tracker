#!/usr/bin/env bash
# Full daily pipeline: extract -> transform (dbt) -> publish (docs/data.json + README).
# Run from anywhere; paths resolve to the repo root.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
mkdir -p build

if [[ "${SKIP_FETCH:-0}" != "1" ]]; then
  python -m tracker.fetch
fi

rm -f build/warehouse.duckdb   # the warehouse is rebuilt from data/ every run
dbt build --project-dir dbt --profiles-dir dbt
python -m tracker.build_site
