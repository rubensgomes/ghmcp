"""
server.py
---------
Implements a basic MCP server for indexing GitHub repositories using GitPython.

Classes:
    GitHubRepoIndexer: Indexes local git repositories.
    MCPGitHubServer: Basic MCP server without tool capabilities.

Usage:
    Instantiate MCPGitHubServer with a list of local repo paths to index repositories.
    For stdio mode: server.run_stdio() or use run_stdio_server() function.
"""

from mcp.server import Server
from ghmcp.utility import get_repo
import os
import os.path
import asyncio
import logging
from typing import List, Dict, Any, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)

class GitHubRepoIndexer:
    """
    Indexes local Git repositories.

    This class takes a list of repository paths, validates them as Git repositories,
    and stores the valid repositories for use by the MCP server. It performs
    repository discovery and validation during initialization.

    Attributes:
        repo_paths (List[str]): List of filesystem paths to potential Git repositories.
        repos (List[Repo]): List of valid GitPython Repo objects found at the provided paths.

    Args:
        repo_paths (List[str]): List of filesystem paths to scan for Git repositories.

    Example:
        indexer = GitHubRepoIndexer(['/path/to/repo1', '/path/to/repo2'])
        print(f"Found {len(indexer.repos)} valid repositories")
    """
    def __init__(self, repo_paths: List[str]):
        logger.info(f"Initializing GitHubRepoIndexer with {len(repo_paths)} repository paths")
        logger.debug(f"Repository paths: {repo_paths}")

        self.repo_paths = repo_paths
        self.repos = []

        # Index repositories and log results
        for i, path in enumerate(repo_paths, 1):
            logger.debug(f"Processing repository {i}/{len(repo_paths)}: {path}")

            if not os.path.exists(path):
                logger.warning(f"Path does not exist: {path}")
                continue

            if not os.path.isdir(path):
                logger.warning(f"Path is not a directory: {path}")
                continue

            logger.debug(f"Attempting to get repository from path: {path}")
            repo = get_repo(path)
            if repo:
                self.repos.append(repo)
                logger.info(f"Successfully indexed repository: {path}")
                logger.debug(f"Repository working directory: {repo.working_dir}")
            else:
                logger.warning(f"Failed to index repository at path: {path} (not a valid Git repository)")

        logger.info(f"GitHubRepoIndexer initialized with {len(self.repos)} valid repositories out of {len(repo_paths)} paths")

        if not self.repos:
            logger.warning("No valid Git repositories found in any of the provided paths")

class MCPGitHubServer(Server):
    """
    Basic MCP server implementation for GitHub repository indexing.

    This server extends the base MCP Server class to provide basic GitHub repository
    indexing capabilities without tool support. It uses GitHubRepoIndexer to scan
    and index local Git repositories.

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
    """
    def __init__(self, repo_paths: List[str], name: str = "ghmcp-server", *args, **kwargs):
        logger.info(f"Initializing MCPGitHubServer '{name}' with {len(repo_paths)} repository paths")
        logger.debug(f"Repository paths: {repo_paths}")
        logger.debug(f"Server args: {args}, kwargs: {kwargs}")

        # Validate inputs
        if not repo_paths:
            raise ValueError("At least one repository path must be provided")

        if not name or not isinstance(name, str):
            raise ValueError("Server name must be a non-empty string")

        try:
            # Pass the name to the parent Server class constructor
            logger.debug(f"Calling parent Server.__init__ with name='{name}'")
            super().__init__(name, *args, **kwargs)
            self.name = name
            logger.debug(f"Parent Server class initialized successfully")

            logger.info("Creating GitHubRepoIndexer instance")
            self.indexer = GitHubRepoIndexer(repo_paths)

            # Validate that indexer was created successfully
            if not hasattr(self, 'indexer') or self.indexer is None:
                raise RuntimeError("Failed to create GitHubRepoIndexer instance")

            logger.info(f"MCPGitHubServer '{name}' initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCPGitHubServer '{name}': {e}")
            logger.debug(f"MCPGitHubServer initialization error details:", exc_info=True)
            raise

    def get_capabilities(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Get the capabilities that this MCP server supports.

        This basic server implementation declares no tool capabilities.

        Args:
            *args: Additional positional arguments from MCP framework
            **kwargs: Additional keyword arguments from MCP framework

        Returns:
            Dict[str, Any]: Server capabilities configuration
        """
        logger.debug(f"Getting capabilities for MCPGitHubServer '{self.name}' with args: {args}, kwargs: {kwargs}")

        capabilities = {
            "experimental": {}  # Basic server with no tools
        }

        logger.info(f"Server '{self.name}' capabilities: {list(capabilities.keys())}")
        return capabilities

    async def run_stdio(self):
        """
        Run the MCP server in stdio mode.

        This method runs the server in stdio mode using the MCP stdio_server
        transport for proper communication via stdin/stdout.

        Example:
            server = MCPGitHubServer(['/path/to/repo'])
            await server.run_stdio()
        """
        logger.info(f"Starting MCPGitHubServer '{self.name}' in stdio mode")
        logger.debug(f"Server will communicate via stdin/stdout")
        try:
            from mcp.server.stdio import stdio_server

            # Use the stdio_server transport to run the server
            async with stdio_server() as (read_stream, write_stream):
                logger.debug("Stdio server transport established")

                # Create initialization options for the server
                initialization_options = self.create_initialization_options()

                # Run the server with stdio streams
                await self.run(
                    read_stream=read_stream,
                    write_stream=write_stream,
                    initialization_options=initialization_options
                )

        except KeyboardInterrupt:
            logger.info(f"Received keyboard interrupt, shutting down stdio server '{self.name}'")
        except Exception as e:
            logger.error(f"Error running server '{self.name}' in stdio mode: {e}")
            logger.debug(f"Server stdio error details:", exc_info=True)
            raise
        finally:
            logger.info(f"MCPGitHubServer '{self.name}' stdio mode stopped")


async def run_stdio_server(repo_paths: List[str], name: str = "ghmcp-server",
                          loop: Optional[asyncio.AbstractEventLoop] = None):
    """
    Create and run an MCPGitHubServer in stdio mode.

    This is a convenience function that creates an MCPGitHubServer instance
    and immediately runs it in stdio mode for MCP client communication.

    Args:
        repo_paths (List[str]): List of filesystem paths to Git repositories to index.
        name (str, optional): Server name identifier. Defaults to "ghmcp-server".
        loop (Optional[asyncio.AbstractEventLoop]): Optional event loop to run the server (deprecated, ignored).

    Raises:
        ValueError: If no valid repositories are found in the provided paths.
        RuntimeError: If the server fails to start.

    Example:
        import asyncio
        asyncio.run(run_stdio_server(['/path/to/repo1', '/path/to/repo2']))
    """
    logger.info(f"Creating and running MCPGitHubServer '{name}' in stdio mode")
    logger.debug(f"Repository paths for stdio server: {repo_paths}")

    try:
        # Create server instance
        server = MCPGitHubServer(repo_paths, name=name)

        # Validate that repositories were found before starting stdio mode
        if not server.indexer.repos:
            raise ValueError("No valid Git repositories found in the provided paths")

        logger.info(f"Successfully indexed {len(server.indexer.repos)} repositories, starting stdio mode")

        # Run in stdio mode (removed loop parameter as it's not supported)
        await server.run_stdio()

    except Exception as e:
        logger.error(f"Failed to run stdio server '{name}': {e}")
        logger.debug(f"Stdio server error details:", exc_info=True)
        raise
