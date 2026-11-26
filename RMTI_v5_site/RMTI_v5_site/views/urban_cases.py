"""Six Sub-Saharan African City Case Studies (Main 3D + 2D + Trajectory) & Geometric 3D RMTI Synthesis."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, short
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig

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


def _city_trajectory(p, rho_target):
    """Compute 4-cycle RMTI Core trajectory R(t) from baseline rho_now to rho_target."""
    pts = []
    for step in range(4):
        frac = step / 3.0
        rho_t = p["rho_now"] + frac * (rho_target - p["rho_now"])
        v_t = max(0.10, p["V"] * (1.0 - 0.08 * frac))
        res = core.score(p["L"], p["E_sel"], v_t, rho_t, p["C"])
        pts.append((f"Cycle {step}", round(rho_t, 3), res["R_raw"], short(res["tier"])))
    return pts


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

    default_after = float(p.get("rho_after", min(0.85, p["rho_now"] + 0.25)))
    rho_sim = st.session_state.get(f"rho_{city_name}", round(default_after, 2))
    r_now = core.score(p["L"], p["E_sel"], p["V"], p["rho_now"], p["C"])["R_raw"]
    r_sim = core.score(p["L"], p["E_sel"], p["V"], rho_sim, p["C"])["R_raw"]
    eal_sim = p["L"] * p["C"] * (1.0 - rho_sim)

    col_left, col_right = st.columns((1.0, 1.0), gap="large")
    with col_left:
        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}
          .frame{{position:relative;background:#FFF;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,0.06)}}
          .pills{{position:absolute;top:12px;left:12px;z-index:3;display:flex;gap:6px}}
          .pill{{background:rgba(15,23,42,0.84);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:999px}}
          video{{width:100%;height:330px;object-fit:cover;background:#F8FAFC;display:block}}
        </style>
        <div class="frame">
          <div class="pills"><span class="pill">Detailed and Dynamic</span><span class="pill">World Bank Compendium 2023</span></div>
          <video autoplay loop muted playsinline controls><source src="{clip_url}" type="video/mp4"><source src="{fb_url}" type="video/mp4"></video>
        </div>
        """, height=338)
        st.markdown(f"### Main 3D Infrastructure Model — {city_name}")
        st.caption(sector_tag)
        st.write(narrative)

    with col_right:
        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}
          .frame{{position:relative;background:#0F172A;border:1px solid #CBD5E1;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,0.08)}}
          .pills{{position:absolute;top:12px;left:12px;z-index:4;display:flex;gap:6px}}
          .pill{{background:rgba(15,23,42,0.84);color:#FFF;font-size:10px;font-weight:700;padding:4px 9px;border-radius:999px}}
          video{{width:100%;height:330px;object-fit:cover;opacity:0.40;display:block}}
          .hud{{position:absolute;inset:44px 14px 14px 14px;z-index:3;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(180deg,rgba(15,23,42,0.12) 0%,rgba(15,23,42,0.90) 100%);border-radius:12px;padding:14px;color:#FFF}}
          .bars{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:end;height:125px}}
          .col{{display:flex;flex-direction:column;align-items:center;gap:4px}}
          .bar{{width:100%;border-radius:6px 6px 2px 2px}}
        </style>
        <div class="frame">
          <div class="pills"><span class="pill">Dual-Layer Storytelling</span><span class="pill">For Data-rich Stories</span></div>
          <video autoplay loop muted playsinline><source src="{clip_url}" type="video/mp4"><source src="{fb_url}" type="video/mp4"></video>
          <div class="hud">
            <div style="font-size:11px;font-weight:800;color:#38BDF8;margin-bottom:8px">2D RMTI MECHANISM OVERLAY · R = L · E · V · (1 − ρ)</div>
            <div class="bars">
              <div class="col"><span style="font-size:11px;font-weight:800">{p['L']:.2f}</span><div class="bar" style="height:{int(p['L']*100)}px;background:#38BDF8"></div><span style="font-size:10px;color:#CBD5E1">Hazard L</span></div>
              <div class="col"><span style="font-size:11px;font-weight:800">{p['E_sel']:.2f}</span><div class="bar" style="height:{int(p['E_sel']*100)}px;background:#F87171"></div><span style="font-size:10px;color:#CBD5E1">Exposure E</span></div>
              <div class="col"><span style="font-size:11px;font-weight:800">{p['V']:.2f}</span><div class="bar" style="height:{int(p['V']*100)}px;background:#FBBF24"></div><span style="font-size:10px;color:#CBD5E1">Vuln. V</span></div>
              <div class="col"><span style="font-size:11px;font-weight:800">{1-rho_sim:.2f}</span><div class="bar" style="height:{int((1-rho_sim)*100)}px;background:#34D399"></div><span style="font-size:10px;color:#CBD5E1">1 − ρ</span></div>
              <div class="col"><span style="font-size:11px;font-weight:800">{r_sim:.3f}</span><div class="bar" style="height:{max(14,int(r_sim*155))}px;background:#FFF"></div><span style="font-size:10px;color:#CBD5E1">Risk R</span></div>
            </div>
          </div>
        </div>
        """, height=338)
        st.markdown(f"### Main 3D + 2D Assessment — {city_name}")
        st.slider(f"Resilience Intervention (ρ) — Baseline: {p['rho_now']:.2f}", 0.05, 0.90, round(default_after, 2), 0.01, key=f"rho_{city_name}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline R", f"{r_now:.3f}", short(core.tier(r_now)), delta_color="off")
        m2.metric("Post-Upgrade R", f"{r_sim:.3f}", f"{(r_sim / r_now - 1) * 100:+.0f}%", delta_color="inverse")
        m3.metric("Simulated EAL", f"{eal_sim:.3f}")
        st.markdown(badge(core.tier(r_sim)), unsafe_allow_html=True)

    # Single-City RMTI Core Trajectory R(t)
    st.subheader(f"RMTI Core Multi-Cycle Trajectory R(t) — {city_name}")
    traj = _city_trajectory(p, rho_sim)
    fig_t = go.Figure()
    add_tier_bands(fig_t)
    fig_t.add_trace(go.Scatter(
        x=[t[0] for t in traj],
        y=[t[2] for t in traj],
        mode="lines+markers+text",
        text=[f"R={t[2]:.3f}<br>(ρ={t[1]:.2f})" for t in traj],
        textposition="top center",
        line=dict(color="#0F172A", width=3.5),
        marker=dict(size=11, color=["#EF4444", "#F59E0B", "#0284C7", "#10B981"]),
    ))
    fig_t.update_layout(height=310, yaxis_title="Residual Risk R(t)", yaxis_range=(0, max(0.55, r_now * 1.25)), showlegend=False)
    st.plotly_chart(style_fig(fig_t, 310), use_container_width=True)
    disclaimer()


def synthesis_page():
    page_header(
        "Six-City Portfolio Compilation & 3D RMTI Geometric Space",
        "Authoritative cross-city comparison (Marolla et al., 2023; Marolla, 2026) and clean light-grid 3D Cartesian coordinate space with directional arrows and tier planes.",
        "Disaster science case studies",
    )

    ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))} for k, v in content.SIX_CITIES.items()})
    rows = []
    for r in ranked:
        c = content.SIX_CITIES[r["name"]]
        rows.append({
            "Priority": r["priority_in_tier"],
            "City": r["name"],
            "Asset": c["asset"],
            "L": c["L"],
            "E": c["E_sel"],
            "V": c["V"],
            "ρ now": c["rho_now"],
            "R now": r["R_now"],
            "Tier now": short(r["tier_now"]),
            "ρ after": c.get("rho_after"),
            "R after": r.get("R_after"),
            "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
            "Reduction %": r.get("risk_reduction_pct"),
            "EAL now": r["EAL_now"],
            "Equity /1M": r["equity_now_per_1M"],
        })
    df = pd.DataFrame(rows)

