"""General RMTI calculator + Custom/Your Field + Excel-style portfolio reassessment."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, elas, short
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

WORKED_EXAMPLES = {
    **{k: {**v, "field": "Urban Infrastructure", "hazard": v["asset"]} for k, v in content.SIX_CITIES.items()},
    "Pacific Palisades (Wildfire)": dict(field="Wildfire Resilience", hazard="WUI Urban Fire (2025)", N=23700, L=0.350, E_sel=0.800, V=0.650, rho_now=0.200, rho_after=0.350, C=4),
    "Altadena (Wildfire)": dict(field="Wildfire Resilience", hazard="Eaton Fire WUI (2025)", N=42000, L=0.400, E_sel=0.800, V=0.600, rho_now=0.200, rho_after=0.350, C=4),
}


def tier_ladder(r_now, r_after=None, height=150):
    fig = go.Figure()
    add_tier_bands(fig, axis="x")
    fig.add_vline(x=r_now, line_width=5, line_color="#0F172A", annotation_text=f"now {r_now:.3f}", annotation_position="top")
    if r_after is not None:
        fig.add_vline(x=r_after, line_width=5, line_color="#BE123C", line_dash="dot", annotation_text=f"after {r_after:.3f}", annotation_position="bottom")
    fig.update_xaxes(range=(0, 0.75), title="Residual risk R")
    fig.update_yaxes(visible=False)
    return style_fig(fig, height)


def render():
    page_header(
        "RMTI Calculator — Assess · Quantify · Treat",
        "Score any custom domain, clinical cohort, or infrastructure asset with R = L · E · V · (1 − ρ), or reassess multi-case portfolios.",
        "Clinical calculators",
    )

    t_one, t_port = st.tabs(["Custom / Your Field (Single Assessment)", "Multi-Case & City Reassessment (Excel Table)"])

    with t_one:
        left, right = st.columns((1.0, 1.25), gap="large")
        with left:
            with st.container(border=True, key="panel"):
                st.subheader("1. Domain & Parameter Inputs")
                preset = st.selectbox("Mode or Worked Example", ["Custom / Your Field"] + list(WORKED_EXAMPLES))
                p = WORKED_EXAMPLES.get(preset, dict(field="Your Domain / Field", hazard="Custom Hazard Mechanism", N=1_000_000, L=0.60, E_sel=0.60, V=0.60, rho_now=0.20, rho_after=0.50, C=4))
                c_f1, c_f2 = st.columns(2)
                field_name = c_f1.text_input("Your Field / Sector", value=p["field"])
                asset_name = c_f2.text_input("Asset / Cohort Name", value="Custom Scenario" if preset == "Custom / Your Field" else preset)
                hazard_desc = st.text_input("Hazard / Mechanism (h)", value=p["hazard"])

                N = st.number_input("Population or Cohort Size (N)", 10, 20_000_000_000, int(p["N"]), step=1000)
                L = st.slider("L · Likelihood / Hazard", 0.0, 1.0, float(p["L"]), 0.005)
                use_elog = st.toggle("Use log-normalised population exposure E_log", False)
                elog = core.e_log(N)
                E = elog if use_elog else st.slider("E · Exposure", 0.0, 1.0, float(p["E_sel"]), 0.005)
                if use_elog:
                    st.caption(f"E = E_log = {elog:.3f}")
                V = st.slider("V · Vulnerability", 0.0, 1.0, float(p["V"]), 0.005)
                rho_now = st.slider("ρ now · Baseline Resilience", 0.0, 0.99, float(p["rho_now"]), 0.005)
                has_after = st.toggle("Model Resilience Investment / Treatment (ρ after)", True)
                rho_after = st.slider("ρ after · Target Resilience", 0.0, 0.99, float(p.get("rho_after", 0.50)), 0.005) if has_after else None
                C = st.select_slider("C · Consequence (1–5)", (1, 2, 3, 4, 5), int(p["C"]), format_func=lambda c: f"{c} {content.C_NAMES[c]}")

        with right:
            res = core.assess(N, L, E, V, rho_now, rho_after, C)
            r_disp = res["R_after"] if rho_after is not None else res["R_now"]
            rho_disp = rho_after if rho_after is not None else rho_now

            # Dual-Layer Main 3D + Main 3D+2D Visual Header
            v1, v2 = st.columns(2, gap="small")
            with v1:
                components.html(f"""
                <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;background:#FFF;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden}}.p{{position:absolute;top:8px;left:8px;z-index:3;display:flex;gap:4px}}.b{{background:rgba(15,23,42,0.85);color:#FFF;font-size:9.5px;font-weight:700;padding:3px 8px;border-radius:999px}}video{{width:100%;height:195px;object-fit:cover;display:block}}</style>
                <div class="f"><div class="p"><span class="b">Main 3D</span><span class="b">{field_name[:18]}</span></div>
                <video autoplay loop muted playsinline><source src="{RAW_VIDEOS}/calc_main3d.mp4" type="video/mp4"><source src="{RAW_VIDEOS}/video1_4stages_3d.mp4" type="video/mp4"></video></div>
                """, height=200)
            with v2:
                components.html(f"""
                <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;background:#0F172A;border-radius:14px;overflow:hidden}}.p{{position:absolute;top:8px;left:8px;z-index:4;display:flex;gap:4px}}.b{{background:rgba(15,23,42,0.85);color:#FFF;font-size:9.5px;font-weight:700;padding:3px 8px;border-radius:999px}}video{{width:100%;height:195px;object-fit:cover;opacity:0.42;display:block}}.h{{position:absolute;inset:32px 10px 8px 10px;z-index:3;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(180deg,rgba(15,23,42,0.1),rgba(15,23,42,0.92));border-radius:10px;padding:8px;color:#FFF}}.g{{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;align-items:end;height:88px}}.c{{display:flex;flex-direction:column;align-items:center;gap:2px}}.bar{{width:100%;border-radius:4px 4px 1px 1px}}</style>
                <div class="f"><div class="p"><span class="b">Main 3D + 2D</span><span class="b">Live Data</span></div>
                <video autoplay loop muted playsinline><source src="{RAW_VIDEOS}/calc_dual2d.mp4" type="video/mp4"><source src="{RAW_VIDEOS}/case_african_cities.mp4" type="video/mp4"></video>
                <div class="h"><div class="g">
                  <div class="c"><span style="font-size:9.5px;font-weight:800">{L:.2f}</span><div class="bar" style="height:{int(L*66)}px;background:#38BDF8"></div><span style="font-size:9px;color:#CBD5E1">L</span></div>
                  <div class="c"><span style="font-size:9.5px;font-weight:800">{E:.2f}</span><div class="bar" style="height:{int(E*66)}px;background:#F87171"></div><span style="font-size:9px;color:#CBD5E1">E</span></div>
                  <div class="c"><span style="font-size:9.5px;font-weight:800">{V:.2f}</span><div class="bar" style="height:{int(V*66)}px;background:#FBBF24"></div><span style="font-size:9px;color:#CBD5E1">V</span></div>
                  <div class="c"><span style="font-size:9.5px;font-weight:800">{1-rho_disp:.2f}</span><div class="bar" style="height:{int((1-rho_disp)*66)}px;background:#34D399"></div><span style="font-size:9px;color:#CBD5E1">1−ρ</span></div>
                  <div class="c"><span style="font-size:9.5px;font-weight:800">{r_disp:.3f}</span><div class="bar" style="height:{max(10,int(r_disp*105))}px;background:#FFF"></div><span style="font-size:9px;color:#CBD5E1">R</span></div>
                </div></div></div>
                """, height=200)

            st.subheader(f"Result: {asset_name} ({field_name})")
            st.caption(f"Hazard / Mechanism: {hazard_desc}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Inherent Risk (IR)", f"{res['IR']:.3f}")
            m2.metric("Residual Risk R", f"{res['R_now']:.3f}")
            m3.metric("EAL Index", f"{res['EAL_now']:.3f}")
            st.markdown(f"**Tier now:** {badge(res['tier_now'])} &nbsp; {res['posture_now']}", unsafe_allow_html=True)

            if rho_after is not None:
                a1, a2, a3 = st.columns(3)
                a1.metric("R after", f"{res['R_after']:.3f}", f"{-res['risk_reduction_pct']:.1f}%", delta_color="inverse")
                a2.metric("Efficiency (IEI)", f"{res['IEI']:.3f}" if res["IEI"] is not None else "n/a")
                a3.metric("EAL after", f"{res['EAL_after']:.3f}")
                st.markdown(f"**Tier after:** {badge(res['tier_after'])} &nbsp; {res['posture_after']}", unsafe_allow_html=True)

            st.plotly_chart(tier_ladder(res["R_now"], res.get("R_after")), width="stretch")
            e = elas.elasticities(L, E, V, rho_now) if rho_now < 1 else {}
            if e:
                st.markdown(f"**Sensitivity.** A 1% change in L, E, or V changes R by 1%. A 1% change in ρ changes R by {e.get('rho', 0):.2f}%.")
            st.caption(f"Per-capita equity rate: {res['equity_now_per_1M']:.4f} EAL per 1M · E_log helper: {res['E_log']:.3f}")

    with t_port:
        st.markdown("Edit any cell below to reassess the six cities or wildfire cases, or click **`+`** at the bottom to add your own **Custom / Your Field** rows.")
        init_rows = [{"Field": v["field"], "Name": k, "Hazard": v["hazard"], "N": v["N"], "L": v["L"], "E_sel": v["E_sel"], "V": v["V"], "rho_now": v["rho_now"], "rho_after": v.get("rho_after"), "C": v["C"]} for k, v in WORKED_EXAMPLES.items()]
        init_rows.append({"Field": "Custom / Your Field", "Name": "Your Asset / Cohort 1", "Hazard": "Enter hazard", "N": 500000, "L": 0.55, "E_sel": 0.60, "V": 0.50, "rho_now": 0.25, "rho_after": 0.55, "C": 4})
        ed = st.data_editor(pd.DataFrame(init_rows), num_rows="dynamic", width="stretch", key="port_ed")

        rows, meta = {}, {}
        for _, r in ed.dropna(subset=["Name", "N", "L", "E_sel", "V", "rho_now", "C"]).iterrows():
            nm = str(r["Name"])
