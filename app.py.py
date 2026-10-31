"""RMTI Platform: Streamlit interface. Run: streamlit run app.py
If RMTI_API_URL is set (e.g. http://localhost:8000) every calculation goes through the REST API;
otherwise the same engine is called in-process."""
import os, io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import time
import service as S
import secure_store as VAULT

API = os.environ.get("RMTI_API_URL")
st.set_page_config(page_title="Oncoclastics Platform", layout="wide")

TIER_COLORS = ["#7F8FA6", "#4A6FA5", "#C9A227", "#C2662D", "#9B2C2C"]   # restrained, no green
LABELS = {
    "hcc": dict(y="Allostatic-load composite (0-6)", delivery="Surveillance adherence (0-1)", ymax=6.0,
                unit="surveillance cycle (e.g. 6-monthly)", who="patient / cohort"),
    "lung": dict(y="Allostatic-load indicator count (0-4)", delivery="Screening-pathway delivery, ρ_care (0-1)", ymax=4.0,
                 unit="screening round (e.g. annual or 2-yearly)", who="patient / cohort"),
    "disaster": dict(y="Vulnerability indicator index (0-10)", delivery="Resilience programme delivered (0-1)", ymax=10.0,
                     unit="review cycle (e.g. annual)", who="city / asset / portfolio"),
}


def call(path, payload, local):
    if API:
        import requests
        r = requests.post(f"{API}{path}", json=payload, timeout=30)
        if r.status_code != 200:
            raise ValueError(r.json().get("detail", r.text))
        return r.json()
    return local()


def tier_badge(t):
    i = S.TIERS.index(t if t.startswith("Tier") else f"Tier {t.replace(' ', ' - ', 1)}")
    return f"<span style='background:{TIER_COLORS[i]};color:#fff;padding:3px 10px;border-radius:4px'>{t}</span>"


# ------------------------------------------------------------------ access gate
def gate():
    """Optional shared access codes: set RMTI_ACCESS_CODES="code1,code2" to require one.
    For institutional use put the app behind SSO (reverse proxy / st.login) instead; see README."""
    import hmac
    codes = [c for c in os.environ.get("RMTI_ACCESS_CODES", "").split(",") if c]
    if not codes or st.session_state.get("ok"):
        return
    st.title("Oncoclastics Platform")
    entered = st.text_input("Access code", type="password")
    if entered and any(hmac.compare_digest(entered, c) for c in codes):
        st.session_state["ok"] = True
        st.rerun()
    elif entered:
        st.error("Invalid code")
    st.stop()


gate()
read_csv = lambda f: S.privacy_check(pd.read_csv(f))   # every upload passes the identifier guard

# ------------------------------------------------------------------ header
st.title("Oncoclastics Platform")
st.caption(f"Risk Mechanism Theory Index (RMTI) · engine v{S.ENGINE_VERSION} · R = L · E · V · (1 − ρ)")
st.warning(S.DISCLAIMER)

FAMILIES = {"Oncoclastics (cancer)": "oncoclastics", "Disaster Science": "disaster_science"}
family = FAMILIES[st.sidebar.radio("RMTI domain", list(FAMILIES))]
if family == "oncoclastics":
    SITES = {"HCC (published application)": "hcc", "Lung cancer (proposed extension)": "lung"}
    domain = SITES[st.sidebar.radio("Cancer-site module", list(SITES))]
else:
    domain = "disaster"
lab = LABELS[domain]
# ---- practitioner workspace (only when the server enables the vault) ----
IDLE = 30 * 60
if VAULT.vault_enabled():
    auth = st.session_state.get("auth")
    if auth and time.time() - auth["seen"] > IDLE:
        st.session_state.pop("auth"); auth = None; st.sidebar.info("Logged out after 30 minutes of inactivity.")
    if auth:
        auth["seen"] = time.time()
        st.sidebar.success(f"Signed in as {auth['username']}")
        if st.sidebar.button("Sign out"):
            st.session_state.pop("auth"); st.rerun()
    else:
        with st.sidebar.expander("Practitioner sign-in", expanded=False):
            mode = st.radio("", ["Sign in", "Register"], horizontal=True, label_visibility="collapsed")
            u = st.text_input("Username (no real names)"); pw = st.text_input("Password", type="password")
            inv = st.text_input("Invite code", type="password") if mode == "Register" else None
            if st.button(mode):
                try:
                    if mode == "Register":
                        VAULT.register(u, pw, inv)
                    sess = VAULT.login(u, pw)
                    st.session_state["auth"] = {**sess, "seen": time.time()}
                    st.rerun()
                except (VAULT.AuthError, Exception) as e:
                    st.error(str(e) if isinstance(e, VAULT.AuthError) else "Sign-in failed.")
    auth = st.session_state.get("auth")
