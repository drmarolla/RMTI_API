"""Case study: chronic liver disease to HCC, built on published work led by Dr. Philip J. Johnson."""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
st.set_page_config(page_title="Johnson case study | RMTI", page_icon="🧬", layout="wide")
import oncoclastic_style as ui  # noqa: E402
import rmti_johnson_case as jc  # noqa: E402

ui.apply()

st.markdown('<div class="rm-kicker">Case study · biological and care-system oncoclastics</div>', unsafe_allow_html=True)
st.title("From chronic liver disease to HCC")
st.markdown("**Built on published work led by Dr. Philip J. Johnson, University of Liverpool.** "
            "Elasticity analysis of the Risk Mechanism Theory Index (RMTI) with the biological and care-system "
            "components of resilience, ρ<sub>bio</sub> and ρ<sub>care</sub>.", unsafe_allow_html=True)
st.markdown('<div class="rm-note">Independent RMTI case study. Dr. Johnson and his co-authors did not review it and are not '
            'responsible for the mapping or the calculations. Research prototype: not validated, not a medical device, '
            'not for patient-care decisions. Study figures are quoted as reported; everything derived is illustrative.</div>',
            unsafe_allow_html=True)

st.header("The two studies")
c1, c2 = st.columns(2)
for col, key in ((c1, "johnson2024"), (c2, "cucchetti2023")):
    s = jc.SOURCES[key]
    with col:
        st.markdown(f'<div class="rm-card"><b>{s["title"]}</b><br>{s["authors"]}<br><i>{s["journal"]}</i><br>'
                    f'<a href="https://doi.org/{s["doi"]}">doi:{s["doi"]}</a></div>', unsafe_allow_html=True)
        for k, v in jc.PUBLISHED[key]:
            st.markdown(f"- **{k}:** {v}")
st.caption(f"The authors' own cure calculator: {jc.LIVERPOOL_CALCULATOR}")

st.header("How RMTI reads them")
st.markdown("""
| RMTI term | Reading in this case study | Source |
|---|---|---|
| **L** | Cumulative HCC risk over the horizon, 1 − exp(−rate × years), from the incidence per 1000 patient-years | Johnson et al. 2024 (derived here) |
| **E**, **V** | Placeholders you can set below. V can be driven by Fib-4 or ALBI grade | Fib-4 and ALBI from both studies |
| **ρ<sub>bio</sub>** | Biological reserve, kept apart from care delivery (placeholder) | Not scored in the papers |
| **ρ<sub>care</sub>** | Delivery of surveillance and follow-up (placeholder; the studies describe programme-level detection) | Context in both studies |
| **C** | Not modified. Cure after ablation depends on tumour size and liver function at detection, which overlaps with ρ<sub>care</sub>: a stated limitation | Cucchetti et al. 2023 |
""", unsafe_allow_html=True)

st.header("Interactive elasticity analysis")
a, b, c, d = st.columns(4)
E = a.slider("E, exposure", 0.05, 1.0, 0.60, 0.05)
V = b.slider("V, vulnerability", 0.05, 1.0, 0.50, 0.05)
rb = c.slider("ρ_bio", 0.0, 0.9, 0.30, 0.05)
yrs = d.slider("Horizon (years)", 3, 20, 10)
e, f = st.columns(2)
low = e.slider("ρ_care, low delivery", 0.0, 0.9, 0.20, 0.05)
high = f.slider("ρ_care, high delivery", 0.0, 0.95, 0.70, 0.05)

rows = jc.case_table(E=E, V=V, rho_bio=rb, rho_care_low=low, rho_care_high=high, years=float(yrs))
st.table([{"Pathway": r["pathway"], "Care delivery": r["care"], "L": f"{r['L']:.3f}", "ρ_care": f"{r['rho_care']:.2f}",
           "ρ (combined)": f"{r['rho']:.3f}", "R": f"{r['R']:.4f}", "ε of R to ρ_care": f"{r['eps_rho_care']:+.2f}"} for r in rows])
st.markdown("ε<sub>L</sub> = ε<sub>E</sub> = ε<sub>V</sub> = 1, and ε<sub>ρcare</sub> = −ρ<sub>care</sub> / (1 − ρ<sub>care</sub>): "
            "the more delivery is already in place, the more a further point of ρ<sub>care</sub> is worth.", unsafe_allow_html=True)

dec = jc.pathway_comparison(rows)
be = jc.breakeven_rho_care(rows[0]["L"], rows[2]["L"], low)
g1, g2 = st.columns(2)
with g1:
    st.subheader("What moves R")
    st.caption("Change in ln R from (non-cirrhotic, low delivery) to (cirrhosis, high delivery)")
    st.bar_chart({"L": dec["dln_L"], "E": dec["dln_E"], "V": dec["dln_V"], "1 − ρ": dec["dln_1-rho"]})
    st.write(f"R changes by {dec['pct_change_R']:+.0f}% in total.")
with g2:
    st.subheader("Break-even delivery")
    if be is None:
        st.write("No ρ_care in [0, 1) makes the cirrhosis pathway match the non-cirrhotic R at the low-delivery level.")
    else:
        st.write(f"For cirrhosis to match the non-cirrhotic R at ρ_care = {low:.2f}, ρ_care would have to reach **{be:.2f}** "
                 "(E, V and ρ_bio equal). Delivery alone has to offset the whole difference in L.")

st.subheader("V driven by Fib-4 (placeholder anchors)")
st.table([{"Fib-4": r["fib4"], "V*": f"{r['V_star']:.3f}", "ε of V* to Fib-4": f"{r['eps_d']:.2f}"} for r in jc.fib4_v_elasticity()])
st.caption("Fib-4 values are the published medians at baseline (1.52 without HCC, 2.4 with HCC) and the 3.25 cirrhosis threshold. "
           "The mapping (V* from 0.35 to 0.85 over Fib-4 0 to 6) is a placeholder, not calibrated.")

st.header("Limits")
st.markdown("""
- Elasticities are local and assume the other terms are fixed and independent; R is a relative index, not a probability.
- ρ_bio and ρ_care are assumed to act independently on the same inherent risk, and ρ_bio must not contain care delivery: propositions to be tested.
- Placeholders for E, V, ρ_bio and ρ_care are not taken from the papers. Whether trajectory adds information beyond a well-measured current level is an open question.
""")
st.caption("Code: rmti_johnson_case.py, rmti_elasticity.py, rmti_resilience_components.py (Apache-2.0).")
