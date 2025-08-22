import pytest
from unittest.mock import patch, MagicMock
from mcp.utility import get_repo, repo_cache, CLONE_DIR
from pathlib import Path

TEST_URL = "https://github.com/example/test-repo.git"
REPO_NAME = "test-repo"
REPO_PATH = CLONE_DIR / REPO_NAME

@pytest.fixture(autouse=True)
def clear_cache():
    repo_cache.clear()
    if REPO_PATH.exists():
        # Remove the repo dir if it exists (cleanup)
        import shutil
        shutil.rmtree(REPO_PATH)

@patch("git.Repo.clone_from")
@patch("git.Repo")
def test_get_repo_clones_if_not_exists(mock_repo, mock_clone_from):
    mock_clone_from.return_value = None
    mock_repo.return_value = MagicMock()
    result = get_repo(TEST_URL)
    assert result == REPO_PATH
    assert repo_cache[REPO_NAME] == REPO_PATH
    mock_clone_from.assert_called_once_with(TEST_URL, REPO_PATH)

@patch("git.Repo.clone_from")
@patch("git.Repo")
def test_get_repo_uses_cache(mock_repo, mock_clone_from):
    repo_cache[REPO_NAME] = REPO_PATH
    result = get_repo(TEST_URL)
    assert result == REPO_PATH
    mock_clone_from.assert_not_called()
    mock_repo.assert_not_called()

@patch("git.Repo.clone_from")
@patch("git.Repo")
def test_get_repo_pulls_if_exists(mock_repo, mock_clone_from):
    # Simulate repo dir exists but not in cache
    REPO_PATH.mkdir(parents=True, exist_ok=True)
    mock_repo_instance = MagicMock()
    mock_repo.return_value = mock_repo_instance
    result = get_repo(TEST_URL)
    assert result == REPO_PATH
    mock_repo_instance.remotes.origin.pull.assert_called_once()
    mock_clone_from.assert_not_called()

