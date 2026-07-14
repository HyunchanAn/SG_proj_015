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
import concurrent.futures

def auto_run_e2e_background(sub_id):
    orchestrator_url = "http://localhost:8024/orchestrate"
    payload = {
        "substrate_id": sub_id,
        "substrate_series": "SGV",
        "thickness_um": 100.0,
        "finish_type": sub_id if sub_id in ["BA", "2B"] else "Hairline",
        "metrics": {
            "surface_energy": 45.0,
            "roughness": 200.0,
            "gloss": 100.0,
            "curvature_radius": 10.0
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

    res = requests.post(orchestrator_url, json=payload, timeout=120.0)
    if res.status_code != 200:
        raise Exception(f"API Error {res.status_code}")
    
    result = res.json()
    status = result.get("status", "error")
    rev_data = result.get("reverse_engineered_result", {}) if status == "matched" else result.get("result", {})
    
    archive_dir = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/reports_archive/demo_reports")
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"demo_e2e_report_{sub_id}_{timestamp}.md"
    file_path = archive_dir / filename

    proc_archive_data = result.get("processability", {})
    
    report_content = f"""# E2E Integrated Pipeline Demonstration Report
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Substrate ID: {sub_id}
- Substrate Series: {payload['substrate_series']}
- Thickness: {payload['thickness_um']} um
- Finish Type: {payload['finish_type']}

## 1. Input Specifications
### Physical Metrology
- Surface Free Energy: {payload['metrics']['surface_energy']} mN/m
- Roughness (Ra): {payload['metrics']['roughness']} um
- Gloss: {payload['metrics']['gloss']} GU
- Curvature Radius: {payload['metrics']['curvature_radius']} mm

### Target Adhesion Requirements
- Initial Adhesion: {payload['target']['target_initial_adhesion']} gf/25mm
- Aged Adhesion: {payload['target']['target_aged_adhesion']} gf/25mm
- Glass Transition Temp (Tg): {payload['target']['target_tg']} C
- Target Viscosity: {payload['target']['target_viscosity']} cps

## 2. Integrated Processing Summary
- E2E Pipeline Output Status: {status.upper()}
- Processability Evaluation: Level {proc_archive_data.get('level', 'N/A')}/5 ({proc_archive_data.get('reason', 'N/A')})

"""
    if status == "matched":
        recoms = result.get("result", {}).get("recommendations", [])
        report_content += "## 3. Product Matching Results\n"
        for r_idx, r in enumerate(recoms):
            report_content += f"- Rank {r_idx+1}: {r.get('product_code')} (Score: {r.get('match_score'):.2f}%)\n"
    else:
        report_content += "## 3. Product Matching Results\n- No database matches found.\n"

    if rev_data:
        report_content += "\n## 4. AI Inverse Molecular Design Results\n"
        report_content += f"- GNN Verification: {'PASSED' if rev_data.get('is_passed') else 'FAILED'}\n"
        p_props = rev_data.get("predicted_properties", {})
        report_content += f"- Adhesion: Target {payload['target']['target_initial_adhesion']} / Predicted {p_props.get('측정_값', 'N/A')}\n"
        report_content += f"- Viscosity: Target {payload['target']['target_viscosity']} / Predicted {p_props.get('점도(cP)', 'N/A')}\n"
        report_content += f"- Tg: Target {payload['target']['target_tg']} / Predicted {p_props.get('Tg', 'N/A')}\n"
        if p_props.get("final_recipe"):
            report_content += "- Optimized Monomer Recipe:\n"
            for m_name, m_ratio in p_props["final_recipe"].items():
                report_content += f"  - {m_name}: {m_ratio:.2f}%\n"

    with open(file_path, "w", encoding="utf-8") as rf:
        rf.write(report_content)
    
    return file_path.name

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

# ---------------------------------------------------------
# NEW: Fully Automated Asynchronous E2E Run on Startup
# ---------------------------------------------------------
if "auto_e2e_completed" not in st.session_state:
    st.session_state["auto_e2e_completed"] = True
    
    # Create an empty container that we can clear later
    loading_container = st.empty()
    
    with loading_container.container():
        st.markdown("<h3 style='text-align: center; color: #4B90E2;'>Surfy가 시연용 사진을 분석하고 있어요... 📸</h3>", unsafe_allow_html=True)
        
        # Centered GIF
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("/Users/hyunchanan/Documents/GitHub/SG_proj_015/Surfy_gif_001.gif", use_container_width=True)

        substrates = ["HL", "2B", "BA"]
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(auto_run_e2e_background, s): s for s in substrates}
                for future in concurrent.futures.as_completed(futures):
                    s = futures[future]
                    completed += 1
                    try:
                        res_file = future.result()
                        st.toast(f"✅ {s} 분석 및 아카이빙 완료! ({res_file})")
                    except Exception as e:
                        st.toast(f"❌ {s} 분석 실패: {e}")
    
    # Clear the loading messages and GIF after completion
    loading_container.empty()
                
    st.success("🎉 모든 3종 피착재에 대한 AI 예측, 매칭, 역설계 및 최종 보고서 아카이빙이 완벽하게 자동 처리되었습니다! (손 안 대셔도 됩니다)")
    st.markdown("---")
# ---------------------------------------------------------

render_health_check(t)
st.markdown('---')
render_step1_vision(t)
render_input_panel(t)
render_results_panel(t)
render_archive_panel(t)
