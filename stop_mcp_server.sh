#!/bin/bash

# stop_mcp_server.sh
# ==================
# Bash script to stop the MCP GitHub server using the stop_server function
#
# This script provides a command-line interface to gracefully shutdown the MCP GitHub server
# or forcefully terminate it using system signals. It supports both graceful shutdown via
# the Python stop_server function and forced termination via SIGTERM/SIGKILL signals.
#
# Author: Generated for ghmcp project
# Usage: ./stop_mcp_server.sh [OPTIONS]

# =============================================================================
# CONFIGURATION AND SETUP
# =============================================================================

# Set script directory and project root
# This ensures the script works regardless of where it's called from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# PID file location for tracking server processes
# Currently used for cleanup but could be extended for better process management
PID_FILE="$PROJECT_ROOT/mcp_server.pid"

# =============================================================================
# HELP AND USAGE FUNCTIONS
# =============================================================================

# Function to display usage information
# Shows all available command-line options and examples
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Stop the running MCP GitHub server."
    echo ""
    echo "OPTIONS:"
    echo "  --force                Force stop using process signals"
    echo "  --help                 Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                     # Gracefully stop the server"
    echo "  $0 --force            # Force stop using SIGTERM/SIGKILL"
    echo ""
}

# =============================================================================
# COMMAND-LINE ARGUMENT PARSING
# =============================================================================

# Initialize variables with default values
FORCE_STOP=false

# Parse command line arguments using a while loop
# This allows for flexible argument ordering and validation
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_STOP=true
            shift
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
# FORCE STOP FUNCTIONALITY
# =============================================================================

# Function to force stop using process signals
# This is used when graceful shutdown fails or when --force flag is used
force_stop_server() {
    echo "Force stopping MCP server processes..."

    # Find Python processes running the MCP server using pattern matching
    # pgrep searches for processes with "ghmcp.main" in their command line
    PIDS=$(pgrep -f "ghmcp.main" 2>/dev/null)

    if [ -z "$PIDS" ]; then
        echo "No MCP server processes found."
        return 0
    fi

    echo "Found MCP server processes: $PIDS"

    # Try SIGTERM first for graceful shutdown
    # SIGTERM allows processes to clean up before terminating
    echo "Sending SIGTERM to processes..."
    for pid in $PIDS; do
        kill -TERM "$pid" 2>/dev/null && echo "Sent SIGTERM to process $pid"
    done

    # Wait a few seconds for graceful shutdown
    sleep 3

    # Check if processes are still running after SIGTERM
    REMAINING_PIDS=$(pgrep -f "ghmcp.main" 2>/dev/null)

    if [ -n "$REMAINING_PIDS" ]; then
        # If processes are still running, use SIGKILL for immediate termination
        echo "Some processes still running, sending SIGKILL..."
        for pid in $REMAINING_PIDS; do
            kill -KILL "$pid" 2>/dev/null && echo "Sent SIGKILL to process $pid"
        done
    fi

    # Clean up PID file if it exists
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"

    echo "Force stop completed."
}

# =============================================================================
# GRACEFUL STOP FUNCTIONALITY
# =============================================================================

# Function to gracefully stop the server
# Attempts to use the Python stop_server function for clean shutdown
graceful_stop_server() {
    echo "Gracefully stopping MCP GitHub server..."

    # Create embedded Python script to call stop_server function
    # This approach allows us to access the server instance and call proper shutdown
    PYTHON_SCRIPT=$(cat << 'EOF'
import sys
import os
import signal
import time

# Add project root to Python path so we can import ghmcp modules
sys.path.insert(0, os.environ.get('PROJECT_ROOT', '.'))

def find_server_process():
    """Find the MCP server process by looking for the global server instance."""
    try:
        # Try to import and check if there's a running server instance
        # The _server_instance global variable is set when server starts
        from ghmcp.main import _server_instance
        return _server_instance
    except ImportError:
        return None

def stop_via_signal():
    """Stop server by sending SIGTERM to Python processes running ghmcp."""
    import subprocess

    try:
        # Find processes running ghmcp using pgrep command
        result = subprocess.run(['pgrep', '-f', 'ghmcp.main'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"Sending SIGTERM to process {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    return True
        return False
    except Exception as e:
        print(f"Error stopping via signal: {e}")
        return False

def main():
    # Strategy 1: Try to find and stop server instance directly
    server_instance = find_server_process()

    if server_instance:
        print("Found running server instance, stopping gracefully...")
        try:
            from ghmcp.main import stop_server
            stop_server(server_instance)
            print("Server stopped successfully.")
            return
        except Exception as e:
            print(f"Error stopping server instance: {e}")

    # Strategy 2: If no server instance found, try to stop via process signals
    print("No server instance found, attempting to stop via process signals...")
    if stop_via_signal():
        print("Sent stop signal to server process(es).")

        # Wait a moment for graceful shutdown to complete
        time.sleep(2)

        # Check if processes are still running after signal
        try:
            result = subprocess.run(['pgrep', '-f', 'ghmcp.main'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Server processes may still be running. Use --force to kill them.")
            else:
                print("Server stopped successfully.")
        except Exception:
            print("Server stop completed.")
    else:
        print("No MCP server processes found running.")

if __name__ == "__main__":
    main()
EOF
)

    # Set environment variable for project root so Python script can find modules
    export PROJECT_ROOT="$PROJECT_ROOT"

    # Check if Poetry is available and use it for dependency management
    # Poetry ensures all dependencies are available in the virtual environment
    if command -v poetry &> /dev/null; then
        echo "Using Poetry to stop the MCP server..."
        cd "$PROJECT_ROOT"  # Change to project directory for Poetry
        echo "$PYTHON_SCRIPT" | poetry run python -
    else
        # Fallback to system Python if Poetry is not available
        echo "Poetry not found, using system Python..."
        echo "$PYTHON_SCRIPT" | python -
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Main execution logic based on command-line arguments
echo "Stopping MCP GitHub server..."

if [ "$FORCE_STOP" = true ]; then
    # Use force stop if --force flag was provided
    force_stop_server
else
    # Use graceful stop by default
    graceful_stop_server
fi

echo "Stop operation completed."
