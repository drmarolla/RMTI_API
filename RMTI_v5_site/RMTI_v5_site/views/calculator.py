"""General RMTI calculator + Custom/Your Field + Urban/Disaster reassessment."""
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
        "RMTI Calculator — Urban, Disaster & Custom Domains",
        "Score any custom field, infrastructure asset, or disaster scenario with R = L · E · V · (1 − ρ). (For clinical oncology triage, use the dedicated HCC Surveillance & Treatment calculators.)",
        "Clinical calculators",
    )

    t_one, t_port = st.tabs(["Custom / Your Field (Single Assessment)", "Multi-Case & City Reassessment (Excel Table)"])

    with t_one:
        left, right = st.columns((1.0, 1.25), gap="large")
        with left:
            with st.container(border=True, key="panel"):
                st.subheader("1. Domain & Parameter Inputs")
                preset = st.selectbox("Mode or Worked Example", ["Custom / Your Field"] + list(WORKED_EXAMPLES))
                is_custom = preset == "Custom / Your Field"
                p = WORKED_EXAMPLES.get(preset, dict(field="Your Domain / Field", hazard="Custom Hazard Mechanism", N=1_000_000, L=0.60, E_sel=0.60, V=0.60, rho_now=0.20, rho_after=0.50, C=4))
                c_f1, c_f2 = st.columns(2)
                field_name = c_f1.text_input("Your Field / Sector", value=p["field"])
                asset_name = c_f2.text_input("Asset / System Name", value="Custom Scenario" if is_custom else preset)
                hazard_desc = st.text_input("Hazard / Mechanism (h)", value=p["hazard"])

                N = st.number_input("Population or System Size (N)", 10, 20_000_000_000, int(p["N"]), step=1000)
                L = st.slider("L · Likelihood / Hazard", 0.0, 1.0, float(p["L"]), 0.005)
                use_elog = st.toggle("Use log-normalised population exposure E_log", False)
                elog = core.e_log(N)
                E = elog if use_elog else st.slider("E · Exposure", 0.0, 1.0, float(p["E_sel"]), 0.005)
                if use_elog:
                    st.caption(f"E = E_log = {elog:.3f}")
                V = st.slider("V · Vulnerability", 0.0, 1.0, float(p["V"]), 0.005)
                rho_now = st.slider("ρ now · Baseline Resilience", 0.0, 0.99, float(p["rho_now"]), 0.005)
                has_after = st.toggle("Model Resilience Investment (ρ after)", True)
                rho_after = st.slider("ρ after · Target Resilience", 0.0, 0.99, float(p.get("rho_after", 0.50)), 0.005) if has_after else None
                C = st.select_slider("C · Consequence (1–5)", (1, 2, 3, 4, 5), int(p["C"]), format_func=lambda c: f"{c} {content.C_NAMES[c]}")

        with right:
            res = core.assess(N, L, E, V, rho_now, rho_after, C)
            r_disp = res["R_after"] if rho_after is not None else res["R_now"]
            rho_disp = rho_after if rho_after is not None else rho_now

            v1, v2 = st.columns(2, gap="small")
            with v1:
                if is_custom:
                    # Domain-neutral animated 3D-style RMTI ring core for Custom / Your Field
                    components.html(f"""
                    <style>
                      @keyframes spin1 {{ from{{transform:rotate(0deg)}} to{{transform:rotate(360deg)}} }}
                      @keyframes spin2 {{ from{{transform:rotate(360deg)}} to{{transform:rotate(0deg)}} }}
                      *{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}
                      .box{{position:relative;height:195px;background:radial-gradient(circle at center,#1E293B 0%,#0F172A 100%);border:1px solid #334155;border-radius:14px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
                      .pill{{position:absolute;top:8px;left:8px;background:rgba(2,132,199,0.28);border:1px solid #38BDF8;color:#38BDF8;font-size:9.5px;font-weight:800;padding:3px 8px;border-radius:999px}}
                      .r1{{position:absolute;width:138px;height:138px;border:2.5px dashed #38BDF8;border-radius:50%;animation:spin1 18s linear infinite}}
                      .r2{{position:absolute;width:108px;height:108px;border:2.5px dashed #F87171;border-radius:50%;animation:spin2 14s linear infinite}}
                      .r3{{position:absolute;width:80px;height:80px;border:2.5px solid rgba(52,211,153,0.75);border-radius:50%}}
                      .core{{text-align:center;color:#FFF;z-index:2}}
                    </style>
                    <div class="box">
                      <span class="pill">Universal RMTI Engine · {field_name[:18]}</span>
                      <div class="r1"></div><div class="r2"></div><div class="r3"></div>
                      <div class="core"><div style="font-size:9.5px;color:#94A3B8;font-weight:700">RESIDUAL R</div><div style="font-size:20px;font-weight:900">{r_disp:.3f}</div></div>
                    </div>
                    """, height=200)
                else:
                    # Urban & Disaster 3D animation for city/wildfire worked examples
                    components.html(f"""
                    <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;background:#FFF;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden}}.p{{position:absolute;top:8px;left:8px;z-index:3;display:flex;gap:4px}}.b{{background:rgba(15,23,42,0.85);color:#FFF;font-size:9.5px;font-weight:700;padding:3px 8px;border-radius:999px}}video{{width:100%;height:195px;object-fit:cover;display:block}}</style>
                    <div class="f"><div class="p"><span class="b">Main 3D</span><span class="b">{field_name[:18]}</span></div>
                    <video autoplay loop muted playsinline><source src="{RAW_VIDEOS}/case_african_cities.mp4" type="video/mp4"></video></div>
                    """, height=200)

            with v2:
                components.html(f"""
                <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;height:195px;background:linear-gradient(180deg,#0F172A 0%,#1E293B 100%);border:1px solid #334155;border-radius:14px;padding:10px;color:#FFF;display:flex;flex-direction:column;justify-content:space-between}}.g{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;align-items:end;height:118px}}.c{{display:flex;flex-direction:column;align-items:center;gap:3px}}.bar{{width:100%;border-radius:4px 4px 1px 1px}}</style>
                <div class="f">
                  <div style="font-size:10px;font-weight:800;color:#38BDF8">2D RMTI DECOMPOSITION · R = L · E · V · (1 − ρ)</div>
                  <div class="g">
                    <div class="c"><span style="font-size:10px;font-weight:800">{L:.2f}</span><div class="bar" style="height:{int(L*85)}px;background:#38BDF8"></div><span style="font-size:9.5px;color:#CBD5E1">L</span></div>
                    <div class="c"><span style="font-size:10px;font-weight:800">{E:.2f}</span><div class="bar" style="height:{int(E*85)}px;background:#F87171"></div><span style="font-size:9.5px;color:#CBD5E1">E</span></div>
                    <div class="c"><span style="font-size:10px;font-weight:800">{V:.2f}</span><div class="bar" style="height:{int(V*85)}px;background:#FBBF24"></div><span style="font-size:9.5px;color:#CBD5E1">V</span></div>
                    <div class="c"><span style="font-size:10px;font-weight:800">{1-rho_disp:.2f}</span><div class="bar" style="height:{int((1-rho_disp)*85)}px;background:#34D399"></div><span style="font-size:9.5px;color:#CBD5E1">1−ρ</span></div>
                    <div class="c"><span style="font-size:10px;font-weight:800">{r_disp:.3f}</span><div class="bar" style="height:{max(10,int(r_disp*125))}px;background:#FFF"></div><span style="font-size:9.5px;color:#CBD5E1">R</span></div>
                  </div>
                </div>
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
