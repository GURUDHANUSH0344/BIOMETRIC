import os
from pathlib import Path
from dulwich.repo import Repo
from dulwich.porcelain import init, add, commit

repo_dir = Path("d:/bio").resolve()

# 1. Initialize Git repository
print(f"Initializing Git repository in {repo_dir}...")
if not (repo_dir / ".git").exists():
    repo = init(str(repo_dir))
else:
    repo = Repo(str(repo_dir))

# 2. Add all project files (ignoring venv, db, pycache)
print("Staging project files...")
ignore_dirs = {'venv', '.venv', '__pycache__', '.git', '.gemini'}
ignore_exts = {'.db', '.sqlite3', '.pyc', '.log'}

files_to_add = []
for root, dirs, files in os.walk(repo_dir):
    # Skip ignored directories
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for f in files:
        if any(f.endswith(ext) for ext in ignore_exts):
            continue
        rel_path = Path(root).joinpath(f).relative_to(repo_dir).as_posix()
        files_to_add.append(rel_path)

add(str(repo_dir), paths=files_to_add)

# 3. Create initial commit
print(f"Staged {len(files_to_add)} files. Creating initial commit...")
commit_sha = commit(
    str(repo_dir),
    message=b"Initial commit of biometric attendance project",
    committer=b"User <user@example.com>",
    author=b"User <user@example.com>"
)

print(f"🎉 Git repository initialized and initial commit created! Commit SHA: {commit_sha.decode('utf-8') if isinstance(commit_sha, bytes) else commit_sha}")
