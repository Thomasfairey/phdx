#!/usr/bin/env python3
"""
Simple script to run the FastAPI server.
Run with: python3 run_server.py
"""

import os
import sys
from pathlib import Path

# Set PYTHONPATH for subprocess
project_dir = str(Path(__file__).parent)
os.environ["PYTHONPATH"] = project_dir

# Add current directory to path
sys.path.insert(0, project_dir)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[project_dir]
    )
