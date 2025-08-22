#!/bin/bash

# start_mcp_server.sh
# ===================
# Bash script to start the MCP GitHub server using the start_server function
#
# This script provides a command-line interface to launch the MCP GitHub server
# with configurable options for server name, host, port, and repository paths.
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
    echo "  --help                 Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Start with current directory"
    echo "  $0 -r /path/to/repo1,/path/to/repo2  # Start with specific repositories"
    echo "  $0 -n my-server -p 9000             # Start with custom name and port"
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

# Add project root to Python path so we can import ghmcp modules
sys.path.insert(0, '$PROJECT_ROOT')

from ghmcp.main import start_server

# Configuration from shell script arguments
repo_paths = $PYTHON_REPO_LIST
name = '$NAME'
host = '$HOST'
port = $PORT

# Display configuration before starting
print(f"Starting MCP GitHub server with configuration:")
print(f"  Name: {name}")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Repositories: {repo_paths}")
print()

try:
    # Call the start_server function with our configuration
    server = start_server(repo_paths, name=name, host=host, port=port)
    print(f"Server started successfully!")
    print(f"Indexed {len(server.query_libraries())} repositories")
    print()
    print("Server is running. Press Ctrl+C to stop.")

    # Keep the server running indefinitely
    import time
    try:
        while True:
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nShutting down server...")
        from ghmcp.main import stop_server
        stop_server(server)
        print("Server stopped.")

except Exception as e:
    print(f"Error starting server: {e}")
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
