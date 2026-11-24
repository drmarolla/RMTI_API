"""4D risk matrix: tier surfaces in (L, V, rho) space, animated across the fourth axis, Exposure."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine import TIER_COLORS, TIER_LABELS, core, short
from rmti_ui import badge, disclaimer, page_header, style_fig

GRID = np.linspace(0, 1, 14)
XX, YY, ZZ = np.meshgrid(GRID, GRID, np.linspace(0, 0.98, 14), indexing="ij")
THRESH = [(0.05, TIER_LABELS[1]), (0.15, TIER_LABELS[2]), (0.35, TIER_LABELS[3]), (0.60, TIER_LABELS[4])]


def surfaces(E):
    R = XX * E * YY * (1 - ZZ)            # x = L, y = V, z = rho
    out = []
    for t, lbl in THRESH:
        out.append(go.Isosurface(x=XX.flatten(), y=YY.flatten(), z=ZZ.flatten(), value=R.flatten(), isomin=t, isomax=t, surface_count=1,
                                 colorscale=[[0, TIER_COLORS[lbl]], [1, TIER_COLORS[lbl]]], showscale=False, opacity=0.55,
                                 caps=dict(x_show=False, y_show=False, z_show=False), name=f"R = {t:.2f} (into {short(lbl)})", showlegend=True))
    return out


def render():
    page_header("4D Risk Matrix", "Each coloured shell is a tier boundary in Likelihood–Vulnerability–Resilience space. Exposure is the fourth dimension: press play or drag the slider.",
                "Interactive models")
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        with st.container(border=True, key="panel"):
            st.subheader("Your point")
            L = st.slider("L", 0.0, 1.0, 0.70, 0.01, key="m4L")
            E = st.slider("E", 0.0, 1.0, 0.80, 0.01, key="m4E")
            V = st.slider("V", 0.0, 1.0, 0.70, 0.01, key="m4V")
            rho = st.slider("ρ", 0.0, 0.98, 0.30, 0.01, key="m4R")
            R = core.score(L, E, V, rho)["R_raw"]
            st.metric("R", f"{R:.3f}")
            st.markdown(badge(core.tier(R)), unsafe_allow_html=True)
            st.caption("Points beyond a shell, toward high L and V and low ρ, sit in a higher tier.")
    es = [0.2, 0.4, 0.6, 0.8, 1.0]
    fig = go.Figure(data=surfaces(E) + [go.Scatter3d(x=[L], y=[V], z=[rho], mode="markers", marker=dict(size=9, color="#0F172A"), name="You are here")],
                    frames=[go.Frame(data=surfaces(e), name=f"{e:.1f}", traces=[0, 1, 2, 3]) for e in es])
    fig.update_layout(scene=dict(xaxis_title="L Likelihood", yaxis_title="V Vulnerability", zaxis_title="ρ Resilience",
                                 xaxis_range=[0, 1], yaxis_range=[0, 1], zaxis_range=[0, 1], camera=dict(eye=dict(x=1.7, y=-1.7, z=0.9))),
                      updatemenus=[dict(type="buttons", showactive=False, x=0.02, y=0.02, buttons=[
                          dict(label="Play E 0.2 → 1.0", method="animate", args=[None, dict(frame=dict(duration=900, redraw=True), fromcurrent=True)]),
                          dict(label="Pause", method="animate", args=[[None], dict(mode="immediate", frame=dict(duration=0))])])],
                      sliders=[dict(active=0, x=0.2, len=0.75, currentvalue=dict(prefix="Exposure E = "),
                                    steps=[dict(method="animate", label=f"{e:.1f}", args=[[f"{e:.1f}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))]) for e in es])],
                      legend=dict(orientation="h", y=1.05))
    with c2:
        st.plotly_chart(style_fig(fig, 720), width="stretch")
        st.caption("Drag to rotate. Click a legend entry to hide a shell; double-click to isolate it.")
    disclaimer()
