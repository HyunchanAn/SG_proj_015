from pathlib import Path
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
from datetime import datetime
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

def render_archive_panel(t):
    from core.api_client import trigger_all_metrology_analyses_automatically
    st.header(t["archive_title"])
    st.write(t["archive_desc"])

    if st.button(t["archive_btn"], use_container_width=True):
        result = st.session_state.get("pipeline_result", {})
        status = result.get("status", "error")
        
        rev_data = {}
        if status == "matched":
            rev_data = result.get("reverse_engineered_result", {})
        elif status == "reverse_engineered":
            rev_data = result.get("result", {})
            
        archive_dir = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/reports_archive/demo_reports")
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
                report_content += f"- Rank {r_idx+1}: {r.get('product_code')} (Score: {r.get('match_score'):.2f}%)\n"
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
