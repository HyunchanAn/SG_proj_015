import os
import glob
import re

base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))
readme_files = glob.glob(f"{base_dir}/SG_proj_*/README.md") + glob.glob(f"{base_dir}/SG_integration_*/README.md")

for r_file in readme_files:
    if not os.path.exists(r_file):
        continue
    with open(r_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    orig = content
    
    # 1. Update Badge
    content = content.replace("Hardware-RTX_5080-lightgrey", "Hardware-Apple_M2_Pro-lightgrey")
    
    # 2. Update Hardware list lines
    content = re.sub(r'AMD Ryzen 9 9900X.*?RTX 5080[^\n]*', 'MacBook Pro 14 (2023), Apple M2 Pro, 16GB Memory', content)
    
    if orig != content:
        with open(r_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {r_file}")
