"""
PHDx Orbit - Premium UI Styles
"""

import streamlit as st


def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * { font-family: 'Inter', sans-serif !important; }

        #MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }

        .block-container { max-width: 95% !important; padding-top: 1rem !important; }

        .stApp { background-color: #0e1117 !important; }

        [data-testid="stSidebar"] { background-color: #262730 !important; }

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #1c1c1c !important;
            border: none !important;
            border-radius: 12px !important;
            color: #fafafa !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5) !important;
        }

        .glass-panel {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.02) !important; border-radius: 12px !important; }
        .stTabs [aria-selected="true"] { background: rgba(99,102,241,0.2) !important; color: #a5b4fc !important; }

        .scroll-container {
            background: rgba(255,255,255,0.02) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            max-height: 300px !important;
            overflow-y: auto !important;
        }

        .model-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .model-badge.claude { background: rgba(99,102,241,0.2); color: #a5b4fc; }
        .model-badge.gpt { background: rgba(16,185,129,0.2); color: #6ee7b7; }
    </style>
    """, unsafe_allow_html=True)
