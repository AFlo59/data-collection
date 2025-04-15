#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run setup_venv.sh first${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/venv/bin/activate"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Virtual environment activated successfully!${NC}"
    echo "Python path: $(which python)"
    echo "Python version: $(python --version)"
else
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi