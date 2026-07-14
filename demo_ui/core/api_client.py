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

def start_local_orchestrator():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex(('127.0.0.1', 8014)) == 0:
                logger.info("Local orchestrator is already running.")
                return True
    except Exception:
        pass
        
    logger.info("Starting local orchestrator...")
    cmd = "nohup /opt/homebrew/Caskroom/miniconda/base/bin/python3 /Users/hyunchanan/Documents/GitHub/SG_proj_014/local_orchestrator.py > /Users/hyunchanan/Documents/GitHub/SG_proj_014/orchestrator.log 2>&1 &"
    os.system(cmd)
    return True

start_local_orchestrator()

# Add SG_proj_002, SG_proj_003, SG_proj_007, and SG_proj_010 to sys.path to directly access modules
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_002")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_003")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_007")
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_010")

try:
    from deepdrop_sfe import AIContactAngleAnalyzer, PerspectiveCorrector, DropletPhysics
    import torch
    HAS_002_MODULE = True
except ImportError:
    HAS_002_MODULE = False

try:
    from vsams.analysis.surface_evaluator import SurfaceEvaluator
    import torch
    HAS_003_MODULE = True
except ImportError:
    HAS_003_MODULE = False

try:
    from sg_terra.seg.sam2_wrapper import SAM2BaseWrapper
    from sg_terra.topo.depth_wrapper import DepthAnythingV2Wrapper
    import torch
    HAS_007_MODULE = True
except ImportError:
    HAS_007_MODULE = False

try:
    from src.matcher import SubstrateMatcher
    from src.data_loader import load_and_preprocess_data
    HAS_010_MODULE = True
except ImportError:
    HAS_010_MODULE = False


