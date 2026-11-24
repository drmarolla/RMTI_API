"""General RMTI calculator + portfolio ranking (any domain)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import content
from engine import core, elas, hcc, tier_of, short, TIER_COLORS
from rmti_ui import add_tier_bands, badge, disclaimer, page_header, style_fig


def tier_ladder(r_now, r_after=None, height=150):
    fig = go.Figure()
    add_tier_bands(fig, axis="x")
    fig.add_vline(x=r_now, line_width=5, line_color="#0F172A", annotation_text=f"now {r_now:.3f}", annotation_position="top")
    if r_after is not None:
        fig.add_vline(x=r_after, line_width=5, line_color="#BE123C", line_dash="dot",
                      annotation_text=f"after {r_after:.3f}", annotation_position="bottom")
    fig.update_xaxes(range=[0, 0.75], title="Residual risk R")
    fig.update_yaxes(visible=False)
    return style_fig(fig, height)


def render():
    page_header("RMTI Calculator", "Score any asset, system or cohort with R = L · E · V · (1 − ρ), see its fixed tier, and test what a resilience investment buys.",
                "Clinical calculators")
    t_one, t_port = st.tabs(["Single assessment", "Portfolio ranking"])

    with t_one:
        left, right = st.columns([1, 1.25], gap="large")
        with left:
            with st.container(border=True, key="panel"):
                st.subheader("Inputs")
                preset = st.selectbox("Start from", ["Custom"] + list(content.SIX_CITIES))
                p = content.SIX_CITIES.get(preset, dict(N=1_000_000, L=0.60, E_sel=0.60, V=0.60, rho_now=0.20, rho_after=0.50, C=4))
                N = st.number_input("Population or cohort size, N", 10, 20_000_000_000, int(p["N"]), step=1000)
                L = st.slider("L · Likelihood", 0.0, 1.0, float(p["L"]), 0.005)
                use_elog = st.toggle("Use the log-normalised population exposure for E", False,
                                     help="E_log is advisory. Turn off to enter a rubric-based exposure.")
                elog = core.e_log(N)
                E = elog if use_elog else st.slider("E · Exposure", 0.0, 1.0, float(p["E_sel"]), 0.005)
                if use_elog:
                    st.caption(f"E = E_log = {elog:.3f}")
                V = st.slider("V · Vulnerability", 0.0, 1.0, float(p["V"]), 0.005)
                rho_now = st.slider("ρ now · Resilience today", 0.0, 0.99, float(p["rho_now"]), 0.005)
                has_after = st.toggle("Model an investment or treatment (ρ after)", preset in ("Bamako", "Lagos", "Lilongwe") or preset == "Custom")
                rho_after = st.slider("ρ after", 0.0, 0.99, float(p.get("rho_after", 0.5)), 0.005) if has_after else None
                C = st.select_slider("C · Consequence", [1, 2, 3, 4, 5], int(p["C"]), format_func=lambda c: f"{c} {content.C_NAMES[c]}")
        with right:
            res = core.assess(N, L, E, V, rho_now, rho_after, C)
            st.subheader("Result")
            m1, m2, m3 = st.columns(3)
            m1.metric("Inherent risk (IR)", f"{res['IR']:.3f}")
            m2.metric("Residual risk R", f"{res['R_now']:.3f}")
            m3.metric("EAL index", f"{res['EAL_now']:.3f}")
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
                st.markdown("**Sensitivity.** A 1% change in L, E or V changes R by 1%. A 1% change in ρ changes R by "
                            f"{e.get('rho', 0):.2f}%.")
            st.caption(f"Equity rate: {res['equity_now_per_1M']:.4f} EAL per million residents.  ·  E_log helper: {res['E_log']:.3f}")

    with t_port:
        st.markdown("Edit the table, add rows at the bottom, and the cohort is ranked by tier first, then by EAL within the tier.")
        base = pd.DataFrame([{"name": k, **{x: v.get(x) for x in ("N", "L", "E_sel", "V", "rho_now", "rho_after", "C")}}
                             for k, v in content.SIX_CITIES.items()])
        ed = st.data_editor(base, num_rows="dynamic", width="stretch", key="port_ed")
        rows = {}
        for _, r in ed.dropna(subset=["name", "N", "L", "E_sel", "V", "rho_now", "C"]).iterrows():
            kw = dict(N=float(r["N"]), L=float(r["L"]), E_sel=float(r["E_sel"]), V=float(r["V"]), rho_now=float(r["rho_now"]), C=int(r["C"]))
            if pd.notna(r.get("rho_after")):
                kw["rho_after"] = float(r["rho_after"])
            rows[str(r["name"])] = kw
        try:
            ranked = core.rank_cohort(rows)
            df = pd.DataFrame([{"Priority in tier": r["priority_in_tier"], "Name": r["name"], "Tier now": short(r["tier_now"]),
                                "R now": r["R_now"], "EAL now": r["EAL_now"], "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
                                "R after": r.get("R_after"), "Reduction %": r.get("risk_reduction_pct"),
                                "Per 1M": r["equity_now_per_1M"]} for r in ranked])
            st.dataframe(df, hide_index=True, width="stretch")
            fig = go.Figure()
            add_tier_bands(fig)
            fig.add_bar(x=df["Name"], y=df["R now"], name="R now", marker_color="#1E3A5F")
            if df["R after"].notna().any():
                fig.add_bar(x=df["Name"], y=df["R after"], name="R after", marker_color="#93C5FD")
            fig.update_layout(barmode="group", yaxis_title="Residual risk R", yaxis_range=[0, 0.7])
            st.plotly_chart(style_fig(fig, 460), width="stretch")
            st.download_button("Download ranking (CSV)", df.to_csv(index=False).encode(), "rmti_ranking.csv", "text/csv")
        except ValueError as exc:
            st.error(f"Check your inputs: {exc}")
    disclaimer()
