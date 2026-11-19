"""
pages/4_RMTI_Step_by_Step.py  --  RMTI explained as a playable animation

Plays R = L * E * V * (1 - rho) one factor at a time:
  left : a point travels through the bounded 0..1 cube (L -> E -> V), colour shifts with rho
  right: a "running product" bar chart so the numbers stay visible (R0 = L*E*V, then R after resilience)
Play / Pause and a step slider are built in. The animation can be downloaded as a standalone HTML file.

Research prototype. Synthetic or de-identified data only.
"""
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

RHO_SCALE = [[0.0, "#d9262c"], [0.5, "#ff6b73"], [1.0, "#1d6fd0"]]   # vulnerable -> resilient
LABELS = ["L", "L·E", "L·E·V", "R₀ (ρ = 0)", "R (ρ now)", "R (ρ after)"]
BAR_COLORS = ["#3f5f86", "#3f5f86", "#3f5f86", "#d9262c", "#ff6b73", "#1d6fd0"]


# ----------------------------------------------------------------- pure logic
def keyframes(L, E, V, rho_now, rho_after):
    """Each keyframe: (u along path 0..3, rho shown, number of bars revealed, title)."""
    r0 = L * E * V
    rn = r0 * (1 - rho_now)
    ra = r0 * (1 - rho_after)
    return [
        (0, 0.0, 0, "Start · R = L · E · V · (1 − ρ). Every factor is bounded 0–1."),
        (1, 0.0, 1, f"Step 1 · L likelihood = {L:.2f}: how probable the hazard is."),
        (2, 0.0, 2, f"Step 2 · × E exposure = {E:.2f}: share reached or affected. L·E = {L*E:.3f}"),
        (3, 0.0, 3, f"Step 3 · × V vulnerability = {V:.2f}: how badly those reached are hurt. L·E·V = {r0:.3f}"),
        (3, 0.0, 4, f"Step 4 · Raw risk R₀ = {r0:.3f}, before any resilience."),
        (3, rho_now, 5, f"Step 5 · × (1 − ρ), ρ = {rho_now:.2f}: resilience absorbs {100*rho_now:.0f}%. R = {rn:.3f}"),
        (3, rho_after, 6, f"Step 6 · Improved state, ρ = {rho_after:.2f}: R = {ra:.3f} ({(ra-rn):+.3f})"),
    ], (L * 1.0, L * E, r0, r0, rn, ra)


def bar_values(final_vals, revealed):
    """revealed may be fractional; bar k grows from 0 to its value as revealed passes k."""
    return [float(final_vals[k]) * float(np.clip(revealed - k, 0, 1)) for k in range(6)]


def pos_on_path(u, L, E, V):
    w = [(0, 0, 0), (L, 0, 0), (L, E, 0), (L, E, V)]
    i = int(min(np.floor(u), 2))
    f = u - i
    a, b = w[i], w[i + 1]
    return [a[j] + (b[j] - a[j]) * f for j in range(3)], w, i


def build_frames(L, E, V, rho_now, rho_after, tween=10, dwell=30):
    kf, finals = keyframes(L, E, V, rho_now, rho_after)
    states, key_index = [], []
    for k, (u, rho, rev, title) in enumerate(kf):
        key_index.append(len(states))
        for _ in range(dwell):
            states.append((u, rho, rev, title))
        if k < len(kf) - 1:
            u2, rho2, rev2, title2 = kf[k + 1]
            for s in range(1, tween + 1):
                t = s / (tween + 1)
                states.append((u + (u2 - u) * t, rho + (rho2 - rho) * t, rev + (rev2 - rev) * t, title2))
    return states, key_index, finals


