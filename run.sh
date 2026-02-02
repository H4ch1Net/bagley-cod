#!/bin/bash
# Simple runner script for Bagley CLI

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run the CLI
python3 "$SCRIPT_DIR/tools/cli.py" "$@"
