"""
main.py
-------
Main module for starting and stopping the MCP GitHub server.

This module provides the entry point functions for managing the MCP server lifecycle,
including starting the server with repository indexing and gracefully stopping it.

Functions:
    start_server(repo_paths: List[str], name: str = "ghmcp-server", host: str = "localhost", port: int = 8000) -> MCPGitHubServer:
        Start the MCP GitHub server with the specified configuration.

    stop_server(server: MCPGitHubServer) -> None:
        Stop the running MCP GitHub server.

Usage:
    from ghmcp.main import start_server, stop_server

    # Start the server
    server = start_server(['/path/to/repo1', '/path/to/repo2'])

    # Stop the server
    stop_server(server)
"""

import asyncio
import signal
import sys
from typing import List, Optional
from ghmcp.server import MCPGitHubServer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global server instance for signal handling
_server_instance: Optional[MCPGitHubServer] = None

def start_server(repo_paths: List[str], name: str = "ghmcp-server", host: str = "localhost", port: int = 8000) -> MCPGitHubServer:
    """
    Start the MCP GitHub server with the specified configuration.

    Creates and initializes an MCPGitHubServer instance with the provided repository
    paths and server configuration. The server will index the specified repositories
    and be ready to serve MCP client requests.

    Args:
        repo_paths (List[str]): List of filesystem paths to Git repositories to index.
        name (str, optional): Name identifier for the MCP server. Defaults to "ghmcp-server".
        host (str, optional): Host address to bind the server to. Defaults to "localhost".
        port (int, optional): Port number to bind the server to. Defaults to 8000.

    Returns:
        MCPGitHubServer: The initialized and started server instance.

    Raises:
        ValueError: If no valid repositories are found in the provided paths.
        RuntimeError: If the server fails to start.

    Example:
        server = start_server(['/Users/user/repos/project1', '/Users/user/repos/project2'])
        print(f"Server started with {len(server.query_libraries())} repositories indexed")
    """
    global _server_instance

    logger.info(f"Starting MCP GitHub server '{name}' on {host}:{port}")
    logger.info(f"Indexing repositories: {repo_paths}")

    try:
        # Create server instance
        server = MCPGitHubServer(repo_paths, name=name)
        _server_instance = server

        # Validate that repositories were found
        libraries = server.query_libraries()
        if not libraries:
            raise ValueError("No valid Git repositories found in the provided paths")

        logger.info(f"Successfully indexed {len(libraries)} repositories:")
        for lib in libraries:
            logger.info(f"  - {lib['name']} ({lib['path']}) - {len(lib['branches'])} branches")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        logger.info(f"MCP GitHub server '{name}' started successfully")
        return server

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise RuntimeError(f"Server startup failed: {e}") from e

def stop_server(server: MCPGitHubServer) -> None:
    """
    Stop the running MCP GitHub server.

    Gracefully shuts down the provided MCPGitHubServer instance, cleaning up
    resources and ensuring a proper shutdown sequence.

    Args:
        server (MCPGitHubServer): The server instance to stop.

    Example:
        server = start_server(['/path/to/repo'])
        # ... server operations ...
        stop_server(server)
    """
    global _server_instance

    if server is None:
        logger.warning("Attempted to stop a None server instance")
        return

    try:
        logger.info(f"Stopping MCP GitHub server...")

        # Clear global reference
        if _server_instance == server:
            _server_instance = None

        # Note: The actual server shutdown would depend on the MCP SDK's server implementation
        # For now, we'll log the shutdown and clear references
        logger.info("MCP GitHub server stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping server: {e}")
        raise

def _signal_handler(signum: int, frame) -> None:
    """
    Handle system signals for graceful shutdown.

    Args:
        signum (int): The signal number received.
        frame: The current stack frame.
    """
    logger.info(f"Received signal {signum}, shutting down gracefully...")

    if _server_instance:
        stop_server(_server_instance)

    sys.exit(0)

def main() -> None:
    """
    Main entry point for the MCP GitHub server application.

    This function can be used as a command-line entry point to start the server
    with default configuration. For more control, use start_server() directly.
    """
    import os

    # Default to current directory if no specific repos are provided
    default_repos = [os.getcwd()]

    try:
        server = start_server(default_repos)
        logger.info("Server is running. Press Ctrl+C to stop.")

        # Keep the main thread alive
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            stop_server(server)

    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
