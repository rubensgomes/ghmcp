"""
server.py
---------
Implements an MCP server for indexing and querying GitHub repositories using GitPython.

Classes:
    GitHubRepoIndexer: Indexes local git repositories and provides library metadata.
    MCPGitHubServer: MCP server that exposes a query_libraries method for MCP clients.

Usage:
    Instantiate MCPGitHubServer with a list of local repo paths. Call query_libraries() to get indexed library info.
"""

from mcp.server import Server
from ghmcp.utility import get_repo
import os
from typing import List

class GitHubRepoIndexer:
    def __init__(self, repo_paths: List[str]):
        self.repo_paths = repo_paths
        self.repos = [get_repo(path) for path in repo_paths if get_repo(path)]

    def list_libraries(self):
        libraries = []
        for repo in self.repos:
            if repo:
                libraries.append({
                    'name': os.path.basename(repo.working_tree_dir),
                    'path': repo.working_tree_dir,
                    'branches': [b.name for b in repo.branches]
                })
        return libraries

class MCPGitHubServer(Server):
    def __init__(self, repo_paths: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indexer = GitHubRepoIndexer(repo_paths)

    def query_libraries(self):
        return self.indexer.list_libraries()
