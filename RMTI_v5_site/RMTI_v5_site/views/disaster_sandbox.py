"""Disaster Science Sandbox: Pacific Palisades (CA) Wildfire & Custom Infrastructure Triage."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from engine import core, short
from rmti_ui import disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

PALISADES_ZONES = [
    {"Name": "Pacific Palisades — WUI Core (2025)", "N": 23700, "L": 0.350, "E_sel": 0.800, "V": 0.650, "rho_now": 0.200, "rho_after": 0.350, "C": 4},
    {"Name": "Palisades Highlands — Canyon Ridges", "N": 6400, "L": 0.420, "E_sel": 0.850, "V": 0.720, "rho_now": 0.180, "rho_after": 0.400, "C": 4},
    {"Name": "PCH & Sunset Evacuation Corridor", "N": 18500, "L": 0.380, "E_sel": 0.820, "V": 0.600, "rho_now": 0.220, "rho_after": 0.450, "C": 5},
    {"Name": "Temescal & Potrero Utility Substation", "N": 12000, "L": 0.360, "E_sel": 0.760, "V": 0.640, "rho_now": 0.210, "rho_after": 0.480, "C": 4},
    {"Name": "Altadena — Eaton Fire WUI (2025)", "N": 42000, "L": 0.400, "E_sel": 0.800, "V": 0.600, "rho_now": 0.200, "rho_after": 0.350, "C": 4},
    {"Name": "Custom Zone / Your Asset", "N": 15000, "L": 0.350, "E_sel": 0.750, "V": 0.550, "rho_now": 0.250, "rho_after": 0.500, "C": 4},
]


def _dual_layer_disaster_card(df, raw_rows, r_mean_now, r_mean_after, eal_mean_now, rho_val):
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
        lbl = t.split(" ", 1)[1]
        bars_html.append(f"""
        <div class="tgroup">
          <div class="pair">
            <div class="bwrap"><span class="cnt">{c0}</span><span class="dot white" style="bottom:{h0 + 14}px"></span><div class="bar base" style="height:{h0}px"></div></div>
            <div class="bwrap"><span class="cnt cyan">{c1}</span><span class="dot cyan" style="bottom:{h1 + 16}px"></span><div class="bar after" style="height:{h1}px"></div></div>
          </div>
          <div class="xlbl">{lbl}</div>
        </div>
        """)

    clip_primary = f"{RAW_VIDEOS}/disaster_dual3d.mp4"
    clip_fallback = f"{RAW_VIDEOS}/case_african_cities.mp4"

    components.html(f"""
    <style>
      *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
      .card{{position:relative;height:365px;border-radius:16px;overflow:hidden;border:1px solid #CBD5E1;background:linear-gradient(125deg,#0F172A 0%,#1E3A5F 48%,#0C4A6E 100%);box-shadow:0 10px 28px rgba(15,23,42,0.10)}}
      video{{position:absolute;left:0;top:0;width:48%;height:100%;object-fit:cover;object-position:left center;opacity:0.88;mask-image:linear-gradient(90deg,#000 68%,transparent 100%);-webkit-mask-image:linear-gradient(90deg,#000 68%,transparent 100%)}}
      .pills{{position:absolute;top:14px;left:14px;z-index:4;display:flex;gap:6px;flex-wrap:wrap}}
      .pill{{background:rgba(15,23,42,0.85);backdrop-filter:blur(6px);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:4px;border:1px solid rgba(56,189,248,0.35)}}
      .overlay{{position:absolute;top:14px;right:18px;bottom:14px;width:58%;z-index:3;display:flex;flex-direction:column;justify-content:space-between;color:#FFF}}
      .math-box{{background:rgba(15,23,42,0.68);backdrop-filter:blur(8px);border:1px solid rgba(56,189,248,0.28);border-radius:10px;padding:8px 12px}}
      .eq-row{{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;font-weight:800}}
      .levers{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.16);font-size:10.5px;text-align:center}}
      .lv b{{display:block;font-size:12px;color:#38BDF8}}
      .plot{{position:relative;flex:1;margin:14px 4px 20px 28px;border-left:1.5px solid rgba(255,255,255,0.72);border-bottom:1.5px solid rgba(255,255,255,0.72);display:grid;grid-template-columns:repeat(5,1fr);align-items:end;padding:0 6px}}
      .yaxis{{position:absolute;left:-28px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:space-between;font-size:10px;font-weight:700;color:rgba(255,255,255,0.9)}}
      .tgroup{{display:flex;flex-direction:column;align-items:center}}
      .pair{{display:flex;align-items:flex-end;gap:5px;height:140px}}
      .bwrap{{position:relative;width:18px;height:100%;display:flex;align-items:flex-end;justify-content:center}}
      .bar{{width:100%;border-radius:2px 2px 0 0;transition:height 0.45s cubic-bezier(0.22,1,0.36,1)}}
      .bar.base{{background:rgba(239,68,68,0.78);border:1px solid rgba(255,255,255,0.3)}}
      .bar.after{{background:rgba(16,185,129,0.88);border:1px solid rgba(255,255,255,0.55)}}
      .cnt{{position:absolute;top:0;font-size:9.5px;font-weight:800;color:#F8FAFC}}
      .cnt.cyan{{color:#6EE7B7}}
      .dot{{position:absolute;left:34%;width:5px;height:5px;transition:bottom 0.45s ease}}
      .dot.white{{background:#FFFFFF;border-radius:50%}}
      .dot.cyan{{background:#10B981;border-radius:1px}}
      .xlbl{{position:absolute;bottom:-19px;font-size:10px;font-weight:700;color:#FFF;white-space:nowrap}}
      .ftr{{display:flex;justify-content:space-between;align-items:center;font-size:11px;font-weight:700;color:#FFF;background:rgba(15,23,42,0.62);padding:5px 10px;border-radius:8px}}
    </style>
    <div class="card">
      <video autoplay loop muted playsinline><source src="{clip_primary}" type="video/mp4"><source src="{clip_fallback}" type="video/mp4"></video>
      <div class="pills">
        <span class="pill">Disaster Science</span>
        <span class="pill">Pacific Palisades, CA</span>
        <span class="pill">Dual-Layer 3D + 2D</span>
      </div>
      <div class="overlay">
        <div class="math-box">
          <div class="eq-row">
            <span>R = L · E · V · (1 − ρ)</span>
            <span style="color:#6EE7B7">EAL = L · C · (1 − ρ) = {eal_mean_now:.3f}</span>
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
          <span>{len(df):,} infrastructure zones · Target ρ = {rho_val:.2f}</span>
          <span>Mean R: {r_mean_now:.3f} → <b style="color:#6EE7B7">{r_mean_after:.3f}</b></span>
        </div>
      </div>
    </div>
    """, height=372)


def render():
    page_header(
        "Disaster Science Sandbox — Pacific Palisades, CA & Custom Infrastructure",
        "Stress-test urban wildfire and infrastructure resilience using the January 2025 Pacific Palisades & Altadena case study (Marolla, 2025/2026), or edit/upload your own zones.",
        "Research tools",
    )

    with st.expander("How to Use the Disaster Science Sandbox (3-Step Guide)", expanded=True):
        g1, g2, g3 = st.columns(3)
        g1.markdown("**1. Customize or Upload Zones**\nEdit any parameter (`L`, `E_sel`, `V`, `ρ_now`, `C`) directly in the table below, click **`+`** to add your own asset, or upload a CSV.")
        g2.markdown("**2. Simulate Resilience (ρ)**\nUse the **Resilience Intervention (`ρ after`)** toggle and slider to model grid hardening, defensible space, and evacuation alerting.")
        g3.markdown("**3. Compare Tiers & Export**\nWatch the **Main 3D + 2D** bars shift across Tiers 1–5 in real time and download your ranked CSV.")

    left, right = st.columns((1.05, 1.85), gap="large")
    with left:
        with st.container(border=True):
            src = st.radio("Data source", ["Pacific Palisades & Custom Table", "Upload CSV"], horizontal=True)
            if src == "Pacific Palisades & Custom Table":
                st.caption("Click any cell to customize values or click `+` at the bottom to add rows:")
                ed = st.data_editor(pd.DataFrame(PALISADES_ZONES), num_rows="dynamic", width="stretch", key="dis_ed")
                raw_rows = {
                    str(r["Name"]): dict(N=float(r["N"]), L=float(r["L"]), E_sel=float(r["E_sel"]), V=float(r["V"]), rho_now=float(r["rho_now"]), rho_after=float(r["rho_after"]) if pd.notna(r.get("rho_after")) else 0.40, C=int(r["C"]))
                    for _, r in ed.dropna(subset=["Name", "L", "E_sel", "V", "rho_now", "C"]).iterrows()
                }
            else:
                up = st.file_uploader("Upload CSV (columns: Name, N, L, E_sel, V, rho_now, C)", type=["csv"], key="dis_up")
                if up is not None:
                    udf = pd.read_csv(up).dropna(subset=["Name", "L", "E_sel", "V", "rho_now"])
                    raw_rows = {str(r["Name"]): dict(N=float(r.get("N", 1000)), L=float(r["L"]), E_sel=float(r["E_sel"]), V=float(r["V"]), rho_now=float(r["rho_now"]), C=int(r.get("C", 4))) for _, r in udf.iterrows()}
                else:
                    st.info("Showing Pacific Palisades baseline until a CSV is uploaded.")
                    raw_rows = {r["Name"]: dict(N=r["N"], L=r["L"], E_sel=r["E_sel"], V=r["V"], rho_now=r["rho_now"], rho_after=r["rho_after"], C=r["C"]) for r in PALISADES_ZONES}

            st.subheader("Scenario")
            override = st.toggle("Override ρ after for every zone", True, key="dis_ov")
            rho_scen = st.slider("ρ after (resilience upgrade)", 0.05, 0.95, 0.45, 0.01, key="dis_rho") if override else None

    if override and rho_scen is not None:
        for v in raw_rows.values():
            v["rho_after"] = float(rho_scen)

    ranked = core.rank_cohort(raw_rows)
    df = pd.DataFrame([{
        "Zone / Asset": r["name"],
        "Priority": r["priority_in_tier"],
        "R now": r["R_now"],
        "Tier now": short(r["tier_now"]),
        "R after": r.get("R_after"),
        "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
        "Reduction %": r.get("risk_reduction_pct"),
        "EAL now": r["EAL_now"],
        "Equity /1M": r["equity_now_per_1M"],
    } for r in ranked])

    mean_now = float(df["R now"].mean())
    mean_after = float(df["R after"].mean()) if df["R after"].notna().any() else mean_now
    mean_eal = float(df["EAL now"].mean())
    pct_chg = ((mean_after / mean_now) - 1.0) * 100 if mean_now > 0 else 0.0

    with right:
        _dual_layer_disaster_card(df, raw_rows, mean_now, mean_after, mean_eal, rho_scen or 0.45)
        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.metric("Zones scored", f"{len(df):,}")
        m2.metric("Mean R now", f"{mean_now:.3f}")
        m3.metric("Mean R after", f"{mean_after:.3f}", f"{pct_chg:+.1f}%", delta_color="inverse")

        st.subheader("Disaster Risk Tier Distribution")
        tiers = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
        fig = go.Figure()
        fig.add_bar(x=tiers, y=[int((df["Tier now"] == t).sum()) for t in tiers], name="now", marker_color="#DC2626")
        fig.add_bar(x=tiers, y=[int((df["Tier after"] == t).sum()) for t in tiers], name="after resilience", marker_color="#10B981")
        fig.update_layout(barmode="group", yaxis_title="Zones or assets")
        st.plotly_chart(style_fig(fig, 300), width="stretch")

        st.dataframe(df, hide_index=True, width="stretch", height=290)
        st.download_button("Download Disaster Science reassessment (CSV)", df.to_csv(index=False).encode(), "rmti_disaster_sandbox.csv", "text/csv")

    disclaimer()

