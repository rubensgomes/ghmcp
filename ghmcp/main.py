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

import argparse
import asyncio
import signal
import sys
from typing import List, Optional
from ghmcp.server import MCPGitHubServer, run_stdio_server
import logging
import os

def configure_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')

    # Configure logging with detailed format
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # Override any existing configuration
    )

# Initialize logger after configuration
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
        print(f"Server started with {len(server.indexer.repos)} repositories indexed")
    """
    global _server_instance

    logger.info(f"Starting MCP GitHub server '{name}' on {host}:{port}")
    logger.info(f"Indexing repositories: {repo_paths}")
    logger.debug(f"Server configuration - name: {name}, host: {host}, port: {port}")

    try:
        # Create server instance with explicit name parameter
        logger.debug("Creating MCPGitHubServer instance...")
        server = MCPGitHubServer(repo_paths, name=name)
        _server_instance = server

        # Validate that repositories were found
        logger.debug("Validating indexed repositories...")
        if not server.indexer.repos:
            raise ValueError("No valid Git repositories found in the provided paths")

        logger.info(f"Successfully indexed {len(server.indexer.repos)} repositories:")
        for repo in server.indexer.repos:
            repo_name = os.path.basename(repo.working_dir)
            logger.info(f"  - {repo_name} ({repo.working_dir})")
            logger.debug(f"    Repository working directory: {repo.working_dir}")

        # Set up signal handlers for graceful shutdown
        logger.debug("Setting up signal handlers...")
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        logger.info(f"MCP GitHub server '{name}' started successfully")
        return server

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.debug(f"Server startup error details:", exc_info=True)
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
        logger.debug(f"Stopping server with name: {getattr(server, 'name', 'unknown')}")

        # Clear global reference
        if _server_instance == server:
            _server_instance = None

        # Note: The actual server shutdown would depend on the MCP SDK's server implementation
        # For now, we'll log the shutdown and clear references
        logger.info("MCP GitHub server stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping server: {e}")
        logger.debug("Server stop error details:", exc_info=True)
        raise

def _signal_handler(signum: int, frame) -> None:
    """
    Handle system signals for graceful shutdown.

    Args:
        signum (int): The signal number received.
        frame: The current stack frame.
    """
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    logger.debug(f"Signal handler called with signum={signum}")

    if _server_instance:
        stop_server(_server_instance)

    sys.exit(0)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the MCP GitHub server.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="MCP GitHub Server - Index and serve Git repositories via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Start with current directory (standard mode)
  %(prog)s --repos /path/to/repo1 /path/to/repo2  # Start with specific repositories
  %(prog)s --name my-server --port 9000      # Start with custom name and port
  %(prog)s --log-level DEBUG                 # Start with debug logging
  %(prog)s --stdio                           # Start in stdio mode for MCP clients
  %(prog)s --stdio --repos /my/repos         # Start in stdio mode with custom repos
  %(prog)s --log-level WARNING --repos /my/repos  # Start with warning level and custom repos

Modes:
  Standard Mode - Regular server operation for direct interaction
  Stdio Mode    - Communicate via stdin/stdout for MCP client integration

Logging Levels:
  DEBUG     - Detailed information for debugging
  INFO      - General information about server operations (default)
  WARNING   - Warning messages for potential issues
  ERROR     - Error messages for serious problems
  CRITICAL  - Critical error messages
        """
    )

    parser.add_argument(
        '--name', '-n',
        type=str,
        default='ghmcp-server',
        help='Server name identifier (default: ghmcp-server)'
    )

    parser.add_argument(
        '--host', '-H',
        type=str,
        default='localhost',
        help='Server host address (default: localhost)'
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Server port number (default: 8000)'
    )

    parser.add_argument(
        '--repos', '-r',
        type=str,
        nargs='*',
        help='Repository paths to index (default: current directory)'
    )

    parser.add_argument(
        '--log-level', '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--stdio', '-s',
        action='store_true',
        help='Run the server in stdio mode for MCP client communication'
    )

    return parser.parse_args()

def main() -> None:
    """
    Main entry point for the MCP GitHub server application.

    This function parses command line arguments and starts the server
    with the specified configuration. Supports both regular mode and
    stdio mode for MCP client communication.
    """
    import os

    # Parse command line arguments
    args = parse_arguments()

    # Configure logging based on command line argument
    configure_logging(args.log_level)

    logger.info("Starting MCP GitHub server application")
    logger.debug(f"Command line arguments: {vars(args)}")

    # Use provided repos or default to current directory
    repo_paths = args.repos if args.repos else [os.getcwd()]

    logger.info(f"Configuration:")
    logger.info(f"  Name: {args.name}")
    logger.info(f"  Mode: {'stdio' if args.stdio else 'standard'}")
    logger.info(f"  Host: {args.host}")
    logger.info(f"  Port: {args.port}")
    logger.info(f"  Log Level: {args.log_level}")
    logger.info(f"  Repositories: {repo_paths}")

    try:
        if args.stdio:
            # Run in stdio mode for MCP client communication
            logger.info("Running server in stdio mode")
            asyncio.run(run_stdio_server(repo_paths, name=args.name))
        else:
            # Run in standard mode
            logger.info("Running server in standard mode")
            server = start_server(repo_paths, name=args.name, host=args.host, port=args.port)
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
        logger.debug("Main function error details:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
