"""Static content: published cohorts, case-study text, anchors. No code is ever shown to visitors."""
import glob
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---- six Sub-Saharan African cities (Marolla 2026, IJMADA 6(1):354-388, Tables 4-6) ------------------------------
SIX_CITIES = {
    "Bamako": dict(N=4_500_000, L=0.800, E_sel=0.850, V=0.750, rho_now=0.20, rho_after=0.58, C=4,
                   country="Mali", hazard="Drought / Niger River flood / heatwave", asset="Urban healthcare network"),
    "Lagos": dict(N=16_000_000, L=0.900, E_sel=0.650, V=0.800, rho_now=0.20, rho_after=0.55, C=5,
                  country="Nigeria", hazard="Coastal and pluvial flood", asset="Mass-transit corridors"),
    "Lilongwe": dict(N=1_100_000, L=0.875, E_sel=0.800, V=0.800, rho_now=0.25, rho_after=0.48, C=4,
                     country="Malawi", hazard="Pluvial / riverine flood", asset="Drainage and utility networks"),
    "Nairobi": dict(N=4_700_000, L=0.900, E_sel=0.880, V=0.550, rho_now=0.55, C=4,
                    country="Kenya", hazard="Pluvial flood", asset="Comparator"),
    "Dar es Salaam": dict(N=7_400_000, L=0.850, E_sel=0.930, V=0.780, rho_now=0.55, C=4,
                          country="Tanzania", hazard="Coastal flood", asset="Comparator"),
    "Lusaka": dict(N=3_360_000, L=0.800, E_sel=0.850, V=0.720, rho_now=0.45, C=3,
                   country="Zambia", hazard="Flood and cholera", asset="Comparator"),
}
SIX_CITIES_PUBLISHED = {  # R_now, R_after as printed in the paper
    "Bamako": (0.408, 0.214), "Lagos": (0.374, 0.211), "Lilongwe": (0.420, 0.291),
    "Nairobi": (0.196, None), "Dar es Salaam": (0.277, None), "Lusaka": (0.269, None)}

# ---- anchors used by the HCC workbook (Reference tab) ---------------------------------------------------------------
HCC_L_ANCHORS = {"Untreated HBV (historical, ~12.8%/yr)": 0.90, "Active viral cirrhosis (2-7%/yr)": 0.55,
                 "Alcohol cirrhosis (1-2.5%/yr)": 0.30, "Cured-HCV cirrhosis (~1.8%/yr)": 0.25,
                 "Suppressed HBV (~1.25%/yr)": 0.20, "NAFLD / MASLD cirrhosis (~1.0%/yr)": 0.15}
HCC_RHO_ANCHORS = {"No / ad-hoc surveillance (uptake <20%)": 0.15, "Usual care (population)": 0.20,
                   "Structured outreach and navigation": 0.45, "Regular specialist hepatology": 0.50,
                   "Optimised (US + AFP + access)": 0.65}
BCLC_C = {"BCLC 0 - very early (C=1)": 1, "BCLC A - early (C=2)": 2, "Early-intermediate (C=3)": 3,
          "BCLC B - intermediate (C=4)": 4, "BCLC C-D - advanced (C=5)": 5}
