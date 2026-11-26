"""Interactive Six Sub-Saharan African Cities showcase (World Bank Compendium 2023 & Marolla 2026)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, short
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

CITY_META = {
    "Lagos": ("city_lagos.mp4", "Coastal Megacity · Mass Transit & Lagoon Surge", "Coastal storm surge and pluvial flooding threaten high-density BRT and bridge corridors; elevating transit nodes and tidal barriers cuts systemic risk."),
    "Lilongwe": ("city_lilongwe.mp4", "Capital Basin · Drainage & Utility Networks", "Rapid urban expansion strains stormwater culverts and water utilities; green-grey retention basins and culvert upgrades lower vulnerability."),
    "Bamako": ("city_bamako.mp4", "Riverine Corridor · Urban Healthcare Continuity", "Compounding Niger River flooding and extreme heatwaves stress clinics and power grids; solar microgrids and flood-proof access roads protect care."),
    "Nairobi": ("city_nairobi.mp4", "Highland Hub · Stormwater & Transit Arteries", "Flash runoff across river valleys disrupts commuter arteries; riparian bioswales and reinforced bridge spans stabilize mobility."),
    "Dar es Salaam": ("city_dar.mp4", "Port Corridor · Coastal & BRT Infrastructure", "Sea-level surge and intense monsoon rainfall threaten coastal transit lanes; seawalls and mangrove-hybrid buffers preserve port-city flow."),
    "Lusaka": ("city_lusaka.mp4", "Plateau City · Aquifer & Drainage Protection", "Seasonal inundation threatens shallow karst aquifers and neighborhood utilities; lined channels and retention ponds prevent cascading failure."),
}


def render():
    page_header(
        "Urban infrastructure: six Sub-Saharan African cities",
        "Interactive Main 3D + 2D dual-layer case studies grounded in the World Bank Compendium (Marolla et al., 2023, DOI: 10.1596/40309) and Marolla (2026).",
        "Disaster science case studies",
    )

    city_names = list(content.SIX_CITIES.keys())
    selected = st.segmented_control("Select a Sub-Saharan African City Case Study:", city_names, default="Lagos") or "Lagos"

    p = content.SIX_CITIES[selected]
    clip_file, sector_tag, narrative = CITY_META.get(selected, ("case_african_cities.mp4", "Urban Resilience", ""))
    clip_url = f"{RAW_VIDEOS}/{clip_file}"
    fallback_url = f"{RAW_VIDEOS}/case_african_cities.mp4"

    # Visual Science-inspired 2-Card Dual-Layer Layout
    col_3d, col_2d = st.columns((1.15, 1.0), gap="large")

    with col_3d:
        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
          .box{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden;box-shadow:0 10px 28px rgba(15,23,42,0.06)}}
          .pills{{display:flex;flex-wrap:wrap;gap:6px;padding:12px 16px;background:#F8FAFC;border-bottom:1px solid #E2E8F0}}
          .pill{{background:#0F172A;color:#FFFFFF;font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:999px}}
          .pill.blue{{background:#0284C7}}
          video{{width:100%;height:340px;object-fit:contain;background:#FFFFFF;display:block}}
        </style>
        <div class="box">
          <div class="pills">
            <span class="pill blue">Detailed and Dynamic</span>
            <span class="pill">World Bank Compendium · 2023</span>
            <span class="pill">{selected}</span>
          </div>
          <video autoplay loop muted playsinline controls>
            <source src="{clip_url}" type="video/mp4">
            <source src="{fallback_url}" type="video/mp4">
          </video>
        </div>
        """, height=405)
        st.markdown(f"### Main 3D Infrastructure Model: {selected}")
        st.caption(f"{sector_tag} · Asset: {p['asset']}")
        st.write(narrative)

    with col_2d:
        with st.container(border=True):
            st.markdown(
                '<span style="background:#0284C7;color:#FFF;font-size:10.5px;font-weight:800;padding:3px 9px;border-radius:999px;">Dual-Layer Storytelling</span> '
                '<span style="background:#10B981;color:#FFF;font-size:10.5px;font-weight:800;padding:3px 9px;border-radius:999px;">For Data-rich Stories</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"### Main 3D + 2D: {selected} RMTI Simulator")
            st.caption("Adjust the Resilience Lever (ρ) to test infrastructure upgrades in real time.")

            default_after = float(p.get("rho_after", min(0.85, p["rho_now"] + 0.25)))
            rho_sim = st.slider(
                f"Resilience Capacity (ρ) — Baseline: {p['rho_now']:.2f}",
                min_value=0.05,
                max_value=0.90,
                value=round(default_after, 2),
                step=0.01,
                key=f"sim_rho_{selected}",
            )

            base_res = core.score(p["L"], p["E_sel"], p["V"], p["rho_now"], p["C"])
            sim_res = core.score(p["L"], p["E_sel"], p["V"], rho_sim, p["C"])
            r_now, r_sim = base_res["R_raw"], sim_res["R_raw"]
            eal_now = p["L"] * p["C"] * (1.0 - p["rho_now"])
            eal_sim = p["L"] * p["C"] * (1.0 - rho_sim)

            m1, m2, m3 = st.columns(3)
            m1.metric("Baseline R", f"{r_now:.3f}", short(core.tier(r_now)), delta_color="off")
            m2.metric("Simulated R", f"{r_sim:.3f}", f"{(r_sim / r_now - 1) * 100:+.0f}%", delta_color="inverse")
            m3.metric("EAL Index", f"{eal_sim:.3f}", f"{(eal_sim - eal_now):+.3f}", delta_color="inverse")

            fig = go.Figure(go.Bar(
                x=["L (Hazard)", "E (Exposure)", "V (Vuln.)", "1 − ρ (Residual)", "R Score"],
                y=[p["L"], p["E_sel"], p["V"], 1.0 - rho_sim, r_sim],
                marker_color=["#0284C7", "#EF4444", "#F59E0B", "#10B981", "#0F172A"],
                text=[f"{v:.2f}" for v in (p["L"], p["E_sel"], p["V"], 1.0 - rho_sim, r_sim)],
                textposition="outside",
            ))
            fig.update_layout(height=210, margin=dict(l=8, r=8, t=12, b=20), yaxis=dict(range=[0, 1.15], visible=False), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(badge(core.tier(r_sim)), unsafe_allow_html=True)

    st.divider()
    st.subheader("Cross-City Portfolio Validation (Tables 4–6, Marolla 2026)")
    ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))} for k, v in content.SIX_CITIES.items()})
    rows = []
    for r in ranked:
        rows.append({
            "Priority in tier": r["priority_in_tier"],
            "City": r["name"],
            "Asset": content.SIX_CITIES[r["name"]]["asset"],
            "R now": r["R_now"],
            "Tier now": short(r["tier_now"]),
            "R after": r.get("R_after"),
            "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
            "Reduction %": r.get("risk_reduction_pct"),
            "EAL now": r["EAL_now"],
            "Equity /1M": r["equity_now_per_1M"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width="stretch")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        add_tier_bands(fig)
        fig.add_bar(x=df["City"], y=df["R now"], name="R now", marker_color="#EF4444")
        fig.add_bar(x=df["City"], y=df["R after"], name="R after ($50M package)", marker_color="#10B981")
        fig.update_layout(barmode="group", yaxis_title="Residual risk R", yaxis_range=(0, 0.65), title="Six-City Residual Risk vs. Fixed Tiers")
        st.plotly_chart(style_fig(fig, 420), width="stretch")
    with c2:
        d2 = df.sort_values("Equity /1M")
        fig = go.Figure(go.Bar(y=d2["City"], x=d2["Equity /1M"], orientation="h", marker_color="#0284C7"))
        fig.update_layout(title="Per-Capita Equity Rate (EAL per Million Residents)", xaxis_title="Equity rate")
        st.plotly_chart(style_fig(fig, 420), width="stretch")

    st.caption(
        "Sources: Marolla et al. (2023). Enhancing the Climate Resilience of Urban Infrastructure Projects in Sub-Saharan Africa. "
        "World Bank Compendium (https://doi.org/10.1596/40309) · Marolla C. (2026). IJMADA 6(1): 354–388 (https://doi.org)."
    )
    disclaimer()
