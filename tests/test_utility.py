import tempfile
import shutil
from git import Repo
from ghmcp.utility import get_repo

def test_get_repo_valid_repo():
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    repo = get_repo(temp_dir)
    assert repo is not None
    shutil.rmtree(temp_dir)

def test_get_repo_invalid_path():
    repo = get_repo("/non/existent/path")
    assert repo is None

def test_get_repo_not_a_repo():
    temp_dir = tempfile.mkdtemp()
    repo = get_repo(temp_dir)
    assert repo is None
    shutil.rmtree(temp_dir)