C_NAMES = {1: "Insignificant", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Severe"}

# ---- cancer case studies (from Dr. Marolla's reading scripts; mapping is illustrative) ------------------------------
CASES = {
    "liver": dict(
        title="Liver cancer", icon=":material/water_drop:",
        study="Lau-Min and colleagues, JAMA Network Open, 2025",
        finding="Among 4,198 patients on systemic therapy, median survival was 8.1 months and only 20.7% reached second-line treatment.",
        stages=[("Stage 1", "One small tumor inside the liver, no vessel invasion. Surgery, ablation or transplant can work."),
                ("Stage 2", "The tumor reaches blood vessels, or several small tumors form, still within the liver."),
                ("Stage 3", "Larger or multiple tumors, major vein invasion, and possibly regional lymph nodes."),
                ("Stage 4", "Cells reach distant sites such as the lungs and bones. Treatment turns systemic.")],
        mapping=[("Vulnerability (V)", "Liver function, by ALBI grade"), ("Exposure (E)", "Concomitant liver disease"),
                 ("Resilience (rho)", "Second-line delivery, only 20.7%")],
        r_before=0.081, r_after=0.025, change="as delivery improves"),
    "lung": dict(
        title="Lung cancer", icon=":material/air:",
        study="Sabakhtarishvili and colleagues, JTO Clinical and Research Reports, 2025",
        finding="Among 3,647 screened people, stage 4 at diagnosis was 13%, versus 35 to 44% under usual care.",
        stages=[("Stage 1", "A small tumor confined to the lung, with no lymph node spread."),
                ("Stage 2", "A larger tumor, or nearby lymph nodes are involved."),
                ("Stage 3", "Spread to central chest lymph nodes or neighboring structures."),
                ("Stage 4", "Distant metastasis, for example to the brain or bone.")],
        mapping=[("Exposure (E)", "Smoking burden"), ("Likelihood (L)", "Two-year cancer detection rate"),
                 ("Resilience (rho)", "Screening delivery, which lowers late-stage presentation")],
        r_before=0.098, r_after=0.044, change="as screening improves"),
    "breast": dict(
        title="Breast cancer", icon=":material/favorite:",
        study="O'Shaughnessy and colleagues, Breast Cancer Research and Treatment, 2026",
        finding="Among 5,041 women with metastatic HR-positive breast cancer, survival after first post-endocrine chemotherapy was 13.5 months and 30% died before a second-line regimen.",
        stages=[("Stage 1", "A small invasive tumor, with lymph nodes clear or minimally involved."),
                ("Stage 2", "A larger tumor, or involvement of axillary lymph nodes."),
                ("Stage 3", "Extensive nodal disease, or spread to the chest wall or skin."),
                ("Stage 4", "Distant metastasis, for example to bone or liver.")],
        mapping=[("Likelihood (L)", "Prior CDK4/6 inhibitor use"), ("Vulnerability (V)", "Performance status and metastatic burden"),
                 ("Resilience (rho)", "The 30% who die before second line")],
        r_before=0.054, r_after=0.023, change="as the delivery gap closes"),
}

# ---- Johnson et al., BJC Reports 2024 (Ogaki cohort) -----------------------------------------------------------------
JOHNSON = dict(n=2592, hcc=172, via_cirrhosis=124, no_cirrhosis=48, no_cirr_share=0.28,
               hbv_total=29, hbv_direct=20, hcv_total=131, hcv_noncirr=25, rate_noncirr=5, rate_cirr=31,
               svr_hcc=23, svr_nohcc=802, na_n=229, na_hcc=18)


def _roots():
    seen, out = set(), []
    for base in (ROOT, os.path.dirname(ROOT)):
        for sub in ("", "media", "videos", "static", "rmti_videos and script"):
            p = os.path.join(base, sub)
            if p not in seen and os.path.isdir(p):
                seen.add(p)
                out.append(p)
    return out


def all_videos():
    out, seen = [], set()
    for folder in _roots():
        for ext in (".mp4", ".webm", ".mov"):
            for f in sorted(glob.glob(os.path.join(folder, "*" + ext))):
                if f not in seen and os.path.getsize(f) > 2048:      # skips Git-LFS pointer files
                    seen.add(f)
                    out.append(f)
    return out


def find_media(*keywords):
    for f in all_videos():
        name = os.path.basename(f).lower()
        if all(k in name for k in keywords):
            return f
    return None


def find_captions(video_path):
    base = os.path.splitext(video_path)[0]
    for ext in (".vtt", ".srt"):
        if os.path.exists(base + ext):
            return base + ext
    return None


# ---- references (peer-reviewed unless marked) ------------------------------------------------------------------------
IJMADA = ("Marolla C. From Narrative to Algorithm: a Risk Mechanism Theory Index for urban infrastructure investment in Sub-Saharan Africa. "
          "Int J Manag Data Anal 2026;6(1):354-388.", "https://doi.org/10.68485/ijmada.20266156", "Peer-reviewed")
REFS = {
    "liver": [("Lau-Min KS et al. JAMA Network Open 2025 (published case study used in the video).", None, "Peer-reviewed"),
              ("Johnson PJ, Kalyuzhnyy A, Boswell E, Toyoda H. Progression of chronic liver disease to hepatocellular carcinoma: implications for surveillance and management. BJC Reports 2024.", "https://doi.org/10.1038/s44276-024-00050-0", "Peer-reviewed"),
              ("Singal AG et al. AASLD Practice Guidance on prevention, diagnosis, and treatment of hepatocellular carcinoma. Hepatology 2023;78:1922-65.", "https://pubmed.ncbi.nlm.nih.gov/37199193/", "Guidance"),
              ("Singal AG et al. HCC surveillance improves early detection, curative treatment receipt, and survival in patients with cirrhosis: a meta-analysis. J Hepatol 2022;77:128-139.", "https://pubmed.ncbi.nlm.nih.gov/35139400/", "Peer-reviewed"),
              ("Kim HN. Surveillance for hepatocellular carcinoma (Lesson 6). Hepatitis C Online, University of Washington, updated April 2024.", "https://www.hepatitisc.uw.edu/go/evaluation-staging-monitoring/surveillance-hepatocellular-carcinoma/core-concept/all", "Educational resource"),
              IJMADA,
              ("Marolla C. The Risk Mechanism Theory Index as a triage and evidence-grading layer for HCC surveillance. SSRN 7427450.", "https://ssrn.com/abstract=7427450", "Preprint, not peer reviewed")],
    "lung": [("Sabakhtarishvili et al. JTO Clinical and Research Reports 2025 (published case study used in the video).", None, "Peer-reviewed"), IJMADA],
    "breast": [("O'Shaughnessy et al. Breast Cancer Research and Treatment 2026 (published case study used in the video).", None, "Peer-reviewed"),
               ("GBD 2023 Breast Cancer Collaborators. Global, regional, and national burden of breast cancer among females, 1990-2023, with forecasts to 2050. Lancet Oncol 2026;27:302-326.", None, "Peer-reviewed"),
               IJMADA],
}
for _k, _v in REFS.items():
    CASES[_k]["refs"] = _v

# ---- GBD 2023 breast cancer (Lancet Oncol 2026;27:302-326) --------------------------------------------------------------
GBD_BREAST = dict(cases_m=2.30, deaths_k=764, dalys_m=24.1, cases_2050_m=3.56, deaths_2050_m=1.37,
                  groups=["High income", "Upper-middle", "Lower-middle", "Low income"],
                  asir=[75.7, 37.3, 39.3, 44.2], asmr=[16.3, 11.2, 19.6, 24.1], asmr_change=[-29.9, -11.9, 72.6, 99.3])

# ---- HCC surveillance guidance, summarised from AASLD 2023 as presented by UW Hepatitis C Online -------------------------
HCC_GUIDE = dict(
    facts=[("Who", "All adults with cirrhosis of any cause. Routine surveillance is not advised after HCV cure in advanced fibrosis without cirrhosis, but continues after cure when cirrhosis is present."),
           ("How often and how", "Abdominal ultrasound plus serum AFP about every 6 months. Six-monthly screening finds more very early tumours than yearly screening."),
           ("If something is found", "A nodule under 1 cm: repeat every 3 months, returning to 6-monthly if stable for 2 years. A nodule over 1 cm: multiphasic CT or MRI."),
           ("Why delivery matters", "In a large US veterans cohort of HCV cirrhosis, only 12.0% had routine surveillance, 58.5% inconsistent and 29.5% none."),
           ("After HCV cure", "DAA therapy lowers HCC risk by 71 to 79% in advanced fibrosis or cirrhosis, but does not remove it. Surveillance continues."),
           ("Outcome stakes", "US 5-year survival with HCC is about 22%, and under 10% when found after symptoms. Very early disease can be cured.")],
    tests=[("Ultrasound, any stage", "60–80%", ">90%"), ("Ultrasound, early stage", "45–60%", "n/a"), ("AFP alone (HCV)", "47–64%", "82–95%")],
)
