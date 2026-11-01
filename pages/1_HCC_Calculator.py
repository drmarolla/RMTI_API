"""HCC patient calculator: the Excel workbook's Calculator and Parameters sheets, on the platform engine (no new equations)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HCC calculator · Oncoclastics", layout="wide")
import registry as R
import sandbox as B
import service as S
import style
from ui_common import gate, call

style.inject()
gate()
HCC = S.HCC_COHORT
style.hero("HCC calculator", "Relative risk-mechanism score for one patient, from routine blood tests and age and sex (RMTI-HCC)",
           [f"Engine v{S.ENGINE_VERSION}", f"Registry {R.stamp()}", "Research prototype", "Not a medical device"])
style.strip()
t_calc, t_how, t_ev = st.tabs(["Calculate", "How it is calculated", "Evidence and limits"])

with t_calc:
    st.markdown("##### 1. Patient values")
    c = st.columns(5)
    age = c[0].number_input("Age (years)", 18.0, 110.0, 62.0, 1.0)
    sex = c[1].selectbox("Sex", ["Male", "Female"])
    alb = c[2].number_input("Albumin (g/L)", 5.0, 70.0, 40.0, 1.0)
    bil = c[3].number_input("Total bilirubin (µmol/L)", 1.0, 1000.0, 14.0, 1.0)
    plt_ = c[4].number_input("Platelets (10⁹/L)", 0.0, 2000.0, 150.0, 5.0)
    st.markdown("##### 2. Settings")
    d = st.columns(5)
    tool = d[0].radio("L tool", ["aMAP-ref", "aMAP"], help="aMAP-ref keeps L (age, sex, platelets) and V (albumin, bilirubin) on separate variables. Full aMAP contains ALBI, so albumin and bilirubin would be counted twice.")
    E = d[1].slider("E: exposure", 0.0, 1.0, 0.60, 0.05, help="Share of the at-risk population reached by the hazard. Entered by you, not measured from the patient.")
    rho = d[2].slider("ρ now: resilience", 0.0, 0.99, 0.20, 0.01, help="Surveillance and care capacity today. Entered by you.")
    rho_after = d[3].slider("ρ after: improved state", 0.0, 0.99, 0.65, 0.01, help="Capacity after an improvement you want to compare against.")
    C = d[4].select_slider("C: consequence index", [1, 2, 3, 4, 5], 5, help="1 low to 5 severe; used for the EAL index only.")
    overlap = False
    if tool == "aMAP":
        overlap = st.checkbox("I understand that albumin and bilirubin then enter both L and V. Show the result as DIAGNOSTIC only, not as the RMTI result.")

    payload = dict(age_years=age, male=int(sex == "Male"), albumin_g_l=alb, bilirubin_umol_l=bil, platelets_1e9_l=plt_,
                   l_tool=tool, allow_overlap=overlap, E=E, rho=rho, rho_after=rho_after, C=C)
    try:
        if tool == "aMAP" and not overlap:
            raise ValueError("Not calculated: L tool aMAP and V (ALBI) both use albumin and bilirubin, so they would be counted twice. Use aMAP-ref, or tick the box above to see a DIAGNOSTIC value.")
        o = call("/v1/hcc/patient", payload, lambda: S.hcc_patient(age, int(sex == "Male"), alb, bil, plt_, tool, E, rho, rho_after, C, overlap))
    except ValueError as e:
        st.error(str(e)); st.stop()

    st.markdown("##### 3. Result")
    (st.error if o["overlap"] else st.success)(o["status"])
    r = st.columns(3)
    with r[0]:
        style.result_card("R now (relative score, 0 to 1)", f"{o['R']:.3f}", o["tier"], f"ρ = {rho:.2f}")
    with r[1]:
        style.result_card("R after (improved ρ)", f"{o['R_after']:.3f}", o["tier_after"], f"ρ = {rho_after:.2f}; change {o['R_after'] - o['R']:+.3f}")
    with r[2]:
        style.result_card("EAL index, L · C · (1 − ρ)", f"{o['EAL']:.3f}", None, "Consequence-weighted; not a tier")
    st.write("")
    st.markdown(f"**In words:** these values place this profile in tier **{o['tier']}** of 5 on a fixed scale (tier boundaries 0.05, 0.15, 0.35, 0.60). "
                "R is a rank, not a probability: it does not say how likely this person is to develop HCC.")

    st.markdown("##### How this result was reached")
    tool_score = o["amap_ref"] if tool == "aMAP-ref" else o["amap"]
    st.dataframe(pd.DataFrame([
        ["ALBI score", f"{o['albi']:.3f}", "0.66 × log10(bilirubin) − 0.085 × albumin  (Johnson 2015)"],
        ["ALBI grade → V", f"grade {o['albi_grade']} → V = {o['V']:.2f}", "Vulnerability anchors 0.35 / 0.60 / 0.85 (assigned)"],
        ["aMAP-ref score" if tool == "aMAP-ref" else "aMAP score (overlaps ALBI)", f"{tool_score:.1f}", "Fan 2020 formula" + (f"; ALBI fixed at {HCC.ALBI_REF}" if tool == "aMAP-ref" else "")],
        ["aMAP risk group", f"group {o['risk_group']}", f"low < {HCC.AMAP_LOW_BELOW:g}, medium to {HCC.AMAP_HIGH_ABOVE:g}, high above"],
        ["Annual incidence of the group → L", f"{100 * o['annual_incidence']:.1f}%/yr → L = {o['L']:.3f}", "Published group incidence, log-scaled between anchors (assigned)"],
        ["E, ρ now", f"{E:.2f}, {rho:.2f}", "Entered by you"],
        ["R = L · E · V · (1 − ρ)", f"{o['L']:.3f} · {E:.2f} · {o['V']:.2f} · {1 - rho:.2f} = {o['R_raw']:.5f}", "Unrounded value decides the tier"],
    ], columns=["Step", "Value", "Basis"]), hide_index=True, column_config={"Value": st.column_config.TextColumn(width="large"), "Basis": st.column_config.TextColumn(width="large")})

    ref = B.dataset_reference("ogaki")
    if ref:
        st.markdown("##### What happened in a reference cohort")
        default = (tool == "aMAP-ref" and abs(E - 0.6) < 1e-9 and abs(rho - 0.2) < 1e-9)
        n = o["tier"]
        if not default:
            style.note("Reference outcomes are shown only at the default settings (aMAP-ref, E 0.60, ρ now 0.20), because tiers shift when settings change.")
        elif n in ref["cif_hcc_by_tier"]:
            v = ref["cif_hcc_by_tier"][n]
            st.markdown(f"In the Ogaki cohort ({ref['n']:,} patients, Japan), patients in tier **{n}** at these settings went on to develop HCC at a cumulative rate of "
                        f"**{100 * v['5']:.1f}% by 5 years** and **{100 * v['10']:.1f}% by 10 years** (death without HCC treated as a competing event).")
            style.note("A description of one cohort, not an independent validation. Single source population; it may not apply elsewhere.")
        else:
            style.note(f"No patients in the Ogaki cohort fell in tier {n}, so there is no reference outcome for it.")

    rec = dict(tool="Oncoclastics HCC calculator", engine=S.ENGINE_VERSION, registry=R.stamp(), inputs=payload, result=o)
    st.download_button("Download this calculation as a record (JSON)", json.dumps(rec, indent=1), "hcc_calculation_record.json", help="Inputs, settings, outputs and versions, for your notes or audit.")

with t_how:
    st.markdown("#### The calculation, step by step")
    st.markdown("""
