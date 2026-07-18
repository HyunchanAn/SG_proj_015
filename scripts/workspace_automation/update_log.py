import os
import glob
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))
log_files = glob.glob(f"{base_dir}/SG_proj_*/development_log.txt") + glob.glob(f"{base_dir}/SG_integration_*/development_log.txt")

date_str = datetime.now().strftime("%Y-%m-%d")
log_entry = f"""
---
Date: {date_str}
Author: Antigravity

[Updates]
- Hardware Specs updated in README.md from RTX 5080/Windows to Apple M2 Pro/macOS.
- Completed all local E2E and unit tests on macOS successfully without abort traps.
- Verified GitHub Actions CI/CD workflows for the projects.
"""

for l_file in log_files:
    if os.path.exists(l_file):
        with open(l_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"Updated log in {l_file}")
