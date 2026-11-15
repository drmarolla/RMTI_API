"""Live Risk Matrix: sliders for L, E, V and rho, the formula with your numbers, and four matrices coloured by the five fixed RMTI tiers.

Use this page to see where risk sits across exposure and vulnerability. To score a patient or a cohort, use the Risk Calculator.
Research prototype. Synthetic, illustrative values only. Not for patient care.
"""
import streamlit as st

st.set_page_config(page_title="Live Risk Matrix", page_icon="🧬", layout="wide")
import rmti_theme
rmti_theme.apply()
st.title("Live Risk Matrix")
st.caption("R = L · E · V · (1 − ρ). Research prototype. Synthetic, illustrative values only. Not for patient care.")
st.markdown("**See where risk sits across exposure (E) and vulnerability (V), for four levels of resilience (ρ).** "
            "To score a patient or a cohort, and to read the tier's posture, open the [Risk Calculator](/Risk_Calculator).")

c1, c2, c3 = st.columns(3)
L = c1.slider("L: likelihood (hazard)", 0.0, 1.0, 0.30, 0.01)
E = c2.slider("E: exposure", 0.0, 1.0, 0.65, 0.01)
V = c3.slider("V: vulnerability", 0.0, 1.0, 0.55, 0.01)
c4, c5 = st.columns(2)
rho = c4.slider("ρ now: resilience / surveillance adequacy", 0.0, 0.95, 0.20, 0.01)
rho2 = c5.slider("ρ after: improved state", 0.0, 0.95, 0.50, 0.01)

R, R2 = L * E * V * (1 - rho), L * E * V * (1 - rho2)
EDGES = (0.05, 0.15, 0.35, 0.60)                                   # fixed tier thresholds, the same for every case
TIER_NAME = ["Low", "Moderate", "High", "Severe", "Critical"]
TIER_BG = ["#e6edf6", "#b9cde4", "#f3c0c2", "#d9262c", "#8f1519"]
TIER_FG = ["#0b2545", "#0b2545", "#0b2545", "#ffffff", "#ffffff"]


def tier_no(r):
    return 1 + sum(r >= e for e in EDGES)


st.latex(r"R = L \cdot E \cdot V \cdot (1-\rho)")
st.latex(rf"R_{{now}} = {L:.2f} \cdot {E:.2f} \cdot {V:.2f} \cdot (1-{rho:.2f}) = {R:.4f}")
st.latex(rf"R_{{after}} = {L:.2f} \cdot {E:.2f} \cdot {V:.2f} \cdot (1-{rho2:.2f}) = {R2:.4f}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("R now", f"{R:.4f}")
m2.metric("R after", f"{R2:.4f}", f"{R2 - R:+.4f}", delta_color="inverse")
m3.metric("Reduction from ρ", f"{(1 - (1 - rho2) / (1 - rho)) * 100:.0f}%")
m4.metric("Tier now → after", f"{tier_no(R)} {TIER_NAME[tier_no(R) - 1]} → {tier_no(R2)} {TIER_NAME[tier_no(R2) - 1]}")

grid = [0, .2, .4, .6, .8, 1]
nearest = lambda x: min(grid, key=lambda g: abs(g - x))


def panel(r):
    rows = ""
    for v in reversed(grid):
        cells = ""
        for e in grid:
            val = L * e * v * (1 - r)
            t = tier_no(val)
            mark = "outline:3px solid #0b2545;outline-offset:-3px;" if (e == nearest(E) and v == nearest(V)) else ""
            cells += (f'<td style="background:{TIER_BG[t - 1]};color:{TIER_FG[t - 1]};{mark}">'
                      f'<b>{val:.2f}</b><br><span style="font-size:.7rem;opacity:.85">T{t}</span></td>')
        rows += f'<tr><th>{v:.1f}</th>{cells}</tr>'
    head = "".join(f"<th>{e:.1f}</th>" for e in grid)
    return (f'<div style="font-family:Inter,Segoe UI,sans-serif;color:#0b2545"><b>ρ = {r:.2f}</b>'
            f'<table style="border-collapse:collapse;width:100%;text-align:center;font-size:.92rem;margin-top:4px">'
            f'<tr><th></th>{head}</tr>{rows}</table></div>')


st.subheader("Four matrices: E across, V up, one matrix per ρ")
legend = "".join(f'<span style="background:{TIER_BG[i]};color:{TIER_FG[i]};padding:3px 10px;border-radius:99px;margin-right:6px;font-weight:600;font-size:.85rem">'
                 f'T{i + 1} {TIER_NAME[i]}</span>' for i in range(5))
st.markdown(f'<div style="margin-bottom:.4rem">{legend}</div>', unsafe_allow_html=True)
st.caption("Each cell shows R and its tier. Colour follows the five fixed RMTI tiers (R below 0.05, 0.15, 0.35, 0.60), so the same colour means the same tier for every L. "
           "L is fixed by its slider. The dark outline marks the cell nearest your E and V.")
cols = st.columns(4)
for col, r in zip(cols, [0.0, 0.25, 0.50, 0.75]):
    col.markdown(panel(r), unsafe_allow_html=True)

try:                                    # cross-check against the platform engine (service.py at the repo root)
    import service as S
    out = S.snapshot(S.resolve_domain("oncoclastics", "hcc"), 100000, L, E, V, rho, rho2, 5)
    st.caption(f"Engine check (HCC module): tier now {out.get('tier_now', 'n/a')}. The matrices use the formula above.")
except Exception as e:                  # noqa: BLE001
    st.caption(f"Engine check unavailable here ({type(e).__name__}). The matrices use the formula above.")
st.caption("Build 2026-11-15 · navy, white and red")
