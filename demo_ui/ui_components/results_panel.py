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

def render_results_panel(t):
    from core.api_client import trigger_all_metrology_analyses_automatically
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
