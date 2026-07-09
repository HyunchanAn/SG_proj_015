import os
import re
import subprocess

repos = {
    r"e:\Github\SG_proj_001": "PolySim",
    r"e:\Github\SG_proj_002": "DeepDrop-SFE",
    r"e:\Github\SG_proj_003": "V-SAMS",
    r"e:\Github\SG_proj_004": "DB",
    r"e:\Github\SG_proj_006": "TransPolymer",
    r"e:\Github\SG_proj_007": "SG-TERRA",
    r"e:\Github\SG_proj_011": "Processability",
    r"e:\Github\SG_proj_012": "Adhesive Matcher",
    r"e:\Github\SG_proj_014": "Orchestrator",
    r"e:\Github\SG_proj_015": "Integrated Log"
}

def restore_logs():
    print("Restoring development_log.txt files in all repos to clean git state...")
    for repo in repos.keys():
        subprocess.run(["git", "checkout", "--", "development_log.txt"], cwd=repo)
    print("Restoration complete.")

def parse_log_strict(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    
    entries = []
    current_header = None
    current_content = []
    
    # Regex to match YYYY-MM-DD or YYYY-MM-DD HH:MM:SS or YYYY-MM-DD HH:MM
    date_regex = r"^(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)(?:\s+(.*))?$"
    
    for line in lines:
        stripped = line.strip()
        # Skip top level file title
        if stripped.startswith("# ") and not stripped.startswith("##"):
            continue
            
        is_header = False
        matched_time = ""
        remaining_text = ""
        
        # Check if line matches header pattern 1: ## [DATE] or ## DATE
        m1 = re.match(r"^##\s*\[?(.*?)\]?$", stripped)
        if m1:
            header_candidate = m1.group(1).strip()
            # Verify it matches date regex
            m_date = re.match(date_regex, header_candidate)
            if m_date:
                is_header = True
                matched_time = m_date.group(1).strip()
                if m_date.group(2):
                    remaining_text = m_date.group(2).strip()
                    
        # Check if line matches header pattern 2: [DATE]
        if not is_header:
            m2 = re.match(r"^\[(.*?)\]\s*(.*)$", stripped)
            if m2:
                header_candidate = m2.group(1).strip()
                m_date = re.match(date_regex, header_candidate)
                if m_date:
                    is_header = True
                    matched_time = m_date.group(1).strip()
                    # Remaining text can be on the same line after the bracket
                    rem = m2.group(2).strip() if m2.group(2) else ""
                    # Also include any date regex extra group
                    if m_date.group(2):
                        rem = (m_date.group(2).strip() + " " + rem).strip()
                    remaining_text = rem
                    
        # Check if line matches header pattern 3: Date: DATE
        if not is_header:
            m3 = re.match(r"^Date:\s*(.*?)$", stripped, re.IGNORECASE)
            if m3:
                header_candidate = m3.group(1).strip()
                m_date = re.match(date_regex, header_candidate)
                if m_date:
                    is_header = True
                    matched_time = m_date.group(1).strip()
                    if m_date.group(2):
                        remaining_text = m_date.group(2).strip()
                        
        if is_header:
            if current_header or current_content:
                entries.append((current_header, current_content))
            current_header = matched_time
            current_content = []
            if remaining_text:
                current_content.append(remaining_text)
        else:
            if stripped or current_content:
                current_content.append(line)
                
    if current_header or current_content:
        entries.append((current_header, current_content))
        
    return entries

def unify_log_strict(repo_path, module_name):
    filepath = os.path.join(repo_path, "development_log.txt")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    print(f"\nProcessing {filepath}...")
    entries = parse_log_strict(filepath)
    
    seen_entries = []
    deduped_entries = []
    
    for header, content_lines in entries:
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()
        content_str = "\n".join(content_lines).strip()
        
        entry_key = (header, content_str)
        if entry_key in seen_entries:
            print(f"  Removing duplicate entry under: {header}")
            continue
            
        if content_str and content_str in [x[1] for x in seen_entries] and len(content_str) > 20:
             print(f"  Removing duplicate content block under: {header}")
             continue
             
        seen_entries.append(entry_key)
        deduped_entries.append((header, content_lines))
        
    repo_name = os.path.basename(repo_path)
    new_content = []
    new_content.append(f"# Development Log - {repo_name} ({module_name})")
    new_content.append("")
    
    for header, content_lines in deduped_entries:
        if not header:
            header = "Legacy Entry"
            
        clean_header = header
        if not clean_header.startswith("["):
            clean_header = f"[{clean_header}]"
            
        new_content.append(f"## {clean_header}")
        new_content.extend(content_lines)
        new_content.append("")
        
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(new_content))
    print(f"  Successfully unified: {filepath}")

if __name__ == "__main__":
    restore_logs()
    for repo, mod in repos.items():
        unify_log_strict(repo, mod)