1. **V (vulnerability)** from the **ALBI grade**, which uses albumin and bilirubin: grade 1 → 0.35, grade 2 → 0.60, grade 3 → 0.85.
2. **L (likelihood)** from the **aMAP-ref** score (age, sex, platelets), which gives a risk group. Each group has a published annual HCC incidence, log-scaled to 0 to 1.
3. **E (exposure)** and **ρ (resilience)** are settings you choose. They are not measured from the patient.
4. **R = L · E · V · (1 − ρ)**, a number between 0 and 1, placed into a fixed tier. **EAL = L · C · (1 − ρ)** is a separate consequence-weighted index.
""")
    st.markdown("**Why aMAP-ref and not aMAP?** No measured variable may feed two terms. Full aMAP already contains ALBI, so using it for L and ALBI for V would count albumin and bilirubin twice. aMAP-ref evaluates the published aMAP formula at a fixed reference ALBI, so L depends only on age, sex and platelets.")
    with st.expander("Constants used (read-only; changed only through a reviewed release, see UPDATING.md)"):
        st.markdown("**ALBI grades:** grade 1 ≤ −2.60, grade 2 ≤ −1.39, otherwise grade 3. **V anchors:** " + ", ".join(f"grade {k}: {v}" for k, v in S.ALBI_V.items()))
        st.dataframe(pd.DataFrame([{"aMAP group": g, "published range (%/yr)": f"{100 * lo:g} to {100 * hi:g}", "value used (%/yr)": 100 * HCC.AMAP_GROUP_INCIDENCE[g]}
                                   for g, (lo, hi) in HCC.AMAP_GROUP_RANGE.items()]), hide_index=True)
        lo, hi = HCC.L_ANCHOR_SETS["primary"]
        st.markdown(f"**L scale:** log10 between {100 * lo:g}%/yr (L = 0) and {100 * hi:g}%/yr (L = 1). **Tiers:** " + " · ".join(S.TIERS))

with t_ev:
    st.markdown("#### Evidence")
    st.markdown("""
- **ALBI:** Johnson PJ et al. *J Clin Oncol* 2015;33:550-558.
- **aMAP:** Fan R et al. *J Hepatol* 2020;73:1368-1378.
- **Reference cohort:** the Ogaki cohort (Japan), described in the Cohort Sandbox page, where the same engine is checked against the Excel workbook.
""")
    st.markdown("#### Limits you should know")
    st.markdown("""
- **Not a probability.** R ranks profiles on a fixed scale. It is not an absolute risk and not a prediction for an individual.
- **Anchors are assigned, not estimated.** The V values and the L scale come from published thresholds and rubric choices, not from fitting.
- **aMAP-ref is an approximation.** Group incidences are approximate for patients at the reference ALBI and are not validated; this is reported, not hidden.
- **E and ρ are your inputs.** The tier moves with them. Change them deliberately and record why.
- **Population.** Evidence comes from published aMAP cohorts and one Japanese cohort. Other populations are untested.
- **Intended use.** Research and teaching. Decisions about care rest with the treating clinicians, current guidelines and their judgment.
""")
    with st.expander("Full disclaimer"):
        st.write(S.DISCLAIMER)
