"""
pages/6_Live_4D_Lab.py  --  LIVE 4D lab: move L, E, V and rho and watch R = L * E * V * (1 - rho) evolve.

Pick a case study, drag any slider, press Play or scrub the time slider under the cube.
The cube, the running-product bars, the tier and the equation with your numbers all update. The same manifest is served by the API
at /v1/scene/{case} (see scene.py / scene_routes.py).
Research prototype. Synthetic or published aggregate values only; no patient data.
"""
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import rmti_cases as K
import scene as SC

st.set_page_config(page_title="RMTI Live 4D Lab", layout="wide")
try:
    from demo_mode import banner
except Exception:          # noqa: BLE001
    def banner():
        st.error("DEMO MODE · public sandbox · synthetic or published aggregate values only · do not enter patient data.")

RHO_SCALE = [[0.0, "#d9262c"], [0.5, "#c9d4e6"], [1.0, "#0b2545"]]
TIER_COL = ["#9fb3c8", "#4d78a8", "#e8a0a3", "#d9262c", "#8f1519"]
TIER_EDGES = [(0, .05), (.05, .15), (.15, .35), (.35, .60), (.60, 5)]
BAR_LABELS = ["L", "L·E", "L·E·V", "R₀ (ρ = 0)", "R (ρ now)", "R (ρ after)"]
BAR_COL = ["#6f8fb5", "#6f8fb5", "#6f8fb5", "#d9262c", "#4d78a8", "#0b2545"]
STEP_LABELS = {"L": "L", "E": "×E", "V": "×V", "resilience_now": "×(1−ρ) now", "resilience_after": "ρ after"}

st.title("Live 4D Lab: move the levers, watch the risk evolve")
st.caption("R = L · E · V · (1 − ρ). Colour = ρ (resilience). Pick a case study (Faria et al. HCC, sub-Saharan Africa, Pacific Palisades or Altadena), drag a slider, then press ▶ Play or scrub the time slider under the cube.")
st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. "
           "R is a relative rubric index, not a probability. After-values are scenarios. Illustrative or published aggregate values only; do not enter identifying data.")
banner()

cases = SC.list_cases()
labels = {c["key"]: f'{c["label"]}  ·  {c["group"].split(": ", 1)[1]}' for c in cases}


def _load():
    c = SC.case_inputs(st.session_state["l6_case"])
    for k in ("L", "E", "V", "rho_now", "rho_after"):
        st.session_state["l6_" + k] = round(float(c[k]), 3)


if "l6_case" not in st.session_state:
    st.session_state["l6_case"] = "faria_hcc"
    _load()
st.selectbox("Case study", [c["key"] for c in cases], key="l6_case",
             format_func=lambda k: labels[k], on_change=_load)
base = SC.case_inputs(st.session_state["l6_case"])
st.caption(f'Source: {base["source"]}')

c1, c2, c3, c4, c5, c6 = st.columns(6)
L = c1.slider("L likelihood", 0.0, 1.0, step=0.001, format="%.3f", key="l6_L")
E = c2.slider("E exposure", 0.0, 1.0, step=0.001, format="%.3f", key="l6_E")
V = c3.slider("V vulnerability", 0.0, 1.0, step=0.001, format="%.3f", key="l6_V")
rho_now = c4.slider("ρ now", 0.0, 0.99, step=0.001, format="%.3f", key="l6_rho_now")
rho_after = c5.slider("ρ after (scenario)", 0.0, 0.99, step=0.001, format="%.3f", key="l6_rho_after")
speed = c6.selectbox("Speed", ["Slow", "Normal", "Fast"], index=1)
frame_ms = {"Slow": 120, "Normal": 70, "Fast": 35}[speed]

sc = SC.build(L, E, V, rho_now, rho_after, label=base["label"], domain=base["domain"])
fr, inp, sm = sc["frames"], sc["inputs"], sc["summary"]
bars = [SC.bar_values(f, inp) for f in fr]


def traces(i):
    trail = [f["pos"] for f in fr[: i + 1]]
    xs, ys, zs = zip(*trail)
    f = fr[i]
    return [go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="#6f8fb5", width=6), hoverinfo="skip"),
            go.Scatter3d(x=[f["pos"][0]], y=[f["pos"][1]], z=[f["pos"][2]], mode="markers",
                         marker=dict(size=11, color=[f["rho"]], colorscale=RHO_SCALE, cmin=0, cmax=1, line=dict(width=2, color="#263238"),
                                     colorbar=dict(title="ρ", thickness=12, x=0.46, len=0.7)),
                         hovertemplate="L=%{x:.2f} E=%{y:.2f} V=%{z:.2f}<extra></extra>"),
            go.Bar(x=BAR_LABELS, y=bars[i], marker_color=BAR_COL, text=[f"{v:.3f}" if v > 1e-9 else "" for v in bars[i]], textposition="outside")]


def title_for(f):
    ph = f["phase"]
    if ph in ("L", "E", "V"):
        return f'Walking the cube · {ph} · running product {f["product"]:.3f}'
    if ph == "resilience_now":
        return f'Resilience absorbs {100 * f["rho"]:.0f}% · R = {f["product"]:.3f} · tier {f["tier"]}'
    return f'Scenario: ρ → {f["rho"]:.2f} · R = {f["product"]:.3f} · tier {f["tier"]}'


fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45], specs=[[{"type": "scene"}, {"type": "xy"}]],
                    subplot_titles=("Position in the bounded L · E · V cube", "Running product (the arithmetic behind the point)"))