else:
    auth = None
    st.sidebar.caption("Secure workspace is off on this deployment (public sandbox). Do not enter patient data here.")


def save_case_ui(kind, payload, key):
    """Offer to save a case to the signed-in practitioner's encrypted workspace."""
    if not auth:
        return
    with st.expander("Save this case to my secure workspace"):
        label = st.text_input("Pseudonymous label (study code, not a name)", key=f"lab_{key}")
        if st.button("Save case", key=f"sv_{key}"):
            try:
                VAULT.save_record(auth, kind, label, payload)
                st.success("Saved (encrypted).")
            except VAULT.StoreError as e:
                st.error(str(e))


def l_input(container, key):
    """L as a slider, or for lung as a 5-year risk from a validated tool, scaled onto 0-1."""
    if domain == "lung":
        r5 = container.number_input("5-year individualised LC risk (%) from a validated tool", 0.0, 50.0, 2.5, 0.1,
                                    key=f"r5_{key}") / 100
        L = S.LUNG.l_from_risk(r5)
        container.caption(f"Scaled L = {L:.2f} (placeholder log scale; NHS high-risk cut-point is 2.5%)")
        return L
    return container.slider("L: likelihood (annual incidence / hazard)", 0.0, 1.0, 0.30, 0.01, key=f"L_{key}")


st.sidebar.markdown(
    "**Who uses what**\n\n- Clinicians and nurses: Snapshot, Trajectory\n- Programme and disaster-risk managers: Cohort, Snapshot\n"
    "- Researchers and climate scientists: Trajectory, Validation\n\nSession data stays in this browser session and is not stored.")

names = (["Snapshot", "Trajectory", "Cohort ranking", "Retrospective validation"]
         + (["Lung: evidence and mapping"] if domain == "lung" else [])
         + (["My cases"] if auth else []) + ["About and limits"])
T = dict(zip(names, st.tabs(names)))
tab_snap, tab_traj, tab_cohort, tab_val, tab_about = (T["Snapshot"], T["Trajectory"], T["Cohort ranking"],
                                                      T["Retrospective validation"], T["About and limits"])

