import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from git import Repo
from ghmcp.server import GitHubRepoIndexer, MCPGitHubServer, run_stdio_server

class TestGitHubRepoIndexer:
    """Tests for GitHubRepoIndexer class."""

    def test_init_with_valid_repository_paths(self):
        """Test that GitHubRepoIndexer initializes correctly with valid paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock repository
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                indexer = GitHubRepoIndexer([repo_path])

                assert indexer.repo_paths == [repo_path]
                assert len(indexer.repos) == 1
                assert indexer.repos[0] == mock_repo
                mock_get_repo.assert_called_once_with(repo_path)

    def test_init_with_nonexistent_path(self):
        """Test that GitHubRepoIndexer handles non-existent paths gracefully."""
        nonexistent_path = "/path/that/does/not/exist"

        indexer = GitHubRepoIndexer([nonexistent_path])

        assert indexer.repo_paths == [nonexistent_path]
        assert len(indexer.repos) == 0

    def test_init_with_file_instead_of_directory(self):
        """Test that GitHubRepoIndexer handles file paths gracefully."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = temp_file.name

            indexer = GitHubRepoIndexer([file_path])

            assert indexer.repo_paths == [file_path]
            assert len(indexer.repos) == 0

    def test_init_with_invalid_repository(self):
        """Test that GitHubRepoIndexer handles invalid repositories gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that's not a git repository
            repo_path = os.path.join(temp_dir, "not_a_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_get_repo.return_value = None  # Simulate invalid repo

                indexer = GitHubRepoIndexer([repo_path])

                assert indexer.repo_paths == [repo_path]
                assert len(indexer.repos) == 0
                mock_get_repo.assert_called_once_with(repo_path)

    def test_init_with_mixed_valid_invalid_paths(self):
        """Test GitHubRepoIndexer with a mix of valid and invalid paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_path = os.path.join(temp_dir, "valid_repo")
            invalid_path = "/nonexistent/path"
            os.makedirs(valid_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = valid_path
                mock_get_repo.return_value = mock_repo

                indexer = GitHubRepoIndexer([valid_path, invalid_path])

                assert indexer.repo_paths == [valid_path, invalid_path]
                assert len(indexer.repos) == 1
                assert indexer.repos[0] == mock_repo


class TestMCPGitHubServer:
    """Tests for MCPGitHubServer class."""

    def test_init_with_valid_repo_paths(self):
        """Test that MCPGitHubServer initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                server = MCPGitHubServer([repo_path], name="test-server")

                assert server.name == "test-server"
                assert hasattr(server, 'indexer')
                assert isinstance(server.indexer, GitHubRepoIndexer)
                assert len(server.indexer.repos) == 1

    def test_init_without_repo_paths(self):
        """Test that MCPGitHubServer raises error with empty repo paths."""
        with pytest.raises(ValueError, match="At least one repository path must be provided"):
            MCPGitHubServer([])

    def test_init_with_invalid_name(self):
        """Test that MCPGitHubServer raises error with invalid name."""
        with pytest.raises(ValueError, match="Server name must be a non-empty string"):
            MCPGitHubServer(["/some/path"], name="")

        with pytest.raises(ValueError, match="Server name must be a non-empty string"):
            MCPGitHubServer(["/some/path"], name=None)

    def test_get_capabilities(self):
        """Test that get_capabilities returns correct capabilities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                server = MCPGitHubServer([repo_path])
                capabilities = server.get_capabilities()

                assert isinstance(capabilities, dict)
                assert "experimental" in capabilities
                assert capabilities["experimental"] == {}
                # Verify no tools capability since we removed tool support
                assert "tools" not in capabilities

    @pytest.mark.asyncio
    async def test_run_stdio_method_exists(self):
        """Test that run_stdio method exists and can be called."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                server = MCPGitHubServer([repo_path])

                # Test that the method exists and is callable
                assert hasattr(server, 'run_stdio')
                assert callable(server.run_stdio)

                # We can't easily test the full stdio functionality without
                # complex mocking, but we can verify the method exists


class TestRunStdioServer:
    """Tests for run_stdio_server function."""

    @pytest.mark.asyncio
    async def test_run_stdio_server_with_no_repos(self):
        """Test that run_stdio_server raises error when no valid repos found."""
        from ghmcp.server import run_stdio_server

        with patch('ghmcp.server.get_repo') as mock_get_repo:
            mock_get_repo.return_value = None  # No valid repos

            with pytest.raises(ValueError, match="No valid Git repositories found"):
                await run_stdio_server(["/nonexistent/path"])

    @pytest.mark.asyncio
    async def test_run_stdio_server_creation(self):
        """Test that run_stdio_server can create server successfully."""
        from ghmcp.server import run_stdio_server

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                # Mock the stdio server to avoid actually running it
                with patch('ghmcp.server.MCPGitHubServer.run_stdio') as mock_run_stdio:
                    mock_run_stdio.return_value = None

                    # This should not raise an error
                    await run_stdio_server([repo_path], name="test-server")

                    mock_run_stdio.assert_called_once()
