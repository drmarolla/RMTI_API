"""Six Sub-Saharan African City Case Studies & 3D Geometric Plane Synthesis."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, short
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

CITY_SPECS = {
    "Lagos": ("city_lagos.mp4", "Coastal Megacity · Mass Transit & Lagoon Surge", "Coastal storm surge and pluvial flooding threaten BRT and bridge corridors; elevating transit nodes and tidal barriers cuts systemic risk."),
    "Lilongwe": ("city_lilongwe.mp4", "Capital Basin · Drainage & Utility Networks", "Rapid urban expansion strains stormwater culverts and water utilities; green-grey retention basins and culvert upgrades lower vulnerability."),
    "Bamako": ("city_bamako.mp4", "Riverine Corridor · Urban Healthcare Continuity", "Compounding Niger River flooding and extreme heatwaves stress clinics and power grids; solar microgrids and flood-proof roads protect care."),
    "Nairobi": ("city_nairobi.mp4", "Highland Hub · Stormwater & Transit Arteries", "Flash runoff across river valleys disrupts commuter arteries; riparian bioswales and reinforced bridge spans stabilize mobility."),
    "Dar es Salaam": ("city_dar.mp4", "Port Corridor · Coastal & BRT Infrastructure", "Sea-level surge and intense monsoon rainfall threaten coastal transit lanes; seawalls and mangrove buffers preserve port-city flow."),
    "Lusaka": ("city_lusaka.mp4", "Plateau City · Aquifer & Drainage Protection", "Seasonal inundation threatens shallow karst aquifers and utilities; lined channels and retention ponds prevent cascading failure."),
}


def city_page(city_name):
    p = content.SIX_CITIES[city_name]
    clip_file, sector_tag, narrative = CITY_SPECS[city_name]
    clip_url, fb_url = f"{RAW_VIDEOS}/{clip_file}", f"{RAW_VIDEOS}/case_african_cities.mp4"
    page_header(f"{city_name}: Urban Infrastructure Resilience Case Study", f"World Bank Compendium (Marolla et al., 2023, DOI: 10.1596/40309) · Asset: {p['asset']}", "Disaster science case studies")

    default_after = float(p.get("rho_after", min(0.85, p["rho_now"] + 0.25)))
    rho_sim = st.session_state.get(f"rho_{city_name}", round(default_after, 2))
    r_now = core.score(p["L"], p["E_sel"], p["V"], p["rho_now"], p["C"])["R_raw"]
    r_sim = core.score(p["L"], p["E_sel"], p["V"], rho_sim, p["C"])["R_raw"]
    eal_sim = p["L"] * p["C"] * (1.0 - rho_sim)

    c1, c2 = st.columns((1.0, 1.0), gap="large")
    with c1:
        components.html(f"""
        <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;background:#FFF;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden}}.p{{position:absolute;top:12px;left:12px;z-index:3;display:flex;gap:6px}}.b{{background:rgba(15,23,42,0.84);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:999px}}video{{width:100%;height:320px;object-fit:cover;display:block}}</style>
        <div class="f"><div class="p"><span class="b">Detailed and Dynamic</span><span class="b">World Bank 2023</span></div><video autoplay loop muted playsinline controls><source src="{clip_url}" type="video/mp4"><source src="{fb_url}" type="video/mp4"></video></div>
        """, height=328)
        st.markdown(f"### Main 3D Infrastructure Model — {city_name}")
        st.caption(sector_tag)
        st.write(narrative)

    with c2:
        components.html(f"""
        <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.f{{position:relative;background:#0F172A;border-radius:16px;overflow:hidden}}.p{{position:absolute;top:12px;left:12px;z-index:4;display:flex;gap:6px}}.b{{background:rgba(15,23,42,0.84);color:#FFF;font-size:10px;font-weight:700;padding:4px 9px;border-radius:999px}}video{{width:100%;height:320px;object-fit:cover;opacity:0.4;display:block}}.h{{position:absolute;inset:42px 14px 14px 14px;z-index:3;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(180deg,rgba(15,23,42,0.1),rgba(15,23,42,0.92));border-radius:12px;padding:12px;color:#FFF}}.g{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:end;height:120px}}.c{{display:flex;flex-direction:column;align-items:center;gap:4px}}.bar{{width:100%;border-radius:6px 6px 2px 2px}}</style>
        <div class="f"><div class="p"><span class="b">Dual-Layer Storytelling</span><span class="b">For Data-rich Stories</span></div><video autoplay loop muted playsinline><source src="{clip_url}" type="video/mp4"><source src="{fb_url}" type="video/mp4"></video>
        <div class="h"><div style="font-size:11px;font-weight:800;color:#38BDF8;margin-bottom:6px">2D RMTI OVERLAY · R = L · E · V · (1 − ρ)</div><div class="g">
          <div class="c"><span style="font-size:11px;font-weight:800">{p['L']:.2f}</span><div class="bar" style="height:{int(p['L']*95)}px;background:#38BDF8"></div><span style="font-size:10px;color:#CBD5E1">Hazard L</span></div>
          <div class="c"><span style="font-size:11px;font-weight:800">{p['E_sel']:.2f}</span><div class="bar" style="height:{int(p['E_sel']*95)}px;background:#F87171"></div><span style="font-size:10px;color:#CBD5E1">Exposure E</span></div>
          <div class="c"><span style="font-size:11px;font-weight:800">{p['V']:.2f}</span><div class="bar" style="height:{int(p['V']*95)}px;background:#FBBF24"></div><span style="font-size:10px;color:#CBD5E1">Vuln. V</span></div>
          <div class="c"><span style="font-size:11px;font-weight:800">{1-rho_sim:.2f}</span><div class="bar" style="height:{int((1-rho_sim)*95)}px;background:#34D399"></div><span style="font-size:10px;color:#CBD5E1">1 − ρ</span></div>
          <div class="c"><span style="font-size:11px;font-weight:800">{r_sim:.3f}</span><div class="bar" style="height:{max(14,int(r_sim*150))}px;background:#FFF"></div><span style="font-size:10px;color:#CBD5E1">Risk R</span></div>
        </div></div></div>
        """, height=328)
        st.markdown(f"### Main 3D + 2D Assessment — {city_name}")
        st.slider(f"Resilience Intervention (ρ) — Baseline: {p['rho_now']:.2f}", 0.05, 0.90, round(default_after, 2), 0.01, key=f"rho_{city_name}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline R", f"{r_now:.3f}", short(core.tier(r_now)), delta_color="off")
        m2.metric("Post-Upgrade R", f"{r_sim:.3f}", f"{(r_sim / r_now - 1) * 100:+.0f}%", delta_color="inverse")
        m3.metric("Simulated EAL", f"{eal_sim:.3f}")
        st.markdown(badge(core.tier(r_sim)), unsafe_allow_html=True)

    st.subheader(f"RMTI Core Multi-Cycle Trajectory R(t) — {city_name}")
    xs, ys, txts = [], [], []
    for step in range(4):
        f = step / 3.0
        rt = p["rho_now"] + f * (rho_sim - p["rho_now"])
        vt = max(0.10, p["V"] * (1.0 - 0.08 * f))
        rv = core.score(p["L"], p["E_sel"], vt, rt, p["C"])["R_raw"]
        xs.append(f"Cycle {step}"); ys.append(rv); txts.append(f"R={rv:.3f} (ρ={rt:.2f})")
    fig_t = go.Figure()
    add_tier_bands(fig_t)
    fig_t.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers+text", text=txts, textposition="top center", line=dict(color="#0F172A", width=3.5), marker=dict(size=11, color=["#EF4444", "#F59E0B", "#0284C7", "#10B981"])))
    fig_t.update_layout(height=290, yaxis_title="Residual Risk R(t)", yaxis_range=(0, max(0.55, r_now * 1.25)), showlegend=False)
    st.plotly_chart(style_fig(fig_t, 290), use_container_width=True)
    disclaimer()


def synthesis_page():
    page_header("Six-City Portfolio Compilation & 3D Geometric Plane Projection", "Complete cross-city comparison (Marolla et al., 2023; Marolla, 2026) and 4D-style geometric risk-plane projection.", "Disaster science case studies")
    ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))} for k, v in content.SIX_CITIES.items()})
    rows = [{"Priority": r["priority_in_tier"], "City": r["name"], "Asset": content.SIX_CITIES[r["name"]]["asset"], "L": content.SIX_CITIES[r["name"]]["L"], "E": content.SIX_CITIES[r["name"]]["E_sel"], "V": content.SIX_CITIES[r["name"]]["V"], "ρ now": content.SIX_CITIES[r["name"]]["rho_now"], "R now": r["R_now"], "Tier now": short(r["tier_now"]), "ρ after": content.SIX_CITIES[r["name"]].get("rho_after"), "R after": r.get("R_after"), "Tier after": short(r["tier_after"]) if "tier_after" in r else "", "Reduction %": r.get("risk_reduction_pct"), "EAL now": r["EAL_now"], "Equity /1M": r["equity_now_per_1M"]} for r in ranked]
    st.subheader("1. Six-City RMTI Compilation & Priority Ranking Table")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.subheader("2. 3D Geometric Risk-Plane Projection (X: Hazard×Exposure · Y: Vulnerability · T: Resilience Trajectory)")
    fig = go.Figure()
    # White/silver tiled floor at z=0
    fig.add_trace(go.Surface(x=[[i * 0.1 for i in range(11)] for _ in range(11)], y=[[j * 0.1 for _ in range(11)] for j in range(11)], z=[[0.0] * 11 for _ in range(11)], colorscale=[[0, "#E2E8F0"], [1, "#F8FAFC"]], showscale=False, opacity=0.95, hoverinfo="skip"))
    for k in range(11):
        v = k * 0.1
        fig.add_trace(go.Scatter3d(x=(0.0, 1.0), y=(v, v), z=(0.002, 0.002), mode="lines", line=dict(color="#64748B", width=1.5), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter3d(x=(v, v), y=(0.0, 1.0), z=(0.002, 0.002), mode="lines", line=dict(color="#64748B", width=1.5), showlegend=False, hoverinfo="skip"))
    # Upper translucent grey plane (z=0.82) + Red (Baseline) & Gold (Post-Resilience) angled beam planes
    fig.add_trace(go.Surface(x=[[0.0, 1.0], [0.0, 1.0]], y=[[0.0, 0.0], [1.0, 1.0]], z=[[0.82, 0.82], [0.82, 0.82]], colorscale=[[0, "rgba(148,163,184,0.32)"], [1, "rgba(148,163,184,0.32)"]], showscale=False, name="Upper Trajectory Plane (T)"))
    fig.add_trace(go.Surface(x=[[0.0, 1.0], [0.0, 1.0]], y=[[0.0, 0.0], [1.0, 1.0]], z=[[0.82, 0.82], [0.82, 0.82]], colorscale=[[0, "rgba(148,163,184,0.32)"], [1, "rgba(148,163,184,0.32)"]], showscale=False, name="Upper Trajectory Plane (T)"))
    fig.add_trace(go.Surface(x=[[0.18, 0.18], [0.78, 0.78]], y=[[0.0, 1.0], [0.0, 1.0]], z=[[0.82, 0.82], [0.02, 0.02]], colorscale=[[0, "rgba(220,38,38,0.72)"], [1, "rgba(220,38,38,0.72)"]], showscale=False, name="Baseline Risk Wedge (Red)"))
    fig.add_trace(go.Surface(x=[[0.36, 0.36], [0.92, 0.92]], y=[[0.0, 1.0], [0.0, 1.0]], z=[[0.82, 0.82], [0.02, 0.02]], colorscale=[[0, "rgba(234,179,8,0.58)"], [1, "rgba(234,179,8,0.58)"]], showscale=False, name="Post-Resilience Wedge (Gold)"))
    fig.add_trace(go.Scatter3d(x=(0.0, 1.06), y=(0.0, 0.0), z=(0.01, 0.01), mode="lines+text", text=("", "X"), textfont=dict(color="#EF4444", size=14), line=dict(color="#EF4444", width=8), name="X: Hazard×Exposure"))
    fig.add_trace(go.Scatter3d(x=(0.0, 0.0), y=(0.0, 1.06), z=(0.01, 0.01), mode="lines+text", text=("", "Y"), textfont=dict(color="#22C55E", size=14), line=dict(color="#22C55E", width=8), name="Y: Vulnerability"))
    fig.add_trace(go.Scatter3d(x=(0.0, 0.0), y=(0.0, 0.0), z=(0.0, 0.96), mode="lines+text", text=("", "T"), textfont=dict(color="#FFFFFF", size=14), line=dict(color="#E2E8F0", width=5), name="T: Resilience Trajectory"))
    fig.add_trace(go.Cone(x=(1.06, 0.0, 0.0), y=(0.0, 1.06, 0.0), z=(0.01, 0.01, 0.96), u=(0.07, 0.0, 0.0), v=(0.0, 0.07, 0.0), w=(0.0, 0.0, 0.07), sizemode="absolute", sizeref=0.06, showscale=False, colorscale=[[0, "#FFFFFF"], [1, "#FFFFFF"]], showlegend=False, hoverinfo="skip"))
    for city, p in content.SIX_CITIES.items():
        le, v, r0 = round(p["L"] * p["E_sel"], 3), p["V"], p["rho_now"]
        r1 = p.get("rho_after", min(0.85, r0 + 0.25))
        fig.add_trace(go.Scatter3d(x=(le, le, le), y=(v, v, v), z=(0.0, r0, r1), mode="lines+markers+text", text=("", "", city), textposition="top center", textfont=dict(color="#FFFFFF", size=11), line=dict(color="#FFFFFF", width=3, dash="dash"), marker=dict(size=(4, 6, 8), color=("#94A3B8", "#EF4444", "#22C55E")), showlegend=False))
    fig.update_layout(height=600, paper_bgcolor="#05070B", font=dict(color="#F8FAFC"), margin=dict(l=0, r=0, t=10, b=0), scene=dict(bgcolor="#05070B", xaxis=dict(visible=False, range=[0, 1.15]), yaxis=dict(visible=False, range=[0, 1.15]), zaxis=dict(visible=False, range=[0, 1.05]), camera=dict(eye=dict(x=1.55, y=-1.55, z=0.82))))
    st.plotly_chart(fig, use_container_width=True)
    disclaimer()


def lagos(): city_page("Lagos")
def lilongwe(): city_page("Lilongwe")
def bamako(): city_page("Bamako")
def nairobi(): city_page("Nairobi")
def dar_es_salaam(): city_page("Dar es Salaam")
def lusaka(): city_page("Lusaka")
