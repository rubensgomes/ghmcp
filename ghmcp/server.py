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
    """
    Indexes local Git repositories and provides metadata about them.

    This class takes a list of repository paths, validates them as Git repositories,
    and provides methods to extract useful information about each repository such as
    name, path, and available branches.

    Attributes:
        repo_paths (List[str]): List of filesystem paths to potential Git repositories.
        repos (List[Repo]): List of valid GitPython Repo objects found at the provided paths.

    Args:
        repo_paths (List[str]): List of filesystem paths to scan for Git repositories.

    Example:
        indexer = GitHubRepoIndexer(['/path/to/repo1', '/path/to/repo2'])
        libraries = indexer.list_libraries()
    """
    def __init__(self, repo_paths: List[str]):
        self.repo_paths = repo_paths
        self.repos = [get_repo(path) for path in repo_paths if get_repo(path)]

    def list_libraries(self):
        """
        Generate a list of library metadata for all indexed repositories.

        Extracts useful information from each valid Git repository including the
        repository name (based on directory name), full filesystem path, and
        available branches.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing repository metadata.
                Each dictionary contains:
                - 'name' (str): Repository name (basename of directory)
                - 'path' (str): Full filesystem path to repository
                - 'branches' (List[str]): List of branch names in the repository

        Example:
            [
                {
                    'name': 'my-project',
                    'path': '/Users/user/repos/my-project',
                    'branches': ['main', 'develop', 'feature-branch']
                }
            ]
        """
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
    """
    MCP (Model Context Protocol) server for indexing and querying GitHub repositories.

    This server extends the base MCP Server class to provide Git repository indexing
    capabilities. It uses GitHubRepoIndexer to scan local repositories and exposes
    methods that MCP clients can use to query repository information.

    Attributes:
        indexer (GitHubRepoIndexer): The repository indexer instance used to scan and catalog repositories.

    Args:
        repo_paths (List[str]): List of filesystem paths to Git repositories to index.
        name (str, optional): Name identifier for the MCP server. Defaults to "ghmcp-server".
        *args: Additional positional arguments passed to the base Server class.
        **kwargs: Additional keyword arguments passed to the base Server class.

    Example:
        server = MCPGitHubServer(['/path/to/repo1', '/path/to/repo2'], name="my-github-server")
        libraries = server.query_libraries()
    """
    def __init__(self, repo_paths: List[str], name: str = "ghmcp-server", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.indexer = GitHubRepoIndexer(repo_paths)

    def query_libraries(self):
        """
        Query and return metadata for all indexed Git repositories.

        This method delegates to the internal GitHubRepoIndexer to retrieve
        a list of repository metadata that can be consumed by MCP clients.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing repository metadata.
                Each dictionary contains:
                - 'name' (str): Repository name (basename of directory)
                - 'path' (str): Full filesystem path to repository
                - 'branches' (List[str]): List of branch names in the repository

        Example:
            server = MCPGitHubServer(['/path/to/repo'])
            libraries = server.query_libraries()
            # Returns: [{'name': 'repo', 'path': '/path/to/repo', 'branches': ['main']}]
        """
        return self.indexer.list_libraries()
