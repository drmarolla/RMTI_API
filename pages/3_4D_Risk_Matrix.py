"""
pages/3_4D_Risk_Matrix.py  --  RMTI 3D/4D multi-dimensional matrix (Oncoclastics Platform)

X = L (likelihood), Y = E (exposure), Z = V (vulnerability): fixed 0..1, cubic, never rescaled.
4th dimension: rho (resilience) = colour; time = path order / animation. Marker size = R.

Trajectory tab : uses your engine (service.trajectory) so V(t), rho(t), R(t) are the engine's own numbers.
                 Manual what-if mode uses the displayed formula R = L*E*V*(1-rho).
Cohort tab     : macro triage matrix + surveillance-backlog detection (formula view, see note on the page).

Research prototype. Synthetic or de-identified data only.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="RMTI 4D Risk Matrix", layout="wide")

try:                       # service.py lives at the repo root next to app.py
    import service as S
except Exception as _e:    # noqa: BLE001
    S = None
    _S_ERR = str(_e)

RHO_SCALE = [[0.0, "#d9262c"], [0.5, "#ff6b73"], [1.0, "#1d6fd0"]]   # vulnerable -> resilient
YMAX = {"hcc": 6.0, "lung": 4.0}


def rmti_formula(L, E, V, rho):
    """R = L*E*V*(1-rho), clipped to [0,1]; scalars or arrays."""
    L, E, V, rho = (np.clip(np.asarray(x, dtype=float), 0, 1) for x in (L, E, V, rho))
    return np.clip(L * E * V * (1 - rho), 0, 1)


def cube_scene():
    ax = dict(range=[0, 1], dtick=0.25, backgroundcolor="rgba(0,0,0,0)", gridcolor="#d3e8fb")
    return dict(xaxis=dict(title="L  likelihood", **ax), yaxis=dict(title="E  exposure", **ax),
                zaxis=dict(title="V  vulnerability", **ax), aspectmode="cube",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)))


def msize(r, lo=6, hi=24):
    return lo + (hi - lo) * np.sqrt(np.clip(np.asarray(r, dtype=float), 0, 1))


def draw_path(df, thr, interv, animate, r_label="R"):
    """df columns: cycle, L, E, V, rho, R, (optional) R_ref."""
    hover = ("<b>%{customdata[0]}</b><br>L=%{x:.2f} E=%{y:.2f} V=%{z:.2f}"
             "<br>ρ=%{customdata[1]:.2f}<br>R=%{customdata[2]:.3f}<extra></extra>")
    cd = df[["cycle", "rho", "R"]].values
    marker = dict(size=msize(df["R"]), color=df["rho"], colorscale=RHO_SCALE, cmin=0, cmax=1,
                  colorbar=dict(title="ρ", thickness=12), line=dict(width=1, color="#0b2545"))
    data = [
        go.Scatter3d(x=df["L"], y=df["E"], z=df["V"], mode="lines",
                     line=dict(color="#3f5f86", width=4), hoverinfo="skip", name="path"),
        go.Scatter3d(x=df["L"], y=df["E"], z=df["V"], mode="markers+text", text=df["cycle"],
                     textposition="top center", customdata=cd, hovertemplate=hover,
                     marker=marker, name="cycles"),
    ]
    if interv != "none" and interv in set(df["cycle"]):
        i = int(df.index[df["cycle"] == interv][0])
        data.append(go.Scatter3d(x=[df.loc[i, "L"]], y=[df.loc[i, "E"]], z=[df.loc[i, "V"]],
                                 mode="markers", hoverinfo="skip", name="intervention",
                                 marker=dict(size=float(msize(df.loc[i, "R"])) + 9, symbol="diamond-open",
                                             color="#1565c0", line=dict(width=3))))
    fig = go.Figure(data=data)
    if animate:
        fig.frames = [
            go.Frame(name=str(k), traces=[0, 1], data=[
                go.Scatter3d(x=df["L"][:k + 1], y=df["E"][:k + 1], z=df["V"][:k + 1]),
                go.Scatter3d(x=df["L"][:k + 1], y=df["E"][:k + 1], z=df["V"][:k + 1],
                             text=df["cycle"][:k + 1], customdata=cd[:k + 1],
                             marker=dict(size=msize(df["R"][:k + 1]), color=df["rho"][:k + 1],
                                         colorscale=RHO_SCALE, cmin=0, cmax=1)),
            ]) for k in range(len(df))]
        fig.update_layout(updatemenus=[dict(
            type="buttons", showactive=False, x=0.02, y=0.02,
            buttons=[dict(label="▶ Play", method="animate",
                          args=[None, dict(frame=dict(duration=700, redraw=True), fromcurrent=True)])])])
    fig.update_layout(scene=cube_scene(), height=620, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    # numeric truth behind the geometry
    f2 = go.Figure()
    f2.add_scatter(x=df["cycle"], y=df["R"], mode="lines+markers", name=r_label, line=dict(color="#1d6fd0", width=3))
    if "R_ref" in df:
        f2.add_scatter(x=df["cycle"], y=df["R_ref"], mode="lines+markers", name="memoryless reference",
                       line=dict(color="#d9262c", dash="dot"))
    f2.add_scatter(x=df["cycle"], y=[thr] * len(df), mode="lines", name=f"Threshold {thr:g} (placeholder)",   # legend entry, not an on-plot label
                   line=dict(color="#ff6b73", dash="dash", width=2))
    f2.update_layout(yaxis=dict(title="R", range=[0, 1]), height=340, margin=dict(l=0, r=120, t=10, b=0))
    st.plotly_chart(f2, use_container_width=True)

    crossed = df[df["R"] >= thr]["cycle"].tolist()
    st.markdown(f"**Latest R:** {df['R'].iloc[-1]:.3f} · **Δ vs first cycle:** "
                f"{df['R'].iloc[-1] - df['R'].iloc[0]:+.3f} · "
                f"**Cycles at/above threshold:** {', '.join(crossed) if crossed else 'none'}")
    st.download_button("Download path (JSON)", df.to_json(orient="records", indent=2),
                       "rmti_4d_path.json", "application/json")


# ---------------------------------------------------------------------------
st.title("RMTI 4D Risk Matrix")
st.caption("Axes L · E · V fixed to 0–1 · colour = ρ (resilience) · size = R = L·E·V·(1−ρ)")
st.warning("Research prototype. Not validated, not a medical device, not for patient-care or emergency "
           "decisions. Parameters are uncalibrated placeholders. Enter synthetic or de-identified data only.")

tab_traj, tab_cohort = st.tabs(["Patient trajectory (longitudinal 4D)", "Cohort matrix (macro triage)"])

# =========================================================================== trajectory
with tab_traj:
    mode = st.radio("Source", ["Engine trajectory (service.trajectory)", "Manual cycles (what-if)"], horizontal=True)

    if mode.startswith("Engine"):
        if S is None:
            st.error(f"Could not import service.py ({_S_ERR}). Use the manual mode, or check the page sits in pages/ next to app.py.")
        else:
            st.caption("Uses the engine's level-and-slope filter. In the engine, L and E are fixed per patient; "
                       "V(t) and ρ(t) evolve, so the path climbs or falls along V with ρ shown as colour.")
            c1, c2, c3, c4, c5 = st.columns(5)
            site = c1.selectbox("Cancer-site module", ["hcc", "lung"])
            L = c2.slider("L", 0.0, 1.0, 0.30, 0.01)
            E = c3.slider("E", 0.0, 1.0, 0.60, 0.01)
            C = c4.select_slider("C", [1, 2, 3, 4, 5], 3)
            rho0 = c5.slider("ρ at baseline", 0.0, 0.95, 0.20, 0.01)
            ymax = YMAX[site]
            st.caption(f"y = allostatic-load composite (0–{ymax:g}); leave y blank for a missed visit. "
                       "delivery = surveillance adherence 0–1.")
            tbl = st.data_editor(
                pd.DataFrame({"y": [1.5, 2.0, None, 2.5, 3.0, 2.5],
                              "delivery": [0.5, 0.5, 0.0, 0.6, 0.9, 0.9]}),
                num_rows="dynamic", use_container_width=True, key="eng_tbl",
                column_config={"y": st.column_config.NumberColumn(min_value=0.0, max_value=ymax, step=0.1),
                               "delivery": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05)})
            tbl = tbl.reset_index(drop=True)
            obs = [None if pd.isna(v) else float(v) for v in tbl["y"]]
            dlv = [None if pd.isna(v) else float(v) for v in tbl["delivery"]]
            if len(obs) < 2:
                st.info("Add at least two cycles.")
            else:
                try:
                    res = S.trajectory(site, L, E, C, rho0, obs, dlv)
                    f = pd.DataFrame(res["filtered"])
                    m = pd.DataFrame(res["memoryless"])
                    df = pd.DataFrame({"cycle": ["T%d" % int(t) for t in f["t"]], "L": L, "E": E,
                                       "V": f["V"].astype(float), "rho": f["rho"].astype(float),
                                       "R": f["R"].astype(float), "R_ref": m["R"].astype(float)})
                    k1, k2, k3 = st.columns(3)
                    thr = k1.slider("Threshold on R (placeholder)", 0.01, 0.50, 0.05, 0.01, key="thr_e")
                    interv = k2.selectbox("Mark intervention at", ["none"] + list(df["cycle"]), key="iv_e")
                    anim = k3.checkbox("Animate (play over time)", key="an_e")
                    draw_path(df, thr, interv, anim, "R(t), engine (filtered)")
                    if "tier" in f:
                        st.dataframe(f[[c for c in ["t", "y", "delivery", "V", "rho", "R", "tier"] if c in f]],
                                     use_container_width=True)
                    if res.get("tier_changes"):
                        with st.expander("Tier changes"):
                            st.write(res["tier_changes"])
                except (ValueError, KeyError) as e:
                    st.error(str(e))
    else:
        st.caption("What-if table: every coordinate is yours. R uses the displayed formula R = L·E·V·(1−ρ).")
        df = st.data_editor(
            pd.DataFrame({"cycle": ["T0", "T1", "T2", "T3", "T4", "T5"],
                          "L": [0.30, 0.34, 0.40, 0.44, 0.42, 0.40], "E": [0.50, 0.62, 0.70, 0.72, 0.45, 0.35],
                          "V": [0.50, 0.52, 0.55, 0.58, 0.58, 0.57], "rho": [0.20, 0.20, 0.18, 0.20, 0.50, 0.60]}),
            num_rows="dynamic", use_container_width=True, key="man_tbl",
            column_config={c: st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.01)
                           for c in ["L", "E", "V", "rho"]}).dropna().reset_index(drop=True)
        if len(df) < 2:
            st.info("Add at least two cycles.")
        else:
            df["R"] = rmti_formula(df["L"], df["E"], df["V"], df["rho"])
            df["R_ref"] = rmti_formula(df["L"], df["E"], df["V"], 0.0)
            k1, k2, k3 = st.columns(3)
            thr = k1.slider("Threshold on R (placeholder)", 0.01, 0.50, 0.05, 0.01, key="thr_m")
            interv = k2.selectbox("Mark intervention at", ["none"] + list(df["cycle"]), key="iv_m")
            anim = k3.checkbox("Animate (play over time)", key="an_m")
            df = df.rename(columns={})  # R_ref here = counterfactual with rho = 0
            draw_path(df, thr, interv, anim, "R (with ρ)")
            st.caption("Dotted line = counterfactual R if ρ were 0.")

# =========================================================================== cohort
with tab_cohort:
    st.subheader("Cohort-wide matrix and surveillance-backlog detection")
    st.caption("View uses R = L·E·V·(1−ρ) on columns you supply. For engine-ranked tiers use the Cohort ranking tab on the main page.")
    src = st.radio("Data source", ["Synthetic demo cohort", "Upload CSV (de-identified)"], horizontal=True)

    if src == "Synthetic demo cohort":
        n = st.slider("Synthetic cohort size", 200, 5000, 1500, 100)
        rng = np.random.default_rng(42)
        sites = rng.choice(["Site A", "Site B", "Site C", "Site D"], n)
        shift = pd.Series(sites).map({"Site A": 0.0, "Site B": 0.12, "Site C": -0.05, "Site D": 0.22}).values
        coh = pd.DataFrame({"site": sites, "L": rng.beta(2, 4, n),
                            "E": np.clip(rng.beta(3, 3, n) + shift, 0, 1),
                            "V": rng.beta(3, 3, n), "rho": np.clip(rng.beta(2, 4, n) - shift, 0, 1)})
        st.caption("Synthetic data for demonstration only. Site D is built with a screening gap.")
    else:
        up = st.file_uploader("CSV with columns L, E, V, rho (optional: site)", type="csv")
        if up is None:
            st.info("Upload a de-identified CSV. No names, MRNs or dates of birth.")
            st.stop()
        coh = pd.read_csv(up)
        miss = {"L", "E", "V", "rho"} - set(coh.columns)
        if miss:
            st.error("Missing columns: " + ", ".join(sorted(miss)))
            st.stop()
        if "site" not in coh.columns:
            coh["site"] = "All"
        coh = coh[["site", "L", "E", "V", "rho"]].dropna()
        if ((coh[["L", "E", "V", "rho"]] < 0) | (coh[["L", "E", "V", "rho"]] > 1)).any().any():
            st.warning("Values outside 0–1 will be clipped.")

    coh[["L", "E", "V", "rho"]] = coh[["L", "E", "V", "rho"]].clip(0, 1)
    coh["R"] = rmti_formula(coh["L"], coh["E"], coh["V"], coh["rho"])

    a, b, c = st.columns(3)
    e_thr = a.slider("Backlog: exposure ≥", 0.0, 1.0, 0.60, 0.05)
    rho_thr = b.slider("Backlog: resilience ≤", 0.0, 1.0, 0.30, 0.05)
    all_sites = sorted(coh["site"].astype(str).unique())
    picks = c.multiselect("Sites", all_sites, default=all_sites)
    coh = coh[coh["site"].astype(str).isin(picks)].copy()
    coh["backlog"] = (coh["E"] >= e_thr) & (coh["rho"] <= rho_thr)

    m1, m2, m3 = st.columns(3)
    m1.metric("Cohort size", f"{len(coh):,}")
    m2.metric("In backlog zone", f"{int(coh['backlog'].sum()):,}",
              f"{100 * coh['backlog'].mean():.1f}%" if len(coh) else None, delta_color="off")
    m3.metric("Mean R", f"{coh['R'].mean():.3f}" if len(coh) else "n/a")

    if len(coh):
        view = coh.sample(min(len(coh), 5000), random_state=1)
        fig3 = go.Figure(go.Scatter3d(
            x=view["L"], y=view["E"], z=view["V"], mode="markers",
            customdata=view[["site", "rho", "R"]].values,
            hovertemplate="%{customdata[0]}<br>L=%{x:.2f} E=%{y:.2f} V=%{z:.2f}"
                          "<br>ρ=%{customdata[1]:.2f} R=%{customdata[2]:.3f}<extra></extra>",
            marker=dict(size=np.where(view["backlog"], 5, 3), color=view["rho"], colorscale=RHO_SCALE,
                        cmin=0, cmax=1, opacity=0.75, colorbar=dict(title="ρ", thickness=12),
                        line=dict(width=0, color="#0b2545"))))
        fig3.update_layout(scene=cube_scene(), height=600, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Outlined points are in the backlog zone (high exposure, low resilience). Up to 5,000 points drawn.")

        left, right = st.columns(2)
        with left:
            edges = np.linspace(0, 1, 11)
            tmp = coh.assign(Eb=pd.cut(coh["E"], edges, include_lowest=True),
                             rb=pd.cut(coh["rho"], edges, include_lowest=True))
            grid = tmp.pivot_table(index="rb", columns="Eb", values="R", aggfunc="mean", observed=False)
            hm = go.Figure(go.Heatmap(z=grid.values, x=edges[:-1] + 0.05, y=edges[:-1] + 0.05,
                                      colorscale="YlOrRd", zmin=0, colorbar=dict(title="mean R")))
            hm.update_layout(xaxis_title="E exposure", yaxis_title="ρ resilience", height=340,
                             margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(hm, use_container_width=True)
        with right:
            by_site = (coh.groupby("site").agg(n=("R", "size"), mean_R=("R", "mean"),
                                               backlog_n=("backlog", "sum"),
                                               backlog_pct=("backlog", lambda s: 100 * s.mean()))
                       .sort_values("backlog_pct", ascending=False).round(3))
            st.dataframe(by_site, use_container_width=True)
        st.download_button("Download flagged records (CSV)", coh[coh["backlog"]].to_csv(index=False),
                           "rmti_backlog.csv", "text/csv")
