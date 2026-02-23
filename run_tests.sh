#!/bin/bash
PYTHONPATH=$(pwd)/src $(pwd)/.venv_clean/bin/python -m pytest tests/ "$@"
