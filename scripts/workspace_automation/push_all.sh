#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
for d in "$BASE_DIR"/SG_proj_*; do
    cd "$d" || continue
    # Ignore test_out.log and refactor scripts
    echo "test_out.log" >> .gitignore
    echo "demo_ui/do_refactor*.py" >> .gitignore
    echo "demo_ui/find_indices.py" >> .gitignore
    echo "demo_ui/refactor.py" >> .gitignore
    
    if [ -n "$(git status --porcelain)" ]; then
        echo "=== Committing in $d ==="
        git add .
        git commit -m "chore: Mac migration fixes, UI refactoring, and E2E test stabilization"
        git push origin main
    fi
done
