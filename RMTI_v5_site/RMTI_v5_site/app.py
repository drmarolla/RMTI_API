V1_VTT = """WEBVTT

00:00:00.000 --> 00:01:13.200
[Stage 1: Fibrosis F1–F3 | Marolla 2026, SSRN: 7427450]
R = L · E · V · (1 - ρ) = 0.15 · 0.60 · 0.35 · 0.80 = 0.025 (Tier 1: Low Urgency).

00:01:13.200 --> 00:02:26.400
[Stage 2: Cirrhosis F4 | Fan et al. aMAP; Sharma et al. THRI]
Annual HCC likelihood L jumps up to 10x (Untreated HBV: L = 0.90 -> R = 0.312, Tier 3 High).

00:02:26.400 --> 00:03:39.600
[Stage 3: Early HCC BCLC 0/A | RHO_ANCHORS_HCC: 0.15 -> 0.65]
Upgrading ultrasound + AFP cuts residual risk by 30% to 56% (>70% 5-year survival).

00:03:39.600 --> 00:04:52.800
[Stage 4: Portal Invasion BCLC B/C | Faria et al. ALBI Cohort, n = 54]
ALBI vulnerability rises (V = 0.522 vs 0.480, p = 0.025) -> R = 0.488 (Tier 4: Severe).

00:04:52.800 --> 00:06:06.000
[Stage 5: Metastasis BCLC D | EAL = L · C · (1 - ρ)]
Within-tier tie-breaker: Patient B (C = 1.00 -> EAL = 0.200) escalates ahead of Patient A (EAL = 0.072).
"""

V2_VTT = """WEBVTT

00:00:00.000 --> 00:00:14.000
[From Snapshot to Trajectory | Marolla 2026, RMTI-Py v2.5]
Time-indexed equation: R(t) = L(t) · E · V*(t) · [1 - ρ(t)] across 6-monthly cycles.

00:00:14.000 --> 00:00:29.000
[Unrounded Precision Engine | core/rmti_core.py]
IR_raw, R_raw, and EAL_raw resolve subtle per-cycle shifts (ΔR ≈ 0.001–0.010).

00:00:29.000 --> 00:00:44.000
[Steady-State Filter: α = 0.41, β = 0.09 | Patient A vs. B]
Patient B escalates R(0)=0.072 -> 0.178 (Tier 3 High); Patient A drops -> 0.022 (Tier 1 Low).

00:00:44.000 --> 00:01:15.000
[Synthetic Landmark Validation: N = 2,000, 2-Yr Horizon]
Filtered trajectory slope adds +0.015 to +0.022 AUROC over static baseline R(0) ≈ 0.55.
"""


@st.dialog("RMTI Clinical Case Studies & 3D Trajectory Models", width="large")
def case_study_dialog():
    v1_mp4 = _find_asset(os.path.join("assets", "videos", "video1_4stages_3d.mp4")) or f"{GITHUB_VIDEO_BASE}/video1_4stages_3d.mp4"
    v2_mp4 = _find_asset(os.path.join("assets", "videos", "video2_trajectory_3d.mp4")) or f"{GITHUB_VIDEO_BASE}/video2_trajectory_3d.mp4"

    tab1, tab2 = st.tabs([
        "Case Study 1: 4-Stage Liver Progression & Cohort Triage",
        "Case Study 2: Time-Indexed Trajectory R(t) & Kalman Filtering",
    ])

    with tab1:
        st.video(v1_mp4, subtitles=V1_VTT)
        st.markdown(
            "**Case & Data Sources:** [Marolla (2026) HCC Preprint (SSRN: 7427450)](https://ssrn.com) · "
            "Faria et al. ALBI Cohort (Harvard Dataverse, *n* = 54) · Singal et al. (2022) · Lau-Min et al. (*JAMA Netw Open* 2025). "
            "*Click **CC** in the player bar to toggle closed captions.*"
        )

    with tab2:
        st.video(v2_mp4, subtitles=V2_VTT)
        st.markdown(
            "**Case & Data Sources:** Marolla (2026) *From Snapshot to Trajectory* (`RMTI-Py v2.5`, Apache-2.0) · "
            "Synthetic 2-Year Landmark Surveillance Cohort (*N* = 2,000, α = 0.41, β = 0.09). "
            "*Click **CC** in the player bar to toggle closed captions.*"
        )
