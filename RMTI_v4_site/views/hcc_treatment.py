"""HCC Stage 2-4 treatment calculator (evidence-gated, sandbox). Mirrors the workbook; research prototype."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import albi, core, s34, short
from rmti_ui import badge, disclaimer, page_header, style_fig

# Provisional registry, read from abstracts and secondary reports (see workbook, Trial Evidence tab).
REGISTRY = [
    dict(id="imbrave150", regimen="Atezolizumab + bevacizumab", comp="sorafenib", hr=0.66, lo=0.52, hi=0.85, ae_t=0.43, ae_c=0.46,
         elig=dict(allowed_child_pugh=["A"], allowed_ecog=[0, 1], excludes_main_pvtt=False),
         src="Finn 2020 NEJM; Cheng 2022 J Hepatol (updated)"),
    dict(id="himalaya_stride", regimen="Tremelimumab + durvalumab (STRIDE)", comp="sorafenib", hr=0.78, lo=0.65, hi=0.93, ae_t=0.258, ae_c=0.369,
         elig=dict(allowed_child_pugh=["A"], allowed_ecog=[0, 1], excludes_main_pvtt=True),
         src="Abou-Alfa 2022 NEJM Evid; Sangro 2024 Ann Oncol"),
    dict(id="checkmate9dw", regimen="Nivolumab + ipilimumab", comp="lenvatinib_or_sorafenib", hr=0.79, lo=0.65, hi=0.96, ae_t=0.41, ae_c=0.42,
         elig=None, src="Yau 2025 Lancet (mixed comparator; eligibility not extracted)"),
]
# Illustrative placeholder calibration, exactly as in the workbook (NOT from any source).
CLIP_RISK = {0: 0.30, 1: 0.40, 2: 0.55, 3: 0.70, 4: 0.85}


def _trial(r, horizon_max=48):
    months = np.arange(0, horizon_max + 1, dtype=float)
    s_ctrl = np.exp(-0.05 * months)          # shape is arbitrary: only the ratio of cumulative hazards is used
    s_trt = s_ctrl ** r["hr"]                # constant HR fallback (assumption A1: proportional hazards)
    return s34.TrialEvidence(id=r["id"], regimen=r["regimen"], comparator=r["comp"], months=months, s_trt=s_trt, s_ctrl=s_ctrl,
                             hr_ci_ratio=(r["lo"] / r["hr"], r["hi"] / r["hr"]), ae_excess=max(r["ae_t"] - r["ae_c"], 0.0),
                             eligibility=r["elig"], verified="abstract", source=r["src"])


def render():
    page_header("HCC Treatment Calculator",
                "Stage 2–4 evidence-gated matching: which regimens have trial evidence for this patient, and how far each moves residual risk.",
                "Clinical calculators")
    st.markdown('<div class="note"><b>Sandbox.</b> Trial entries are provisional (abstract level), the CLIP calibration is an illustrative '
                'placeholder, and effects use a constant hazard ratio. Results demonstrate the method. They are not treatment advice.</div>',
                unsafe_allow_html=True)
    st.write("")
    mode = st.radio("Evidence mode", ["Sandbox", "Strict"], horizontal=True,
                    help="Strict requires full-text verified trials and a verified CLIP calibration. None are loaded yet.")
    left, right = st.columns([1, 1.3], gap="large")
    with left:
        with st.container(border=True, key="panel"):
            st.subheader("Patient (synthetic)")
            cp = st.selectbox("Child-Pugh class", ["A", "B", "C"])
            ecog = st.select_slider("ECOG performance status", [0, 1, 2, 3, 4], 0)
            pvtt = st.toggle("Main portal vein thrombosis", False)
            clip = st.slider("CLIP score", 0, 6, 1, help="Computed upstream from the clinical record. At most 4 in Child-Pugh A.")
            a1, a2 = st.columns(2)
            alb = a1.number_input("Albumin (g/L)", 10.0, 60.0, 38.0)
            bil = a2.number_input("Bilirubin (µmol/L)", 1.0, 400.0, 14.0)
            rho_bio = st.slider("ρ_bio · biological reserve", 0.0, 0.9, 0.20, 0.01)
            rho_care = st.slider("ρ_care · treatment-pathway delivery", 0.0, 0.9, 0.20, 0.01)
            horizon = st.slider("Horizon (months)", 6, 48, 24)
            lam = st.slider("Harm weight λ (assigned)", 0.0, 2.0, 0.5, 0.1)
            C = st.select_slider("Consequence C", [1, 2, 3, 4, 5], 5)
    with right:
        sc, grade = albi(alb, bil)
        st.subheader("Result")
        if mode == "Strict":
            st.error("Strict mode refuses to compute: the loaded trial entries are abstract-level and the CLIP calibration is a placeholder. "
                     "Load full-text verified evidence first (this is by design).")
            disclaimer()
            return
        if cp == "A" and clip > s34.CLIP_MAX_CHILD_PUGH_A:
            st.error("A CLIP score above 4 is impossible for Child-Pugh class A. Adjust the inputs.")
            disclaimer()
            return
        if clip not in CLIP_RISK:
            st.warning("No calibration entry for this CLIP score (5 and 6 are not reachable in Child-Pugh A). Choose 0–4.")
            disclaimer()
            return
        calib = s34.ClipCalibration(table=CLIP_RISK, horizon_months=24, r_lo=0.10, r_hi=0.95, source="ILLUSTRATIVE PLACEHOLDER", verified="placeholder")
        L = s34.l_from_clip(clip, calib, child_pugh=cp, strict=False)
        rho_now = round(1 - (1 - rho_bio) * (1 - rho_care), 12)
        ci = s34.core_inputs_for_reading("strict", L, rho_now, {"child_pugh": cp}, C=C)
        patient = dict(child_pugh=cp, ecog=ecog, main_pvtt=pvtt, egd_cleared=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ALBI grade", f"{grade}", f"score {sc}", delta_color="off")
        m2.metric("L (from CLIP)", f"{L:.3f}")
        m3.metric("ρ now", f"{rho_now:.3f}")
        out = core.assess(**{**ci})
        m4.metric("R now", f"{out['R_now']:.3f}")
        st.markdown(f"**Tier now:** {badge(out['tier_now'])}", unsafe_allow_html=True)
        sorafenib = [_trial(r) for r in REGISTRY if r["comp"] == "sorafenib"]
        rows, notes = [], []
        for t in sorafenib + [_trial(r) for r in REGISTRY if r["comp"] != "sorafenib"]:
            res = s34.assess_regimen(ci, patient, t, horizon, None, None, lam)
            if res["status"] == "ELIGIBLE_MATCH":
                c = res["core"]
                rows.append({"Regimen": t.regimen, "Status": "Eligible match", "Effect (HR)": round(res["hr_eff"], 3), "ρ after": round(res["rho_after"], 3),
                             "R after": c["R_after"], "Interval": f"{res['R_after_interval'][0]:.3f} to {res['R_after_interval'][1]:.3f}",
                             "Tier after": short(c["tier_after"]), "Reduction %": c["risk_reduction_pct"]})
            else:
                rows.append({"Regimen": t.regimen, "Status": res["status"].replace("_", " ").title(), "Effect (HR)": None, "ρ after": None,
                             "R after": None, "Interval": "; ".join(res.get("reasons", [])), "Tier after": "", "Reduction %": None})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        try:
            cmp_ = s34.compare_regimens(ci, patient, sorafenib, horizon, None, None, lam)
            st.markdown(f"**Decision support among sorafenib-comparator trials:** {cmp_['decision']}")
            if cmp_.get("tipping_psi"):
                st.caption(f"Tipping point: a modifier of {cmp_['tipping_psi']:.2f} on the leading regimen's unprotected fraction would separate the options.")
        except ValueError as exc:
            st.warning(str(exc))
        st.caption("Nivolumab + ipilimumab used a mixed comparator and cannot be ranked against the sorafenib-comparator trials (rule I8). "
                   "If the top two intervals overlap, the honest output is no preferred therapy.")
        fig = go.Figure()
        for r in rows:
            if r["R after"] is not None:
                lo, hi = [float(x) for x in r["Interval"].split(" to ")]
                fig.add_trace(go.Scatter(x=[lo, r["R after"], hi], y=[r["Regimen"]] * 3, mode="lines+markers", name=r["Regimen"],
                                         marker=dict(size=[8, 14, 8])))
        fig.add_vline(x=out["R_now"], line_dash="dot", annotation_text="R now")
        fig.update_layout(xaxis_title="Residual risk after therapy (point and interval)", showlegend=False)
        if fig.data:
            st.plotly_chart(style_fig(fig, 300), width="stretch")
    disclaimer()