# ----------------------------------------------------------------- figure
def make_figure(L, E, V, rho_now, rho_after, frame_ms):
    states, key_index, finals = build_frames(L, E, V, rho_now, rho_after)

    def traces_for(u, rho, rev):
        p, w, i = pos_on_path(u, L, E, V)
        xs = [q[0] for q in w[: i + 1]] + [p[0]]
        ys = [q[1] for q in w[: i + 1]] + [p[1]]
        zs = [q[2] for q in w[: i + 1]] + [p[2]]
        vals = bar_values(finals, rev)
        path = go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="#3f5f86", width=6), hoverinfo="skip")
        dot = go.Scatter3d(x=[p[0]], y=[p[1]], z=[p[2]], mode="markers",
                           marker=dict(size=11, color=[rho], colorscale=RHO_SCALE, cmin=0, cmax=1,
                                       line=dict(width=2, color="#0b2545"),
                                       colorbar=dict(title="ρ", thickness=12, x=0.46, len=0.7)),
                           hovertemplate="L=%{x:.2f} E=%{y:.2f} V=%{z:.2f}<extra></extra>")
        bars = go.Bar(x=LABELS, y=vals, marker_color=BAR_COLORS,
                      text=[f"{v:.3f}" if v > 1e-9 else "" for v in vals], textposition="outside")
        return [path, dot, bars]

    u0, rho0, rev0, _ = states[0]
    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45], specs=[[{"type": "scene"}, {"type": "xy"}]],
                        subplot_titles=("Position in the bounded L · E · V cube (colour = ρ)",
                                        "Running product (the arithmetic behind the point)"))
    t0 = traces_for(u0, rho0, rev0)
    fig.add_trace(t0[0], row=1, col=1)
    fig.add_trace(t0[1], row=1, col=1)
    fig.add_trace(t0[2], row=1, col=2)

    frames = []
    for n, (u, rho, rev, title) in enumerate(states):
        frames.append(go.Frame(name=str(n), traces=[0, 1, 2], data=traces_for(u, rho, rev),
                               layout=dict(title=dict(text=title, x=0.01, font=dict(size=17)))))
    fig.frames = frames

    ax = dict(range=[0, 1], dtick=0.25, backgroundcolor="rgba(0,0,0,0)", gridcolor="#d3e8fb")
    fig.update_layout(
        scene=dict(xaxis=dict(title="L", **ax), yaxis=dict(title="E", **ax), zaxis=dict(title="V", **ax),
                   aspectmode="cube", camera=dict(eye=dict(x=1.7, y=1.5, z=1.0))),
        yaxis=dict(range=[0, 1], title="value (0–1)"),
        title=dict(text=states[0][3], x=0.01, font=dict(size=17)),
        height=640, margin=dict(l=10, r=10, t=90, b=90), showlegend=False,
        updatemenus=[dict(type="buttons", direction="left", x=0.0, y=-0.02, xanchor="left", yanchor="top",
                          buttons=[
                              dict(label="▶ Play", method="animate",
                                   args=[None, dict(frame=dict(duration=frame_ms, redraw=True), fromcurrent=True,
                                                    transition=dict(duration=0))]),
                              dict(label="⏸ Pause", method="animate",
                                   args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate",
                                                      transition=dict(duration=0))]),
                          ])],
        sliders=[dict(x=0.18, y=-0.02, len=0.8, xanchor="left", yanchor="top", currentvalue=dict(visible=False),
                      steps=[dict(label=lbl, method="animate",
                                  args=[[str(key_index[k])], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                                                  transition=dict(duration=0))])
                             for k, lbl in enumerate(["Start", "L", "×E", "×V", "R₀", "×(1−ρ)", "ρ after"])])],
    )
    return fig, finals


# ----------------------------------------------------------------- page
st.set_page_config(page_title="RMTI step by step", layout="wide")
try:
    from demo_mode import banner
    import rmti_cases as K
except Exception:          # noqa: BLE001
    K = None

    def banner():
        st.error("DEMO MODE · public sandbox · illustrative values only · do not enter patient data.")

st.title("RMTI step by step: play the calculation")
st.caption("R = L · E · V · (1 − ρ). Press ▶ Play under the chart, or drag the slider to jump to a step.")
st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. "
           "Parameters are uncalibrated placeholders. Illustrative values only; do not enter identifying data.")

banner()

DEF = dict(L=0.30, E=0.65, V=0.55, rho_now=0.20, rho_after=0.50)


def _apply_preset():
    name = st.session_state["preset"]
    src = DEF if (name == "Generic illustration" or K is None) else K.PRESETS[name]
    for k in DEF:
        st.session_state["s_" + k] = round(float(src[k]), 3)      # sliders step 0.001 (V is rounded to 3 decimals)


for k, v in DEF.items():
    st.session_state.setdefault("s_" + k, v)

presets = ["Generic illustration"] + (list(K.PRESETS) if K else [])
st.selectbox("Preset (published aggregate or illustrative values only)", presets, key="preset", on_change=_apply_preset)
if K and st.session_state.get("preset") in K.PRESETS:
    st.caption(K.PRESETS[st.session_state["preset"]]["source"])

c1, c2, c3, c4, c5, c6 = st.columns(6)
L = c1.slider("L likelihood", 0.0, 1.0, step=0.001, format="%.3f", key="s_L")
E = c2.slider("E exposure", 0.0, 1.0, step=0.001, format="%.3f", key="s_E")
V = c3.slider("V vulnerability", 0.0, 1.0, step=0.001, format="%.3f", key="s_V")
rho_now = c4.slider("ρ now", 0.0, 0.99, step=0.001, format="%.3f", key="s_rho_now")
rho_after = c5.slider("ρ after", 0.0, 0.99, step=0.001, format="%.3f", key="s_rho_after")
speed = c6.selectbox("Speed", ["Slow", "Normal", "Fast"], index=1)
frame_ms = {"Slow": 110, "Normal": 70, "Fast": 35}[speed]

fig, finals = make_figure(L, E, V, rho_now, rho_after, frame_ms)
st.plotly_chart(fig, use_container_width=True)

r0, rn, ra = finals[3], finals[4], finals[5]
m1, m2, m3 = st.columns(3)
m1.metric("R₀ = L·E·V", f"{r0:.3f}")
m2.metric("R now", f"{rn:.3f}")
m3.metric("R after", f"{ra:.3f}", f"{ra - rn:+.3f}", delta_color="inverse")

try:                       # cross-check against the platform engine (service.py at the repo root)
    import service as S
    out = S.snapshot("hcc", 100_000, L, E, V, rho_now, rho_after, 5)
    st.caption(f"Engine check (HCC module): R now {out['R_now']:.3f} · tier {out['tier_now']} · "
               f"R after {out.get('R_after', float('nan')):.3f}. "
               + ("Matches the animation." if abs(out["R_now"] - rn) < 0.0006 else "Differs from the plain product: the engine's value is the one to use."))
except Exception as e:     # noqa: BLE001
    st.caption(f"Engine check unavailable here ({type(e).__name__}).")

st.download_button("Download this animation as a standalone HTML file",
                   fig.to_html(include_plotlyjs="cdn", auto_play=False), "rmti_step_by_step.html", "text/html")
st.caption("Contact: cesar.marolla@alumni.harvard.edu")
