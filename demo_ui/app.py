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

# Add SG_proj_002, SG_proj_003, SG_proj_007, and SG_proj_010 to sys.path to directly access modules
sys.path.append("e:/Github/SG_proj_002")
sys.path.append("e:/Github/SG_proj_003")
sys.path.append("e:/Github/SG_proj_007")
sys.path.append("e:/Github/SG_proj_010")

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
def load_adherend_master_from_db() -> list[dict]:
    db_path = "E:/Github/SG_proj_004/sg_proj_004.db"
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
def check_service_status() -> dict[str, bool]:
    services = {
        "001 (PolySim)": 8001,
        "002 (SFE Vision)": 8002,
        "003 (V-SAMS Vision)": 8003,
        "004 (Database API)": 8004,
        "005 (Anomaly Detect)": 8005,
        "006 (TransPolymer GNN)": 8006,
        "007 (SG-TERRA 3D)": 8007,
        "008 (Shear Holding QC)": 8008,
        "009 (IR Simulator)": 8009,
        "010 (Material ID)": 8010,
        "011 (Processability)": 8011,
        "012 (Matching Engine)": 8012,
        "013 (QA Gateway)": 8013,
        "014 (Orchestrator)": 8014
    }
    
    status_results = {}
    for name, port in services.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                s.connect(("127.0.0.1", port))
                status_results[name] = True
        except (socket.timeout, ConnectionRefusedError, OSError):
            status_results[name] = False
    return status_results

# Helper to generate Mermaid code
def generate_mermaid_code(health: dict[str, bool]) -> str:
    mapping = {
        "001 (PolySim)": "M001",
        "002 (SFE Vision)": "M002",
        "003 (V-SAMS Vision)": "M003",
        "004 (Database API)": "M004",
        "005 (Anomaly Detect)": "M005",
        "006 (TransPolymer GNN)": "M006",
        "007 (SG-TERRA 3D)": "M007",
        "008 (Shear Holding QC)": "M008",
        "009 (IR Simulator)": "M009",
        "010 (Material ID)": "M010",
        "011 (Processability)": "M011",
        "012 (Matching Engine)": "M012",
        "013 (QA Gateway)": "M013",
        "014 (Orchestrator)": "M014"
    }
    
    code = """%%{init: {'flowchart': {'curve': 'ortho'}}}%%
    flowchart TD
    classDef online fill:#059669,stroke:#047857,color:#ffffff,stroke-width:2px;
    classDef offline fill:#dc2626,stroke:#b91c1c,color:#ffffff,stroke-width:2px;

    subgraph STEP1 ["Step 1: Vision & Physics Metrology"]
        M002["002 SFE Vision"]
        M003["003 V-SAMS"]
        M007["007 SG-TERRA 3D"]
    end

    subgraph QC ["Quality Control (Independent)"]
        M005["005 Anomaly QC"]
        M008["008 Shear QC"]
    end

    subgraph STEP2 ["Step 2: Orchestration & Databases"]
        M014["014 Orchestrator API"]
        M011["011 Processability"]
        M010["010 Material ID"]
        M012["012 Matching Engine"]
        M004[("004 Database API")]
    end

    subgraph STEP3 ["Step 3: AI Inverse Design Loop"]
        M013["013 QA Gateway"]
        M001["001 PolySim Model"]
        M006["006 TransPolymer GNN"]
        M009["009 IR Simulator"]
    end

    STEP1 --> STEP2
    STEP2 --> STEP3

    M002 --> M014
    M003 --> M014
    M007 --> M011
    M007 --> M014

    M014 --> M011
    M014 --> M010
    M010 --> M014
    M011 --> M012
    M014 --> M012
    M012 --> M014
    M014 --> M004

    M014 --> M013
    M013 --> M001
    M013 --> M006
    M001 --> M009
    M006 --> M009
    M009 --> M013

    M003 --> M004
    M012 --> M004
    M004 --> M012
    M010 --> M004
    M001 --> M004
    M009 --> M004
    """
    for name, is_active in health.items():
        node_id = mapping.get(name)
        if node_id:
            cls = "online" if is_active else "offline"
            code += f"\n    class {node_id} {cls};"
    return code

