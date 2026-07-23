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
        "014 (Orchestrator)": 8024
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

def render_health_check(t):
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
