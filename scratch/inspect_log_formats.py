import os

repositories = [
    r"e:\Github\SG_proj_001",
    r"e:\Github\SG_proj_002",
    r"e:\Github\SG_proj_003",
    r"e:\Github\SG_proj_004",
    r"e:\Github\SG_proj_006",
    r"e:\Github\SG_proj_007",
    r"e:\Github\SG_proj_011",
    r"e:\Github\SG_proj_012",
    r"e:\Github\SG_proj_014",
    r"e:\Github\SG_proj_015"
]

def check_log_formats():
    for repo in repositories:
        log_path = os.path.join(repo, "development_log.txt")
        if os.path.exists(log_path):
            print(f"\n=== {log_path} ===")
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # Print first 10 lines and last 10 lines
                print(f"Total lines: {len(lines)}")
                print("--- Head (First 5 lines) ---")
                for line in lines[:5]:
                    print(repr(line))
                print("--- Tail (Last 8 lines) ---")
                for line in lines[-8:]:
                    print(repr(line))
            except Exception as e:
                print(f"Error reading {log_path}: {e}")
        else:
            print(f"\n=== {log_path} (DOES NOT EXIST) ===")

if __name__ == "__main__":
    check_log_formats()
