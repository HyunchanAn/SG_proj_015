import os
import glob

repositories = [
    r"e:\Github\SG_integration_step1",
    r"e:\Github\SG_integration_step2",
    r"e:\Github\SG_integration_step3",
    r"e:\Github\SG_proj_001",
    r"e:\Github\SG_proj_002",
    r"e:\Github\SG_proj_003",
    r"e:\Github\SG_proj_004",
    r"e:\Github\SG_proj_005",
    r"e:\Github\SG_proj_006",
    r"e:\Github\SG_proj_007",
    r"e:\Github\SG_proj_008",
    r"e:\Github\SG_proj_009",
    r"e:\Github\SG_proj_010",
    r"e:\Github\SG_proj_011",
    r"e:\Github\SG_proj_012",
    r"e:\Github\SG_proj_013",
    r"e:\Github\SG_proj_014",
    r"e:\Github\SG_proj_015"
]

def scan_files():
    target_files = []
    for repo in repositories:
        if not os.path.exists(repo):
            continue
        # Search recursively for .md and development_log
        for root, dirs, files in os.walk(repo):
            # Skip .git, .venv, etc.
            dirs[:] = [d for d in dirs if d not in ['.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.idea', '.vscode']]
            for file in files:
                filepath = os.path.join(root, file)
                if file.endswith('.md') or 'development_log' in file.lower():
                    target_files.append(filepath)
                    
    print(f"Found {len(target_files)} target files to check.")
    
    corrupted_files = []
    for filepath in target_files:
        has_error = False
        reason = ""
        
        # Try reading as binary
        try:
            with open(filepath, 'rb') as f:
                content_bytes = f.read()
        except Exception as e:
            print(f"Error reading binary {filepath}: {e}")
            continue
            
        # 1. Check if it decodes as UTF-8
        try:
            content_utf8 = content_bytes.decode('utf-8')
            # Check if it has replacement character (which suggests it was saved with replacement)
            if '\uFFFD' in content_utf8:
                has_error = True
                reason = "Contains replacement character (\\uFFFD / )"
        except UnicodeDecodeError as e:
            has_error = True
            reason = f"UnicodeDecodeError on UTF-8: {e}"
            
        if has_error:
            corrupted_files.append((filepath, reason, content_bytes))
            
    print(f"\nFound {len(corrupted_files)} files with potential encoding issues:")
    for filepath, reason, _ in corrupted_files:
        print(f"- {filepath}: {reason}")
        
    return corrupted_files

if __name__ == "__main__":
    scan_files()
