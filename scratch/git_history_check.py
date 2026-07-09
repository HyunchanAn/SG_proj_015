import subprocess
import os

repos = [
    r'e:\Github\SG_proj_001',
    r'e:\Github\SG_proj_002',
    r'e:\Github\SG_proj_003',
    r'e:\Github\SG_proj_004',
    r'e:\Github\SG_proj_006',
    r'e:\Github\SG_proj_007',
    r'e:\Github\SG_proj_011',
    r'e:\Github\SG_proj_012',
    r'e:\Github\SG_proj_014',
    r'e:\Github\SG_proj_015'
]

def check_history():
    out_path = r'E:\Github\SG_proj_015\scratch\git_history_report.txt'
    with open(out_path, 'w', encoding='utf-8') as report:
        for repo in repos:
            report.write(f"\n=========================================\n")
            report.write(f"Repo: {repo}\n")
            report.write(f"=========================================\n")
            
            # Get git commits for development_log.txt
            try:
                res = subprocess.run(
                    ['git', 'log', '--format=%H|%s|%an|%ad', 'development_log.txt'],
                    cwd=repo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                stdout_str = res.stdout.decode('utf-8', errors='replace')
                commits = [line.split('|') for line in stdout_str.strip().split('\n') if line.strip()]
            except Exception as e:
                report.write(f"Error getting git log: {e}\n")
                continue
                
            report.write(f"Found {len(commits)} commits for development_log.txt\n")
            for commit in commits[:6]:
                if len(commit) < 2:
                    continue
                c_hash = commit[0]
                c_msg = commit[1]
                
                # Get file content at this commit
                try:
                    res_show = subprocess.run(
                        ['git', 'show', f'{c_hash}:development_log.txt'],
                        cwd=repo,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    content_bytes = res_show.stdout
                except Exception as e:
                    report.write(f"  Commit {c_hash[:8]} ({c_msg}): Failed to git show: {e}\n")
                    continue
                
                # Check different decodings
                # Try UTF-8 first
                try:
                    text_utf8 = content_bytes.decode('utf-8')
                    repl_utf8 = text_utf8.count('\uFFFD')
                    has_decode_err = False
                except UnicodeDecodeError:
                    text_utf8 = None
                    repl_utf8 = -1
                    has_decode_err = True
                    
                # Try CP949
                try:
                    text_cp949 = content_bytes.decode('cp949')
                    repl_cp949 = text_cp949.count('\uFFFD')
                    has_cp949_err = False
                except UnicodeDecodeError:
                    text_cp949 = None
                    repl_cp949 = -1
                    has_cp949_err = True
                    
                report.write(f"  Commit {c_hash[:8]} ({c_msg}):\n")
                report.write(f"    UTF-8: DecodeErr={has_decode_err}, ReplacementCount={repl_utf8}\n")
                report.write(f"    CP949: DecodeErr={has_cp949_err}, ReplacementCount={repl_cp949}\n")
                
                # Show first 3 lines of UTF-8 if decoded
                if text_utf8:
                    lines = text_utf8.split('\n')[:3]
                    report.write(f"    UTF-8 preview: {lines}\n")
                if text_cp949:
                    lines = text_cp949.split('\n')[:3]
                    report.write(f"    CP949 preview: {lines}\n")
                    
    print(f"Report written to {out_path}")

if __name__ == '__main__':
    check_history()
