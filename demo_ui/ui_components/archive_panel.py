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
    st.header(t["archive_title"])
    st.write("자동화 모드: 아래 버튼을 누르면 HL, 2B, BA 피착재에 대해 E2E 파이프라인(물성 분석, 역설계)이 자동으로 순차 실행되며 보고서가 즉시 영구 아카이빙됩니다.")

    if st.button("🚀 자동화 데모 전체 실행 (HL, 2B, BA) 및 자동 아카이빙", use_container_width=True):
        substrates_to_run = ["HL", "2B", "BA"]
        script_dir = Path(__file__).resolve().parent
        archive_dir = script_dir.parents[1] / "demo_reports"
        if not archive_dir.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
        orchestrator_url = "http://localhost:8024/orchestrate"

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, sub_id in enumerate(substrates_to_run):
            status_text.write(f"Running E2E Pipeline for {sub_id}... ({idx+1}/{len(substrates_to_run)})")
            
            # Create a mock payload based on typical defaults
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

            try:
                res = requests.post(orchestrator_url, json=payload, timeout=120.0)
                if res.status_code == 200:
                    result = res.json()
                    status = result.get("status", "error")
                    
                    rev_data = {}
                    if status == "matched":
                        rev_data = result.get("reverse_engineered_result", {})
                    elif status == "reverse_engineered":
                        rev_data = result.get("result", {})
                        
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"demo_e2e_report_{sub_id}_{timestamp}.md"
                    file_path = archive_dir / filename

                    proc_archive_data = result.get("processability", {})
                    proc_level_arch = proc_archive_data.get("level", "N/A")
                    proc_reason_arch = proc_archive_data.get("reason", "N/A")

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
                        report_content += f"  - Adhesion: Target {payload['target']['target_initial_adhesion']} / Predicted {p_props.get('측정_값', 'N/A')}\n"
                        report_content += f"  - Viscosity: Target {payload['target']['target_viscosity']} / Predicted {p_props.get('점도(cP)', 'N/A')}\n"
                        report_content += f"  - Tg: Target {payload['target']['target_tg']} / Predicted {p_props.get('Tg', 'N/A')}\n"

                        final_rec = p_props.get("final_recipe", {})
                        if final_rec:
                            report_content += "- Optimized Monomer Recipe:\n"
                            for m_name, m_ratio in final_rec.items():
                                report_content += f"  - {m_name}: {m_ratio:.2f}%\n"

                    with open(file_path, "w", encoding="utf-8") as rf:
                        rf.write(report_content)
                    
                    st.success(f"{sub_id} 파이프라인 실행 및 아카이빙 완료: {file_path.name}")
                else:
                    st.error(f"{sub_id} API Error (HTTP {res.status_code})")
            except Exception as e:
                st.error(f"{sub_id} 실행 실패: {e}")
                
            progress_bar.progress((idx + 1) / len(substrates_to_run))

        status_text.write("✅ 모든 E2E 파이프라인 실행 및 자동 아카이빙이 완료되었습니다.")
