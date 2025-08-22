#!/bin/bash

# start_mcp_server.sh
# ===================
# Bash script to start the MCP GitHub server using the start_server function
#
# This script provides a command-line interface to launch the MCP GitHub server
# with configurable options for server name, host, port, repository paths, and logging level.
# It automatically detects and uses Poetry if available, otherwise falls back
# to system Python.
#
# Author: Generated for ghmcp project
# Usage: ./start_mcp_server.sh [OPTIONS]

# =============================================================================
# CONFIGURATION AND SETUP
# =============================================================================

# Set script directory and project root
# This ensures the script works regardless of where it's called from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Default configuration values
# These can be overridden via command-line arguments
DEFAULT_NAME="ghmcp-server"        # Default server name identifier
DEFAULT_HOST="localhost"           # Default host to bind server to
DEFAULT_PORT="8000"               # Default port number
DEFAULT_REPOS="$PWD"              # Default to current working directory
DEFAULT_LOG_LEVEL="INFO"          # Default logging level

# =============================================================================
# HELP AND USAGE FUNCTIONS
# =============================================================================

# Function to display usage information
# Shows all available command-line options and examples
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Start the MCP GitHub server with specified configuration."
    echo ""
    echo "OPTIONS:"
    echo "  -n, --name NAME        Server name (default: $DEFAULT_NAME)"
    echo "  -h, --host HOST        Server host (default: $DEFAULT_HOST)"
    echo "  -p, --port PORT        Server port (default: $DEFAULT_PORT)"
    echo "  -r, --repos PATHS      Comma-separated repository paths (default: current directory)"
    echo "  -l, --log-level LEVEL  Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: $DEFAULT_LOG_LEVEL)"
    echo "  --help                 Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Start with current directory"
    echo "  $0 -r /path/to/repo1,/path/to/repo2  # Start with specific repositories"
    echo "  $0 -n my-server -p 9000             # Start with custom name and port"
    echo "  $0 -l DEBUG                         # Start with debug logging"
    echo "  $0 -l WARNING -r /my/repos          # Start with warning level and custom repos"
    echo ""
    echo "LOGGING LEVELS:"
    echo "  DEBUG     - Detailed information for debugging"
    echo "  INFO      - General information about server operations"
    echo "  WARNING   - Warning messages for potential issues"
    echo "  ERROR     - Error messages for serious problems"
    echo "  CRITICAL  - Critical error messages"
    echo ""
}

# =============================================================================
# COMMAND-LINE ARGUMENT PARSING
# =============================================================================

# Initialize variables with default values
NAME="$DEFAULT_NAME"
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
REPOS="$DEFAULT_REPOS"
LOG_LEVEL="$DEFAULT_LOG_LEVEL"

# Parse command line arguments using a while loop
# This allows for flexible argument ordering and validation
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            NAME="$2"
            shift 2  # Skip both the flag and its value
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -r|--repos)
            REPOS="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# =============================================================================
# INPUT VALIDATION
# =============================================================================

# Validate port number is numeric and within valid range (1-65535)
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "Error: Port must be a number between 1 and 65535"
    exit 1
fi

# Validate logging level is one of the accepted values
VALID_LOG_LEVELS=("DEBUG" "INFO" "WARNING" "ERROR" "CRITICAL")
LOG_LEVEL_UPPER=$(echo "$LOG_LEVEL" | tr '[:lower:]' '[:upper:]')
if [[ ! " ${VALID_LOG_LEVELS[@]} " =~ " ${LOG_LEVEL_UPPER} " ]]; then
    echo "Error: Invalid logging level '$LOG_LEVEL'"
    echo "Valid levels are: ${VALID_LOG_LEVELS[*]}"
    exit 1
fi
LOG_LEVEL="$LOG_LEVEL_UPPER"  # Use uppercase for consistency

# =============================================================================
# DATA PROCESSING
# =============================================================================

# Convert comma-separated repository paths to Python list format
# This transforms "repo1,repo2,repo3" into "['repo1', 'repo2', 'repo3']"
IFS=',' read -ra REPO_ARRAY <<< "$REPOS"  # Split on commas into array
PYTHON_REPO_LIST="["
for i in "${!REPO_ARRAY[@]}"; do
    if [ $i -gt 0 ]; then
        PYTHON_REPO_LIST+=", "  # Add comma separator for subsequent items
    fi
    # Wrap each path in single quotes for Python string literal
    PYTHON_REPO_LIST+="'${REPO_ARRAY[$i]}'"
done
PYTHON_REPO_LIST+="]"

# =============================================================================
# PYTHON SCRIPT GENERATION
# =============================================================================

# Create embedded Python script that will call the start_server function
# This approach allows us to pass shell variables into Python context
PYTHON_SCRIPT=$(cat << EOF
import sys
import os
import logging

# Add project root to Python path so we can import ghmcp modules
sys.path.insert(0, '$PROJECT_ROOT')

# Configure logging before importing our modules
# This ensures all loggers use the specified level
logging.basicConfig(
    level=logging.$LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create a logger for this script
logger = logging.getLogger('start_mcp_server')

from ghmcp.main import start_server

# Configuration from shell script arguments
repo_paths = $PYTHON_REPO_LIST
name = '$NAME'
host = '$HOST'
port = $PORT
log_level = '$LOG_LEVEL'

# Display configuration before starting
logger.info("Starting MCP GitHub server with configuration:")
logger.info(f"  Name: {name}")
logger.info(f"  Host: {host}")
logger.info(f"  Port: {port}")
logger.info(f"  Log Level: {log_level}")
logger.info(f"  Repositories: {repo_paths}")

try:
    # Call the start_server function with our configuration
    logger.info("Initializing server...")
    server = start_server(repo_paths, name=name, host=host, port=port)

    logger.info("Server started successfully!")
    libraries = server.query_libraries()
    logger.info(f"Indexed {len(libraries)} repositories")

    if log_level == 'DEBUG':
        for lib in libraries:
            logger.debug(f"  Repository: {lib['name']} at {lib['path']} with {len(lib['branches'])} branches")

    logger.info("Server is running. Press Ctrl+C to stop.")

    # Keep the server running indefinitely
    import time
    try:
        while True:
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Shutdown signal received...")
        from ghmcp.main import stop_server
        stop_server(server)
        logger.info("Server stopped successfully.")

except Exception as e:
    logger.error(f"Error starting server: {e}")
    sys.exit(1)
EOF
)

# =============================================================================
# EXECUTION
# =============================================================================

# Check if Poetry is available and use it for dependency management
# Poetry ensures all dependencies are available in the virtual environment
if command -v poetry &> /dev/null; then
    echo "Using Poetry to run the MCP server..."
    cd "$PROJECT_ROOT"  # Change to project directory for Poetry
    echo "$PYTHON_SCRIPT" | poetry run python -
else
    # Fallback to system Python if Poetry is not available
    echo "Poetry not found, using system Python..."
    echo "Warning: Make sure all dependencies are installed in your Python environment"
    echo "$PYTHON_SCRIPT" | python -
fi