# ------------------------------------------------------------------ snapshot
with tab_snap:
    st.subheader("Single assessment, optional before/after intervention")
    c1, c2, c3 = st.columns(3)
    N = c1.number_input("N: at-risk population or cohort size", 1, 100_000_000, 100_000)
    L = l_input(c1, "snap")
    E = c2.slider("E: exposure (share reached/affected)", 0.0, 1.0, 0.65, 0.01)
    V = c2.slider("V: vulnerability", 0.0, 1.0, 0.55, 0.01)
    rho_now = c3.slider("ρ now: resilience / surveillance adequacy", 0.0, 0.99, 0.20, 0.01)
    use_after = c3.checkbox("Compare with an improved state", True)
    rho_after = c3.slider("ρ after", 0.0, 0.99, 0.50, 0.01) if use_after else None
    C = st.select_slider("C: consequence index (1 low … 5 severe)", [1, 2, 3, 4, 5], 5)
    if domain == "hcc":
        with st.expander("Reference anchors (advisory, not lookups)"):
            st.write("V from ALBI grade:", S.ALBI_V, " ·  ρ surveillance ladder:", S.RHO_ANCHORS,
                     " ·  C from BCLC stage:", S.C_LADDER)
    try:
        payload = dict(domain=domain, N=N, L=L, E=E, V=V, rho_now=rho_now, rho_after=rho_after, C=C)
        out = call("/v1/snapshot", payload, lambda: S.snapshot(domain, N, L, E, V, rho_now, rho_after, C))
        m1, m2, m3 = st.columns(3)
        m1.metric("R now", f"{out['R_now']:.3f}")
        m1.markdown(tier_badge(out["tier_now"]), unsafe_allow_html=True)
        m1.caption(out["posture_now"])
        m2.metric("EAL index now", f"{out['EAL_now']:.3f}")
        if "R_after" in out:
            m3.metric("R after", f"{out['R_after']:.3f}", f"{out['R_after'] - out['R_now']:+.3f}", delta_color="inverse")
            m3.markdown(tier_badge(out["tier_after"]), unsafe_allow_html=True)
            m3.caption(f"Risk reduction {out['risk_reduction_pct']}% · investment efficiency {out['IEI']}")
        with st.expander("Full output (JSON)"):
            st.json(out)
        save_case_ui("snapshot", dict(domain=domain, inputs=payload, result=out), "snap")
        if family == "oncoclastics":
            with st.expander("Oncoclastics: two senses of resilience (biological ρ_bio, care-system ρ_care)"):
                st.caption("Biological sense: L, E, V and ρ_bio. Care-system sense: ρ_care only; the ρ entered above is read as ρ_care. "
                           "ρ_bio = 0 means not scored and reproduces the score above. Assumes the two act independently, which is itself untested. "
                           "Do not use any measure for ρ_bio that already sets V or L.")
                rb_default, ecog_pick = 0.0, "not scored"
                if domain == "lung":
                    st.warning("Lung ρ_bio ladder (v2.4.0) is PROVISIONAL: the five levels are anchored to ECOG performance status. ECOG partly reflects disease "
                               "already counted in V and saturates in screening populations; consensus (Delphi) work is still to do.")
                    ecog_pick = st.selectbox("ECOG performance status (optional helper)", ["not scored", 0, 1, 2, 3, 4], key="ecog_snap")
                    if ecog_pick != "not scored":
                        rb_default = S.LUNG.rho_bio_from_ecog(int(ecog_pick))
                rb = st.slider("ρ_bio (0.10 little · 0.25 limited · 0.40 moderate · 0.55 good · 0.70 excellent)", 0.0, S.RHO_BIO_CEILING, float(rb_default), 0.05, key=f"rb_snap_{ecog_pick}")
                after = st.slider("ρ_care after a disruption of care (care-system sense)", 0.0, 0.99, max(0.0, round(rho_now - 0.15, 2)), 0.01, key="rc_after")
                ts = S.two_sense_snapshot(L, E, V, rb, rho_now, C, after)
                q1, q2, q3 = st.columns(3)
                q1.metric("Combined ρ", f"{ts['rho']:.3f}")
                q2.metric("R (both senses)", f"{ts['R_raw']:.3f}")
                q3.metric("Tier", ts["tier"])
                st.write(f"Marginal effect of care-system capacity: R falls by {ts['care_effect']:.3f} when ρ_care is present. "
                         f"Marginal effect of biological reserve: {ts['bio_effect']:.3f}. These are order-dependent and do not sum to the total absorbed risk.")
                cd = ts["care_disruption"]
                st.write(f"Care-system disruption (ρ_care {rho_now:.2f} → {after:.2f}): R {cd['R_before']:.3f} → {cd['R_after']:.3f} "
                         f"({cd['delta_R']:+.3f}); tier {cd['tier_before']} → {cd['tier_after']}" + (" (tier changed)." if cd["tier_changed"] else "."))
            with st.expander("Export this reading as a FHIR R4 RiskAssessment (research use)"):
                st.caption("Status is always 'preliminary'. The score is exported as a tier plus a named extension, never as a probability. "
                           "Subject carries only a pseudonymous label. Structurally checked, not run through the official HL7 validator.")
                flabel = st.text_input("Pseudonymous label (study code, not a name)", key="fhir_label")
                if flabel:
                    try:
                        ra = S.fhir_risk_assessment(flabel, family, dict(N=N, L=L, E=E, V=V, rho_now=rho_now, rho_after=rho_after, C=C, rho_bio=rb), site=domain)
                        import json as _json
                        st.download_button("Download FHIR JSON", _json.dumps(ra, indent=2), "rmti_risk_assessment.fhir.json", mime="application/fhir+json")
                        st.json(ra, expanded=False)
                    except ValueError as e:
                        st.error(str(e))
    except ValueError as e:
        st.error(str(e))

