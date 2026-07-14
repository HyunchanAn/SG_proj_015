import streamlit as st
import requests
import json
import socket
import pandas as pd
import plotly.graph_objects as go
import cv2
import numpy as np
import os
import sys
from loguru import logger
import streamlit.components.v1 as components
from translations import TRANSLATIONS
from utils import *

sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_002")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_003")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_007")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_010")

try:
    from deepdrop_sfe import AIContactAngleAnalyzer, PerspectiveCorrector, DropletPhysics
    import torch
except ImportError:
    pass
try:
    from vsams.analysis.surface_evaluator import SurfaceEvaluator
    import torch
except ImportError:
    pass
try:
    from sg_terra.seg.sam2_wrapper import SAM2BaseWrapper
    from sg_terra.topo.depth_wrapper import DepthAnythingV2Wrapper
    import torch
except ImportError:
    pass
try:
    from src.matcher import SubstrateMatcher
    from src.data_loader import load_and_preprocess_data
except ImportError:
    pass

def init_state():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }

        .main-title {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #1f4068, #162447, #e43f5a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-align: center;
        }

        .sub-title {
            font-size: 1rem;
            color: #6c757d;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .status-card {
            padding: 1.2rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 1.2rem;
        }

        .custom-card {
            background: rgba(15, 23, 42, 0.6);
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 1.5rem;
        }

        .result-badge {
            padding: 0.8rem;
            border-radius: 8px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(59, 130, 246, 0.3);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        img {
            max-width: 100% !important;
            height: auto !important;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state for E2E step 1 vision variables
    if "extracted_sfe" not in st.session_state:
        st.session_state["extracted_sfe"] = 42.5
    if "extracted_roughness" not in st.session_state:
        st.session_state["extracted_roughness"] = 250.0
    if "extracted_gloss" not in st.session_state:
        st.session_state["extracted_gloss"] = 120.0
    if "extracted_finish" not in st.session_state:
        st.session_state["extracted_finish"] = "2B"
    if "extracted_curvature" not in st.session_state:
        st.session_state["extracted_curvature"] = 150.0


    # Initialize 002/003/007 analysis display triggers
    if "droplet_analysis_done" not in st.session_state:
        st.session_state["droplet_analysis_done"] = False
    if "water_angle_res" not in st.session_state:
        st.session_state["water_angle_res"] = 0.0
    if "glycerol_angle_res" not in st.session_state:
        st.session_state["glycerol_angle_res"] = 0.0

    if "roughness_analysis_done" not in st.session_state:
        st.session_state["roughness_analysis_done"] = False
    if "roughness_res" not in st.session_state:
        st.session_state["roughness_res"] = 0.0
    if "gloss_res" not in st.session_state:
        st.session_state["gloss_res"] = 0.0
    if "vsams_overlay" not in st.session_state:
        st.session_state["vsams_overlay"] = None

    if "terra_analysis_done" not in st.session_state:
        st.session_state["terra_analysis_done"] = False
    if "terra_blended_img" not in st.session_state:
        st.session_state["terra_blended_img"] = None
    if "terra_depth_img" not in st.session_state:
        st.session_state["terra_depth_img"] = None
    if "terra_depth_grid" not in st.session_state:
        st.session_state["terra_depth_grid"] = None

    # Session state for 010 Material ID
    if "identified_substrate" not in st.session_state:
        st.session_state["identified_substrate"] = "SUS304-2B"
    if "identified_similarity" not in st.session_state:
        st.session_state["identified_similarity"] = 100.0
    if "show_010_alert" not in st.session_state:
        st.session_state["show_010_alert"] = False

    if "water_overlay" not in st.session_state:
        st.session_state["water_overlay"] = None
    if "glycerol_overlay" not in st.session_state:
        st.session_state["glycerol_overlay"] = None
    if "pipeline_result" not in st.session_state:
        st.session_state["pipeline_result"] = None

    # Real TCP socket connection check to diagnose service ports
    @st.cache_data(ttl=10)
