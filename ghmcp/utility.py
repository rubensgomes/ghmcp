import git
from pathlib import Path
import tempfile

# Where repos will be cloned locally
CLONE_DIR = Path(tempfile.gettempdir()) / "github_repos"
CLONE_DIR.mkdir(parents=True, exist_ok=True)

# Keep a cache of repo paths
repo_cache = {}

# Utility: clone or update a repo
def get_repo(repo_url: str) -> Path:
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = CLONE_DIR / repo_name

    if repo_name not in repo_cache:
        if not repo_path.exists():
            git.Repo.clone_from(repo_url, repo_path)
        else:
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
        repo_cache[repo_name] = repo_path

    return repo_cache[repo_name]
