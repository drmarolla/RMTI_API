"""
pages/7_Liver_Progression_4D.py  --  the RMTI time-indexed trajectory (HCC) on a rotating 3D liver.

R(t) = L * E * V*(t) * (1 - rho(t)). V*(t) comes from the filtered allostatic-load indicator, rho(t) from surveillance delivery,
both from the unchanged RMTI time-indexed engine. The liver turns through one full 360-degree rotation while the cycles play:
its surface and colour follow V*(t); the sphere on the right lobe has volume proportional to R(t) and the colour of the tier.
Research prototype. A stylised model, not an image of a patient. Synthetic or de-identified values only.
"""
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import liver_progression as LP

st.set_page_config(page_title="RMTI Liver Progression 4D", layout="wide")
try:
    from demo_mode import banner
except Exception:          # noqa: BLE001
    def banner():
        st.error("DEMO MODE · public sandbox · synthetic or published aggregate values only · do not enter patient data.")

TIER_BANDS = [(0, .05), (.05, .15), (.15, .35), (.35, .60), (.60, 5)]
TIER_NAMES = ["T1 Low", "T2 Moderate", "T3 High", "T4 Severe", "T5 Critical"]

st.title("Liver progression in 4D: the RMTI time-indexed trajectory")
st.caption("R(t) = L · E · V*(t) · (1 − ρ(t)). Press ▶ Play: the liver makes one full 360° turn while the cycles advance, "
           "and the surface, colour, sphere and numbers follow the engine's trajectory. Drag the liver to look around when paused.")
st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. "
           "The liver is a stylised model, not an image of a patient. Its surface and colour are a display of V*(t); the sphere's volume is proportional to R(t). "
           "Neither is a fibrosis stage, a tumour size or a forecast. Synthetic or de-identified values only; do not enter identifying data.")
banner()

names = list(LP.PRESETS)
preset = st.selectbox("Scenario (synthetic)", names, key="lp_preset")
P = LP.PRESETS[preset]

c1, c2, c3, c4, c5, c6 = st.columns(6)
L = c1.slider("L likelihood", 0.0, 1.0, float(P["L"]), 0.01, key=f"lp_L_{preset}")
E = c2.slider("E exposure", 0.0, 1.0, float(P["E"]), 0.01, key=f"lp_E_{preset}")
C = c3.select_slider("C consequence", [1, 2, 3, 4, 5], int(P["C"]), key=f"lp_C_{preset}")
rho0 = c4.slider("ρ at baseline", 0.0, 0.95, float(P["rho0"]), 0.01, key=f"lp_rho_{preset}")
turns = c5.selectbox("Rotation while playing", [1, 2, 0], format_func=lambda t: {0: "None (fixed view)", 1: "One 360° turn", 2: "Two turns"}[t], key="lp_turns")
speed = c6.selectbox("Speed", ["Slow", "Normal", "Fast"], index=1, key="lp_speed")
frame_ms = {"Slow": 110, "Normal": 65, "Fast": 30}[speed]

st.caption("y = allostatic-load composite (0–6), blank = missed visit (the filter carries its prediction forward). delivery = surveillance adherence (0–1). Edit the table to change the story.")
tbl = st.data_editor(pd.DataFrame({"y": P["y"], "delivery": P["delivery"]}), num_rows="dynamic", use_container_width=True, key=f"lp_tbl_{preset}",
                     column_config={"y": st.column_config.NumberColumn(min_value=0.0, max_value=6.0, step=0.1),
                                    "delivery": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05)}).reset_index(drop=True)
obs = [None if pd.isna(v) else float(v) for v in tbl["y"]]
dlv = [None if pd.isna(v) else float(v) for v in tbl["delivery"]]

if len(obs) < 2 or obs[0] is None:
    st.info("Add at least two cycles, and give the first cycle a y value.")
    st.stop()
try:
    m = LP.manifest(L, E, C, rho0, obs, dlv, sub=8, turns=turns)
except (ValueError, KeyError) as e:
    st.error(str(e))
    st.stop()

