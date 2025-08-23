import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
from ghmcp.utility import get_repo

class TestGetRepo:
    """Tests for get_repo function."""

    def test_get_repo_with_valid_repository(self):
        """Test that get_repo returns a Repo object for valid Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize a real Git repository
            repo = Repo.init(temp_dir)

            # Test the get_repo function
            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            assert result.working_dir == os.path.abspath(temp_dir)

    def test_get_repo_with_nonexistent_path(self):
        """Test that get_repo returns None for non-existent path."""
        nonexistent_path = "/path/that/does/not/exist"

        result = get_repo(nonexistent_path)

        assert result is None

    def test_get_repo_with_empty_path(self):
        """Test that get_repo returns None for empty path."""
        result = get_repo("")
        assert result is None

        result = get_repo(None)
        assert result is None

    def test_get_repo_with_invalid_path_type(self):
        """Test that get_repo returns None for invalid path types."""
        result = get_repo(123)
        assert result is None

        result = get_repo(["/some/path"])
        assert result is None

        result = get_repo({"path": "/some/path"})
        assert result is None

    def test_get_repo_with_file_instead_of_directory(self):
        """Test that get_repo returns None when path is a file, not directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            result = get_repo(temp_file.name)
            assert result is None

    def test_get_repo_with_directory_not_git_repo(self):
        """Test that get_repo returns None for directory that's not a Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't initialize as Git repo
            result = get_repo(temp_dir)
            assert result is None

    def test_get_repo_with_bare_repository(self):
        """Test that get_repo handles bare repositories correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize a bare Git repository
            repo = Repo.init(temp_dir, bare=True)

            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            assert result.bare is True

    def test_get_repo_with_relative_path(self):
        """Test that get_repo handles relative paths correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize a Git repository
            Repo.init(temp_dir)

            # Change to parent directory and use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(os.path.dirname(temp_dir))
                relative_path = os.path.basename(temp_dir)

                result = get_repo(relative_path)

                assert result is not None
                assert isinstance(result, Repo)
                # Should convert to absolute path
                assert os.path.isabs(result.working_dir)
            finally:
                os.chdir(original_cwd)

    def test_get_repo_with_repository_with_commits(self):
        """Test get_repo with a repository that has commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize repository and make a commit
            repo = Repo.init(temp_dir)

            # Configure user for commit
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create a file and commit it
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            # Should have at least one commit
            commits = list(result.iter_commits())
            assert len(commits) >= 1

    def test_get_repo_with_repository_with_branches(self):
        """Test get_repo with a repository that has multiple branches."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize repository
            repo = Repo.init(temp_dir)

            # Configure user for commit
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create initial commit
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            repo.index.add([test_file])
            repo.index.commit("Initial commit")

            # Create a new branch
            repo.create_head("feature-branch")

            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            # Should have multiple heads
            assert len(result.heads) >= 2  # main/master + feature-branch

    def test_get_repo_with_repository_with_remotes(self):
        """Test get_repo with a repository that has remotes configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize repository
            repo = Repo.init(temp_dir)

            # Add a remote
            repo.create_remote("origin", "https://github.com/example/repo.git")

            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            # Should have remotes
            assert len(result.remotes) >= 1
            assert "origin" in [remote.name for remote in result.remotes]

    def test_get_repo_with_permission_error(self):
        """Test that get_repo handles permission errors gracefully."""
        with patch('git.Repo') as mock_repo:
            mock_repo.side_effect = PermissionError("Permission denied")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = get_repo(temp_dir)
                assert result is None

    def test_get_repo_with_invalid_git_repository_error(self):
        """Test that get_repo handles InvalidGitRepositoryError gracefully."""
        with patch('git.Repo') as mock_repo:
            mock_repo.side_effect = InvalidGitRepositoryError("Not a git repository")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = get_repo(temp_dir)
                assert result is None

    def test_get_repo_with_no_such_path_error(self):
        """Test that get_repo handles NoSuchPathError gracefully."""
        with patch('git.Repo') as mock_repo:
            mock_repo.side_effect = NoSuchPathError("Path not found")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = get_repo(temp_dir)
                assert result is None

    def test_get_repo_with_unexpected_error(self):
        """Test that get_repo handles unexpected errors gracefully."""
        with patch('git.Repo') as mock_repo:
            mock_repo.side_effect = RuntimeError("Unexpected error")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = get_repo(temp_dir)
                assert result is None

    def test_get_repo_logging_behavior(self):
        """Test that get_repo logs appropriate messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.init(temp_dir)

            with patch('ghmcp.utility.logger') as mock_logger:
                result = get_repo(temp_dir)

                assert result is not None
                # Verify that debug and info logging calls were made
                mock_logger.debug.assert_called()
                mock_logger.info.assert_called()

    def test_get_repo_with_detached_head(self):
        """Test get_repo with a repository in detached HEAD state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize repository and make commits
            repo = Repo.init(temp_dir)

            # Configure user for commit
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create multiple commits
            for i in range(2):
                test_file = os.path.join(temp_dir, f"test{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"test content {i}")

                repo.index.add([test_file])
                repo.index.commit(f"Commit {i}")

            # Get the first commit and checkout to create detached HEAD
            commits = list(repo.iter_commits())
            if len(commits) >= 2:
                repo.git.checkout(commits[-1].hexsha)  # Checkout first commit

            result = get_repo(temp_dir)

            assert result is not None
            assert isinstance(result, Repo)
            # The function should handle detached HEAD gracefully