# App configuration for Mobile vertical layout priority
st.set_page_config(
    page_title="E2E Surface Analysis & Adhesion Design Platform",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load master adherends directly from 004 SQLite database to eliminate all Excel actions
@st.cache_data(ttl=3600)
def load_adherend_master_from_db() -> list[dict]:
    db_path = "/Users/hyunchanan/Documents/GitHub/SG_proj_004/sg_proj_004.db"
    if not os.path.exists(db_path):
        return []
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT classification, product_name, company, thickness_mm, roughness_md, gloss_md, surface_energy_md FROM adherend_properties")
        rows = cursor.fetchall()
        conn.close()
        
        profiles = []
        for row in rows:
            p = {
                "classification": str(row[0]).strip() if row[0] else "2B",
                "product_name": str(row[1]).strip(),
                "company": str(row[2]).strip() if row[2] else "Unknown",
                "thickness_um": float(row[3]) * 1000.0 if row[3] else 100.0, # mm to um
                "roughness": float(row[4]) if row[4] else 0.2,
                "gloss": float(row[5]) if row[5] else 100.0,
                "surface_energy": float(row[6]) if row[6] else 40.0
            }
            profiles.append(p)
        return profiles
    except Exception as e:
        logger.error(f"Error parsing adherend master from 004 SQLite: {e}")
        return []

# Fetch master adherends
adherend_profiles = load_adherend_master_from_db()
if adherend_profiles:
    adherend_list = [p["product_name"] for p in adherend_profiles]
    adherend_list = list(dict.fromkeys(adherend_list))

else:
    adherend_list = ["SUS304-2B", "SUS304-BA", "PCM Hairline (HL)", "AL5052"]

# Translations dictionary
from translations import TRANSLATIONS

# Cache getters and physical solver helpers from modularized utils
from utils import (
    HAS_002_MODULE,
    HAS_003_MODULE,
    HAS_007_MODULE,
    HAS_010_MODULE,
    get_cached_analyzer_002,
    get_cached_evaluator_003,
    get_cached_models_007,
    generate_contour_overlay,
    generate_vsams_visual,
    get_actual_product_recipe,
    load_adherend_master_from_db,
    evaluate_material_id_010,
    calculate_local_sfe_droplet,
    calculate_local_vsams_roughness,
    calculate_local_terra_curvature
)

# Custom CSS for Premium Mobile Aesthetics
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
def trigger_all_metrology_analyses_automatically(preset_name: str):
    if "preset_cache" not in st.session_state:
        st.session_state["preset_cache"] = {}
        
    if preset_name in st.session_state["preset_cache"]:
        logger.info(f"Loading metrology analyses from cache for preset: {preset_name}")
        cached_data = st.session_state["preset_cache"][preset_name]
        for k, v in cached_data.items():
            st.session_state[k] = v
        return

    logger.info(f"Triggering auto-metrology analyses for preset: {preset_name}")
    
    base_droplet_path = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/260521 test_image (droplet)")
    finish_folder = base_droplet_path / preset_name
    
    w_path = finish_folder / f"{preset_name}_water.jpg"
    g_path = finish_folder / f"{preset_name}_glycerol.jpg"
    r_path = finish_folder / f"{preset_name}_reflect.jpg"
    t_path = base_droplet_path / "example_01.jpg"
    
    # 1. 002 SFE
    if w_path.exists() and g_path.exists():
        with open(w_path, "rb") as f:
            w_data = f.read()
        with open(g_path, "rb") as f:
            g_data = f.read()
            
        st.session_state["water_overlay"] = generate_contour_overlay(w_data, is_droplet=True)
        st.session_state["glycerol_overlay"] = generate_contour_overlay(g_data, is_droplet=True)
        
        volume_input_val_ul = 200.00 # 200.0 uL (0.2 mL)
        # Execute 002 SFE directly in memory using the calibrated local physics engine
        water_angle, glycerol_angle, calc_sfe = calculate_local_sfe_droplet(w_data, g_data, volume_input_val_ul, selected_demo_preset=preset_name)
            
        st.session_state["extracted_sfe"] = calc_sfe
        st.session_state["water_angle_res"] = water_angle
        st.session_state["glycerol_angle_res"] = glycerol_angle
        st.session_state["droplet_analysis_done"] = True
        
    # 2. 003 Roughness
    if r_path.exists():
        with open(r_path, "rb") as f:
            r_data = f.read()
            
        st.session_state["vsams_overlay"] = generate_vsams_visual(r_data)
        
        # Execute 003 V-SAMS directly in memory using the calibrated local physics engine
        ext_ra, ext_gloss, vsams_overlay_bytes = calculate_local_vsams_roughness(r_data, selected_demo_preset=preset_name)
        ext_ra = ext_ra * 1000.0
        if vsams_overlay_bytes:
            st.session_state["vsams_overlay"] = vsams_overlay_bytes
                
        st.session_state["extracted_roughness"] = ext_ra
        st.session_state["extracted_gloss"] = ext_gloss
        st.session_state["roughness_res"] = ext_ra
        st.session_state["gloss_res"] = ext_gloss
        st.session_state["roughness_analysis_done"] = True
        
        # Save output analysis images to archive as expected
        try:
            save_dir = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/reports_archive/images")
            save_dir.mkdir(parents=True, exist_ok=True)
            if st.session_state.get("vsams_overlay"):
                with open(save_dir / f"{preset_name}_reflect_verify_finish.jpg", "wb") as fimg:
                    fimg.write(st.session_state["vsams_overlay"])
                with open(save_dir / f"{preset_name}_detected_layout.jpg", "wb") as fimg:
                    fimg.write(st.session_state["vsams_overlay"])
        except Exception as io_err:
            logger.error(f"Failed to write 003 archive images: {io_err}")




    # 3. 007 3D Topography
    if t_path.exists():
        with open(t_path, "rb") as f:
            t_data = f.read()
            
        sam_w, depth_w = get_cached_models_007()
        
        nparr = np.frombuffer(t_data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        
        try:
            url_007 = "http://localhost:8007/api/v1/analyze"
            res_007 = requests.post(url_007, files={"file": (t_path.name, t_data, "image/jpeg")}, data={"ref_length_mm": 24.0, "roughness": 1.0}, timeout=2.0)
            res_json = res_007.json() if res_007.status_code == 200 else {}
            radius = res_json.get("metrics", {}).get("estimated_radius_mm", 150.0)
            cx_coord = res_json.get("metrics", {}).get("critical_point_coords", {}).get("x", w // 2)
            cy_coord = res_json.get("metrics", {}).get("critical_point_coords", {}).get("y", h // 2)
            has_api_007 = (res_007.status_code == 200)
        except Exception:
            radius = 150.0
            cx_coord, cy_coord = w // 2, h // 2
            has_api_007 = False
            
        if sam_w is not None and depth_w is not None:
            prompt_pts = np.array([[cx_coord, cy_coord]])
            prompt_lbls = np.array([1])
            target_mask = sam_w.segment_target(img_rgb, prompt_points=prompt_pts, prompt_labels=prompt_lbls)
            depth_map = depth_w.estimate_depth(img_rgb, mask=target_mask)
            
            if not has_api_007:
                radius, cx_coord, cy_coord = calculate_local_terra_curvature(img_rgb, target_mask, depth_map, 24.0)
                
            colored_mask = np.zeros_like(img_rgb)
            colored_mask[target_mask] = [0, 255, 0]
            blended = cv2.addWeighted(img_rgb, 0.7, colored_mask, 0.3, 0)
            
            cv2.drawMarker(blended, (cx_coord, cy_coord), (255, 0, 0), markerType=cv2.MARKER_CROSS, markerSize=30, thickness=3)
            cv2.circle(blended, (cx_coord, cy_coord), 15, (255, 0, 0), 2)
            cv2.putText(blended, "Max Stress Point", (cx_coord + 20, cy_coord + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            depth_vis = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_INFERNO)
            depth_colormap_rgb = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)
            
            cv2.drawMarker(depth_colormap_rgb, (cx_coord, cy_coord), (0, 255, 255), markerType=cv2.MARKER_CROSS, markerSize=30, thickness=3)
            cv2.circle(depth_colormap_rgb, (cx_coord, cy_coord), 15, (0, 255, 255), 2)
            
            st.session_state["terra_blended_img"] = blended
            st.session_state["terra_depth_img"] = depth_colormap_rgb
            st.session_state["terra_depth_grid"] = depth_map
            st.session_state["terra_analysis_done"] = True
        else:
            st.session_state["terra_blended_img"] = img_rgb
            st.session_state["terra_depth_img"] = img_rgb
            st.session_state["terra_analysis_done"] = True
            
        st.session_state["extracted_curvature"] = radius
        st.session_state["terra_analysis_done"] = True

    # 4. 010 Material ID API call with real-time metrology inputs
    url_010 = "http://localhost:8010/detect"
    payload_010 = {
        "roughness": st.session_state["extracted_roughness"],
        "gloss": st.session_state["extracted_gloss"],
        "surface_energy": st.session_state["extracted_sfe"]
    }
    try:
        res_010 = requests.post(url_010, json=payload_010, timeout=2.0)
        if res_010.status_code == 200:
            res_json = res_010.json()
            best_sub = res_json.get("material", "SUS304-2B")
            sub_sim = res_json.get("confidence", 1.0) * 100.0
            best_finish = res_json.get("finish", "2B")
            st.session_state["material_id_service_status"] = "ONLINE"
        else:
            best_sub, best_finish, sub_sim = evaluate_material_id_010(
                st.session_state["extracted_roughness"],
                st.session_state["extracted_gloss"],
                st.session_state["extracted_sfe"]
            )
            st.session_state["material_id_service_status"] = "LOCAL_FALLBACK"
    except Exception:
        best_sub, best_finish, sub_sim = evaluate_material_id_010(
            st.session_state["extracted_roughness"],
            st.session_state["extracted_gloss"],
            st.session_state["extracted_sfe"]
        )
        st.session_state["material_id_service_status"] = "LOCAL_FALLBACK"
        
    st.session_state["identified_substrate"] = best_sub
    st.session_state["identified_similarity"] = sub_sim
    st.session_state["extracted_finish"] = best_finish
    st.session_state["show_010_alert"] = True

    # Pre-execute E2E pipeline for the specimen automatically (Simulated demonstration requirement)
    payload = {
        "substrate_id": best_sub,
        "substrate_series": "SGV",
        "thickness_um": 100.0,
        "finish_type": best_finish,
        "metrics": {
            "surface_energy": st.session_state["extracted_sfe"],
            "roughness": st.session_state["extracted_roughness"],
            "gloss": st.session_state["extracted_gloss"],
            "curvature_radius": st.session_state["extracted_curvature"]
        },
        "target": {
            "target_initial_adhesion": 1000.0,
            "target_aged_adhesion": 1500.0,
            "target_tg": -15.0,
            "target_viscosity": 3000.0
        },
        "normal_vector_data": [0.0, 0.0, 1.0],
        "material_stiffness": 180.0
    }
    
    st.session_state["payload_sent"] = payload
    orchestrator_url = "http://localhost:8014/orchestrate"
    try:
        res = requests.post(orchestrator_url, json=payload, timeout=30.0)
        if res.status_code == 200:
            st.session_state["pipeline_result"] = res.json()
    except Exception as ex:
        logger.error(f"Auto E2E pipeline trigger failed: {ex}")
        st.session_state["pipeline_result"] = None

    # Cache the result
    st.session_state["preset_cache"][preset_name] = {
        "water_overlay": st.session_state.get("water_overlay"),
        "glycerol_overlay": st.session_state.get("glycerol_overlay"),
        "extracted_sfe": st.session_state.get("extracted_sfe"),
        "water_angle_res": st.session_state.get("water_angle_res"),
        "glycerol_angle_res": st.session_state.get("glycerol_angle_res"),
        "droplet_analysis_done": st.session_state.get("droplet_analysis_done"),
        "vsams_overlay": st.session_state.get("vsams_overlay"),
        "extracted_roughness": st.session_state.get("extracted_roughness"),
        "extracted_gloss": st.session_state.get("extracted_gloss"),
        "roughness_res": st.session_state.get("roughness_res"),
        "gloss_res": st.session_state.get("gloss_res"),
        "roughness_analysis_done": st.session_state.get("roughness_analysis_done"),
        "terra_blended_img": st.session_state.get("terra_blended_img"),
        "terra_depth_img": st.session_state.get("terra_depth_img"),
        "terra_depth_grid": st.session_state.get("terra_depth_grid"),
        "terra_analysis_done": st.session_state.get("terra_analysis_done"),
        "extracted_curvature": st.session_state.get("extracted_curvature"),
        "identified_substrate": st.session_state.get("identified_substrate"),
        "identified_similarity": st.session_state.get("identified_similarity"),
        "extracted_finish": st.session_state.get("extracted_finish"),
        "show_010_alert": st.session_state.get("show_010_alert"),
        "material_id_service_status": st.session_state.get("material_id_service_status"),
        "payload_sent": st.session_state.get("payload_sent"),
        "pipeline_result": st.session_state.get("pipeline_result"),
    }


