"""
pages/5_Case_Studies_and_Videos.py  --  narrated 3D/4D videos + Lever Lab (liver HCC, flood, heat, wildfire)

Videos live in <repo>/media (mp4 + srt + vtt). Captions are a separate track you turn on/off in the player.
Lever Lab: pick a published case, move L, E, V, rho, and see R, the tier, a sweep of one lever, the sensitivity of every lever
and what single-lever value would be needed to reach the next-lower tier.
Research prototype. Synthetic / published aggregate data only.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="RMTI case studies and lever lab", layout="wide")
try:
    from rmti_theme import apply as _theme
    _theme()
except Exception:          # noqa: BLE001
    pass
try:
    from demo_mode import banner
except Exception:          # noqa: BLE001
    def banner():
        st.error("DEMO MODE · public sandbox · synthetic or published aggregate values only · do not enter patient data.")
import rmti_cases as K

MEDIA = Path(__file__).resolve().parent.parent / "media"
VIDEOS = [
    ("1 · RMTI explained", "rmti_1_explained", "The equation, the four levers in both domains, fixed tiers, sensitivity and expected loss."),
    ("2 · Liver cancer (HCC)", "rmti_2_liver_case_studies", "HBV, viral, alcohol and cured-HCV cirrhosis cohorts; surveillance, treating the cause and liver reserve; Faria et al. ALBI counts."),
    ("3 · Flood and heat", "rmti_3_flood_heat_case_studies", "Lilongwe, Lagos and Bamako: resilience, exposure and vulnerability what-ifs and single-lever thresholds."),
]
RHO_SCALE = [[0.0, "#b3261e"], [0.5, "#e8a317"], [1.0, "#1b7f5c"]]
TIER_COL = ["#7F8FA6", "#4A6FA5", "#C9A227", "#C2662D", "#9B2C2C"]
TIER_EDGES = [(0, .05), (.05, .15), (.15, .35), (.35, .60), (.60, 5)]
GROUPS = {
    "Liver cancer (HCC): published cohorts": [c["label"] for c in K.LIVER_CASES] + ["HBV suppressed"],
    "Liver cancer (HCC): Faria et al. (V from published counts)": [c["label"] for c in K.ONCOLOGY_CASES],
    "Flood and heat: African cities": [c["label"] for c in K.FLOOD_HEAT_CASES],
    "Wildfire: Los Angeles 2025": [c["label"] for c in K.DISASTER_CASES],
}

st.title("Case studies and Lever Lab")
st.caption("Core Logic Created and Formulated by Dr. Cesar Marolla  |  Quantifying Systemic Risk in Disaster Science and Oncology")
banner()

# ------------------------------------------------------------------------------------------------ videos
st.header("Watch: narrated 3D/4D walkthroughs")
pick = st.radio("Video", [v[0] for v in VIDEOS], horizontal=True)
label, stem, blurb = next(v for v in VIDEOS if v[0] == pick)
cc_mode = st.radio("Captions", ["Switch on/off in the player (CC button)", "Always visible under the picture"], horizontal=True)
burned = cc_mode.startswith("Always")
mp4 = MEDIA / (f"{stem}_CC.mp4" if burned else f"{stem}.mp4")
vtt, srt = MEDIA / f"{stem}.vtt", MEDIA / f"{stem}.srt"
st.write(blurb)
if mp4.exists():
    st.video(str(mp4), subtitles=None if burned else ({"English": str(vtt)} if vtt.exists() else None))
    st.caption("Captions follow the narration word for word. "
               + ("They are part of the picture, in a band under the graphics. " if burned else "Use the CC button in the player to turn them on or off. ")
               + "Illustrative values, published rows and aggregate counts only; no patient data.")
    ch = MEDIA / f"{stem}_chapters.txt"
    if ch.exists():
        with st.expander("Chapters"):
            st.text(ch.read_text(encoding="utf-8"))
    if srt.exists():
        st.download_button("Download captions (.srt)", srt.read_bytes(), srt.name, "application/x-subrip")
else:
    st.info("This video is being prepared and will appear here soon. The Lever Lab below works now.")

# ------------------------------------------------------------------------------------------------ lever lab
st.header("Lever Lab")
st.write("Pick a published case, then pull each lever. **L** treat or avoid the cause · **E** who is in harm's way · "
         "**V** how fragile they are · **ρ** how well the system copes. Everything is computed from R = L · E · V · (1 − ρ).")

DEF = "HBV untreated"
LABELS = [x for g in GROUPS.values() for x in g]
if "lab_case" not in st.session_state:
    st.session_state["lab_case"] = DEF


def _load():
    c = K.PRESETS[st.session_state["lab_case"]]
    for k, v in (("L", c["L"]), ("E", c["E"]), ("V", c["V"]), ("rho", c["rho_now"])):
        st.session_state["lab_" + k] = round(float(v), 3)


if "lab_L" not in st.session_state:
    _load()
case_name = st.selectbox("Case", LABELS, key="lab_case", on_change=_load,
                         format_func=lambda x: f"{x}  ·  {[g for g, v in GROUPS.items() if x in v][0].split(':')[0]}")
base = K.PRESETS[case_name]
posture = K.POSTURE_HCC if base["domain"] == "oncology" else K.POSTURE_DISASTER

c1, c2, c3, c4 = st.columns(4)
L = c1.slider("L likelihood", 0.0, 1.0, step=0.001, format="%.3f", key="lab_L")
E = c2.slider("E exposure", 0.0, 1.0, step=0.001, format="%.3f", key="lab_E")
V = c3.slider("V vulnerability", 0.0, 1.0, step=0.001, format="%.3f", key="lab_V")
rho = c4.slider("ρ resilience", 0.0, 0.99, step=0.001, format="%.3f", key="lab_rho")
cur = dict(base, L=L, E=E, V=V, rho_now=rho)

R0, R = K.r_with(base), K.r_with(cur)
t0, t1 = K.tier(R0), K.tier(R)
m1, m2, m3, m4 = st.columns(4)
m1.metric("R at the published values", f"{R0:.3f}", t0)
m2.metric("R with your levers", f"{R:.3f}", f"{R - R0:+.3f}", delta_color="inverse")
m3.metric("Tier now", t1)
m4.metric("Inherent risk R₀ = L·E·V", f"{L * E * V:.3f}")
st.info(f"**Posture for {t1}:** {posture[int(t1[0])]}")

left, right = st.columns([1.1, 1])
with left:
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[base["L"]], y=[base["E"]], z=[base["V"]], mode="markers+text", text=["published"], textposition="bottom center",
                               marker=dict(size=9, color="#90a4ae", symbol="circle-open", line=dict(width=3, color="#546e7a")), hoverinfo="skip", name="published"))
    fig.add_trace(go.Scatter3d(x=[base["L"], L], y=[base["E"], E], z=[base["V"], V], mode="lines", line=dict(color="#90a4ae", width=5, dash="dash"), hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[L], y=[E], z=[V], mode="markers+text", text=["your levers"], textposition="top center",
                               marker=dict(size=12, color=[rho], colorscale=RHO_SCALE, cmin=0, cmax=1, line=dict(width=2, color="#263238"), colorbar=dict(title="ρ", thickness=12, len=0.6)),
                               hovertemplate="L=%{x:.3f} E=%{y:.3f} V=%{z:.3f}<extra></extra>"))
    ax = dict(range=[0, 1], dtick=0.25, backgroundcolor="rgba(0,0,0,0)", gridcolor="#cfd8dc")
    fig.update_layout(scene=dict(xaxis=dict(title="L", **ax), yaxis=dict(title="E", **ax), zaxis=dict(title="V", **ax), aspectmode="cube",
                                 camera=dict(eye=dict(x=1.6, y=1.5, z=1.0))), height=520, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Axes are fixed to 0–1 and never rescaled. Colour = ρ (red low resilience, green high). Size of R is read from the numbers, not the picture.")

with right:
    lever = st.radio("Sweep one lever", ["rho", "V", "E", "L"], horizontal=True, format_func=lambda k: {"rho": "ρ resilience", "V": "V vulnerability", "E": "E exposure", "L": "L likelihood"}[k])
    cur_v = K._val(cur, lever)
    xs, ys = K.sweep(cur, lever, 0.0, 0.99 if lever == "rho" else 1.0, 80)
    f2 = go.Figure()
    ymax = max(max(ys) * 1.15, 0.07)
    for (lo, hi), col, nm in zip(TIER_EDGES, TIER_COL, K.TIERS):
        if lo < ymax:
            f2.add_hrect(y0=lo, y1=min(hi, ymax), fillcolor=col, opacity=0.13, line_width=0, annotation_text="T" + nm[1], annotation_position="right", annotation_font_size=10)
    f2.add_scatter(x=xs, y=ys, mode="lines", line=dict(color="#0b5c63", width=3), name="R")
    f2.add_scatter(x=[cur_v], y=[K.r_with(cur)], mode="markers", marker=dict(size=13, color=TIER_COL[int(t1[0]) - 1], line=dict(width=2, color="#263238")), name="you")
    f2.update_layout(height=300, margin=dict(l=0, r=40, t=10, b=0), showlegend=False, xaxis_title=lever, yaxis=dict(title="R", range=[0, ymax]))
    st.plotly_chart(f2, use_container_width=True)

    b, d = K.tornado(cur)
    names = {"L": "L likelihood", "E": "E exposure", "V": "V vulnerability", "rho": "ρ resilience"}
    order = sorted(d, key=lambda k: -abs(d[k]))
    f3 = go.Figure(go.Bar(y=[names[k] for k in order][::-1], x=[abs(d[k]) for k in order][::-1], orientation="h",
                          marker_color=["#b0bec5" if k == "L" else "#0b5c63" for k in order][::-1],
                          text=[f"−{abs(d[k]):.3f}" for k in order][::-1], textposition="outside"))
    f3.update_layout(height=230, margin=dict(l=0, r=30, t=26, b=0), title=dict(text="R falls by… if each lever moves 0.10 in the risk-reducing direction", font=dict(size=13)), xaxis=dict(visible=False))
    st.plotly_chart(f3, use_container_width=True)
    st.caption("Equal absolute steps: an illustration of sensitivity, not an intervention effect size. L is often set by nature or biology.")

nt = K.to_next_tier(cur)
if nt:
    st.subheader(f"What would it take to leave {K.tier(R)}?  (R must fall below {nt['target']:.2f})")
    rows = []
    for k, lab, rel in (("rho", "ρ resilience", "at least"), ("V", "V vulnerability", "at most"), ("E", "E exposure", "at most"), ("L", "L likelihood", "at most")):
        need = nt["need"][k]; ok = nt["feasible"][k]
        note = ""
        if base["domain"] == "oncology" and k == "V" and ok and need < 0.35:
            note = "below the lowest ALBI anchor (0.35)"; ok = False
        if base["domain"] == "oncology" and k == "rho" and ok and need > 0.65:
            note = "above the top of the published ladder (0.65)"
        rows.append({"lever": lab, "now": round(K._val(cur, k), 3), "single-lever value needed": f"{rel} {need:.3f}" if ok or note else "not reachable alone", "note": note})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Single-lever what-ifs with the others held fixed; combinations of levers would need less of each. Not a plan or a recommendation.")
else:
    st.success("Already in tier 1 (Low): there is no lower tier to reach.")

st.caption(f"Source: {base['source']}")
st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. R is a relative rubric index, "
           "not a probability, forecast or loss estimate. After-values are scenarios, not observations.")
st.caption("Contact: cesar.marolla@alumni.harvard.edu")