# Render Mermaid
def render_mermaid(code: str, height: int = 700):
    html_code = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>
                mermaid.initialize({{ 
                    startOnLoad: true, 
                    theme: 'dark',
                    themeVariables: {{
                        background: 'transparent',
                        primaryColor: '#1e293b',
                        lineColor: '#64748b',
                        edgeLabelBackground: '#1e293b',
                        tertiaryColor: '#0f172a'
                    }}
                }});
            </script>
            <style>
                body {{
                    background-color: transparent !important;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }}
                .mermaid {{
                    background: transparent;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid">
                {code}
            </div>
        </body>
    </html>
    """
    components.html(html_code, height=height)



# Automatic orchestration runner to trigger step 1 metrology processes dynamically
def trigger_all_metrology_analyses_automatically(preset_name: str):
    logger.info(f"Triggering auto-metrology analyses for preset: {preset_name}")
    
    base_droplet_path = Path("E:/Github/SG_proj_015/260521 test_image (droplet)")
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
            save_dir = Path("E:/Github/SG_proj_015/reports_archive/images")
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
            "target_initial_adhesion": 450.0,
            "target_aged_adhesion": 850.0,
            "target_tg": -25.0,
            "target_viscosity": 4000.0
        },
        "normal_vector_data": [0.0, 0.0, 1.0],
        "material_stiffness": 200000.0
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





# Language Selector Setup
selected_lang = st.radio("Language Selector", options=["KO", "EN"], horizontal=True, index=0)
t = TRANSLATIONS[selected_lang]

st.markdown(f'<div class="main-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{t["subtitle"]}</div>', unsafe_allow_html=True)

# 1. System Health Status Panel
st.header(t["health_check_title"])
with st.spinner(t["health_check_spinner"]):
    health_status = check_service_status()

active_count = sum(1 for v in health_status.values() if v)
total_count = len(health_status)

mermaid_diagram_code = generate_mermaid_code(health_status)
render_mermaid(mermaid_diagram_code, height=650)

st.subheader(t["table_summary_header"])
summary_data = []
for name, is_active in health_status.items():
    badge = "🟢 ONLINE" if is_active else "🔴 OFFLINE"
    summary_data.append({"Service": name.split(" (")[0], "Status": badge})
st.table(pd.DataFrame(summary_data))

if active_count == total_count:
    st.success(t["healthy_status"].format(active=active_count, total=total_count))
elif active_count > 0:
    st.warning(t["partial_status"].format(active=active_count, total=total_count))
else:
    st.error(t["offline_status"])

st.divider()

# 1.5 Live Step 1 Vision Metrology
st.header(t["step1_vision_title"])
st.write(t["step1_desc"])

selected_demo_preset = st.selectbox(t["specimen_select_label"], options=["HL", "BA", "2B"], index=0)

if "last_demo_preset" not in st.session_state:
    st.session_state["last_demo_preset"] = None

# Automatically run all analyses when specimen preset is changed or initial load happens
if st.session_state["last_demo_preset"] != selected_demo_preset:
    st.session_state["last_demo_preset"] = selected_demo_preset
    trigger_all_metrology_analyses_automatically(selected_demo_preset)
    st.rerun()

base_droplet_path = Path("E:/Github/SG_proj_015/260521 test_image (droplet)")
finish_folder = base_droplet_path / selected_demo_preset

default_water_path = finish_folder / f"{selected_demo_preset}_water.jpg"
default_glycerol_path = finish_folder / f"{selected_demo_preset}_glycerol.jpg"
default_reflect_path = finish_folder / f"{selected_demo_preset}_reflect.jpg"
default_007_path = base_droplet_path / "example_01.jpg"


# --- 002 SFE Module Section ---
st.markdown('<div class="status-card">', unsafe_allow_html=True)
st.subheader(t["droplet_section"])
st.caption(t["droplet_desc"])

water_file = st.file_uploader(t["upload_water"], type=["png", "jpg", "jpeg"])
if water_file:
    st.image(water_file, caption="Polar Droplet (Uploaded)", use_container_width=True)
elif default_water_path.exists():
    st.image(default_water_path.as_posix(), caption=f"Preset: {selected_demo_preset}_water.jpg", use_container_width=True)

if st.session_state["water_overlay"]:
    st.image(st.session_state["water_overlay"], caption="Water Droplet & Coin Segmented Boundaries", use_container_width=True)

glycerol_file = st.file_uploader(t["upload_glycerol"], type=["png", "jpg", "jpeg"])
if glycerol_file:
    st.image(glycerol_file, caption="Dispersive Droplet (Uploaded)", use_container_width=True)
elif default_glycerol_path.exists():
    st.image(default_glycerol_path.as_posix(), caption=f"Preset: {selected_demo_preset}_glycerol.jpg", use_container_width=True)

if st.session_state["glycerol_overlay"]:
    st.image(st.session_state["glycerol_overlay"], caption="Glycerol Droplet & Coin Segmented Boundaries", use_container_width=True)

volume_input_val_ul = st.number_input("Liquid Droplet Volume (uL)", min_value=0.1, max_value=500.0, value=200.0, step=1.0)
run_droplet = st.button(t["run_droplet_btn"], type="secondary", use_container_width=True)

if run_droplet:
    water_data, glycerol_data = None, None
    w_name, g_name = None, None
    
    if water_file:
        water_data = water_file.read()
        w_name = water_file.name
    elif default_water_path.exists():
        with open(default_water_path, "rb") as f:
            water_data = f.read()
        w_name = default_water_path.name
        
    if glycerol_file:
        glycerol_data = glycerol_file.read()
        g_name = glycerol_file.name
    elif default_glycerol_path.exists():
        with open(default_glycerol_path, "rb") as f:
            glycerol_data = f.read()
        g_name = default_glycerol_path.name
        
    if water_data and glycerol_data:
        st.session_state["water_overlay"] = generate_contour_overlay(water_data, is_droplet=True)
        st.session_state["glycerol_overlay"] = generate_contour_overlay(glycerol_data, is_droplet=True)
        
        # Execute 002 SFE directly in memory using the calibrated local physics engine
        water_angle, glycerol_angle, calc_sfe = calculate_local_sfe_droplet(water_data, glycerol_data, volume_input_val_ul, selected_demo_preset=selected_demo_preset)
            
        st.session_state["extracted_sfe"] = calc_sfe
        st.session_state["water_angle_res"] = water_angle
        st.session_state["glycerol_angle_res"] = glycerol_angle
        st.session_state["droplet_analysis_done"] = True
        
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


        
        st.success(t["droplet_success"])
        st.rerun()

# Visually display result parameters of 002 if executed
if st.session_state["droplet_analysis_done"]:
    html_content = """
    <div class="result-badge">
        <h4 style="margin:0; color:#3b82f6;">002 SFE Analysis Output</h4>
        <div style="display:flex; justify-content:space-between; margin-top:0.5rem; font-size:0.95rem;">
            <span>Water Contact Angle: <b>{:.2f}°</b></span>
            <span>Glycerol Contact Angle: <b>{:.2f}°</b></span>
            <span>OWRK 표면에너지: <b>{:.2f} dyne/cm</b></span>
        </div>
    </div>
    """.format(st.session_state['water_angle_res'], st.session_state['glycerol_angle_res'], st.session_state['extracted_sfe'])
    st.markdown(html_content, unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)


# --- 003 V-SAMS Module Section ---
st.markdown('<div class="status-card">', unsafe_allow_html=True)
st.subheader(t["roughness_section"])
st.caption(t["roughness_desc"])

reflect_file = st.file_uploader(t["upload_reflect"], type=["png", "jpg", "jpeg"])

if reflect_file:
    st.image(reflect_file, caption="Anisotropic Reflect Surface (Uploaded)", use_container_width=True)
elif default_reflect_path.exists():
    st.image(default_reflect_path.as_posix(), caption=f"Preset: {selected_demo_preset}_reflect.jpg", use_container_width=True)

if st.session_state["vsams_overlay"]:
    st.image(st.session_state["vsams_overlay"], caption="Sharpness Variance Gradient Map (V-SAMS Edge Contrast)", use_container_width=True)
        
run_roughness = st.button(t["run_roughness_btn"], type="secondary", use_container_width=True)

if run_roughness:
    ref_data = None
    ref_name = None
    
    if reflect_file:
        ref_data = reflect_file.read()
        ref_name = reflect_file.name
    elif default_reflect_path.exists():
        with open(default_reflect_path, "rb") as f:
            ref_data = f.read()
        ref_name = default_reflect_path.name
        
    if ref_data:
        # Generate and save V-SAMS sharpness gradient colormap
        st.session_state["vsams_overlay"] = generate_vsams_visual(ref_data)
        
        # Execute 003 V-SAMS directly in memory using the calibrated local physics engine
        ext_ra, ext_gloss, vsams_overlay_bytes = calculate_local_vsams_roughness(ref_data, selected_demo_preset=selected_demo_preset)
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
            save_dir = Path("E:/Github/SG_proj_015/reports_archive/images")
            save_dir.mkdir(parents=True, exist_ok=True)
            if st.session_state.get("vsams_overlay"):
                with open(save_dir / f"{selected_demo_preset}_reflect_verify_finish.jpg", "wb") as fimg:
                    fimg.write(st.session_state["vsams_overlay"])
                with open(save_dir / f"{selected_demo_preset}_detected_layout.jpg", "wb") as fimg:
                    fimg.write(st.session_state["vsams_overlay"])
        except Exception as io_err:
            logger.error(f"Failed to write 003 archive images: {io_err}")


        
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


        
        st.success(t["roughness_success"])
        st.rerun()

# Visually display result parameters of 003 if executed
if st.session_state["roughness_analysis_done"]:
    html_content_rough = """
    <div class="result-badge">
        <h4 style="margin:0; color:#3b82f6;">003 V-SAMS Analysis Output</h4>
        <div style="display:flex; justify-content:space-between; margin-top:0.5rem; font-size:0.95rem;">
            <span>측정 표면 조도 Ra: <b>{:.1f} nm</b></span>
            <span>측정 광택도: <b>{:.1f} GU</b></span>
        </div>
    </div>
    """.format(st.session_state['roughness_res'], st.session_state['gloss_res'])
    st.markdown(html_content_rough, unsafe_allow_html=True)




st.markdown('</div>', unsafe_allow_html=True)


# --- 007 SG-TERRA 3D Module Section ---
st.markdown('<div class="status-card">', unsafe_allow_html=True)
st.subheader(t["terra_section"])
st.caption(t["terra_desc"])

terra_file = st.file_uploader(t["upload_007"], type=["png", "jpg", "jpeg"])

if terra_file:
    st.image(terra_file, caption="Metal Press Specimen (Uploaded)", use_container_width=True)
elif default_007_path.exists():
    st.image(default_007_path.as_posix(), caption="Default Preset: example_01.jpg (Metal Press)", use_container_width=True)
    
reference_scale = st.number_input(t["scale_label"], min_value=1.0, max_value=500.0, value=24.0, step=1.0)

run_007 = st.button(t["run_007_btn"], type="secondary", use_container_width=True)

if run_007:
    image_data = None
    file_name = None
    
    if terra_file:
        image_data = terra_file.read()
        file_name = terra_file.name
    elif default_007_path.exists():
        with open(default_007_path, "rb") as f:
            image_data = f.read()
        file_name = default_007_path.name
        
    if image_data:
        sam_w, depth_w = get_cached_models_007()
        
        nparr = np.frombuffer(image_data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        
        url_007 = "http://localhost:8007/api/v1/analyze"
        files_payload = {"file": (file_name, image_data, "image/jpeg")}
        form_payload = {"ref_length_mm": reference_scale, "roughness": 1.0}
        
        try:
            res_007 = requests.post(url_007, files=files_payload, data=form_payload, timeout=10.0)
            res_json = res_007.json()
            radius = res_json.get("metrics", {}).get("estimated_radius_mm", 150.0)
            cx_coord = res_json.get("metrics", {}).get("critical_point_coords", {}).get("x", w // 2)
            cy_coord = res_json.get("metrics", {}).get("critical_point_coords", {}).get("y", h // 2)
        except Exception:
            radius = 150.0
            cx_coord, cy_coord = w // 2, h // 2
            
        if sam_w is not None and depth_w is not None:
            prompt_pts = np.array([[cx_coord, cy_coord]])
            prompt_lbls = np.array([1])
            target_mask = sam_w.segment_target(img_rgb, prompt_points=prompt_pts, prompt_labels=prompt_lbls)
            depth_map = depth_w.estimate_depth(img_rgb, mask=target_mask)
            
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
        st.success(t["007_success"].format(radius=radius))
        st.rerun()

# Display real 007 segmentation & depth maps if executed
if st.session_state["terra_analysis_done"]:
    st.subheader("007 Multimodal Outputs")
    col1, col2 = st.columns(2)
    with col1:
        st.image(st.session_state["terra_blended_img"], caption="SAM 2 Target Segmentation Mask (with Max Stress Point)", use_container_width=True)
    with col2:
        st.image(st.session_state["terra_depth_img"], caption="Depth-Anything-V2 Topography Depth Map", use_container_width=True)
        
    if st.session_state["terra_depth_grid"] is not None:
        with st.expander("Show Interactive 3D Topographic Grid (Plotly)", expanded=False):
            resized = cv2.resize(st.session_state["terra_depth_grid"], (80, 80), interpolation=cv2.INTER_AREA)
            fig = go.Figure(data=[go.Surface(z=resized, colorscale="Inferno")])
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=10),
                height=300,
                scene=dict(aspectratio=dict(x=1, y=1, z=0.3))
            )
            st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 010 Material ID Real-Time Result Card ---
if st.session_state["show_010_alert"]:
    status_msg = ""
    status_style = "background: rgba(16, 185, 129, 0.15); border: 1.5px solid #10b981; padding: 1.2rem; border-radius: 12px; margin-top: 1.5rem; margin-bottom: 1.5rem;"
    title_color = "#10b981"
    
    if st.session_state.get("material_id_service_status", "ONLINE") == "LOCAL_FALLBACK":
        status_style = "background: rgba(245, 158, 11, 0.15); border: 1.5px solid #f59e0b; padding: 1.2rem; border-radius: 12px; margin-top: 1.5rem; margin-bottom: 1.5rem;"
        title_color = "#f59e0b"
        status_msg = "<br><span style='color: #f59e0b; font-weight: bold;'>[오프라인 알림] 010 API 서비스 포트(8010) 오프라인 상태로 인해, 대시보드 내 인메모리 로컬 물리 매처(SubstrateMatcher)로 대체 분석을 수행했습니다.</span>"

    st.markdown(f"""
    <div style="{status_style}">
        <h4 style="margin: 0; color: {title_color};">[010 피착재 자동 판단 모듈 (Material ID)]</h4>
        <p style="margin: 0.5rem 0 0 0; color: #cbd5e1; font-size: 0.95rem;">
            비전 계측 물성 대조 분석 결과, 감지된 피착재는 <b>{st.session_state['identified_substrate']}</b> 입니다. (정합 유사도: <b>{st.session_state['identified_similarity']:.2f}%</b>)
            {status_msg}
            <br><span style="font-size: 0.85rem; color: #94a3b8;">*이 판단 결과는 아래 2단계 제품명(피착재명)에 자동으로 자동 바인딩되었습니다.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    
    st.caption("010 Matching Diagnostic Database Comparison Profile:")
    st.table(pd.DataFrame([
        {"Feature": "Surface Free Energy (SFE)", "Input Value": f"{st.session_state['extracted_sfe']:.2f} dyne/cm"},
        {"Feature": "Surface Roughness (Ra)", "Input Value": f"{st.session_state['extracted_roughness']:.1f} nm"},
        {"Feature": "Specular Gloss (GU)", "Input Value": f"{st.session_state['extracted_gloss']:.1f} GU"}
    ]))


st.divider()

# 2. Control Panel & Inputs
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
        orchestrator_url = "http://localhost:8014/orchestrate"
        
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
    st.header(t["result_title"])
    
    result = st.session_state["pipeline_result"]
    status = result.get("status", "error")
    
    if status == "matched":
        st.markdown(f"""
        <div class="custom-card" style="border-left: 8px solid #2ecc71;">
            <h2 style="color: #2ecc71; margin-top: 0; font-size: 1.5rem;">{t["status_matched"]}</h2>
            <p style="color: #cbd5e1; font-size: 0.95rem;">{t["status_matched_desc"]}</p>
        </div>
        """, unsafe_allow_html=True)
    elif status == "reverse_engineered":
        st.markdown(f"""
        <div class="custom-card" style="border-left: 8px solid #f39c12;">
            <h2 style="color: #f39c12; margin-top: 0; font-size: 1.5rem;">{t["status_rev"]}</h2>
            <p style="color: #cbd5e1; font-size: 0.95rem;">{t["status_rev_desc"]}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Pipeline failed.")
        
    tab1, tab2, tab3 = st.tabs([t["tab1_title"], t["tab2_title"], t["tab3_title"]])
    
    with tab1:
        st.subheader(t["sfe_title"])
        
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown(f"### {t['sfe_title']}")
        original_sfe = st.session_state["payload_sent"]["metrics"]["surface_energy"]
        
        corrected_sfe = original_sfe
        is_hl = st.session_state["payload_sent"]["finish_type"] == "Hairline"
        measured_roughness = st.session_state["payload_sent"]["metrics"]["roughness"]
        
        if is_hl and measured_roughness > 0:
            alpha = 0.35
            # Convert measured_roughness from nm to um for the original equation
            corrected_sfe = min(45.0, original_sfe * (1.0 + alpha * (measured_roughness / 1000.0)))
            
        st.write(f"{t['measured_sfe_label']}: {original_sfe:.2f} dyne/cm")
        st.write(f"{t['corrected_sfe_label']}: {corrected_sfe:.2f} dyne/cm")
        
        if is_hl:
            st.info(t["sfe_hl_info"])
            delta = corrected_sfe - original_sfe
            st.metric(t["sfe_shift_label"], f"{delta:+.2f} dyne/cm", delta_color="normal")
        else:
            st.info(t["sfe_no_hl_info"])

        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown(f"### {t['proc_title']}")
        
        st.write(f"{t['sub_series_label']}: {st.session_state['payload_sent']['substrate_series']}")
        st.write(f"{t['thick_label']}: {st.session_state['payload_sent']['thickness_um']} um")
        
        # Binding processability outputs from actual central orchestrator API (011 result)
        proc_data = result.get("processability", {})
        final_level = proc_data.get("level", 3)
        reason = proc_data.get("reason", "Standard processability.")
        is_fallback = proc_data.get("is_fallback", False)
        
        st.markdown(f"**{t['calc_sev_label']}**: `Level {final_level}/5`")
        st.progress(final_level / 5.0)
        st.caption(f"Evaluation Reason: {reason}")
        if is_fallback:
            st.caption("*Dynamic boundary safety fallback level applied.")
        st.markdown('</div>', unsafe_allow_html=True)

            
    with tab2:
        st.subheader(t["db_match_title"])
        if status == "matched":
            match_data = result.get("result", {})
            recoms = match_data.get("recommendations", [])
            
            if recoms:
                for idx, rec in enumerate(recoms):
                    st.markdown(f"""
                    <div class="status-card" style="border-top: 5px solid #2ecc71;">
                        <h4 style="margin: 0; color: #2ecc71;">{t['rank_label']} {idx+1}: {rec.get('product_code')}</h4>
                        <p style="font-size: 1.3rem; font-weight: 600; margin: 0.5rem 0;">{t['score_label']}: {rec.get('match_score'):.2%}</p>
                        <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;">{t['match_details_label']}:</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.json(rec.get("match_reason", {}))
            else:
                st.info("No specific products returned in recommendation schema.")
        else:
            st.warning(t["db_failed"])
            
    with tab3:
        st.subheader(t["inverse_title"])
        
        rev_data = {}
        if status == "matched":
            rev_data = result.get("reverse_engineered_result", {})
        elif status == "reverse_engineered":
            rev_data = result.get("result", {})
            
        if rev_data:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown(f"### {t['conv_status']}")
            is_passed = rev_data.get("is_passed", False)
            conf_score = rev_data.get("confidence_score", 0.0)
            
            pass_badge = t["verdict_passed"] if is_passed else t["verdict_failed"]
            st.write(f"{t['verdict_label']}: {pass_badge}")
            st.write(f"{t['gnn_conf_label']}: {conf_score:.2%}")
            st.progress(conf_score)
            
            st.markdown(f"#### {t['adh_rhead_label']}")
            pred_props = rev_data.get("predicted_properties", {})
            error_rates = rev_data.get("error_rates", {})
            
            target_data = st.session_state["payload_sent"]["target"]
            
            lbl_init_adh = "Initial Adhesion (gf/25mm)" if selected_lang == "EN" else "초기 점착력 (gf/25mm)"
            lbl_visc = "Viscosity (cps)" if selected_lang == "EN" else "점도 (cps)"
            lbl_tg = "Tg (°C)" if selected_lang == "EN" else "Tg (°C)"
            
            compare_rows = [
                {"Metric": lbl_init_adh, "Target": target_data["target_initial_adhesion"], "Predicted": pred_props.get("측정_값", "N/A"), "Error Rate": f"{error_rates.get('측정_값', 0.0):.2%}" if "측정_값" in error_rates else "N/A"},
                {"Metric": lbl_visc, "Target": target_data["target_viscosity"], "Predicted": pred_props.get("점도(cP)", "N/A"), "Error Rate": f"{error_rates.get('점도(cP)', 0.0):.2%}" if "점도(cP)" in error_rates else "N/A"},
                {"Metric": lbl_tg, "Target": target_data["target_tg"], "Predicted": pred_props.get("Tg", "N/A"), "Error Rate": f"{error_rates.get('Tg', 0.0):.2%}" if "Tg" in error_rates else "N/A"}
            ]
            st.table(pd.DataFrame(compare_rows))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown(f"### {t['recipe_title']}")
            
            recipe = pred_props.get("final_recipe", {})
            if not recipe and "recipe" in rev_data:
                recipe = rev_data["recipe"]
                
            if recipe:
                labels = list(recipe.keys())
                values = list(recipe.values())
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values, 
                    circle=.4,
                    marker=dict(colors=["#1f4068", "#162447", "#e43f5a", "#3b82f6", "#10b981", "#f59e0b"])
                )])
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=250,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f1f5f9")
                )
                st.plotly_chart(fig, use_container_width=True)
                
                recipe_str = ", ".join([f"{k}: {v:.2f}%" for k, v in recipe.items()])
                st.caption(f"{t['opt_form_label']}: {recipe_str}")
            else:
                st.info(t["no_recipe_info"])
            st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.subheader(t["comp_title"])
            st.caption(t["comp_desc"])
            
            matched_success = (status == "matched")
            top_product = None
            if matched_success:
                match_data = result.get("result", {})
                recoms = match_data.get("recommendations", [])
                if recoms:
                    top_product = recoms[0].get("product_code")
            
            if top_product:
                comm_recipe = get_actual_product_recipe(top_product)
                ai_recipe = pred_props.get("final_recipe", {})
                if not ai_recipe and "recipe" in rev_data:
                    ai_recipe = rev_data["recipe"]
                
                all_monomers = sorted(list(set(comm_recipe.keys()) | set(ai_recipe.keys())))
                
                st.markdown(f"**{t['comm_recipe_label']} ({top_product})**")
                labels_c = list(comm_recipe.keys())
                values_c = list(comm_recipe.values())
                fig_c = go.Figure(data=[go.Pie(
                    labels=labels_c,
                    values=values_c,
                    hole=.4,
                    marker=dict(colors=["#3b82f6", "#10b981", "#f59e0b", "#e43f5a"])
                )])
                fig_c.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=200,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f1f5f9")
                )
                st.plotly_chart(fig_c, use_container_width=True)
                
                st.divider()
                
                st.markdown(f"**{t['ai_recipe_label']}**")
                labels_a = list(ai_recipe.keys())
                values_a = list(ai_recipe.values())
                fig_a = go.Figure(data=[go.Pie(
                    labels=labels_a,
                    values=values_a,
                    hole=.4,
                    marker=dict(colors=["#1f4068", "#162447", "#e43f5a", "#3b82f6", "#10b981", "#f59e0b"])
                )])
                fig_a.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=200,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f1f5f9")
                )
                st.plotly_chart(fig_a, use_container_width=True)
                
                st.markdown(f"**{t['deviation_label']}**")
                comp_rows = []
                bar_labels = []
                bar_comm_vals = []
                bar_ai_vals = []
                
                for m in all_monomers:
                    c_val = comm_recipe.get(m, 0.0)
                    a_val = ai_recipe.get(m, 0.0)
                    err = abs(c_val - a_val)
                    comp_rows.append({
                        t["monomer_name_label"]: m,
                        t["comm_ratio_label"]: f"{c_val:.2f}%",
                        t["ai_ratio_label"]: f"{a_val:.2f}%",
                        t["abs_error_label"]: f"{err:.2f}%"
                    })
                    bar_labels.append(m)
                    bar_comm_vals.append(c_val)
                    bar_ai_vals.append(a_val)
                
                st.table(pd.DataFrame(comp_rows))
                
                fig_bar = go.Figure(data=[
                    go.Bar(name=t['comm_recipe_label'], x=bar_labels, y=bar_comm_vals, marker_color="#3b82f6"),
                    go.Bar(name=t['ai_recipe_label'], x=bar_labels, y=bar_ai_vals, marker_color="#e43f5a")
                ])
                fig_bar.update_layout(
                    barmode='group',
                    height=250,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f1f5f9")
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            else:
                st.info(t["no_matched_prod_info"])
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(t["no_inverse_info"])
            
    # 4. Archivial Action
    st.divider()
    st.header(t["archive_title"])
    st.write(t["archive_desc"])
    
    if st.button(t["archive_btn"], use_container_width=True):
        archive_dir = Path("E:/Github/SG_proj_015/reports_archive/demo_reports")
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_e2e_report_{st.session_state['payload_sent']['substrate_id']}_{timestamp}.md"
        file_path = archive_dir / filename
        
        proc_archive_data = result.get("processability", {})
        proc_level_arch = proc_archive_data.get("level", "N/A")
        proc_reason_arch = proc_archive_data.get("reason", "N/A")

        report_content = f"""# E2E Integrated Pipeline Demonstration Report
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Substrate ID: {st.session_state['payload_sent']['substrate_id']}
- Substrate Series: {st.session_state['payload_sent']['substrate_series']}
- Thickness: {st.session_state['payload_sent']['thickness_um']} um
- Finish Type: {st.session_state['payload_sent']['finish_type']}

## 1. Input Specifications
### Physical Metrology
- Surface Free Energy: {st.session_state['payload_sent']['metrics']['surface_energy']} mN/m
- Roughness (Ra): {st.session_state['payload_sent']['metrics']['roughness']} um
- Gloss: {st.session_state['payload_sent']['metrics']['gloss']} GU
- Curvature Radius: {st.session_state['payload_sent']['metrics']['curvature_radius']} mm

### Target Adhesion Requirements
- Initial Adhesion: {st.session_state['payload_sent']['target']['target_initial_adhesion']} gf/25mm
- Aged Adhesion: {st.session_state['payload_sent']['target']['target_aged_adhesion']} gf/25mm
- Glass Transition Temp (Tg): {st.session_state['payload_sent']['target']['target_tg']} C
- Target Viscosity: {st.session_state['payload_sent']['target']['target_viscosity']} cps

## 2. Integrated Processing Summary
- E2E Pipeline Output Status: {status.upper()}
- Processability Evaluation: Level {proc_level_arch}/5 ({proc_reason_arch})

"""

        if status == "matched":
            match_data = result.get("result", {})
            recoms = match_data.get("recommendations", [])
            report_content += "## 3. Product Matching Results\n"
            for r_idx, r in enumerate(recoms):
                report_content += f"- Rank {r_idx+1}: {r.get('product_code')} (Score: {r.get('match_score'):.2%})\n"
                report_content += f"  - Reason: {json.dumps(r.get('match_reason'), indent=2)}\n"
        else:
            report_content += "## 3. Product Matching Results\n- No database matches found.\n"

        if rev_data:
            report_content += "\n## 4. AI Inverse Molecular Design Results\n"
            report_content += f"- GNN Verification: {'PASSED' if rev_data.get('is_passed') else 'FAILED'}\n"
            report_content += f"- GNN Confidence Score: {rev_data.get('confidence_score', 0.0):.2%}\n"
            
            p_props = rev_data.get("predicted_properties", {})
            report_content += "- Predicted vs Target Deviation:\n"
            report_content += f"  - Adhesion: Target {st.session_state['payload_sent']['target']['target_initial_adhesion']} / Predicted {p_props.get('측정_값', 'N/A')}\n"
            report_content += f"  - Viscosity: Target {st.session_state['payload_sent']['target']['target_viscosity']} / Predicted {p_props.get('점도(cP)', 'N/A')}\n"
            report_content += f"  - Tg: Target {st.session_state['payload_sent']['target']['target_tg']} / Predicted {p_props.get('Tg', 'N/A')}\n"
            
            final_rec = p_props.get("final_recipe", {})
            if final_rec:
                report_content += "- Optimized Monomer Recipe:\n"
                for m_name, m_ratio in final_rec.items():
                    report_content += f"  - {m_name}: {m_ratio:.2f}%\n"

        try:
            with open(file_path, "w", encoding="utf-8") as rf:
                rf.write(report_content)
            st.success(t["archive_success"].format(path=file_path.as_posix()))
        except Exception as save_err:
            st.error(f"Failed to save archive report: {save_err}")
