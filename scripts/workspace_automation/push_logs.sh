#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
for d in "$BASE_DIR"/SG_proj_* "$BASE_DIR"/SG_integration_*; do
    cd "$d" || continue
    if [ -n "$(git status --porcelain)" ]; then
        echo "=== Committing in $d ==="
        git add development_log.txt 2>/dev/null || true
        git commit -m "docs: fix language formatting in development_log.txt to Korean"
        git push origin main
    fi
done
