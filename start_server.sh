#!/bin/bash
# Temporary workaround for ModuleNotFoundError and missing dependencies
# Sets PYTHONPATH to include the 'src' directory and local '.pylibs'

export PYTHONPATH=$(pwd)/src:$PYTHONPATH
echo "=== Debug Info ==="
which .venv_clean/bin/python
.venv_clean/bin/python --version
.venv_clean/bin/python -c "import struct; print(struct.calcsize('P') * 8)"
echo "PYTHONPATH: $PYTHONPATH"
echo "=================="

# Direct invocation to bypass potential CLI/Typer issues and ensure server starts
.venv_clean/bin/python -c "import uvicorn; uvicorn.run('showrunner_tool.server.app:app', host='0.0.0.0', port=8000)"
