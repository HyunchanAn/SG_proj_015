#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
for d in "$BASE_DIR"/SG_proj_* "$BASE_DIR"/SG_integration_*; do
    cd "$d" || continue
    if [ -n "$(git status --porcelain)" ]; then
        echo "=== Committing in $d ==="
        git add README.md development_log.txt 2>/dev/null || true
        git commit -m "docs: update hardware specifications to Apple M2 Pro and update dev logs"
        git push origin main
    fi
done
