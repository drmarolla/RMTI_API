"""Live risk matrix: tier maps over pairs of levers, updating as you move the sliders."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine import TIER_COLORS, TIER_LABELS, core, short
from rmti_ui import badge, disclaimer, page_header, style_fig

SCALE = []
for i, lbl in enumerate(TIER_LABELS):
    SCALE += [[i / 5, TIER_COLORS[lbl]], [(i + 1) / 5, TIER_COLORS[lbl]]]


def tier_map(xname, yname, fixed, cur, n=70):
    xs = np.linspace(0, 1, n)
    ys = np.linspace(0, 0.99 if yname == "rho" else 1, n)
    X, Y = np.meshgrid(xs, ys)
    args = dict(fixed)
    args[xname], args[yname] = X, Y
    R = args["L"] * args["E"] * args["V"] * (1 - args["rho"])
    Z = np.digitize(R, [0.05, 0.15, 0.35, 0.60])
    fig = go.Figure(go.Heatmap(x=xs, y=ys, z=Z, customdata=R, colorscale=SCALE, zmin=0, zmax=4.999, showscale=False,
                               hovertemplate=f"{xname}=%{{x:.2f}}<br>{yname}=%{{y:.2f}}<br>R=%{{customdata:.3f}}<extra></extra>"))
    fig.add_trace(go.Contour(x=xs, y=ys, z=R, contours=dict(start=0.05, end=0.6, size=0.1, coloring="none", showlabels=False),
                             line=dict(color="white", width=1), showscale=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[cur[xname]], y=[cur[yname]], mode="markers", marker=dict(size=18, color="white", line=dict(width=4, color="#0F172A")),
                             name="You are here", hoverinfo="skip"))
    fig.update_layout(xaxis_title=xname if xname != "rho" else "ρ", yaxis_title=yname if yname != "rho" else "ρ", showlegend=False)
    return style_fig(fig, 480)


def render():
    page_header("Live Risk Matrix", "Move the four levers and watch the fixed tier map redraw. Resilience always pushes the point toward a lower tier.",
                "Interactive models")
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        with st.container(border=True, key="panel"):
            L = st.slider("L · Likelihood", 0.0, 1.0, 0.70, 0.01)
            E = st.slider("E · Exposure", 0.0, 1.0, 0.65, 0.01)
            V = st.slider("V · Vulnerability", 0.0, 1.0, 0.70, 0.01)
            rho = st.slider("ρ · Resilience", 0.0, 0.99, 0.30, 0.01)
            R = core.score(L, E, V, rho)["R_raw"]
            t = core.tier(R)
            st.metric("Residual risk R", f"{R:.3f}")
            st.markdown(badge(t), unsafe_allow_html=True)
            st.caption(core.TIER_POSTURE[t])
    cur = dict(L=L, E=E, V=V, rho=rho)
    with c2:
        a, b = st.tabs(["Vulnerability × Resilience", "Likelihood × Exposure"])
        with a:
            st.plotly_chart(tier_map("V", "rho", dict(L=L, E=E), cur), width="stretch")
            st.caption("Held fixed: L and E. White lines mark the tier boundaries 0.05, 0.15, 0.35 and 0.60.")
        with b:
            st.plotly_chart(tier_map("L", "E", dict(V=V, rho=rho), cur), width="stretch")
            st.caption("Held fixed: V and ρ.")
        st.markdown(" ".join(f'<span class="tier t{i + 1}">{short(l)}</span>' for i, l in enumerate(TIER_LABELS)), unsafe_allow_html=True)
    disclaimer()
