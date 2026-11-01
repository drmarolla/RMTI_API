--- a/app.py.py (your current file)	2026-11-01 22:53:50.844405611 +0000
+++ b/app.py.py (patched)
@@ -57,12 +57,18 @@
 
 
 gate()
-read_csv = lambda f: S.privacy_check(pd.read_csv(f))   # every upload passes the identifier guard
+def _ascii_headers(df):
+    """Accept the Greek letter in file headers: ρ0 -> rho0, ρ_now -> rho_now, ρ_after -> rho_after. Engine and API field names stay ASCII."""
+    df.columns = [str(c).replace("ρ", "rho").replace("₀", "0") for c in df.columns]
+    return df
+
+
+read_csv = lambda f: S.privacy_check(_ascii_headers(pd.read_csv(f)))   # every upload passes the identifier guard
 
 # ------------------------------------------------------------------ header
 st.title("Oncoclastics Platform")
 st.caption(f"Risk Mechanism Theory Index (RMTI) · engine v{S.ENGINE_VERSION} · R = L · E · V · (1 − ρ)")
-st.warning(S.DISCLAIMER)
+BANNER = st.empty()      # filled once the domain is known, so the wording matches it
 
 FAMILIES = {"Oncoclastics (cancer)": "oncoclastics", "Disaster Science": "disaster_science"}
 family = FAMILIES[st.sidebar.radio("RMTI domain", list(FAMILIES))]
@@ -72,6 +78,16 @@
 else:
     domain = "disaster"
 lab = LABELS[domain]
+DIS = family == "disaster_science"      # medical wording belongs to the Oncoclastics domain only
+BANNER.warning("Research prototype. Not validated, not for emergency, safety or engineering decisions. Scores are relative, rubric-based indices, not forecasts, engineering assessments or actuarial figures. "
+               "Parameters are uncalibrated placeholders. Do not enter identifying data." if DIS else S.DISCLAIMER)
+VOC = (dict(unit="asset or area", units="Assets", ids="asset_id", sub="region, hazard type, building class...",
+            perm="Real data may need permission from the data owners", demo="Results mean nothing.",
+            het="subgroups can differ; a pooled C-index can hide a failing subgroup", dl="Download per-asset results")
+       if DIS else
+       dict(unit="patient", units="Patients", ids="patient_id", sub="smoking status, histology, sex...",
+            perm="This needs ethics approval and a data-use agreement for real data", demo="Results mean nothing clinically.",
+            het="cancers are heterogeneous; a pooled C-index can hide a failing subgroup", dl="Download per-patient results"))
 # ---- practitioner workspace (only when the server enables the vault) ----
 IDLE = 30 * 60
 if VAULT.vault_enabled():
@@ -100,7 +116,7 @@
     auth = st.session_state.get("auth")
 else:
     auth = None
-    st.sidebar.caption("Secure workspace is off on this deployment (public sandbox). Do not enter patient data here.")
+    st.sidebar.caption("Secure workspace is off on this deployment (public sandbox). Do not enter " + ("personal or sensitive data" if DIS else "patient data") + " here.")
 
 
 def save_case_ui(kind, payload, key):
