"""Oncology Cohort Sandbox: Hepatocellular Carcinoma (HCC) & Custom Cohort Triage."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from engine import core, short
from rmti_ui import disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

HCC_COHORT_PRESETS = [
    {"Name": "Fibrosis F1–F3 Baseline (BCLC 0)", "N": 1, "L": 0.150, "E_sel": 0.600, "V": 0.350, "rho_now": 0.200, "C": 3},
    {"Name": "Untreated HBV Cirrhosis F4 (Fan aMAP)", "N": 1, "L": 0.900, "E_sel": 0.720, "V": 0.600, "rho_now": 0.200, "C": 4},
    {"Name": "Early HCC BCLC 0/A (US + AFP)", "N": 1, "L": 0.650, "E_sel": 0.680, "V": 0.480, "rho_now": 0.250, "C": 4},
    {"Name": "Portal Invasion BCLC B/C (Faria ALBI n=54)", "N": 1, "L": 0.820, "E_sel": 0.780, "V": 0.522, "rho_now": 0.180, "C": 5},
    {"Name": "Metastatic HCC BCLC D Subgroup", "N": 1, "L": 0.880, "E_sel": 0.850, "V": 0.740, "rho_now": 0.150, "C": 5},
    {"Name": "Custom Oncology Cohort / Your Data", "N": 1, "L": 0.550, "E_sel": 0.600, "V": 0.500, "rho_now": 0.250, "C": 4},
]


def _synthetic_cohort(n, seed):
    rng = np.random.default_rng(int(seed))
    rows = {}
    for i in range(int(n)):
        cid = f"HCC-{i + 1:03d}"
        L = float(np.clip(rng.beta(2.2, 4.5), 0.05, 0.95))
        E = float(np.clip(rng.beta(2.5, 3.0), 0.10, 0.95))
        V = float(np.clip(rng.beta(2.4, 3.2), 0.10, 0.95))
        rho0 = float(np.clip(rng.beta(2.0, 4.0), 0.05, 0.80))
        C = int(rng.choice((2, 3, 4, 5), p=(0.20, 0.35, 0.30, 0.15)))
        rows[cid] = dict(N=1, L=round(L, 3), E_sel=round(E, 3), V=round(V, 3), rho_now=round(rho0, 3), C=C)
    return rows


def _dual_layer_sandbox_card(df, raw_rows, r_mean_now, r_mean_after, eal_mean_now, rho_val):
    tiers = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
    now_counts = [int((df["Tier now"] == t).sum()) for t in tiers]
    aft_counts = [int((df["Tier after"] == t).sum()) for t in tiers] if "Tier after" in df else now_counts
    max_c = max(1, max(now_counts + aft_counts))

    vals = list(raw_rows.values())
    mean_L = float(np.mean([v["L"] for v in vals]))
    mean_E = float(np.mean([v["E_sel"] for v in vals]))
    mean_V = float(np.mean([v["V"] for v in vals]))
    mean_res = float(np.mean([1.0 - v.get("rho_after", v["rho_now"]) for v in vals]))

    bars_html = []
    for t, c0, c1 in zip(tiers, now_counts, aft_counts):
        h0 = max(4, int((c0 / max_c) * 110))
        h1 = max(4, int((c1 / max_c) * 110))
        lbl = t.partition(" ")[2]
        bars_html.append(f"""
        <div class="sb-tgroup">
          <div class="sb-pair">
            <div class="sb-bwrap"><span class="sb-cnt">{c0}</span><span class="sb-dot white" style="bottom:{h0 + 14}px"></span><div class="sb-bar base" style="height:{h0}px"></div></div>
            <div class="sb-bwrap"><span class="sb-cnt cyan">{c1}</span><span class="sb-dot cyan" style="bottom:{h1 + 16}px"></span><div class="sb-bar after" style="height:{h1}px"></div></div>
          </div>
          <div class="sb-xlbl">{lbl}</div>
        </div>
        """)

    clip_primary = f"{RAW_VIDEOS}/sandbox_dual3d.mp4"
    clip_fallback = f"{RAW_VIDEOS}/video1_4stages_3d.mp4"

    components.html(f"""
    <style>
      *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
      .sb-card{{position:relative;height:365px;border-radius:16px;overflow:hidden;border:1px solid #D6B899;background:linear-gradient(125deg,#F3DFC8 0%,#C88A55 52%,#8F562E 100%);box-shadow:0 10px 28px rgba(15,23,42,0.09)}}
      .sb-card video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.95}}
      .sb-scrim{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(28,16,9,0.08) 0%,rgba(42,24,14,0.34) 38%,rgba(34,19,11,0.72) 100%)}}
      .sb-pills{{position:absolute;top:14px;left:14px;z-index:4;display:flex;gap:6px;flex-wrap:wrap}}
      .sb-pill{{background:rgba(36,21,13,0.72);backdrop-filter:blur(6px);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:4px;border:1px solid rgba(255,255,255,0.16)}}
      .sb-overlay{{position:absolute;top:14px;right:18px;bottom:14px;width:62%;z-index:3;display:flex;flex-direction:column;justify-content:space-between;color:#FFF}}
      .sb-math{{background:rgba(28,16,9,0.52);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.22);border-radius:10px;padding:8px 12px}}
      .sb-eq{{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;font-weight:800}}
      .sb-levers{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.16);font-size:10.5px;text-align:center}}
      .sb-lv b{{display:block;font-size:12px;color:#FDE68A}}
      .sb-plot{{position:relative;flex:1;margin:14px 4px 18px 28px;border-left:1.5px solid rgba(255,255,255,0.72);border-bottom:1.5px solid rgba(255,255,255,0.72);display:grid;grid-template-columns:repeat(5,1fr);align-items:end;padding:0 6px}}
      .sb-yaxis{{position:absolute;left:-28px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:space-between;font-size:10px;font-weight:700;color:rgba(255,255,255,0.9)}}
      .sb-tgroup{{display:flex;flex-direction:column;align-items:center}}
      .sb-pair{{display:flex;align-items:flex-end;gap:5px;height:142px}}
      .sb-bwrap{{position:relative;width:18px;height:100%;display:flex;align-items:flex-end;justify-content:center}}
      .sb-bar{{width:100%;border-radius:2px 2px 0 0;transition:height 0.45s cubic-bezier(0.22,1,0.36,1)}}
      .sb-bar.base{{background:rgba(68,48,36,0.72);border:1px solid rgba(255,255,255,0.3)}}
      .sb-bar.after{{background:rgba(56,189,248,0.86);border:1px solid rgba(255,255,255,0.55)}}
      .sb-cnt{{position:absolute;top:0;font-size:9.5px;font-weight:800;color:#F8FAFC}}
      .sb-cnt.cyan{{color:#7DD3FC}}
      .sb-dot{{position:absolute;left:34%;width:5px;height:5px;transition:bottom 0.45s ease}}
      .sb-dot.white{{background:#FFFFFF;border-radius:50%}}
      .sb-dot.cyan{{background:#38BDF8;border-radius:1px}}
      .sb-xlbl{{position:absolute;bottom:-19px;font-size:10px;font-weight:700;color:#FFF;white-space:nowrap}}
      .sb-ftr{{display:flex;justify-content:space-between;align-items:center;font-size:11px;font-weight:700;color:#FFF;background:rgba(28,16,9,0.45);padding:5px 10px;border-radius:8px}}
    </style>
    <div class="sb-card">
      <video autoplay loop muted playsinline><source src="{clip_primary}" type="video/mp4"><source src="{clip_fallback}" type="video/mp4"></video>
      <div class="sb-scrim"></div>
      <div class="sb-pills">
        <span class="sb-pill">Clinical Oncology</span>
        <span class="sb-pill">HCC · BCLC &amp; ALBI</span>
        <span class="sb-pill">Dual-Layer 3D + 2D</span>
      </div>
      <div class="sb-overlay">
        <div class="sb-math">
          <div class="sb-eq">
            <span>R = L · E · V · (1 − ρ)</span>
            <span style="color:#7DD3FC">EAL = L · C · (1 − ρ) = {eal_mean_now:.3f}</span>
          </div>
          <div class="sb-levers">
            <div class="sb-lv">Mean L<b>{mean_L:.2f}</b></div>
            <div class="sb-lv">Mean E<b>{mean_E:.2f}</b></div>
            <div class="sb-lv">Mean V<b>{mean_V:.2f}</b></div>
            <div class="sb-lv">Mean (1−ρ)<b>{mean_res:.2f}</b></div>
          </div>
        </div>
        <div class="sb-plot">
          <div class="sb-yaxis"><span>{max_c}</span><span>{max_c//2}</span><span>0</span></div>
          {''.join(bars_html)}
        </div>
        <div class="sb-ftr">
          <span>n = {len(df):,} oncology cohort units · Target ρ = {rho_val:.2f}</span>
          <span>Mean R: {r_mean_now:.3f} → <b style="color:#7DD3FC">{r_mean_after:.3f}</b></span>
        </div>
      </div>
    </div>
    """, height=372)


def render():
    page_header(
        "Oncology Cohort Sandbox — Hepatocellular Carcinoma (HCC) & Custom Cohort Triage",
        "Case Study: Hepatocellular Carcinoma (HCC) BCLC & ALBI Surveillance Cohort (Marolla, 2026, SSRN: 7427450; Faria et al. ALBI Cohort, n = 54; Singal et al., 2022; Lau-Min et al., JAMA Netw Open, 2025).",
        "Research tools",
    )

    with st.expander("How to Use the Oncology Cohort Sandbox (3-Step Guide)", expanded=False):
        g1, g2, g3 = st.columns(3)
        g1.markdown("**1. Select or Customize Cohort**\nRun a synthetic HCC cohort, switch to **Custom Editable Table** to edit BCLC/ALBI rows or add your own with **`+`**, or upload an aggregate CSV.")
        g2.markdown("**2. Simulate Surveillance (ρ)**\nAdjust **ρ after (surveillance scenario)** to model ultrasound + AFP adherence, LDCT screening, or second-line systemic delivery.")
        g3.markdown("**3. Inspect Tier Shifts & Export**\nWatch the **Main 3D + 2D** columns redistribute across Tiers 1–5 in real time and download your ranked CSV.")

    st.warning("Do not upload patient-identifiable data. Files are processed in memory for your session and are never stored. Use synthetic or aggregate values.")

    left, right = st.columns((1.05, 1.85), gap="large")
    with left:
        with st.container(border=True):
            src = st.radio("Data source", ["Synthetic HCC cohort", "Custom Editable Table", "Upload CSV"], horizontal=True)
            if src == "Synthetic HCC cohort":
                n_pts = st.slider("Synthetic patients", 50, 2000, 850, 50)
                seed = st.number_input("Random seed", 1, 99999, 2026, 1)
                raw_rows = _synthetic_cohort(n_pts, seed)
            elif src == "Custom Editable Table":
                st.caption("Click any cell to customize values or click `+` at the bottom to add custom cohorts:")
