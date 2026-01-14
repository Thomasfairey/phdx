"""
PHDx - PhD Thesis Command Center
================================
Main entry point for Streamlit Cloud deployment.

Run locally with:
    streamlit run app.py

For production, Streamlit Cloud will automatically detect this file.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path for imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Import and run the main dashboard
from ui.dashboard import main

if __name__ == "__main__":
    main()