# ------------------------------------------------------------------ trajectory
with tab_traj:
    st.subheader("Time-indexed trajectory")
    st.caption("Enter one row per cycle. Leave y empty for a missed visit; the filter carries its prediction forward. "
               "A trajectory is a reading of the framework, not a forecast.")
    a, b = st.columns([1, 2])
    with a:
        tL = l_input(a, "traj")
        tE = st.slider("E", 0.0, 1.0, 0.65, 0.01, key="tE")
        tC = st.select_slider("C", [1, 2, 3, 4, 5], 3, key="tC")
        rho0 = st.slider("ρ at baseline" if family != "oncoclastics" else "ρ_care at baseline (care-system sense)", 0.0, 0.95, 0.20, 0.01, key="rho0")
        rho_bio = (st.slider("ρ_bio (biological sense; 0 = not scored)", 0.0, S.RHO_BIO_CEILING, 0.0, 0.05, key="rho_bio_t")
                   if family == "oncoclastics" else 0.0)
        with st.expander("Filter parameters (uncalibrated placeholders)"):
            base = S.HCC_PARAMS if domain == "hcc" else S.DISASTER_PARAMS
            alpha = st.number_input("α level gain", 0.0, 1.0, base.alpha, 0.01)
            beta = st.number_input("β slope gain", 0.0, 1.0, base.beta, 0.01)
            look = st.number_input("κ·H look-ahead (cycles)", 0.0, 5.0, base.look_ahead, 0.1)
            lam = st.number_input("λ delivery → ρ gain", 0.0, 3.0, base.lam, 0.1)
    with b:
        default = pd.DataFrame({"cycle": [0, 1, 2, 3], "y": [2.0, 1.0, 1.0, 0.0],
                                "delivery": [0.40, 0.55, 0.70, 0.75]})
        up = st.file_uploader("Or upload CSV (columns: cycle, y, delivery)", type="csv", key="trajcsv")
        if up is not None:
            default = read_csv(up)
        edited = st.data_editor(default, num_rows="dynamic", use_container_width=True,
                                column_config={"y": st.column_config.NumberColumn(lab["y"], min_value=0.0, max_value=lab["ymax"]),
                                               "delivery": st.column_config.NumberColumn(lab["delivery"], min_value=0.0, max_value=1.0)})
    clean = lambda s: [None if pd.isna(v) else float(v) for v in s]
    obs, dlv = clean(edited["y"]), clean(edited["delivery"])
    try:
        po = dict(alpha=alpha, beta=beta, look_ahead=look, lam=lam)
        res = call("/v1/trajectory", dict(domain=domain, L=tL, E=tE, C=tC, rho0=rho0, observations=obs,
                                          delivery=dlv, params=po),
                   lambda: S.trajectory(domain, tL, tE, tC, rho0, obs, dlv, po))
        n = len(res["filtered"])
        upto = st.slider(f"Show through {lab['unit']}", 0, n - 1, n - 1) if n > 1 else 0
        f, m = pd.DataFrame(res["filtered"]).iloc[:upto + 1], pd.DataFrame(res["memoryless"]).iloc[:upto + 1]
        fig = go.Figure()
        for lo, hi, col, nm in [(0, .05, 0, "Tier 1"), (.05, .15, 1, "Tier 2"), (.15, .35, 2, "Tier 3"), (.35, .60, 3, "Tier 4")]:
            fig.add_hrect(y0=lo, y1=hi, fillcolor=TIER_COLORS[col], opacity=0.10, line_width=0,
                          annotation_text=nm, annotation_position="right")
        fig.add_trace(go.Scatter(x=f["t"], y=f["R"], mode="lines+markers", name="R(t), filtered",
                                 line=dict(color="#1F4E79", width=3)))
        fig.add_trace(go.Scatter(x=m["t"], y=m["R"], mode="lines+markers", name="R(t), memoryless",
                                 line=dict(color="#7F8FA6", dash="dash")))
        fig.update_layout(height=380, xaxis_title=lab["unit"], yaxis_title="Residual risk R",
                          margin=dict(l=10, r=60, t=20, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=f["t"], y=f["V"], name="V(t)", line=dict(color="#C2662D")))
        fig2.add_trace(go.Scatter(x=f["t"], y=f["rho"], name="ρ(t)", line=dict(color="#4A6FA5")))
        fig2.update_layout(height=260, xaxis_title=lab["unit"], margin=dict(l=10, r=60, t=10, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(f[["t", "y", "delivery", "level", "slope", "V", "rho", "R", "tier", "posture", "EAL", "dR"]],
                     use_container_width=True)
        if res["tier_changes"]:
            st.info("Tier changes (descriptive only; a raw flip on a noisy path can be a false alert): " +
                    "; ".join(f"cycle {c['t']}: {c['from']} → {c['to']}" for c in res["tier_changes"]))
        if family == "oncoclastics":
            tsr = S.two_sense_trajectory(domain, tL, tE, tC, rho_bio, rho0, obs, dlv, po)
            ev = [e for e in tsr["events"] if e["t"] <= upto]
            st.markdown("**Candidate oncoclastic events** (each names its sense; descriptive flags, not alerts, diagnoses or recommendations)")
            st.dataframe(pd.DataFrame(ev) if ev else pd.DataFrame({"events": ["none in the displayed cycles"]}), use_container_width=True)
            if rho_bio > 0:
                st.dataframe(pd.DataFrame(tsr["rows"]).iloc[:upto + 1][["t", "rho_bio", "rho_care", "rho_total", "R_two_sense", "tier_two_sense", "care_effect", "bio_effect"]],
                             use_container_width=True)
        st.download_button("Download trajectory CSV", f.to_csv(index=False), "rmti_trajectory.csv")
        save_case_ui("trajectory", dict(domain=domain, L=tL, E=tE, C=tC, rho0=rho0, observations=obs, delivery=dlv,
                                        params=po, tiers=[r["tier"] for r in res["filtered"]]), "traj")
    except ValueError as e:
        st.error(str(e))

# ------------------------------------------------------------------ cohort
with tab_cohort:
    st.subheader("Rank a cohort or portfolio")
    st.caption("Columns: name, N, L, E, V, rho_now, optional rho_after, C. Ranked by tier, then EAL; priority resets within each tier. "
               "Use pseudonymous IDs only.")
    src = st.file_uploader("Upload CSV", type="csv", key="cohcsv")
    if src is not None:
        df = read_csv(src)
    else:
        fn = {"hcc": "published_cohorts_snapshot.csv", "lung": "synthetic_lung_cohort.csv", "disaster": "published_disaster_cohort.csv"}[domain]
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), "sample_data", fn))
        st.caption({"hcc": "Showing the six published HCC cohorts from the manuscript as an example.",
                    "lung": "Showing SYNTHETIC lung examples (risk5 = 5-year risk as a fraction, scaled to L internally).",
                    "disaster": "Showing the published Sub-Saharan Africa and California cases as an example."}[domain])
    df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="coh_editor")
    try:
        rows = [{k: v for k, v in r.items() if pd.notna(v)} for r in df.to_dict("records")]
        ranked = call("/v1/cohort/rank", dict(domain=domain, patients=rows), lambda: S.cohort(domain, rows))
        cols = ["priority_in_tier", "name", "tier_now", "R_now", "EAL_now", "posture_now", "R_after", "tier_after", "risk_reduction_pct"]
        rk = pd.DataFrame(ranked)
        st.dataframe(rk[[c for c in cols if c in rk.columns]], use_container_width=True)
        st.download_button("Download ranking CSV", rk.to_csv(index=False), "rmti_ranking.csv")
    except (ValueError, KeyError) as e:
        st.error(f"Check your columns and ranges: {e}")

