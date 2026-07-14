import sys
import os

sys.path.append(os.path.abspath("demo_ui"))
import streamlit as st
from core.api_client import trigger_all_metrology_analyses_automatically

print("Testing pipeline with default HL preset...")
try:
    trigger_all_metrology_analyses_automatically("HL")
    print(f"Pipeline Result: {st.session_state.get('pipeline_result')}")
except Exception as e:
    print(f"Error: {e}")
