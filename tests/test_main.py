import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from git import Repo
from ghmcp.main import start_server, stop_server
from ghmcp.server import MCPGitHubServer

def test_start_server_with_valid_repos():
    """
    Test that start_server correctly initializes with valid repositories.
    """
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    try:
        server = start_server([temp_dir], name="test-server")
        assert isinstance(server, MCPGitHubServer)
        libs = server.query_libraries()
        assert len(libs) == 1
        assert libs[0]['name'] == temp_dir.split('/')[-1]
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir)

def test_start_server_with_invalid_repos():
    """
    Test that start_server raises RuntimeError when no valid repositories are found.
    """
    with pytest.raises(RuntimeError, match="Server startup failed"):
        start_server(['/non/existent/path'])

def test_stop_server_with_none():
    """
    Test that stop_server handles None input gracefully.
    """
    # Should not raise an exception
    stop_server(None)

def test_start_server_with_multiple_repos():
    """
    Test that start_server works with multiple valid repositories.
    """
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()
    Repo.init(temp_dir1)
    Repo.init(temp_dir2)
    try:
        server = start_server([temp_dir1, temp_dir2], name="multi-test-server")
        libs = server.query_libraries()
        assert len(libs) == 2
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)

@patch('ghmcp.main.signal.signal')
def test_start_server_sets_signal_handlers(mock_signal):
    """
    Test that start_server sets up signal handlers.
    """
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    try:
        server = start_server([temp_dir])
        # Verify signal handlers were set
        assert mock_signal.call_count >= 2  # SIGINT and SIGTERM
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir)
