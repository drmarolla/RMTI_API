"""Six Sub-Saharan African City Case Studies (Main 3D + 2D Dual-Layer) & 3D RMTI Coordinate Axis Synthesis."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, short
from rmti_ui import badge, disclaimer, page_header

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

CITY_SPECS = {
    "Lagos": ("city_lagos.mp4", "Coastal Megacity · Mass Transit & Lagoon Surge",
              "Coastal storm surge and pluvial flooding threaten high-density BRT and bridge corridors; elevating transit nodes and tidal barriers cuts systemic risk."),
    "Lilongwe": ("city_lilongwe.mp4", "Capital Basin · Drainage & Utility Networks",
                 "Rapid urban expansion strains stormwater culverts and water utilities; green-grey retention basins and culvert upgrades lower vulnerability."),
    "Bamako": ("city_bamako.mp4", "Riverine Corridor · Urban Healthcare Continuity",
               "Compounding Niger River flooding and extreme heatwaves stress clinics and power grids; solar microgrids and flood-proof access roads protect care."),
    "Nairobi": ("city_nairobi.mp4", "Highland Hub · Stormwater & Transit Arteries",
                "Flash runoff across river valleys disrupts commuter arteries; riparian bioswales and reinforced bridge spans stabilize mobility."),
    "Dar es Salaam": ("city_dar.mp4", "Port Corridor · Coastal & BRT Infrastructure",
                      "Sea-level surge and intense monsoon rainfall threaten coastal transit lanes; seawalls and mangrove-hybrid buffers preserve port-city flow."),
    "Lusaka": ("city_lusaka.mp4", "Plateau City · Aquifer & Drainage Protection",
               "Seasonal inundation threatens shallow karst aquifers and neighborhood utilities; lined channels and retention ponds prevent cascading failure."),
}


def city_page(city_name):
    p = content.SIX_CITIES[city_name]
    clip_file, sector_tag, narrative = CITY_SPECS[city_name]
    clip_url = f"{RAW_VIDEOS}/{clip_file}"
    fb_url = f"{RAW_VIDEOS}/case_african_cities.mp4"

    page_header(
        f"{city_name}: Urban Infrastructure Resilience Case Study",
        f"World Bank Compendium (Marolla et al., 2023, DOI: 10.1596/40309) · Sector Asset: {p['asset']}",
        "Disaster science case studies",
    )

    col_left, col_right = st.columns((1.0, 1.0), gap="large")

    # Card 1: Main 3D Infrastructure Animation
    with col_left:
        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
          .frame{{position:relative;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden;box-shadow:0 10px 28px rgba(15,23,42,0.07)}}
          .pills{{position:absolute;top:12px;left:12px;z-index:3;display:flex;gap:6px;flex-wrap:wrap}}
          .pill{{background:rgba(15,23,42,0.82);backdrop-filter:blur(6px);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:999px}}
          video{{width:100%;height:340px;object-fit:cover;background:#F8FAFC;display:block}}
        </style>
        <div class="frame">
          <div class="pills">
            <span class="pill">Detailed and Dynamic</span>
            <span class="pill">World Bank Compendium 2023</span>
          </div>
          <video autoplay loop muted playsinline controls>
            <source src="{clip_url}" type="video/mp4">
            <source src="{fb_url}" type="video/mp4">
          </video>
        </div>
        """, height=348)
        st.markdown(f"### Main 3D Infrastructure Model — {city_name}")
        st.caption(sector_tag)
        st.write(narrative)

    # Card 2: Main 3D + 2D Dual-Layer Integration
    with col_right:
        default_after = float(p.get("rho_after", min(0.85, p["rho_now"] + 0.25)))
        rho_sim = st.session_state.get(f"rho_{city_name}", round(default_after, 2))
        r_now = core.score(p["L"], p["E_sel"], p["V"], p["rho_now"], p["C"])["R_raw"]
        r_sim = core.score(p["L"], p["E_sel"], p["V"], rho_sim, p["C"])["R_raw"]
        eal_sim = p["L"] * p["C"] * (1.0 - rho_sim)

        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
          .frame{{position:relative;background:#0F172A;border:1px solid #CBD5E1;border-radius:16px;overflow:hidden;box-shadow:0 10px 28px rgba(15,23,42,0.10)}}
          .pills{{position:absolute;top:12px;left:12px;z-index:4;display:flex;gap:6px;flex-wrap:wrap}}
          .pill{{background:rgba(15,23,42,0.82);backdrop-filter:blur(6px);color:#FFF;font-size:10px;font-weight:700;padding:4px 9px;border-radius:999px;border:1px solid rgba(255,255,255,0.18)}}
          video{{width:100%;height:340px;object-fit:cover;opacity:0.42;display:block}}
          .hud{{position:absolute;inset:44px 14px 14px 14px;z-index:3;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(180deg,rgba(15,23,42,0.15) 0%,rgba(15,23,42,0.88) 100%);border-radius:12px;padding:14px;color:#FFF}}
          .hud-title{{font-size:11px;font-weight:800;letter-spacing:0.6px;text-transform:uppercase;color:#38BDF8;margin-bottom:8px}}
          .bars{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:end;height:130px;padding-top:10px}}
          .col{{display:flex;flex-direction:column;align-items:center;gap:4px}}
          .val{{font-size:11px;font-weight:800;color:#FFF}}
          .bar{{width:100%;border-radius:6px 6px 2px 2px;transition:height 0.3s ease}}
          .lbl{{font-size:10px;font-weight:700;color:#CBD5E1;text-align:center}}
        </style>
        <div class="frame">
          <div class="pills">
            <span class="pill">Detailed and Dynamic</span>
            <span class="pill">Dual-Layer Storytelling</span>
            <span class="pill">For Data-rich Stories</span>
          </div>
          <video autoplay loop muted playsinline>
            <source src="{clip_url}" type="video/mp4">
            <source src="{fb_url}" type="video/mp4">
          </video>
          <div class="hud">
            <div class="hud-title">2D RMTI Mechanism Overlay · R = L · E · V · (1 − ρ)</div>
            <div class="bars">
              <div class="col"><span class="val">{p['L']:.2f}</span><div class="bar" style="height:{int(p['L']*105)}px;background:#38BDF8;"></div><span class="lbl">Hazard (L)</span></div>
              <div class="col"><span class="val">{p['E_sel']:.2f}</span><div class="bar" style="height:{int(p['E_sel']*105)}px;background:#F87171;"></div><span class="lbl">Exposure (E)</span></div>
              <div class="col"><span class="val">{p['V']:.2f}</span><div class="bar" style="height:{int(p['V']*105)}px;background:#FBBF24;"></div><span class="lbl">Vuln. (V)</span></div>
              <div class="col"><span class="val">{1-rho_sim:.2f}</span><div class="bar" style="height:{int((1-rho_sim)*105)}px;background:#34D399;"></div><span class="lbl">1 − ρ</span></div>
              <div class="col"><span class="val">{r_sim:.3f}</span><div class="bar" style="height:{max(14,int(r_sim*160))}px;background:#FFFFFF;"></div><span class="lbl">Residual R</span></div>
            </div>
          </div>
        </div>
        """, height=348)
        st.markdown(f"### Main 3D + 2D Assessment — {city_name}")
        st.caption("Combines the 3D physical corridor model with real-time 2D RMTI parameter overlays inside a single frame.")
        st.slider(
            f"Interactive Resilience Intervention (ρ) — Baseline: {p['rho_now']:.2f}",
            0.05, 0.90, round(default_after, 2), 0.01, key=f"rho_{city_name}",
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline R", f"{r_now:.3f}", short(core.tier(r_now)), delta_color="off")
        m2.metric("Post-Upgrade R", f"{r_sim:.3f}", f"{(r_sim / r_now - 1) * 100:+.0f}%", delta_color="inverse")
        m3.metric("Simulated EAL", f"{eal_sim:.3f}")
        st.markdown(badge(core.tier(r_sim)), unsafe_allow_html=True)

    st.caption("Source: Marolla et al. (2023). Climate Resilient Investment in Sub-Saharan Africa Compendium Volume. World Bank. https://doi.org")
    disclaimer()


def synthesis_page():
    page_header(
        "Six-City Portfolio Synthesis & 3D RMTI Coordinate Axis",
        "Complete cross-city comparison table (Marolla et al., 2023; Marolla, 2026) and interactive 3D Cartesian coordinate space with directional risk vectors.",
        "Disaster science case studies",
    )

    ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))} for k, v in content.SIX_CITIES.items()})
    rows = []
    for r in ranked:
        rows.append({
            "Priority": r["priority_in_tier"],
            "City": r["name"],
            "Infrastructure Asset": content.SIX_CITIES[r["name"]]["asset"],
            "L": content.SIX_CITIES[r["name"]]["L"],
            "E": content.SIX_CITIES[r["name"]]["E_sel"],
            "V": content.SIX_CITIES[r["name"]]["V"],
            "ρ now": content.SIX_CITIES[r["name"]]["rho_now"],
            "R now": r["R_now"],
            "Tier now": short(r["tier_now"]),
            "ρ after": content.SIX_CITIES[r["name"]].get("rho_after"),
            "R after": r.get("R_after"),
            "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
            "Reduction %": r.get("risk_reduction_pct"),
            "EAL now": r["EAL_now"],
            "Equity /1M": r["equity_now_per_1M"],
        })
    df = pd.DataFrame(rows)

    st.subheader("1. Six-City RMTI Calculator & Portfolio Table")
    st.dataframe(df, hide_index=True, width="stretch")

    st.subheader("2. Interactive 3D RMTI Coordinate Axis (X: Hazard×Exposure · Y: Vulnerability · Z: Resilience ρ)")