# ------------------------------------------------------------------ validation
with tab_val:
    st.subheader("Retrospective validation on serial data")
    st.caption("Long format, one row per patient per cycle: patient_id, cycle, y, optional delivery, L, E, C, rho0, and per patient "
               "event (0/1) and time, and optionally a stratum column (smoking status, histology, sex...). Computes final-cycle and baseline R per patient, then discrimination and tier-wise event rates. "
               "This needs ethics approval and a data-use agreement for real data; the example is synthetic.")
    vs = st.file_uploader("Upload serial CSV", type="csv", key="valcsv")
    if vs is not None:
        vdf = read_csv(vs)
    else:
        vdf = S.example_serial(y_max=lab["ymax"])
        st.info("Using SYNTHETIC demonstration data (outcome generated from an arbitrary rule). Results mean nothing clinically.")
    try:
        vp = S.validate_serial(vdf, domain)
        if "c_index_final" in vp:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Patients / events", f"{vp['n']} / {vp['events']}")
            k2.metric("C-index, final cycle", f"{vp['c_index_final']:.3f}")
            k3.metric("C-index, baseline only", f"{vp['c_index_baseline']:.3f}")
            k4.metric("AUC final / baseline", f"{vp['auc_final']:.2f} / {vp['auc_baseline']:.2f}")
            st.caption(vp["note"])
            nb = st.number_input("Bootstrap resamples for 95% CIs (0 = off)", 0, 2000, 300, 100)
            if nb:
                ci = S.bootstrap_ci(vp["patients"], int(nb))
                if "c_final" in ci:
                    st.write(f"C-index final {ci['c_final'][0]:.2f}-{ci['c_final'][1]:.2f} · baseline "
                             f"{ci['c_baseline'][0]:.2f}-{ci['c_baseline'][1]:.2f} · **difference (final minus baseline) "
                             f"{ci['delta_c'][0]:+.2f} to {ci['delta_c'][1]:+.2f}**. " +
                             ("The interval excludes zero." if ci["delta_c_excludes_zero"] else
                              "The interval includes zero: no demonstrated gain from trajectory over level."))
                else:
                    st.warning(ci["note"])
            g1, g2 = st.columns(2)
            kmf = go.Figure()
            for i, (t, curve) in enumerate(sorted(vp["km"].items())):
                xs, ys = zip(*curve)
                kmf.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line_shape="hv", name=t,
                                         line=dict(color=TIER_COLORS[S.TIERS.index(t)])))
            kmf.update_layout(title="Event-free survival by final tier (Kaplan-Meier)", height=330,
                              xaxis_title="time", yaxis_title="S(t)", yaxis_range=[0, 1.02])
            g1.plotly_chart(kmf, use_container_width=True)
            cb = S.calibration(vp["patients"]); tt = cb["by_tier"]
            cal = go.Figure(go.Bar(x=tt["tier_final"], y=tt["observed_event_rate"],
                                   marker_color=[TIER_COLORS[S.TIERS.index(t)] for t in tt["tier_final"]],
                                   error_y=dict(type="data", symmetric=False,
                                                array=tt["ci_high"] - tt["observed_event_rate"],
                                                arrayminus=tt["observed_event_rate"] - tt["ci_low"])))
            cal.update_layout(title="Observed event rate by tier", height=330, yaxis_title="share with event")
            g2.plotly_chart(cal, use_container_width=True)
            st.dataframe(tt, use_container_width=True)
            st.caption(f"Logistic slope of event on log(R): {cb['slope_log_R']:.2f}. R is a relative score, not a probability, "
                       "so this describes association strength, not calibration of absolute risk. Bars show Wilson 95% intervals.")
        else:
            st.info("No event/time columns found: showing per-patient trajectory summaries only.")
        if "by_stratum" in vp:
            st.markdown("**Discrimination by subgroup** (cancers are heterogeneous; a pooled C-index can hide a failing subgroup)")
            st.dataframe(vp["by_stratum"], use_container_width=True)
        st.dataframe(vp["patients"], use_container_width=True)
        st.download_button("Download per-patient results", vp["patients"].to_csv(index=False), "rmti_validation_patients.csv")
    except ValueError as e:
        st.error(str(e))

