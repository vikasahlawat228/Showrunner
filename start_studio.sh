#!/bin/bash

# Showrunner Studio - Development Environment Launcher

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Showrunner Studio ===${NC}"

# 1. Setup Backend Environment
echo -e "${GREEN}[Backend] checking dependencies...${NC}"
export PYTHONPATH=$(pwd)/src

# Check if .venv exists, if so use it
if [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
    PIP_CMD=".venv/bin/pip"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# Ensure critical packages are installed
$PIP_CMD install fastapi uvicorn > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[Backend] Dependencies ready.${NC}"
else
    echo -e "${RED}[Backend] Failed to install dependencies. Please run 'pip install fastapi uvicorn' manually.${NC}"
fi

# 2. Start Backend in Background
echo -e "${GREEN}[Backend] Starting Server on port 8000...${NC}"
$PYTHON_CMD -m showrunner_tool.server.app &
BACKEND_PID=$!

# 3. Start Frontend
echo -e "${GREEN}[Frontend] Starting Next.js on port 3000...${NC}"
cd src/web
npm run dev &
FRONTEND_PID=$!

# 4. Handle Cleanup
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Wait for both processes
wait
