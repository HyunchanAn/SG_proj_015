import os

files_to_recover = [
    r"e:\Github\SG_proj_002\development_log.txt",
    r"e:\Github\SG_proj_004\development_log.txt",
    r"e:\Github\SG_proj_007\development_log.txt",
    r"e:\Github\SG_proj_011\development_log.txt",
    r"e:\Github\SG_proj_012\development_log.txt"
]

def recover_file(path):
    print(f"Processing: {path}")
    if not os.path.exists(path):
        print(f"Skipping (does not exist): {path}")
        return

    # Read binary bytes
    with open(path, "rb") as f:
        binary_data = f.read()

    # Split into lines
    lines = binary_data.split(b"\n")
    decoded_lines = []

    for i, line in enumerate(lines):
        cleaned_line = line.rstrip(b"\r")
        
        try:
            # 1. Try UTF-8
            decoded = cleaned_line.decode("utf-8")
        except UnicodeDecodeError:
            try:
                # 2. Try CP949 (Korean Windows encoding)
                decoded = cleaned_line.decode("cp949")
            except UnicodeDecodeError:
                # 3. Fallback with replacement
                decoded = cleaned_line.decode("utf-8", errors="replace")
                print(f"  Line {i+1} decoded with replacement")

        decoded_lines.append(decoded)

    # Write back as clean UTF-8
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(decoded_lines))
    print(f"  Successfully recovered and saved as UTF-8: {path}")

def verify_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read()
        print(f"Verification PASSED: {path} is readable in UTF-8")
        return True
    except Exception as e:
        print(f"Verification FAILED: {path} - {e}")
        return False

if __name__ == "__main__":
    for p in files_to_recover:
        recover_file(p)
        verify_file(p)