fr, rows = m["frames"], m["cycles"]
n, sub = len(rows), m["sub"]


def liver_traces(f):
    x, y, z, i, j, k, col = LP.liver_mesh(f["stage_f"], 40, 20)
    sx, sy, sz, *_ = LP.sphere_mesh(f["glyph_radius"], nt=20, npp=10)
    return dict(liver=dict(x=x, y=y, z=z, color=col), glyph=dict(x=sx, y=sy, z=sz, color=LP.TIER_HEX[f["tier_no"] - 1]))


def title_for(f):
    return (f'Cycle {f["cycle"]:.1f} · V* {f["V"]:.3f} · ρ {f["rho"]:.2f} · R {f["R"]:.3f} · {f["tier"]} · display band: {f["stage_band"]}')


def camera(az):
    import math
    a = math.radians(-60 + az)
    return dict(eye=dict(x=2.1 * math.cos(a), y=2.1 * math.sin(a), z=0.95), up=dict(x=0, y=0, z=1))


i0, j0, k0 = LP._faces(40, 20)
si, sj, sk = LP._faces(20, 10)
t0 = liver_traces(fr[0])
cyc_x = [r["t"] for r in rows]
ymax = max(max(r["R"] for r in rows) * 1.25, 0.07)

fig = make_subplots(rows=1, cols=2, column_widths=[0.62, 0.38], specs=[[{"type": "scene"}, {"type": "xy"}]],
                    subplot_titles=("Stylised liver: surface = V*(t), sphere volume = R(t)", "R(t) from the engine, with the five tiers"))
fig.add_trace(go.Mesh3d(**t0["liver"], i=i0, j=j0, k=k0, flatshading=False, name="liver",
                        lighting=dict(ambient=0.5, diffuse=0.85, specular=0.25, roughness=0.55, fresnel=0.15), lightposition=dict(x=2000, y=-1500, z=3000),
                        hoverinfo="skip"), row=1, col=1)
fig.add_trace(go.Mesh3d(**t0["glyph"], i=si, j=sj, k=sk, flatshading=False, name="risk glyph", opacity=0.97,
                        lighting=dict(ambient=0.55, diffuse=0.8, specular=0.4), hoverinfo="skip"), row=1, col=1)
for q, ((lo, hi), nm) in enumerate(zip(TIER_BANDS, TIER_NAMES)):          # tier bands as plain shapes (add_hrect cannot mix with a 3D scene subplot)
    if lo < ymax:
        top = min(hi, ymax)
        fig.add_shape(type="rect", xref="x domain", yref="y", x0=0, x1=1, y0=lo, y1=top, fillcolor=LP.TIER_HEX[q], opacity=0.13, line_width=0, layer="below")
        fig.add_annotation(xref="x domain", yref="y", x=1.0, y=(lo + top) / 2, text=nm, showarrow=False, xanchor="left", font=dict(size=9, color=LP.TIER_HEX[q]))
fig.add_trace(go.Scatter(x=cyc_x, y=[r["R"] for r in rows], mode="lines+markers", line=dict(color="#0b5c63", width=3), marker=dict(size=7),
                         name="R(t)", hovertemplate="cycle %{x}: R=%{y:.3f}<extra></extra>"), row=1, col=2)
fig.add_trace(go.Scatter(x=[fr[0]["cycle"]], y=[fr[0]["R"]], mode="markers", marker=dict(size=15, color=LP.TIER_HEX[fr[0]["tier_no"] - 1], line=dict(width=2, color="#263238")),
                         name="now", hoverinfo="skip"), row=1, col=2)
LIVER, GLYPH, CURVE, NOW = 0, 1, 2, 3        # trace indices in the figure

