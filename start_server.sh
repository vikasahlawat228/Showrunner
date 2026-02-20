#!/bin/bash
# Temporary workaround for ModuleNotFoundError and missing dependencies
# Sets PYTHONPATH to include the 'src' directory and local '.pylibs'

export PYTHONPATH=$(pwd)/.pylibs_v2:$(pwd)/src:$PYTHONPATH
echo "=== Debug Info ==="
which python3
python3 --version
python3 -c "import struct; print(struct.calcsize('P') * 8)"
echo "PYTHONPATH: $PYTHONPATH"
ls -l .pylibs_v2/pydantic_core/
echo "=================="

# Direct invocation to bypass potential CLI/Typer issues and ensure server starts
python3 -c "import uvicorn; uvicorn.run('antigravity_tool.server.app:app', host='0.0.0.0', port=8000)"
