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

def render_input_panel(t):
    from core.api_client import trigger_all_metrology_analyses_automatically, load_adherend_master_from_db
    
    db_profiles = load_adherend_master_from_db()
    adherend_list = list(dict.fromkeys([p.get("product_name", "Unknown") for p in db_profiles]))
    if not adherend_list:
        adherend_list = ["#4", "HL", "BA", "SM", "2B"]

    st.header(t["input_panel_title"])

    with st.form("pipeline_input_form"):
        st.subheader(t["sub_attr"])

        def_sub_idx = 0
        if st.session_state["identified_substrate"] in adherend_list:
            def_sub_idx = adherend_list.index(st.session_state["identified_substrate"])
        sub_id = st.selectbox(t["sub_id"], options=adherend_list, index=def_sub_idx, disabled=True)

        sub_series = st.selectbox(t["sub_series"], options=["SGV", "SGO", "SGE"], index=0)
        thickness = st.number_input(t["thickness"], min_value=10.0, max_value=500.0, value=100.0, step=10.0)

        finish_opts = ["Hairline", "Mirror", "BA", "2B", "2D"]
        def_idx = 3
        if st.session_state["extracted_finish"] in finish_opts:
            def_idx = finish_opts.index(st.session_state["extracted_finish"])
        finish_type = st.selectbox(t["finish_type"], options=finish_opts, index=def_idx, disabled=True)

        st.divider()
        st.subheader(t["phys_met"])

        lock_inputs = st.session_state["droplet_analysis_done"] or st.session_state["roughness_analysis_done"] or st.session_state["terra_analysis_done"]

        sfe_val = st.number_input(t["measured_sfe"], min_value=10.0, max_value=1000.0, value=float(np.clip(st.session_state["extracted_sfe"], 10.0, 999.0)), step=1.0, disabled=lock_inputs)
        roughness_val = st.number_input(t["roughness"], min_value=0.0, max_value=50000.0, value=st.session_state["extracted_roughness"], step=1.0, disabled=lock_inputs)
        gloss_val = st.number_input(t["gloss"], min_value=0.0, max_value=2000.0, value=st.session_state["extracted_gloss"], step=10.0, disabled=lock_inputs)
        curvature_val = st.number_input(t["curvature"], min_value=0.01, max_value=10000.0, value=st.session_state["extracted_curvature"], step=10.0, disabled=lock_inputs)

        st.divider()
        st.subheader(t["target_spec"])
        target_init_adh = st.number_input(t["target_init_adh"], min_value=0.0, max_value=3000.0, value=450.0, step=10.0)
        target_aged_adh = st.number_input(t["target_aged_adh"], min_value=0.0, max_value=5000.0, value=850.0, step=10.0)
        target_tg_val = st.slider(t["target_tg"], min_value=-80.0, max_value=0.0, value=-25.0, step=1.0)
        target_viscosity = st.number_input(t["target_visc"], min_value=0.0, max_value=20000.0, value=4000.0, step=100.0)

        submit_button = st.form_submit_button(t["trigger_btn"], use_container_width=True)

    # Processing E2E pipeline
    if submit_button:
        validation_passed = True

        if target_init_adh > target_aged_adh:
            st.error(t["validation_adh"])
            validation_passed = False

        if abs(curvature_val) < 0.01:
            st.error(t["validation_curv"])
            validation_passed = False

        if validation_passed:
            payload = {
                "substrate_id": sub_id,
                "substrate_series": sub_series,
                "thickness_um": thickness,
                "finish_type": finish_type,
                "metrics": {
                    "surface_energy": sfe_val,
                    "roughness": roughness_val,
                    "gloss": gloss_val,
                    "curvature_radius": curvature_val
                },
                "target": {
                    "target_initial_adhesion": target_init_adh,
                    "target_aged_adhesion": target_aged_adh,
                    "target_tg": target_tg_val,
                    "target_viscosity": target_viscosity
                },
                "normal_vector_data": [0.0, 0.0, 1.0],
                "material_stiffness": 200000.0
            }

            st.session_state["payload_sent"] = payload
            orchestrator_url = "http://localhost:8024/orchestrate"

            with st.spinner(t["trigger_spinner"]):
                try:
                    res = requests.post(orchestrator_url, json=payload, timeout=120.0)
                    if res.status_code == 200:
                        st.session_state["pipeline_result"] = res.json()
                        st.success(t["success_msg"])
                    elif res.status_code == 422:
                        st.session_state["pipeline_result"] = None
                        err_data = res.json()
                        st.error(f"Domain Validation Failed (HTTP 422): {err_data.get('detail')}")
                        st.json(err_data.get("validation_errors", []))
                    else:
                        st.session_state["pipeline_result"] = None
                        st.error(f"API Error (HTTP {res.status_code}): {res.text}")
                except requests.exceptions.RequestException as req_err:
                    st.session_state["pipeline_result"] = None
                    st.error(f"Orchestrator Connection Failed: {req_err}")

    # 3. Result Visualization Dashboard (V-scroll optimized)
    if st.session_state.get("pipeline_result") is not None:
        st.divider()