frames = []
for f in fr:
    tr = liver_traces(f)
    frames.append(go.Frame(name=str(f["k"]), traces=[LIVER, GLYPH, NOW], data=[
        go.Mesh3d(**tr["liver"]), go.Mesh3d(**tr["glyph"]),
        go.Scatter(x=[f["cycle"]], y=[f["R"]], marker=dict(size=15, color=LP.TIER_HEX[f["tier_no"] - 1], line=dict(width=2, color="#263238")))],
        layout=dict(title=dict(text=title_for(f), x=0.01, font=dict(size=15)), scene=dict(camera=camera(f["azimuth_deg"])))))
fig.frames = frames

hide = dict(visible=False, showbackground=False)
fig.update_layout(
    scene=dict(xaxis=dict(range=[-1.35, 1.35], **hide), yaxis=dict(range=[-1.0, 1.0], **hide), zaxis=dict(range=[-0.8, 0.8], **hide),
               aspectmode="manual", aspectratio=dict(x=2.0, y=1.5, z=1.2), camera=camera(fr[0]["azimuth_deg"])),
    xaxis=dict(title="cycle", dtick=1, range=[-0.3, n - 0.7]), yaxis=dict(title="R", range=[0, ymax]),
    title=dict(text=title_for(fr[0]), x=0.01, font=dict(size=15)), height=640, margin=dict(l=10, r=40, t=90, b=90), showlegend=False,
    updatemenus=[dict(type="buttons", direction="left", x=0.0, y=-0.02, xanchor="left", yanchor="top", buttons=[
        dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=frame_ms, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
        dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])])],
    sliders=[dict(x=0.18, y=-0.02, len=0.8, xanchor="left", yanchor="top", currentvalue=dict(visible=False),
                  steps=[dict(label="T%d" % c, method="animate", args=[[str(c * sub)], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                         for c in range(n)])])
st.plotly_chart(fig, use_container_width=True)

st.markdown("**The equation with the engine's numbers, cycle by cycle**")
last = rows[-1]
st.latex(rf"R(t) = L \times E \times V^*(t) \times (1-\rho(t)) \;\Rightarrow\; R({last['t']}) = {L:.2f} \times {E:.2f} \times {last['V']:.3f} \times (1-{last['rho']:.3f}) = \mathbf{{{last['R']:.3f}}}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("R at the last cycle", f"{last['R']:.3f}", f"{last['R'] - rows[0]['R']:+.3f} vs first", delta_color="inverse")
m2.metric("Tier", last["tier"])
m3.metric("V*(t)", f"{last['V']:.3f}", f"{last['V'] - rows[0]['V']:+.3f}", delta_color="inverse")
m4.metric("ρ(t)", f"{last['rho']:.2f}", f"{last['rho'] - rows[0]['rho']:+.2f}")
st.dataframe(pd.DataFrame([{"cycle": r["t"], "y": r["y"], "delivery": r["delivery"], "V*": round(r["V"], 3), "ρ": round(r["rho"], 3),
                            "R": round(r["R"], 4), "tier": r["tier"], "posture": r["posture"]} for r in rows]), use_container_width=True, hide_index=True)
if m["tier_changes"]:
    with st.expander("Tier changes (descriptive, not alerts)"):
        st.write(m["tier_changes"])
st.caption("Display bands for the surface: " + "  ·  ".join(b[1] for b in LP.BANDS) + ". A band is a display bin of V*(t) between the ALBI grade-1 and grade-3 anchors; "
           "the engine has no fibrosis-stage input, so a band is not a METAVIR score.")

with st.expander("What the API returns for this animation (/v1/liver/progression)"):
    st.write(f"{m['frame_count']} frames plus the engine's cycle rows. The same JSON is served by POST `/v1/liver/progression` (geometry is drawn in the browser, not sent).")
    st.json({**{k: v for k, v in m.items() if k not in ("frames", "cycles", "disclaimer")}, "frames": fr[:2] + ["…"] + fr[-1:]}, expanded=False)
    st.download_button("Download this trajectory (JSON)", json.dumps(m, indent=1, default=str), "rmti_liver_progression.json", "application/json")

st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. Parameters are uncalibrated placeholders.")
st.caption("Contact: cesar.marolla@alumni.harvard.edu")
