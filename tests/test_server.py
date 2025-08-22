import tempfile
import shutil
from git import Repo
from ghmcp.server import MCPGitHubServer

def test_query_libraries_returns_repo_info():
    """
    Test that MCPGitHubServer returns correct info for a valid git repo.
    """
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    try:
        server = MCPGitHubServer([temp_dir], name="test-server")
        libs = server.query_libraries()
        assert isinstance(libs, list)
        assert len(libs) == 1
        assert libs[0]['name'] == temp_dir.split('/')[-1]
    finally:
        shutil.rmtree(temp_dir)

def test_query_libraries_empty():
    """
    Test that MCPGitHubServer returns an empty list for invalid repo paths.
    """
    server = MCPGitHubServer(['/non/existent/path'], name="test-server")
    libs = server.query_libraries()
    assert isinstance(libs, list)
    assert libs == []

def test_query_libraries_multiple_repos():
    """
    Test that MCPGitHubServer indexes multiple valid repos.
    """
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()
    Repo.init(temp_dir1)
    Repo.init(temp_dir2)
    try:
        server = MCPGitHubServer([temp_dir1, temp_dir2], name="test-server")
        libs = server.query_libraries()
        assert isinstance(libs, list)
        assert len(libs) == 2
        names = [lib['name'] for lib in libs]
        assert temp_dir1.split('/')[-1] in names
        assert temp_dir2.split('/')[-1] in names
    finally:
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)
