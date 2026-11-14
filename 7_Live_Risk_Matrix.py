"""Live Risk Matrix: sliders for L, E, V and rho, the formula with your numbers, and four 4D matrices."""
import streamlit as st

st.set_page_config(page_title="Live Risk Matrix", page_icon="🧬", layout="wide")
import rmti_theme
rmti_theme.apply()
st.title("Live Risk Matrix")
st.caption("R = L · E · V · (1 − ρ). Research prototype. Synthetic, illustrative values only. Not for patient care.")

c1, c2, c3 = st.columns(3)
L = c1.slider("L: likelihood (hazard)", 0.0, 1.0, 0.30, 0.01)
E = c2.slider("E: exposure", 0.0, 1.0, 0.65, 0.01)
V = c3.slider("V: vulnerability", 0.0, 1.0, 0.55, 0.01)
c4, c5 = st.columns(2)
rho = c4.slider("ρ now: resilience / surveillance adequacy", 0.0, 0.95, 0.20, 0.01)
rho2 = c5.slider("ρ after: improved state", 0.0, 0.95, 0.50, 0.01)

R, R2 = L * E * V * (1 - rho), L * E * V * (1 - rho2)
st.latex(r"R = L \cdot E \cdot V \cdot (1-\rho)")
st.latex(rf"R_{{now}} = {L:.2f} \cdot {E:.2f} \cdot {V:.2f} \cdot (1-{rho:.2f}) = {R:.4f}")
st.latex(rf"R_{{after}} = {L:.2f} \cdot {E:.2f} \cdot {V:.2f} \cdot (1-{rho2:.2f}) = {R2:.4f}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("R now", f"{R:.4f}")
m2.metric("R after", f"{R2:.4f}", f"{R2 - R:+.4f}", delta_color="inverse")
m3.metric("Reduction from ρ", f"{(1 - (1 - rho2) / (1 - rho)) * 100:.0f}%")
tier = "n/a"
try:
    import service as S
    out = S.snapshot(S.resolve_domain("oncoclastics", "hcc"), 100000, L, E, V, rho, rho2, 5)
    tier = str(out.get("tier_now", "n/a"))
except Exception:
    pass
m4.metric("Engine tier (HCC module)", tier)

def colour(v):                       # 0 -> white-blue, 0.5 -> light blue, 1 -> red
    stops = [(0, (238, 246, 254)), (0.5, (125, 184, 238)), (1, (217, 38, 44))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            t = (v - a) / (b - a)
            return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
    return stops[-1][1]

grid = [0, .2, .4, .6, .8, 1]
nearest = lambda x: min(grid, key=lambda g: abs(g - x))
def panel(r):
    rows = ""
    for v in reversed(grid):
        cells = ""
        for e in grid:
            val = L * e * v * (1 - r)
            f = val / L if L > 0 else 0
            rr, gg, bb = colour(f)
            me = "outline:3px solid #0f2a4a;" if (e == nearest(E) and v == nearest(V)) else ""
            cells += f'<td style="background:rgb({rr},{gg},{bb});color:{"#fff" if f > .6 else "#0f2a4a"};{me}">{val:.2f}</td>'
        rows += f'<tr><th>{v:.1f}</th>{cells}</tr>'
    head = "".join(f"<th>{e:.1f}</th>" for e in grid)
    return (f'<div style="font-family:Inter,Segoe UI,sans-serif"><b>ρ = {r:.2f}</b><table style="border-collapse:collapse;width:100%;text-align:center;font-size:.8rem;margin-top:4px">'
            f'<tr><th></th>{head}</tr>{rows}</table></div>')

st.subheader("Four matrices: E across, V up, one matrix per ρ")
st.caption("L is fixed by its slider. The dark outline marks the cell nearest your E and V. Red is higher risk, light blue lower.")
cols = st.columns(4)
for col, r in zip(cols, [0.0, 0.25, 0.50, 0.75]):
    col.markdown(panel(r), unsafe_allow_html=True)
st.caption("Matrices use the formula above. The engine tier comes from the HCC module in service.py.")