t0 = traces(0)
fig.add_trace(t0[0], row=1, col=1); fig.add_trace(t0[1], row=1, col=1); fig.add_trace(t0[2], row=1, col=2)
fig.frames = [go.Frame(name=str(i), traces=[0, 1, 2], data=traces(i), layout=dict(title=dict(text=title_for(f), x=0.01, font=dict(size=16))))
              for i, f in enumerate(fr)]
first_of = {}
for f in fr:
    first_of.setdefault(f["phase"], f["i"])
ax = dict(range=[0, 1], dtick=0.25, backgroundcolor="rgba(0,0,0,0)", gridcolor="#cfd8dc")
fig.update_layout(
    scene=dict(xaxis=dict(title="L", **ax), yaxis=dict(title="E", **ax), zaxis=dict(title="V", **ax), aspectmode="cube",
               camera=dict(eye=dict(x=1.7, y=1.5, z=1.0))),
    yaxis=dict(range=[0, 1], title="value (0–1)"), title=dict(text=title_for(fr[0]), x=0.01, font=dict(size=16)),
    height=640, margin=dict(l=10, r=10, t=90, b=90), showlegend=False,
    updatemenus=[dict(type="buttons", direction="left", x=0.0, y=-0.02, xanchor="left", yanchor="top", buttons=[
        dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=frame_ms, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
        dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])])],
    sliders=[dict(x=0.18, y=-0.02, len=0.8, xanchor="left", yanchor="top", currentvalue=dict(visible=False),
                  steps=[dict(label=STEP_LABELS[p], method="animate",
                              args=[[str(first_of[p])], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                         for p in sc["phases"]])])
st.plotly_chart(fig, use_container_width=True)

st.markdown("**The equation with your numbers**")
e1, e2 = st.columns(2)
e1.latex(rf"R_{{now}} = {L:.3f} \times {E:.3f} \times {V:.3f} \times (1 - {rho_now:.3f}) = \mathbf{{{sm['R_now']:.3f}}}")
e2.latex(rf"R_{{after}} = {L:.3f} \times {E:.3f} \times {V:.3f} \times (1 - {rho_after:.3f}) = \mathbf{{{sm['R_after']:.3f}}}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Inherent risk R₀ = L·E·V", f"{sm['R0']:.3f}")
m2.metric("R now", f"{sm['R_now']:.3f}", sm["tier_now"], delta_color="off")
m3.metric("R after (scenario)", f"{sm['R_after']:.3f}", f"{sm['delta']:+.3f}", delta_color="inverse")
m4.metric("Tier after", sm["tier_after"])
st.info(f"**Posture for {sm['tier_now']}:** {sm['posture_now']}")

left, right = st.columns(2)
with left:
    case = dict(L=L, E=E, V=V, rho_now=rho_now)
    xs, ys = K.sweep(case, "rho", 0.0, 0.99, 80)
    ymax = max(max(ys) * 1.15, 0.07)
    f2 = go.Figure()
    for (lo, hi), col, nm in zip(TIER_EDGES, TIER_COL, K.TIERS):
        if lo < ymax:
            f2.add_hrect(y0=lo, y1=min(hi, ymax), fillcolor=col, opacity=0.13, line_width=0, annotation_text="T" + nm[1], annotation_position="right", annotation_font_size=10)
    f2.add_scatter(x=xs, y=ys, mode="lines", line=dict(color="#1d4e89", width=3), name="R")
    f2.add_scatter(x=[rho_now, rho_after], y=[sm["R_now"], sm["R_after"]], mode="markers+text", text=["now", "after"], textposition="top center",
                   marker=dict(size=13, color=["#4d78a8", "#0b2545"], line=dict(width=2, color="#263238")))
    f2.update_layout(height=300, margin=dict(l=0, r=40, t=30, b=0), showlegend=False, xaxis_title="ρ resilience", yaxis=dict(title="R", range=[0, ymax]),
                     title=dict(text="R against resilience, with your L, E and V", font=dict(size=13)))
    st.plotly_chart(f2, use_container_width=True)
with right:
    steps = sm["lever_steps_R_falls_by"]
    names = {"L": "L likelihood", "E": "E exposure", "V": "V vulnerability", "rho": "ρ resilience"}
    order = sorted(steps, key=lambda k: -abs(steps[k]))
    f3 = go.Figure(go.Bar(y=[names[k] for k in order][::-1], x=[steps[k] for k in order][::-1], orientation="h",
                          marker_color=["#b0bec5" if k == "L" else "#1d4e89" for k in order][::-1],
                          text=[f"−{steps[k]:.3f}" for k in order][::-1], textposition="outside"))
    f3.update_layout(height=300, margin=dict(l=0, r=30, t=30, b=0), xaxis=dict(visible=False),
                     title=dict(text="R falls by… if each lever moves 0.10 in the risk-reducing direction", font=dict(size=13)))
    st.plotly_chart(f3, use_container_width=True)
st.caption("Equal absolute steps: an illustration of sensitivity, not an intervention effect size. L is often set by nature or biology.")

with st.expander("What the API returns for this scene (/v1/scene)"):
    st.write(f"{sc['frame_count']} time-indexed frames plus a summary. The same JSON is served at `/v1/scene/{st.session_state['l6_case']}` (published values) "
             "or by POST `/v1/scene` with your own numbers.")
    st.json({**{k: v for k, v in sc.items() if k not in ("frames", "disclaimer")}, "frames": fr[:3] + ["…"] + fr[-1:]}, expanded=False)
    st.download_button("Download this scene (JSON)", json.dumps(sc, indent=1), f"rmti_scene_{st.session_state['l6_case']}.json", "application/json")

st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. After-values are scenarios, not observations.")
st.caption("Contact: cesar.marolla@alumni.harvard.edu · Build 2026-11-15 · navy, white and red")