# ------------------------------------------------------------------ lung evidence and mapping
if domain == "lung":
    from oncology import lung_evidence as EV
    with T["Lung: evidence and mapping"]:
        st.subheader("Lung cancer in Oncoclastics: mapping and evidence")
        st.caption("Proposed extension, not part of the published RMTI papers. v2.3.0 definitions for an individual patient are used; each term is "
                   "assigned to the biological sense (L, E, V, ρ_bio) or the care-system sense (ρ_care).")
        st.markdown("""
| Term | Lung reading (proposed) | Sense |
|---|---|---|
| L | 5-year risk from a validated tool, rescaled to 0-1 (placeholder log anchors; pre-register) | biological |
| E | Cumulative exposure burden (magnitude, duration, frequency) not already in L | biological |
| V | Allostatic-load indicator count (below), not already in L | biological |
| ρ_bio | Biological reserve on the 0.10-0.70 ladder; lung descriptors still to be agreed | biological |
| ρ_care | Delivery of screening and follow-up, adherence, continuity | care-system |
| C | Stage-anchored severity, ordinal | outcome |
""")
        st.info("L is a 5-year risk. The UK Biobank model reports 2-year risk, so do not enter its output here without a justified conversion.")
        st.markdown("**No double counting.** Choose the tool that supplies L; any variable it already contains cannot be reused in E, V or ρ.")
        tool = st.selectbox("Tool supplying L", list(EV.L_TOOL_VARIABLES))
        vocab = sorted({v for vs in EV.L_TOOL_VARIABLES.values() for v in vs} | {i["variable"] for i in EV.V_ITEMS})
        used = st.multiselect("Variables already in that tool", vocab, default=EV.L_TOOL_VARIABLES[tool], key=f"vars_{tool}")
        clash = set(S.LUNG.overlap(used))
        ticked = []
        for it in EV.V_ITEMS:
            dis = it["label"] in clash
            if st.checkbox(it["label"] + ("  (already in L: not usable)" if dis else ""), key=f"v_{it['label']}", disabled=dis, help=it["source"]):
                ticked.append(it["label"])
        try:
            st.write(f"V indicator y = **{S.LUNG.v_indicator(ticked, used)} of {len(EV.V_ITEMS)}** (enter in the Trajectory tab). Items and mapping are uncalibrated proposals.")
        except ValueError as e:
            st.error(str(e))
        st.markdown("**Provisional ρ_bio ladder (ECOG-anchored; consensus still to do)**")
        st.dataframe(pd.DataFrame([{"ρ_bio": v, "level": n, "ECOG": e, "evidence grade": S.LUNG.RHO_BIO_LUNG_EVIDENCE[v], "descriptor": d} for v, n, e, d in reversed(S.LUNG.RHO_BIO_LUNG)]), use_container_width=True)
        st.caption("ECOG partly reflects disease already counted in V and saturates in screening populations (nearly everyone is 0-1). Ordering across all five levels is supported by Jang 2014 (mixed advanced cancers); the largest real-world cohort (Lee 2024) pools ECOG 3-4; the Vietnam stage III cohort supports only <2 versus >=2. Step sizes are NOT calibrated, and grades are reviewer-assigned. Do not score ECOG together with a V item that is a component of it.")

        st.markdown("#### Evidence base (peer-reviewed sources set every default)")
        st.dataframe(pd.DataFrame([{"status": e["status"], "source": e["cite"], "what it contributes": e["use"], "limits": e["limits"]} for e in EV.EVIDENCE]),
                     use_container_width=True)
        with st.expander("Findings used from each source"):
            for e in EV.EVIDENCE:
                st.markdown(f"**{e['status'].capitalize()}.** {e['cite']}  \n*Design:* {e['design']}  \n*Findings:* {e['findings']}")
        with st.expander("Supplementary sources (abstracts, secondary analyses: shown, never used for defaults)"):
            st.dataframe(pd.DataFrame([{"source": e["cite"], "findings": e["findings"], "limits": e["limits"]} for e in EV.EVIDENCE_SUPPLEMENTARY]), use_container_width=True)
        import registry as REG
        st.caption("Evidence registry %s. Parameters locked: %s. Every API response carries this stamp." % (REG.stamp(), REG.load()["parameters"]["locked"]))

        st.markdown("#### Face-validity check: ladder versus published adjusted hazard ratios")
        for chk in [c for nm in ("B", "A") for c in REG.ladder_face_validity(ladder=nm)]:
            st.caption("Ladder %s, %s: reference ECOG %d; the ladder cannot express a multiplier above %.2f. %s" % (chk["ladder"], chk["source"], chk["reference_ecog"], chk["ladder_max_multiplier"], chk["model"]))
            st.dataframe(pd.DataFrame(chk["levels"]), use_container_width=True)
        st.caption("Ladder B is derived from this source, so this source cannot validate it. Not calibration: R is not a hazard, values are assigned not estimated, and survival in patients with cancer is a different construct from reserve. Use it to decide the ladder before pre-registration.")

        st.markdown("#### Does a new cohort support each ρ_bio step?")
        st.write("Upload a de-identified file with columns ecog (0-4), time (>0) and event (0/1). The report is descriptive, unadjusted, stored nowhere, and changes no constant. Changes to the ladder are proposed and reviewed, never automatic.")
        up = st.file_uploader("Cohort CSV (pseudonymous)", type=["csv"], key="ladder_support_up")
        min_ev = st.number_input("Minimum events per level", 1, 1000, 10, key="ladder_support_min")
        if up is not None:
            try:
                dfc = S.privacy_check(pd.read_csv(up))
                rep = REG.ladder_support(dfc, min_events=int(min_ev))
                st.dataframe(pd.DataFrame(rep["levels"]), use_container_width=True)
                st.dataframe(pd.DataFrame(rep["steps"]), use_container_width=True)
                (st.success if rep["supports_five_levels"] else st.warning)(
                    "All four steps separate in this dataset." if rep["supports_five_levels"] else
                    "This dataset does not separate every step: keep those steps provisional. " + rep["note"])
            except Exception as ex:
                st.error(str(ex))

        st.markdown("#### Heterogeneity: suggested strata for the Validation tab")
        st.write("; ".join(EV.STRATA_SUGGESTED) + ". A pooled C-index can hide a subgroup in which the score fails, and risk tools built in one population need local recalibration before use in another.")

        st.markdown("#### Method demo: risk versus treatment and prognosis (RTP)")
        st.warning("SYNTHETIC placeholder anchors, invented to show the arithmetic. They are not from any study. Replace them with your own final values, privately.")
        anchors = {}
        for key, title in (("p_resection", "P(resection | early detection) at 5-year risk"), ("s5_resection", "Survival after resection at 5-year risk")):
            anchors[key] = st.data_editor(pd.DataFrame(S.RTP_DEMO_ANCHORS[key], columns=["risk5", "value"]), key=f"anc_{key}",
                                          num_rows="dynamic", use_container_width=True)
            st.caption(title)
        try:
            A = {k: [(float(r), float(v)) for r, v in zip(df["risk5"], df["value"])] for k, df in anchors.items()}
            curve = pd.DataFrame(S.rtp_curve(A))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=curve["risk"] * 100, y=curve["index"], name="With downstream terms", line=dict(color="#1F4E79", width=3)))
            fig.add_trace(go.Scatter(x=curve["risk"] * 100, y=curve["linear_reference"], name="Risk magnification (downstream held at lowest risk)",
                                     line=dict(color="#7F8FA6", dash="dash")))
            fig.update_layout(height=320, xaxis_title="5-year risk (%)", yaxis_title="risk × P(resection) × survival (illustrative)", legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Occurrence risk is not benefit: factors that raise risk can lower the chance of curative treatment. No extrapolation beyond the anchors; "
                       "stage shift, lead time, overdiagnosis and harms are ignored, so this is not a benefit estimate.")
        except (ValueError, TypeError, KeyError) as e:
            st.error(f"Check the anchor tables: {e}")

