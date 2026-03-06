#!/bin/bash
export PYTHONPATH=$(pwd)/src
if [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi
$PYTHON_CMD -m showrunner_tool.server.app &
SERVER_PID=$!
sleep 5
echo "--- executing curl ---"
curl -s -X POST http://localhost:8000/api/v1/cascade/update -H "Content-Type: application/json" -d '{"file_path": "fragment/test.yaml", "dry_run": true}'
echo ""
echo "--- shutting down server ---"
kill $SERVER_PID
