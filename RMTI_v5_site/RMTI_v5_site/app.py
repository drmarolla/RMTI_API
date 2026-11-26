"""Risk Mechanism Theory Index (RMTI) - entry point.   streamlit run app.py"""
import base64
import streamlit as st
from engine import APP_TITLE
from rmti_ui import inject_css
from views import author, calculator, cases, developer_api, docs, hcc_surveillance, hcc_treatment, home, library, live_matrix, matrix4d, models3d, sandbox, urban_cases

st.set_page_config(page_title=APP_TITLE, page_icon=":material/monitoring:", layout="wide", initial_sidebar_state="expanded")
inject_css()

_NS = "".join(["http://", "www.w3.", "org/2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<circle cx="32" cy="32" r="20" fill="none" stroke="rgba(255,255,255,0.28)" stroke-width="1" stroke-dasharray="4 3"/>'
    '<rect x="20" y="28" width="5.5" height="16" rx="2.5" fill="#93C5FD"/>'
    '<rect x="29.25" y="19" width="5.5" height="25" rx="2.5" fill="#38BDF8"/>'
    '<rect x="38.5" y="23" width="5.5" height="21" rx="2.5" fill="#FFFFFF"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" letter-spacing="1.4" fill="#FFFFFF">RMTI</text>'
    '<text x="69" y="45" font-family="Arial, sans-serif" font-weight="700" font-size="9.5" letter-spacing="0.6" fill="#E2E8F0">RISK MECHANISM</text>'
    '<text x="69" y="56" font-family="Arial, sans-serif" font-weight="700" font-size="9.5" letter-spacing="0.6" fill="#93C5FD">THEORY INDEX</text>'
    '</svg>'
)
st.logo("data:image/svg+xml;base64," + base64.b64encode(_SVG.encode()).decode(), size="large")
st.markdown("""
<style>
@keyframes rmtiPulse {
  0%, 100% { filter: drop-shadow(0 0 3px rgba(56,189,248,0.35)); }
  50% { filter: drop-shadow(0 0 8px rgba(56,189,248,0.75)); }
}
[data-testid="stSidebarHeader"] { padding-top: 10px !important; padding-bottom: 10px !important; }
[data-testid="stSidebarHeader"] img, [data-testid="stLogo"] {
  height: 54px !important; width: auto !important; max-width: 245px !important;
  cursor: pointer !important; transition: transform 0.25s ease, filter 0.25s ease !important;
  animation: rmtiPulse 4s ease-in-out infinite;
}
[data-testid="stSidebarHeader"] img:hover, [data-testid="stLogo"]:hover {
  transform: scale(1.06) !important;
  filter: drop-shadow(0 0 14px rgba(56,189,248,1)) drop-shadow(0 0 4px rgba(255,255,255,0.8)) !important;
}
</style>
""", unsafe_allow_html=True)


def P(fn, title, icon, slug, default=False):
    return st.Page(fn, title=title, icon=f":material/{icon}:", url_path=slug, default=default)


RAW_BASE = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets"])

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

00:00:00.000 --> 00:00:18.000
[From Snapshot to Trajectory | Marolla 2026, RMTI-Py v2.5]
Time-indexed equation: R(t) = L(t) · E · V*(t) · [1 - ρ(t)] across 6-monthly cycles.

00:00:18.000 --> 00:00:38.000
[Unrounded Precision Engine | core/rmti_core.py]
IR_raw, R_raw, and EAL_raw resolve subtle per-cycle shifts (ΔR ≈ 0.001–0.010).

00:00:38.000 --> 00:01:02.000
[Steady-State Filter: α = 0.41, β = 0.09 | Patient A vs. B]
Patient B escalates R(0)=0.072 -> 0.178 (Tier 3 High); Patient A drops -> 0.022 (Tier 1 Low).

00:01:02.000 --> 00:01:25.000
[Synthetic Landmark Validation: N = 2,000, 2-Yr Horizon]
Filtered trajectory slope adds +0.015 to +0.022 AUROC over static baseline R(0) ≈ 0.55.
"""


@st.dialog("RMTI Clinical Case Studies & 3D Trajectory Models", width="large")
def case_study_dialog():
    v1_mp4 = f"{RAW_BASE}/videos/video1_4stages_3d.mp4?v=7"
    v2_mp4 = f"{RAW_BASE}/videos/video2_trajectory_3d.mp4?v=7"
    v2_mp3 = f"{RAW_BASE}/raw/video2_trajectory_voice.mp3.mp3"
    tab1, tab2 = st.tabs([
        "Case Study 1: 4-Stage Liver Progression & Cohort Triage",
        "Case Study 2: Time-Indexed Trajectory R(t) & Kalman Filtering",
    ])
    with tab1:
        st.video(v1_mp4, subtitles=V1_VTT)
        st.markdown("**Case & Data Sources:** [Marolla (2026) HCC Preprint (SSRN: 7427450)](https://ssrn.com) · Faria et al. ALBI Cohort (*n* = 54) · Singal et al. (2022) · Lau-Min et al. (*JAMA Netw Open* 2025).")
    with tab2:
        st.video(v2_mp4, subtitles=V2_VTT)
        st.audio(v2_mp3)
        st.markdown("**Case & Data Sources:** Marolla (2026) *From Snapshot to Trajectory* (`RMTI-Py v2.5`) · Synthetic 2-Year Landmark Cohort (*N* = 2,000, α = 0.41, β = 0.09).")


PG = {
    "home": P(home.render, "Home", "home", "home", True),
    "calc": P(calculator.render, "RMTI Calculator", "calculate", "rmti-calculator"),
    "hccs": P(hcc_surveillance.render, "HCC Surveillance Calculator", "monitor_heart", "hcc-surveillance"),
    "hcct": P(hcc_treatment.render, "HCC Treatment Calculator", "medication", "hcc-treatment"),
    "sandbox": P(sandbox.render, "Cohort Sandbox", "folder_open", "cohort-sandbox"),
    "models": P(models3d.render, "Interactive Tumor Models", "deployed_code", "tumor-models"),
    "live": P(live_matrix.render, "Live Risk Matrix", "grid_view", "live-risk-matrix"),
    "m4d": P(matrix4d.render, "4D Risk Matrix", "view_in_ar", "4d-risk-matrix"),
    "library": P(library.render, "All case studies", "library_books", "case-studies"),
    "liver": P(cases.liver, "Liver cancer (HCC)", "water_drop", "case-liver"),
    "lung": P(cases.lung, "Lung cancer", "air", "case-lung"),
    "breast": P(cases.breast, "Breast cancer", "favorite", "case-breast"),
    "johnson": P(cases.johnson_page, "HCC pathway (Johnson)", "timeline", "case-hcc-pathway"),
    "lagos": P(urban_cases.lagos, "Lagos, Nigeria", "location_city", "case-lagos"),
    "lilongwe": P(urban_cases.lilongwe, "Lilongwe, Malawi", "water", "case-lilongwe"),
    "bamako": P(urban_cases.bamako, "Bamako, Mali", "local_hospital", "case-bamako"),
    "nairobi": P(urban_cases.nairobi, "Nairobi, Kenya", "alt_route", "case-nairobi"),
    "dar": P(urban_cases.dar_es_salaam, "Dar es Salaam, Tanzania", "directions_boat", "case-dar"),
    "lusaka": P(urban_cases.lusaka, "Lusaka, Zambia", "layers", "case-lusaka"),
    "urban": P(urban_cases.synthesis_page, "Six-City Synthesis & 3D Axis", "3d_rotation", "case-urban"),
    "videos": P(cases.videos_page, "Video library", "movie", "video-library"),
    "pubs": P(author.publications_page, "Books & Peer-Reviewed Work", "auto_stories", "publications"),
    "bio": P(author.bio_page, "Author Biography & CV", "person", "author-biography"),
    "method": P(docs.method, "Method and tiers", "functions", "method"),
    "steps": P(docs.steps, "Step by step", "checklist", "step-by-step"),
    "refs": P(docs.references, "References and disclaimer", "menu_book", "references"),
    "api": P(developer_api.render, "Developer API", "code", "developer-api"),
}
home.PAGES = PG
pg = st.navigation({
    "": [PG["home"]],
    "Clinical calculators": [PG["calc"], PG["hccs"], PG["hcct"]],
    "Research tools": [PG["sandbox"]],
    "Interactive models": [PG["models"], PG["live"], PG["m4d"]],
    "Case studies": [PG["library"], PG["videos"]],
    "Oncology case studies": [PG["liver"], PG["lung"], PG["breast"], PG["johnson"]],
    "Disaster science case studies": [PG["lagos"], PG["lilongwe"], PG["bamako"], PG["nairobi"], PG["dar"], PG["lusaka"], PG["urban"]],
    "Publications & Author": [PG["pubs"], PG["bio"]],
    "Documentation": [PG["method"], PG["steps"], PG["refs"]],
    "Platform": [PG["api"]],
})
_, b0, b1, b2 = st.columns([3, 2, 1.5, 2])
if b0.button("Watch the case study", width="stretch", key="top_case"):
    case_study_dialog()
if b1.button("Developer API", width="stretch", key="top_dev"):
    st.switch_page(PG["api"])
if b2.button("Request API access", type="primary", width="stretch", key="top_req"):
    developer_api.request_access_dialog()
pg.run()
