#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Python virtual environment...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Virtual environment created successfully!${NC}"
    else
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Virtual environment already exists${NC}"
fi

# Create necessary directories if they don't exist
echo "Creating project directories..."
mkdir -p data/scraping/{spells,items,classes