"""
PHDx - PhD Thesis Command Center
"""
import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from ui.dashboard import main

if __name__ == "__main__":
      main()