# ------------------------------------------------------------------ my cases
if auth:
    with T["My cases"]:
        st.subheader("My secure workspace")
        st.caption("Cases are encrypted with a key derived from your password. A forgotten password cannot be recovered by anyone, "
                   "including the server operator. Store pseudonymous labels only.")
        recs = VAULT.list_records(auth)
        if not recs:
            st.info("No saved cases yet. Use the 'Save this case' panel under Snapshot or Trajectory results.")
        for r in recs:
            with st.expander(f"{r['label']}  ·  {r['kind']}  ·  {time.strftime('%Y-%m-%d %H:%M', time.localtime(r['created']))}"):
                st.json(r["payload"])
                if st.button("Delete this case", key=f"del_{r['id']}"):
                    VAULT.delete_record(auth, r["id"]); st.rerun()
        if recs:
            st.download_button("Export all my cases (JSON)", VAULT.export_all(auth), "my_rmti_cases.json")
        with st.expander("Account"):
            old, new = st.text_input("Current password", type="password", key="pw_old"), st.text_input("New password", type="password", key="pw_new")
            if st.button("Change password"):
                try:
                    VAULT.change_password(auth, old, new); st.success("Password changed.")
                except VAULT.AuthError as e:
                    st.error(str(e))
            st.dataframe(pd.DataFrame(VAULT.audit_log(auth)), use_container_width=True)
            pw_del = st.text_input("Password to confirm deletion", type="password", key="pw_del")
            if st.button("Delete my account and all my cases"):
                try:
                    VAULT.delete_account(auth, pw_del); st.session_state.pop("auth"); st.rerun()
                except VAULT.AuthError as e:
                    st.error(str(e))

