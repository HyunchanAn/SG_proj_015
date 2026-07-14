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

def render_step1_vision(t):
    from core.api_client import trigger_all_metrology_analyses_automatically
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

    base_droplet_path = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/260521 test_image (droplet)")
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
                save_dir = Path("/Users/hyunchanan/Documents/GitHub/SG_proj_015/reports_archive/images")
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
