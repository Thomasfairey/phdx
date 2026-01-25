"""
PHDx UI Tabs - Modular tab components for the dashboard.
"""

from ui.tabs.data_lab_tab import render_data_lab_tab
from ui.tabs.writing_desk_tab import render_writing_desk_tab
from ui.tabs.narrative_tab import render_narrative_tab
from ui.tabs.auditor_tab import render_auditor_tab
from ui.tabs.library_tab import render_library_tab

__all__ = [
    "render_data_lab_tab",
    "render_writing_desk_tab",
    "render_narrative_tab",
    "render_auditor_tab",
    "render_library_tab",
]