# ------------------------------------------------------------------ about
with tab_about:
    st.subheader("What this platform is and is not")
    st.markdown("""
- It scores relative risk with a fixed, pre-registered tier scale and tracks V(t) and ρ(t) across cycles. The model has **no tumour-size or imaging component**; for HCC the indicator is an allostatic-load composite and the resilience driver is surveillance adherence.
- Parameters (α, β, κ·H, λ, V anchors, ρ ceiling) are **uncalibrated placeholders**; examples are synthetic. Scores are not probabilities and not forecasts.
- It does not diagnose, stage or prescribe. Posture text describes surveillance-programme intensity for discussion by a clinical team.
- Whether trajectory adds information beyond a well-measured current level is an open hypothesis. The Validation tab compares final-cycle against baseline discrimination so the question can be tested on retrospective data.
- Do not enter names or identifying information. Real patient data require ethics review and data-use agreements. The practitioner workspace stores only pseudonymous, encrypted cases and is available only on servers that enable it.
- **Oncoclastics** (RMTI v2.3.0) is the application of hazard-exposure-vulnerability-resilience assessment, as developed in disaster-risk reduction, to the fragmentation of cancer-related trajectories, in two named senses: **biological** (L, E, V, ρ_bio) and **care-system** (ρ_care). It organizes existing predictors; it does not describe a therapy and does not imply destruction of tumour. **Disaster Science** is the other RMTI v2.3.0 domain.
- **Lung cancer** is a proposed Oncoclastics module. L is a 5-year risk from a validated tool, rescaled with placeholder log anchors on which the fixed tiers depend. Any variable already in that tool cannot be reused for E, V or ρ. Defaults come only from peer-reviewed sources listed in the module; unpublished manuscript figures are deliberately absent. Lung cancer is heterogeneous (smoking status, histology, sex, performance status, mutation status, ancestry), so use the subgroup table in the Validation tab and do not read a pooled result as universal.
- Engine: RMTI time-indexed v2.3.0 (Apache-2.0), vendored unchanged. Cite via the repository's CITATION.cff.
""")
