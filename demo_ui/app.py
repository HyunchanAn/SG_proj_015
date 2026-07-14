import streamlit as st
import requests
import json
import socket
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from loguru import logger
import streamlit.components.v1 as components
import os
import cv2
import numpy as np
import sys
import subprocess

from core.api_client import start_local_orchestrator
from core.state_manager import init_state
from ui_components.network_status import render_health_check
from ui_components.vision_panel import render_step1_vision
from ui_components.input_panel import render_input_panel
from ui_components.results_panel import render_results_panel
from ui_components.archive_panel import render_archive_panel
from translations import TRANSLATIONS

start_local_orchestrator()
init_state()

# Language Selector Setup
selected_lang = st.radio("Language Selector", options=["KO", "EN"], horizontal=True, index=0)
t = TRANSLATIONS[selected_lang]

st.markdown(f'<div class="main-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{t["subtitle"]}</div>', unsafe_allow_html=True)

render_health_check(t)
st.markdown('---')
render_step1_vision(t)
render_input_panel(t)
render_results_panel(t)
render_archive_panel(t)
