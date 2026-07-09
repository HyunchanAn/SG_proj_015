import os
import subprocess

repos_to_commit = [
    r"e:\Github\SG_proj_002",
    r"e:\Github\SG_proj_004",
    r"e:\Github\SG_proj_007",
    r"e:\Github\SG_proj_011",
    r"e:\Github\SG_proj_012",
    r"e:\Github\SG_proj_015"
]

def run_git(cwd, args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

if __name__ == "__main__":
    for repo in repos_to_commit:
        print(f"\n=========================================")
        print(f"Git operations for {repo}")
        print(f"=========================================")
        
        # Check status
        ok, status_out = run_git(repo, ["status", "--porcelain"])
        if not ok:
            print(f"Failed to run git status: {status_out}")
            continue
            
        if not status_out.strip():
            print("No changes to commit.")
            continue
            
        print("Changes detected:")
        print(status_out)
        
        # Git add
        ok, add_out = run_git(repo, ["add", "."])
        if not ok:
            print(f"Failed git add: {add_out}")
            continue
            
        # Git commit
        ok, commit_out = run_git(repo, ["commit", "-m", "docs: recover Korean encoding in development_log to UTF-8"])
        if not ok:
            print(f"Failed git commit: {commit_out}")
            continue
        print(commit_out)
        
        # Get current branch
        ok, branch_out = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
        branch_name = branch_out.strip() if ok else "main"
        
        # Git push
        print(f"Pushing to origin {branch_name}...")
        ok, push_out = run_git(repo, ["push", "origin", branch_name])
        if not ok:
            print(f"Failed git push: {push_out}")
        else:
            print("Successfully pushed changes.")
