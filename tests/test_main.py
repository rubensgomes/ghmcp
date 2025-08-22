import pytest
from unittest.mock import patch, MagicMock
from mcp.main import list_resources, read_resource, repo_cache
from pathlib import Path
import asyncio

@pytest.fixture(autouse=True)
def clear_cache():
    repo_cache.clear()

@pytest.mark.asyncio
async def test_list_resources_empty():
    resources = await list_resources()
    assert resources == []

@pytest.mark.asyncio
async def test_list_resources_with_repo():
    repo_cache["test-repo"] = Path("/tmp/test-repo")
    resources = await list_resources()
    assert resources[0]["name"] == "GitHub Repo: test-repo"
    assert resources[0]["uri"] == "repo://test-repo"

@pytest.mark.asyncio
async def test_read_resource_repo_root():
    repo_cache["test-repo"] = Path("/tmp/test-repo")
    result = await read_resource("repo://test-repo")
    assert "Repo root: test-repo" in result["contents"][0]["text"]

@pytest.mark.asyncio
async def test_read_resource_file_found(tmp_path):
    repo_cache["test-repo"] = tmp_path
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello world")
    uri = f"repo://test-repo/file.txt"
    result = await read_resource(uri)
    assert result["contents"][0]["text"] == "hello world"

@pytest.mark.asyncio
async def test_read_resource_file_not_found(tmp_path):
    repo_cache["test-repo"] = tmp_path
    uri = f"repo://test-repo/missing.txt"
    with pytest.raises(FileNotFoundError):
        await read_resource(uri)

@pytest.mark.asyncio
async def test_read_resource_repo_not_found():
    uri = "repo://notfound/file.txt"
    with pytest.raises(ValueError):
        await read_resource(uri)

