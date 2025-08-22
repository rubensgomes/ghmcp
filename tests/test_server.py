import tempfile
import shutil
from git import Repo
from ghmcp.server import MCPGitHubServer

def test_query_libraries_returns_repo_info():
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    server = MCPGitHubServer([temp_dir])
    libs = server.query_libraries()
    assert isinstance(libs, list)
    assert len(libs) == 1
    assert libs[0]['name'] == temp_dir.split('/')[-1]
    shutil.rmtree(temp_dir)

def test_query_libraries_empty():
    server = MCPGitHubServer(['/non/existent/path'])
    libs = server.query_libraries()
    assert libs == []

