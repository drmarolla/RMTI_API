"""Cohort sandbox: synthetic or uploaded aggregate cohorts, ranked by tier then EAL."""
import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import TIER_COLORS, TIER_LABELS, core, hcc, short
from rmti_ui import add_tier_bands, disclaimer, page_header, style_fig

COLS = ["name", "N", "L", "E", "V", "rho_now", "rho_after", "C"]


def synth(n, seed):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "name": [f"SYN-{i + 1:03d}" for i in range(n)], "N": 100_000,
        "L": rng.choice([0.15, 0.20, 0.25, 0.30, 0.55, 0.90], n, p=[.25, .2, .2, .15, .15, .05]),
        "E": np.round(rng.uniform(0.45, 0.80, n), 2), "V": rng.choice([0.35, 0.60, 0.85], n, p=[.5, .4, .1]),
        "rho_now": rng.choice([0.15, 0.20, 0.45, 0.50], n, p=[.2, .45, .2, .15]), "rho_after": 0.65,
        "C": rng.choice([2, 3, 4, 5], n, p=[.15, .2, .25, .4])})


def render():
    page_header("Cohort Sandbox", "Score and rank a synthetic cohort, or upload your own aggregate table, then test a surveillance-improvement scenario.",
                "Research tools")
    st.markdown('<div class="note"><b>Do not upload patient-identifiable data.</b> Files are processed in memory for your session only '
                'and are never stored. Use synthetic or aggregate values.</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns([1, 1.6], gap="large")
    with c1:
        with st.container(border=True, key="panel"):
            src = st.radio("Data source", ["Synthetic cohort", "Upload CSV"], horizontal=True)
            if src == "Synthetic cohort":
                n = st.slider("Synthetic patients", 20, 1000, 200, 20)
                seed = st.number_input("Random seed", 0, 99999, 2026)
                df = synth(n, int(seed))
            else:
                tpl = pd.DataFrame([{"name": "Example cohort A", "N": 100000, "L": 0.25, "E": 0.60, "V": 0.48, "rho_now": 0.20, "rho_after": 0.55, "C": 5}])
                st.download_button("Download the CSV template", tpl.to_csv(index=False).encode(), "rmti_cohort_template.csv", "text/csv")
                up = st.file_uploader("CSV with columns: " + ", ".join(COLS), type="csv")
                if up is None:
                    st.info("Upload a file to continue, or switch to the synthetic cohort.")
                    disclaimer()
                    return
                if up.size > 5_000_000:
                    st.error("File too large (limit 5 MB).")
                    return
                df = pd.read_csv(io.BytesIO(up.getvalue()))
                missing = [c for c in COLS[:-2] + ["C"] if c not in df.columns]
                if missing:
                    st.error("Missing columns: " + ", ".join(missing))
                    return
                df = df.head(5000)
                if "rho_after" not in df.columns:
                    df["rho_after"] = np.nan
            st.markdown("**Scenario**")
            scen = st.toggle("Override ρ after for every row", True)
            rho_s = st.slider("ρ after (scenario)", 0.0, 0.95, 0.65, 0.01, disabled=not scen)
            if scen:
                df["rho_after"] = rho_s
    rows, bad = {}, 0
    for _, r in df.iterrows():
        try:
            kw = dict(N=float(r["N"]), L=float(r["L"]), E=float(r["E"]), V=float(r["V"]), rho_now=float(r["rho_now"]), C=int(r["C"]))
            if pd.notna(r.get("rho_after")):
                kw["rho_after"] = float(r["rho_after"])
            core.score(kw["L"], kw["E"], kw["V"], kw["rho_now"], kw["C"])
            rows[str(r["name"])] = kw
        except (ValueError, TypeError):
            bad += 1
    with c2:
        if not rows:
            st.error("No valid rows. Check ranges: L, E, V in [0, 1], ρ in [0, 1), C in 1–5.")
            return
        ranked = hcc.rank_cohort_hcc(rows)
        out = pd.DataFrame([{"Name": r["name"], "Priority in tier": r["priority_in_tier"], "R now": r["R_now"], "Tier now": core.tier(r["R_now"]),
                             "R after": r.get("R_after"), "Tier after": core.tier(r["R_after"]) if "R_after" in r else None,
                             "Reduction %": r.get("risk_reduction_pct"), "EAL now": r["EAL_now"]} for r in ranked])
        k1, k2, k3 = st.columns(3)
        k1.metric("Rows scored", len(out), f"{bad} skipped" if bad else None, delta_color="off")
        k2.metric("Mean R now", f"{out['R now'].mean():.3f}")
        if out["R after"].notna().any():
            k3.metric("Mean R after", f"{out['R after'].mean():.3f}", f"{(out['R after'].mean() / out['R now'].mean() - 1) * 100:.1f}%", delta_color="inverse")
        now = out["Tier now"].value_counts().reindex(TIER_LABELS, fill_value=0)
        aft = out["Tier after"].value_counts().reindex(TIER_LABELS, fill_value=0) if out["Tier after"].notna().any() else None
        fig = go.Figure()
        fig.add_bar(x=[short(t) for t in TIER_LABELS], y=now.values, name="Now", marker_color="#1E3A5F")
        if aft is not None:
            fig.add_bar(x=[short(t) for t in TIER_LABELS], y=aft.values, name="After scenario", marker_color="#93C5FD")
        fig.update_layout(barmode="group", yaxis_title="Patients or cohorts", title="Tier distribution")
        st.plotly_chart(style_fig(fig, 380), width="stretch")
        st.dataframe(out, hide_index=True, width="stretch", height=360)
        st.download_button("Download ranked results (CSV)", out.to_csv(index=False).encode(), "rmti_ranked.csv", "text/csv")
    disclaimer()
