"""HCC surveillance calculator (mirrors the RMTI-HCC workbook)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import content
from engine import albi, core, hcc, short
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig
from views.calculator import tier_ladder


def render():
    page_header("HCC Surveillance Calculator",
                "Triage hepatocellular carcinoma surveillance for a patient or a cohort. Reproduces the six published cohorts and the Pearl-protocol aetiologies.",
                "Clinical calculators")
    t_pat, t_coh = st.tabs(["Patient or cohort", "Published cohorts"])
    with t_pat:
        left, right = st.columns([1, 1.25], gap="large")
        with left:
            with st.container(border=True, key="panel"):
                st.subheader("Inputs")
                aet = st.selectbox("Aetiology → likelihood L", list(content.HCC_L_ANCHORS))
                L = st.slider("L · annual HCC likelihood", 0.0, 1.0, content.HCC_L_ANCHORS[aet], 0.01,
                              help="Anchor from annual incidence. Use a validated score (aMAP, THRI) where available.")
                vmode = st.radio("Vulnerability V from", ["ALBI grade", "Albumin and bilirubin"], horizontal=True)
                if vmode == "ALBI grade":
                    g = st.select_slider("ALBI grade", [1, 2, 3], 1)
                else:
                    a1, a2 = st.columns(2)
                    alb = a1.number_input("Albumin (g/L)", 10.0, 60.0, 40.0)
                    bil = a2.number_input("Bilirubin (µmol/L)", 1.0, 400.0, 12.0)
                    sc, g = albi(alb, bil)
                    st.caption(f"ALBI score {sc} → grade {g}")
                V = hcc.albi_to_v(g)
                st.caption(f"V = {V:.2f} (ALBI grade {g} anchor)")
                E = st.slider("E · share of at-risk reached by surveillance", 0.0, 1.0, 0.60, 0.01)
                ctx_now = st.selectbox("Surveillance today → ρ now", list(content.HCC_RHO_ANCHORS), 1)
                ctx_after = st.selectbox("Improved surveillance → ρ after", list(content.HCC_RHO_ANCHORS), 4)
                stage = st.selectbox("Stage if a tumour is missed → C", list(content.BCLC_C), 4)
                N = st.number_input("At-risk population N", 100, 5_000_000, 100_000, step=1000)
        with right:
            res = hcc.assess_patient(N, L, E, V, content.HCC_RHO_ANCHORS[ctx_now], content.HCC_RHO_ANCHORS[ctx_after], content.BCLC_C[stage])
            st.subheader("Result")
            m1, m2, m3 = st.columns(3)
            m1.metric("Inherent L·E·V", f"{res['IR']:.3f}")
            m2.metric("R now", f"{res['R_now']:.3f}")
            m3.metric("R after", f"{res['R_after']:.3f}", f"{-res['risk_reduction_pct']:.1f}%", delta_color="inverse")
            full_now, full_after = core.tier(res["R_now"]), core.tier(res["R_after"])
            st.markdown(f"**Now:** {badge(full_now)} &nbsp; {res['posture_now']}", unsafe_allow_html=True)
            st.markdown(f"**After:** {badge(full_after)} &nbsp; {res['posture_after']}", unsafe_allow_html=True)
            st.plotly_chart(tier_ladder(res["R_now"], res["R_after"]), width="stretch")
            s1, s2 = st.columns(2)
            s1.metric("EAL now → after", f"{res['EAL_now']:.3f} → {res['EAL_after']:.3f}")
            s2.metric("Investment efficiency", f"{res['IEI']:.3f}" if res["IEI"] is not None else "n/a")
            st.caption("Decision support for surveillance intensity. Not a diagnosis and not a treatment recommendation.")
    with t_coh:
        which = st.radio("Cohort set", ["Six published cohorts (Table 2)", "Pearl protocol (Table 3)"], horizontal=True)
        src = hcc.PUBLISHED_COHORTS if which.startswith("Six") else hcc.PEARL_COHORTS
        ranked = hcc.rank_cohort_hcc(hcc._scoreable(src))
        df = pd.DataFrame([{"Priority": r["priority_in_tier"], "Cohort": r["name"], "Incidence": src[r["name"]]["incidence"],
                            "R now": r["R_now"], "Tier now": r["tier_now"], "R after": r["R_after"], "Tier after": r["tier_after"],
                            "Reduction %": r["risk_reduction_pct"], "EAL now": r["EAL_now"]} for r in ranked])
        st.dataframe(df, hide_index=True, width="stretch")
        fig = go.Figure()
        add_tier_bands(fig)
        fig.add_bar(x=df["Cohort"], y=df["R now"], name="R now", marker_color="#1E3A5F")
        fig.add_bar(x=df["Cohort"], y=df["R after"], name="R after", marker_color="#93C5FD")
        fig.update_layout(barmode="group", yaxis_title="Residual risk R", yaxis_range=[0, 0.4])
        st.plotly_chart(style_fig(fig, 460), width="stretch")
    disclaimer()
