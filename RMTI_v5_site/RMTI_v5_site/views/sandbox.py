"""Cohort Sandbox: Synthetic/CSV triage + Main 3D + 2D RMTI Mathematical Overlay."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from engine import core, short
from rmti_ui import disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])


def _synthetic_cohort(n, seed):
    rng = np.random.default_rng(int(seed))
    rows = {}
    for i in range(int(n)):
        cid = f"SYN-{i + 1:03d}"
        L = float(np.clip(rng.beta(2.2, 4.5), 0.05, 0.95))
        E = float(np.clip(rng.beta(2.5, 3.0), 0.10, 0.95))
        V = float(np.clip(rng.beta(2.4, 3.2), 0.10, 0.95))
        rho0 = float(np.clip(rng.beta(2.0, 4.0), 0.05, 0.80))
        C = int(rng.choice((2, 3, 4, 5), p=(0.20, 0.35, 0.30, 0.15)))
        rows[cid] = dict(N=1, L=round(L, 3), E_sel=round(E, 3), V=round(V, 3), rho_now=round(rho0, 3), C=C)
    return rows


def _dual_layer_sandbox_card(df, raw_rows, r_mean_now, r_mean_after, eal_mean_now, rho_val):
    """Visual Science-style Main 3D + 2D Dual-Layer Frame with live RMTI equations & moving columns."""
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
        h0 = max(4, int((c0 / max_c) * 112))
        h1 = max(4, int((c1 / max_c) * 112))
        lbl = t.split(" ", 1)[1]
        bars_html.append(f"""
        <div class="tgroup">
          <div class="pair">
            <div class="bwrap" title="Baseline {t}: {c0}">
              <span class="cnt">{c0}</span>
              <span class="dot white" style="bottom:{h0 + 14}px"></span>
              <span class="dot white" style="bottom:{h0 + 7}px;left:58%"></span>
              <div class="bar base" style="height:{h0}px"></div>
            </div>
            <div class="bwrap" title="Scenario {t}: {c1}">
              <span class="cnt cyan">{c1}</span>
              <span class="dot cyan" style="bottom:{h1 + 16}px"></span>
              <span class="dot cyan" style="bottom:{h1 + 8}px;left:30%"></span>
              <div class="bar after" style="height:{h1}px"></div>
            </div>
          </div>
          <div class="xlbl">{lbl}</div>
        </div>
        """)

    clip_primary = f"{RAW_VIDEOS}/sandbox_dual3d.mp4"
    clip_fallback = f"{RAW_VIDEOS}/video1_4stages_3d.mp4"

    components.html(f"""
    <style>
      *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
      .card{{position:relative;height:365px;border-radius:16px;overflow:hidden;border:1px solid #D6B899;background:linear-gradient(125deg,#F3DFC8 0%,#C88A55 52%,#8F562E 100%);box-shadow:0 10px 28px rgba(15,23,42,0.09)}}
      video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.95}}
      .scrim{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(28,16,9,0.08) 0%,rgba(42,24,14,0.34) 38%,rgba(34,19,11,0.72) 100%)}}
      .pills{{position:absolute;top:14px;left:14px;z-index:4;display:flex;gap:6px;flex-wrap:wrap}}
      .pill{{background:rgba(36,21,13,0.72);backdrop-filter:blur(6px);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:4px;border:1px solid rgba(255,255,255,0.16)}}
      .overlay{{position:absolute;top:14px;right:18px;bottom:14px;width:62%;z-index:3;display:flex;flex-direction:column;justify-content:space-between;color:#FFF}}
      .math-box{{background:rgba(28,16,9,0.52);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.22);border-radius:10px;padding:8px 12px}}
      .eq-row{{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;font-weight:800;letter-spacing:0.01em}}
      .levers{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.16);font-size:10.5px;text-align:center}}
      .lv b{{display:block;font-size:12px;color:#FDE68A}}
      .plot{{position:relative;flex:1;margin:14px 4px 18px 28px;border-left:1.5px solid rgba(255,255,255,0.72);border-bottom:1.5px solid rgba(255,255,255,0.72);display:grid;grid-template-columns:repeat(5,1fr);align-items:end;padding:0 6px}}
      .yaxis{{position:absolute;left:-28px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:space-between;font-size:10px;font-weight:700;color:rgba(255,255,255,0.9)}}
      .tgroup{{display:flex;flex-direction:column;align-items:center}}
      .pair{{display:flex;align-items:flex-end;gap:5px;height:142px}}
      .bwrap{{position:relative;width:18px;height:100%;display:flex;align-items:flex-end;justify-content:center}}
      .bar{{width:100%;border-radius:2px 2px 0 0;transition:height 0.45s cubic-bezier(0.22,1,0.36,1)}}
      .bar.base{{background:rgba(68,48,36,0.72);border:1px solid rgba(255,255,255,0.3)}}
      .bar.after{{background:rgba(56,189,248,0.86);border:1px solid rgba(255,255,255,0.55)}}
      .cnt{{position:absolute;top:0;font-size:9.5px;font-weight:800;color:#F8FAFC}}
      .cnt.cyan{{color:#7DD3FC}}
      .dot{{position:absolute;left:34%;width:5px;height:5px;transition:bottom 0.45s ease}}
      .dot.white{{background:#FFFFFF;border-radius:50%}}
      .dot.cyan{{background:#38BDF8;border-radius:1px}}
      .xlbl{{position:absolute;bottom:-19px;font-size:10px;font-weight:700;color:#FFF;white-space:nowrap}}
      .ftr{{display:flex;justify-content:space-between;align-items:center;font-size:11px;font-weight:700;color:rgba(255,255,255,0.95);background:rgba(28,16,9,0.45);padding:5px 10px;border-radius:8px}}
    </style>
    <div class="card">
      <video autoplay loop muted playsinline>
        <source src="{clip_primary}" type="video/mp4">
        <source src="{clip_fallback}" type="video/mp4">
      </video>
      <div class="scrim"></div>
      <div class="pills">
        <span class="pill">Detailed and Dynamic</span>
        <span class="pill">Dual-Layer Storytelling</span>
        <span class="pill">For Data-rich Stories</span>
      </div>
      <div class="overlay">
        <div class="math-box">
          <div class="eq-row">
            <span>R = L · E · V · (1 − ρ)</span>
            <span style="color:#7DD3FC">EAL = L · C · (1 − ρ) = {eal_mean_now:.3f}</span>
          </div>
          <div class="levers">
            <div class="lv">Mean L<b>{mean_L:.2f}</b></div>
            <div class="lv">Mean E<b>{mean_E:.2f}</b></div>
            <div class="lv">Mean V<b>{mean_V:.2f}</b></div>
            <div class="lv">Mean (1−ρ)<b>{mean_res:.2f}</b></div>
          </div>
        </div>
        <div class="plot">
          <div class="yaxis"><span>{max_c}</span><span>{max_c//2}</span><span>0</span></div>
          {''.join(bars_html)}
        </div>
        <div class="ftr">
          <span>n = {len(df):,} cohort units · ρ target = {rho_val:.2f}</span>
          <span>Mean R: {r_mean_now:.3f} → <b style="color:#7DD3FC">{r_mean_after:.3f}</b></span>
        </div>
      </div>
    </div>
    """, height=372)


def render():
    page_header(
        "Cohort Sandbox",
        "Score and rank a synthetic cohort, or upload your own aggregate table, then test a surveillance-improvement scenario.",
        "Research tools",
    )
    st.warning("Do not upload patient-identifiable data. Files are processed in memory for your session and are never stored. Use synthetic or aggregate values.")

    left, right = st.columns((1.0, 1.85), gap="large")
    with left:
        with st.container(border=True):
            src = st.radio("Data source", ["Synthetic cohort", "Upload CSV"], horizontal=True)
            if src == "Synthetic cohort":
                n_pts = st.slider("Synthetic patients", 50, 2000, 850, 50)
                seed = st.number_input("Random seed", 1, 99999, 2026, 1)
                raw_rows = _synthetic_cohort(n_pts, seed)
            else:
                up = st.file_uploader("Upload CSV (columns: Name, N, L, E_sel, V, rho_now, C)", type=["csv"])
                if up is not None:
                    udf = pd.read_csv(up).dropna(subset=["Name", "L", "E_sel", "V", "rho_now"])
                    raw_rows = {
                        str(r["Name"]): dict(
                            N=float(r.get("N", 1)),
                            L=float(r["L"]),
                            E_sel=float(r["E_sel"]),
                            V=float(r["V"]),
                            rho_now=float(r["rho_now"]),
                            C=int(r.get("C", 3)),
                        )
                        for _, r in udf.iterrows()
                    }
                else:
                    st.info("Showing 250-patient synthetic preview until a CSV is uploaded.")
                    raw_rows = _synthetic_cohort(250, 2026)

            st.subheader("Scenario")
            override = st.toggle("Override ρ after for every row", True)
            rho_scen = st.slider("ρ after (scenario)", 0.05, 0.95, 0.65, 0.01) if override else None

    if override and rho_scen is not None:
        for v in raw_rows.values():
            v["rho_after"] = float(rho_scen)

    ranked = core.rank_cohort(raw_rows)
    out = []
    for r in ranked:
        out.append({
            "Name": r["name"],
            "Priority in tier": r["priority_in_tier"],
            "R now": r["R_now"],
            "Tier now": short(r["tier_now"]),
            "R after": r.get("R_after"),