@@ -129,8 +145,9 @@
 
 
 st.sidebar.markdown(
-    "**Who uses what**\n\n- Clinicians and nurses: Snapshot, Trajectory\n- Programme and disaster-risk managers: Cohort, Snapshot\n"
-    "- Researchers and climate scientists: Trajectory, Validation\n\nSession data stays in this browser session and is not stored.")
+    "**Who uses what**\n\n" + ("- Programme and disaster-risk managers: Cohort, Snapshot\n- Researchers and climate scientists: Trajectory, Validation" if DIS else
+                              "- Clinicians and nurses: Snapshot, Trajectory\n- Programme managers: Cohort, Snapshot\n- Researchers: Trajectory, Validation")
+    + "\n\nSession data stays in this browser session and is not stored.")
 
 names = (["Snapshot", "Trajectory", "Cohort ranking", "Retrospective validation"]
          + (["Lung: evidence and mapping"] if domain == "lung" else [])
@@ -147,7 +164,7 @@
     L = l_input(c1, "snap")
     E = c2.slider("E: exposure (share reached/affected)", 0.0, 1.0, 0.65, 0.01)
     V = c2.slider("V: vulnerability", 0.0, 1.0, 0.55, 0.01)
-    rho_now = c3.slider("ρ now: resilience / surveillance adequacy", 0.0, 0.99, 0.20, 0.01)
+    rho_now = c3.slider("ρ now: resilience / preparedness" if DIS else "ρ now: resilience / surveillance adequacy", 0.0, 0.99, 0.20, 0.01)
     use_after = c3.checkbox("Compare with an improved state", True)
     rho_after = c3.slider("ρ after", 0.0, 0.99, 0.50, 0.01) if use_after else None
     C = st.select_slider("C: consequence index (1 low … 5 severe)", [1, 2, 3, 4, 5], 5)
@@ -285,7 +302,7 @@
 # ------------------------------------------------------------------ cohort
 with tab_cohort:
     st.subheader("Rank a cohort or portfolio")
-    st.caption("Columns: name, N, L, E, V, rho_now, optional rho_after, C. Ranked by tier, then EAL; priority resets within each tier. "
+    st.caption("Columns: name, N, L, E, V, rho_now (ρ now), optional rho_after (ρ after), C; a Greek ρ in the header (ρ_now) also works. Ranked by tier, then EAL; priority resets within each tier. "
                "Use pseudonymous IDs only.")
     src = st.file_uploader("Upload CSV", type="csv", key="cohcsv")
     if src is not None:
@@ -310,20 +327,23 @@
 # ------------------------------------------------------------------ validation
 with tab_val:
     st.subheader("Retrospective validation on serial data")
-    st.caption("Long format, one row per patient per cycle: patient_id, cycle, y, optional delivery, L, E, C, rho0, and per patient "
-               "event (0/1) and time, and optionally a stratum column (smoking status, histology, sex...). Computes final-cycle and baseline R per patient, then discrimination and tier-wise event rates. "
-               "This needs ethics approval and a data-use agreement for real data; the example is synthetic.")
+    st.caption(f"Long format, one row per {VOC['unit']} per cycle: {VOC['ids']}, cycle, y, optional delivery, L, E, C, ρ₀ (file column rho0, or ρ0), and per {VOC['unit']} "
+               f"event (0/1) and time, and optionally a stratum column ({VOC['sub']}). Computes final-cycle and baseline R per {VOC['unit']}, then discrimination and tier-wise event rates. "
+               f"{VOC['perm']}; the example is synthetic.")
     vs = st.file_uploader("Upload serial CSV", type="csv", key="valcsv")
     if vs is not None:
         vdf = read_csv(vs)
     else:
-        vdf = S.example_serial(y_max=lab["ymax"])
-        st.info("Using SYNTHETIC demonstration data (outcome generated from an arbitrary rule). Results mean nothing clinically.")
+        vdf = (pd.read_csv(os.path.join(os.path.dirname(__file__), "sample_data", "synthetic_disaster_serial.csv")) if DIS
+               else S.example_serial(y_max=lab["ymax"]))
+        st.info(f"Using SYNTHETIC demonstration data (outcome generated from an arbitrary rule). {VOC['demo']}")
+    if DIS:   # the engine's identifier column is patient_id; disaster files may call it asset_id or area_id
+        vdf = vdf.rename(columns={"asset_id": "patient_id", "area_id": "patient_id"})
     try:
         vp = S.validate_serial(vdf, domain)
         if "c_index_final" in vp:
             k1, k2, k3, k4 = st.columns(4)
-            k1.metric("Patients / events", f"{vp['n']} / {vp['events']}")
+            k1.metric(f"{VOC['units']} / events", f"{vp['n']} / {vp['events']}")
             k2.metric("C-index, final cycle", f"{vp['c_index_final']:.3f}")
             k3.metric("C-index, baseline only", f"{vp['c_index_baseline']:.3f}")
             k4.metric("AUC final / baseline", f"{vp['auc_final']:.2f} / {vp['auc_baseline']:.2f}")
@@ -362,10 +382,11 @@
         else:
             st.info("No event/time columns found: showing per-patient trajectory summaries only.")
         if "by_stratum" in vp:
-            st.markdown("**Discrimination by subgroup** (cancers are heterogeneous; a pooled C-index can hide a failing subgroup)")
+            st.markdown(f"**Discrimination by subgroup** ({VOC['het']})")
             st.dataframe(vp["by_stratum"], use_container_width=True)
-        st.dataframe(vp["patients"], use_container_width=True)
-        st.download_button("Download per-patient results", vp["patients"].to_csv(index=False), "rmti_validation_patients.csv")
+        shown = vp["patients"].rename(columns={"patient_id": "asset_id"}) if DIS else vp["patients"]
+        st.dataframe(shown, use_container_width=True)
+        st.download_button(VOC["dl"], shown.to_csv(index=False), "rmti_validation_assets.csv" if DIS else "rmti_validation_patients.csv")
     except ValueError as e:
         st.error(str(e))
 
@@ -496,13 +517,25 @@
 # ------------------------------------------------------------------ about
 with tab_about:
     st.subheader("What this platform is and is not")
-    st.markdown("""
-- It scores relative risk with a fixed, pre-registered tier scale and tracks V(t) and ρ(t) across cycles. The model has **no tumour-size or imaging component**; for HCC the indicator is an allostatic-load composite and the resilience driver is surveillance adherence.
-- Parameters (α, β, κ·H, λ, V anchors, ρ ceiling) are **uncalibrated placeholders**; examples are synthetic. Scores are not probabilities and not forecasts.
-- It does not diagnose, stage or prescribe. Posture text describes surveillance-programme intensity for discussion by a clinical team.
-- Whether trajectory adds information beyond a well-measured current level is an open hypothesis. The Validation tab compares final-cycle against baseline discrimination so the question can be tested on retrospective data.
-- Do not enter names or identifying information. Real patient data require ethics review and data-use agreements. The practitioner workspace stores only pseudonymous, encrypted cases and is available only on servers that enable it.
-- **Oncoclastics** (RMTI v2.3.0) is the application of hazard-exposure-vulnerability-resilience assessment, as developed in disaster-risk reduction, to the fragmentation of cancer-related trajectories, in two named senses: **biological** (L, E, V, ρ_bio) and **care-system** (ρ_care). It organizes existing predictors; it does not describe a therapy and does not imply destruction of tumour. **Disaster Science** is the other RMTI v2.3.0 domain.
-- **Lung cancer** is a proposed Oncoclastics module. L is a 5-year risk from a validated tool, rescaled with placeholder log anchors on which the fixed tiers depend. Any variable already in that tool cannot be reused for E, V or ρ. Defaults come only from peer-reviewed sources listed in the module; unpublished manuscript figures are deliberately absent. Lung cancer is heterogeneous (smoking status, histology, sex, performance status, mutation status, ancestry), so use the subgroup table in the Validation tab and do not read a pooled result as universal.
-- Engine: RMTI time-indexed v2.3.0 (Apache-2.0), vendored unchanged. Cite via the repository's CITATION.cff.
-""")
+    ABOUT_SHARED = [
+        "It scores relative risk with a fixed, pre-registered tier scale and tracks V(t) and ρ(t) across cycles.",
+        "Parameters (α, β, κ·H, λ, V anchors, ρ ceiling) are **uncalibrated placeholders**; examples are synthetic. Scores are not probabilities and not forecasts.",
+        "Whether trajectory adds information beyond a well-measured current level is an open hypothesis. The Validation tab compares final-cycle against baseline discrimination so the question can be tested on retrospective data.",
+    ]
+    ABOUT_DEF = ["**Disaster Science** is an RMTI v2.3.0 domain: hazard-exposure-vulnerability-resilience assessment for climate, severe-weather and infrastructure risk. The other domain, **Oncoclastics**, applies the same logic to cancer trajectories."] if DIS else [
+        "**Oncoclastics** (RMTI v2.3.0) is the application of hazard-exposure-vulnerability-resilience assessment, as developed in disaster-risk reduction, to the fragmentation of cancer-related trajectories, in two named senses: **biological** (L, E, V, ρ_bio) and **care-system** (ρ_care). It organizes existing predictors; it does not describe a therapy and does not imply destruction of tumour. **Disaster Science** is the other RMTI v2.3.0 domain, for climate and severe-weather risk."]
+    ABOUT_ONC = [
+        "The model has **no tumour-size or imaging component**; for HCC the indicator is an allostatic-load composite and the resilience driver is surveillance adherence.",
+        "It does not diagnose, stage or prescribe. Posture text describes surveillance-programme intensity for discussion by a clinical team.",
+        "Do not enter names or identifying information. Real patient data require ethics review and data-use agreements. The practitioner workspace stores only pseudonymous, encrypted cases and is available only on servers that enable it.",
+        "**Lung cancer** is a proposed Oncoclastics module. L is a 5-year risk from a validated tool, rescaled with placeholder log anchors on which the fixed tiers depend. Any variable already in that tool cannot be reused for E, V or ρ. Defaults come only from peer-reviewed sources listed in the module; unpublished manuscript figures are deliberately absent. Lung cancer is heterogeneous (smoking status, histology, sex, performance status, mutation status, ancestry), so use the subgroup table in the Validation tab and do not read a pooled result as universal.",
+    ]
+    ABOUT_DIS = [
+        "For disaster, infrastructure and climate use, scores are relative, rubric-based indices, not forecasts, engineering assessments or actuarial figures; worked examples are teaching illustrations.",
+        "The disaster mapping (vulnerability indicator → V, programme delivery → ρ) is an extension proposed in this repository and is not part of the published RMTI papers.",
+        "Posture text is a reading of a research framework for discussion by the responsible programme team, not an instruction.",
+        "Do not enter personal or sensitive data. Real asset, infrastructure or community data may need permission from the data owners.",
+    ]
+    st.markdown("\n".join("- " + x for x in ABOUT_SHARED + (ABOUT_DIS if DIS else ABOUT_ONC[:3]) + ABOUT_DEF + ([] if DIS else ABOUT_ONC[3:])
+                           + ["Engine: RMTI time-indexed v2.3.0 (Apache-2.0), vendored unchanged. Cite via the repository's CITATION.cff."]))
+
