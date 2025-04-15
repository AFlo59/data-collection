#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${RED}Virtual environment is not activated. Please run 'source setup/activate_venv.sh' first${NC}"
    exit 1
fi

echo -e "${GREEN}Installing/Updating pip...${NC}"
python -m pip install --upgrade pip

echo -e "${GREEN}Installing requirements...${NC}"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Requirements installed successfully!${NC}"
        
        # Install Chrome WebDriver
        echo -e "${YELLOW}Installing Chrome WebDriver...${NC}"
        python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
        
        echo -e "${GREEN}All dependencies installed successfully!${NC}"
    else
        echo -e "${RED}Failed to install requirements${NC}"
        exit 1
    fi
else
    echo -e "${RED}requirements.txt not found in $PROJECT_ROOT${NC}"
    exit 1
fi

# Display installed packages
echo -e "${GREEN}Installed packages:${NC}"
pip list