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
import logging
from typing import List, Dict, Any, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)

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
        logger.info(f"Initializing GitHubRepoIndexer with {len(repo_paths)} repository paths")
        logger.debug(f"Repository paths: {repo_paths}")

        self.repo_paths = repo_paths
        self.repos = []

        # Index repositories and log results
        for path in repo_paths:
            logger.debug(f"Attempting to get repository from path: {path}")
            repo = get_repo(path)
            if repo:
                self.repos.append(repo)
                logger.info(f"Successfully indexed repository: {path}")
            else:
                logger.warning(f"Failed to index repository at path: {path}")

        logger.info(f"GitHubRepoIndexer initialized with {len(self.repos)} valid repositories out of {len(repo_paths)} paths")

    def list_libraries(self) -> List[Dict[str, Any]]:
        """
        Generate a list of library metadata for all indexed repositories.

        Extracts useful information from each valid Git repository including the
        repository name (based on directory name), full filesystem path, and
        available branches.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing repository metadata.
            Each dictionary contains:
                - 'name': Repository name (directory name)
                - 'path': Full filesystem path to repository
                - 'branches': List of available branch names

        Example:
            [
                {
                    'name': 'my-project',
                    'path': '/Users/user/repos/my-project',
                    'branches': ['main', 'develop', 'feature-x']
                }
            ]
        """
        logger.info(f"Generating library list for {len(self.repos)} repositories")
        libraries = []

        for repo in self.repos:
            try:
                logger.debug(f"Processing repository: {repo.working_dir}")

                # Extract repository name from directory path
                repo_name = os.path.basename(repo.working_dir)
                logger.debug(f"Repository name: {repo_name}")

                # Get available branches
                branches = [ref.name.replace('origin/', '') for ref in repo.refs if 'origin/' in ref.name]
                if not branches:
                    # Fallback to local branches if no remote branches found
                    branches = [head.name for head in repo.heads]

                logger.debug(f"Found {len(branches)} branches for {repo_name}: {branches}")

                library_info = {
                    'name': repo_name,
                    'path': repo.working_dir,
                    'branches': branches
                }

                libraries.append(library_info)
                logger.info(f"Added library info for repository: {repo_name}")

            except Exception as e:
                logger.error(f"Error processing repository {repo.working_dir}: {e}")
                continue

        logger.info(f"Successfully generated library list with {len(libraries)} entries")
        return libraries


class MCPGitHubServer(Server):
    """
    MCP server implementation for GitHub repository indexing and querying.

    This server extends the base MCP Server class to provide GitHub repository
    indexing capabilities. It uses GitHubRepoIndexer to scan and index local
    Git repositories, making their metadata available to MCP clients.

    Attributes:
        indexer (GitHubRepoIndexer): Repository indexer instance.
        name (str): Server name identifier.

    Args:
        repo_paths (List[str]): List of filesystem paths to Git repositories to index.
        name (str, optional): Server name identifier. Defaults to "ghmcp-server".
        *args: Additional arguments passed to parent Server class.
        **kwargs: Additional keyword arguments passed to parent Server class.

    Example:
        server = MCPGitHubServer(['/path/to/repo1', '/path/to/repo2'], name="my-server")
        libraries = server.query_libraries()
    """
    def __init__(self, repo_paths: List[str], name: str = "ghmcp-server", *args, **kwargs):
        logger.info(f"Initializing MCPGitHubServer '{name}' with {len(repo_paths)} repository paths")
        logger.debug(f"Server args: {args}, kwargs: {kwargs}")

        super().__init__(*args, **kwargs)
        self.name = name

        try:
            logger.info("Creating GitHubRepoIndexer instance")
            self.indexer = GitHubRepoIndexer(repo_paths)
            logger.info(f"MCPGitHubServer '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCPGitHubServer '{name}': {e}")
            raise

    def query_libraries(self) -> List[Dict[str, Any]]:
        """
        Query and return metadata for all indexed libraries.

        Delegates to the GitHubRepoIndexer to generate a list of library metadata
        for all successfully indexed Git repositories.

        Returns:
            List[Dict[str, Any]]: List of library metadata dictionaries.
            Each dictionary contains repository name, path, and available branches.

        Raises:
            RuntimeError: If the indexer is not properly initialized.

        Example:
            server = MCPGitHubServer(['/path/to/repo'])
            libraries = server.query_libraries()
            print(f"Found {len(libraries)} libraries")
        """
        logger.info(f"Querying libraries from MCPGitHubServer '{self.name}'")

        if not hasattr(self, 'indexer') or self.indexer is None:
            error_msg = "GitHubRepoIndexer is not initialized"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            libraries = self.indexer.list_libraries()
            logger.info(f"Successfully queried {len(libraries)} libraries from server '{self.name}'")
            logger.debug(f"Library names: {[lib['name'] for lib in libraries]}")
            return libraries
        except Exception as e:
            logger.error(f"Error querying libraries from server '{self.name}': {e}")
            raise
