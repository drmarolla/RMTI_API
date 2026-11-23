"""Interactive 3D tumour-stage models (schematic). Layers can be hidden, isolated or faded, like an anatomy viewer."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

import content
from rmti_ui import disclaimer, page_header

LAYERS = ["Organ", "Vessels and ducts", "Tumor", "Lymph nodes", "Distant sites"]


def ell(c, r, n=30, hemi=False):
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi / (2 if hemi else 1), n // 2 + 1)
    x = c[0] + r[0] * np.outer(np.cos(u), np.sin(v))
    y = c[1] + r[1] * np.outer(np.sin(u), np.sin(v))
    z = c[2] + r[2] * np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def surf(c, r, color, name, layer, opacity=1.0, hemi=False, n=30, show_legend=True):
    x, y, z = ell(c, r, n, hemi)
    return go.Surface(x=x, y=y, z=z, colorscale=[[0, color], [1, color]], showscale=False, opacity=opacity, name=name, legendgroup=layer,
                      showlegend=show_legend, hoverinfo="name", lighting=dict(ambient=0.55, diffuse=0.85, specular=0.3, roughness=0.55),
                      meta=layer)


def line(pts, color, name, layer, width=7, dash=None, show_legend=True):
    p = np.array(pts, float)
    return go.Scatter3d(x=p[:, 0], y=p[:, 1], z=p[:, 2], mode="lines", line=dict(color=color, width=width, dash=dash or "solid"),
                        name=name, legendgroup=layer, showlegend=show_legend, hoverinfo="name", meta=layer)


MODELS = {
    "liver": dict(
        shells=[((0.8, 0, 0), (1.7, 1.1, 0.8), "#A0522D", "Right lobe"), ((-1.1, 0.25, 0.05), (1.0, 0.7, 0.6), "#B5651D", "Left lobe"),
                ((0.75, -0.95, -0.55), (0.28, 0.42, 0.26), "#4D7C0F", "Gallbladder")],
        vessels=[([(0.3, -1.1, -0.1), (0.1, -0.5, 0.0), (-0.3, 0.0, 0.05)], "#1D4ED8", "Portal vein (trunk)"),
                 ([(0.1, -0.5, 0.0), (0.9, -0.1, 0.15), (1.6, 0.2, 0.2)], "#2563EB", "Portal branch (right)"),
                 ([(-0.3, 0.0, 0.05), (-1.0, 0.2, 0.1)], "#3B82F6", "Portal branch (left)"),
                 ([(0.4, -0.2, 0.7), (0.3, 0.0, 0.1), (0.2, 0.3, -0.2)], "#EF4444", "Hepatic artery"),
                 ([(0.2, 0.5, 0.75), (0.5, 0.2, 0.3), (1.1, -0.2, 0.2)], "#0EA5E9", "Hepatic vein")],
        invasion={2: ("Portal branch (right)",), 3: ("Portal branch (right)", "Portal vein (trunk)")},
        tumors={1: [((1.2, 0.1, 0.2), 0.28)], 2: [((1.2, 0.1, 0.2), 0.38), ((0.55, -0.2, 0.3), 0.2), ((1.75, 0.3, -0.1), 0.18)],
                3: [((1.2, 0.1, 0.2), 0.55), ((0.45, -0.3, 0.2), 0.35), ((1.8, 0.4, -0.2), 0.3), ((-1.0, 0.3, 0.2), 0.25)]},
        nodes=[(-0.1, -1.35, -0.2), (0.4, -1.45, -0.3), (-0.55, -1.25, -0.25)], nodes_involved_from=3,
        distant=[((1.0, 0.2, 3.6), 0.5, "Lung metastasis"), ((-3.0, 0.0, 2.4), 0.4, "Bone metastasis")], anchor=(0.3, 0.0, 0.4), cam=(1.6, -2.2, 1.2)),
    "lung": dict(
        shells=[((1.35, 0, 0), (1.0, 0.8, 1.9), "#E8A0A8", "Right lung"), ((-1.35, 0, 0), (0.9, 0.75, 1.8), "#EFB3BA", "Left lung")],
        vessels=[([(0, 0, 2.6), (0, 0, 0.9)], "#94A3B8", "Trachea"), ([(0, 0, 0.9), (0.9, 0, 0.3), (1.5, 0, -0.5)], "#94A3B8", "Bronchus (right)"),
                 ([(0, 0, 0.9), (-0.9, 0, 0.3), (-1.4, 0, -0.4)], "#94A3B8", "Bronchus (left)"),
                 ([(0, 0.2, -0.5), (0.8, 0.2, 0.1), (1.5, 0.2, 0.6)], "#EF4444", "Pulmonary artery"),
                 ([(0, -0.2, -0.5), (-0.8, -0.2, 0.0), (-1.4, -0.2, 0.5)], "#2563EB", "Pulmonary vein")],
        invasion={}, tumors={1: [((1.6, 0.2, 0.9), 0.25)], 2: [((1.6, 0.2, 0.9), 0.4)], 3: [((1.5, 0.2, 0.8), 0.6)]},
        nodes=[(0.55, 0.1, 0.3), (-0.55, 0.1, 0.3), (0.0, 0.1, 0.95), (0.0, 0.1, 1.35)], nodes_involved_from=2,
        distant=[((0.0, 0.0, 4.4), 0.5, "Brain metastasis"), ((3.1, 0.0, 0.2), 0.35, "Bone metastasis")], anchor=(1.4, 0.2, 0.8), cam=(0.2, -3.2, 1.2)),
    "breast": dict(
        shells=[((0, 0, 0), (1.8, 1.8, 0.95), "#E8C39E", "Breast tissue", True), ((0, 0, 0.93), (0.13, 0.13, 0.1), "#C97B63", "Nipple"),
                ((0, 0, -0.35), (3.3, 3.0, 0.3), "#B8654F", "Chest wall muscle")],
        vessels=[([(0, 0, 0.9), (0.9, 0.8, 0.35), (1.5, 1.3, 0.05)], "#F59E0B", "Duct"), ([(0, 0, 0.9), (-0.9, 0.9, 0.35), (-1.4, 1.4, 0.05)], "#F59E0B", "Duct"),
                 ([(0, 0, 0.9), (0.2, -1.0, 0.4), (0.4, -1.6, 0.05)], "#F59E0B", "Duct"), ([(0, 0, 0.9), (-1.0, -0.6, 0.4), (-1.5, -1.0, 0.05)], "#F59E0B", "Duct"),
                 ([(-1.6, 1.6, 0.1), (-0.6, 0.4, 0.35), (0.6, -0.8, 0.25)], "#2563EB", "Vein"),
                 ([(-1.4, 1.8, 0.0), (-0.4, 0.8, 0.3), (0.8, -0.4, 0.25)], "#EF4444", "Artery")],
        invasion={}, tumors={1: [((0.7, 0.5, 0.4), 0.22)], 2: [((0.7, 0.5, 0.4), 0.38)], 3: [((0.6, 0.4, 0.15), 0.6)]},
        nodes=[(-2.6, 1.0, 0.2), (-2.9, 1.6, 0.25), (-2.3, 1.9, 0.2)], nodes_involved_from=2, extra_nodes=[(0.2, -2.1, 0.1)],
        distant=[((0.0, -3.7, -1.6), 0.45, "Bone metastasis"), ((3.4, -2.6, -1.7), 0.5, "Liver metastasis")], anchor=(0.7, 0.4, 0.4), cam=(1.4, -2.4, 1.6)),
}


def build(key, stage, organ_opacity, camera=None):
    m, tr = MODELS[key], []
    for s in m["shells"]:
        c, r, color, name = s[:4]
        tr.append(surf(c, r, color, name, "Organ", organ_opacity, hemi=len(s) > 4, show_legend=True))
    for pts, color, name in m["vessels"]:
        tr.append(line(pts, color, name, "Vessels and ducts", 6))
    inv = m["invasion"].get(min(stage, 3), ()) if stage >= 2 else ()
    for pts, color, name in m["vessels"]:
        if name in inv:
            tr.append(line(pts, "#7F1D1D", "Vessel invasion", "Tumor", 12))
    for i, (c, r) in enumerate(m["tumors"][min(stage, 3)]):
        tr.append(surf(c, (r, r, r), "#DC2626", "Tumor" if i == 0 else "Satellite tumor", "Tumor", 1.0, n=22))
    for i, c in enumerate(m["nodes"]):
        involved = stage >= m["nodes_involved_from"] and i < (1 if stage == 2 else len(m["nodes"]))
        tr.append(surf(c, (0.13, 0.13, 0.13), "#7C3AED" if involved else "#94A3B8", "Involved node" if involved else "Lymph node", "Lymph nodes", 1.0, n=16))
    for c in m.get("extra_nodes", []):
        tr.append(surf(c, (0.12, 0.12, 0.12), "#94A3B8", "Lymph node", "Lymph nodes", 1.0, n=16))
    if stage >= 4:
        for c, r, name in m["distant"]:
            tr.append(surf(c, (r, r, r), "#7F1D1D", name, "Distant sites", 1.0, n=20))
            tr.append(line([m["anchor"], c], "#7F1D1D", name + " route", "Distant sites", 3, "dot", False))
    return tr


def render():
    page_header("Interactive Tumor Models", "Rotate each organ, step through tumor stages 1 to 4, and hide, isolate or fade structures. Schematic illustrations for teaching, not anatomical atlases.",
                "Interactive models")
    organ = st.radio("Organ", ["liver", "lung", "breast"], format_func=lambda k: content.CASES[k]["title"], horizontal=True)
    case = content.CASES[organ]
    info, view = st.columns([1, 2.6], gap="large")
    with info:
        with st.container(border=True, key="panel"):
            st.subheader("Structure")
            stage = st.select_slider("Tumor stage", [1, 2, 3, 4], 1, format_func=lambda s: f"Stage {s}")
            st.markdown(f'<span class="stageno">Stage {stage}</span> {case["stages"][stage - 1][1]}', unsafe_allow_html=True)
            st.markdown("**How RMTI reads this case**")
            for lever, text in case["mapping"]:
                st.markdown(f"- **{lever}:** {text}")
            st.caption("The lever mapping is illustrative (from the case-study scripts).")
            st.divider()
            st.markdown("**Layers**")
            hidden = st.multiselect("Hide", LAYERS, default=[])
            iso = st.selectbox("Isolate", ["None"] + LAYERS)
            fade = st.slider("Organ opacity", 0.05, 1.0, 0.35, 0.05)
    with view:
        traces = build(organ, stage, fade)
        fig = go.Figure(traces)
        for t in fig.data:
            layer = t.meta
            visible = (layer not in hidden) and (iso == "None" or layer == iso)
            t.visible = True if visible else False
        cx, cy, cz = MODELS[organ]["cam"]
        fig.update_layout(height=720, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="#0B1220",
                          scene=dict(aspectmode="data", bgcolor="#0B1220", camera=dict(eye=dict(x=cx, y=cy, z=cz)),
                                     xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                          legend=dict(font=dict(color="#E2E8F0", size=14), bgcolor="rgba(15,23,42,.6)", x=0.01, y=0.99),
                          font=dict(color="#E2E8F0"))
        st.plotly_chart(fig, width="stretch")
        st.caption("Drag to rotate, scroll to zoom. Click a legend entry to hide it and double-click to isolate it.")
    disclaimer()
