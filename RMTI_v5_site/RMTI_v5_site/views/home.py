"""Home view — Full-page dark cinematic video background (Visual Science style) + all RMTI tools & menus."""
import streamlit as st
import streamlit.components.v1 as components

PAGES = {}

RAW_VIDEOS = (
    "https://raw."
    "githubusercontent"
    ".com/"
    "drmarolla/RMTI_API/main/assets/videos"
)
RAW_ROOT = (
    "https://raw."
    "githubusercontent"
    ".com/"
    "drmarolla/RMTI_API/main"
)


def render():
    oncology_mp4 = f"{RAW_VIDEOS}/home_oncology.mp4"
    disaster_mp4 = f"{RAW_VIDEOS}/home_disaster.mp4"
    fallback_oncology = f"{RAW_VIDEOS}/video1_4stages_3d.mp4"
    fallback_disaster = f"{RAW_ROOT}/rmti_3_flood_heat_case_studies.mp4"

    # Full-page dark high-contrast theme over the fixed full-viewport video background
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: transparent !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            position: relative;
            z-index: 2;
        }
        /* Keep sidebar dark-frosted and legible over the full-page video */
        [data-testid="stSidebar"] {
            background: rgba(11, 17, 32, 0.90) !important;
            backdrop-filter: blur(14px);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        [data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }
        /* High-contrast typography across main page */
        .main h1, .main h2, .main h3, .main p, .main span, .main label, .main div {
            color: #F8FAFC;
        }
        .hero-wrap {
            padding: 36px 8px 28px 8px;
            max-width: 660px;
        }
        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }
        .hero-pill {
            background: #FFFFFF;
            color: #0F172A !important;
            font-size: 11.5px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 4px;
            letter-spacing: 0.25px;
        }
        .hero-pill.red {
            background: #DC2626;
            color: #FFFFFF !important;
        }
        .hero-pill.blue {
            background: #0284C7;
            color: #FFFFFF !important;
        }
        .hero-lead {
            color: #E2E8F0 !important;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 18px;
            max-width: 560px;
        }
        .hero-title {
            color: #FFFFFF !important;
            font-size: 52px;
            font-weight: 800;
            line-height: 1.06;
            letter-spacing: -0.03em;
            margin-bottom: 22px;
        }
        .hero-eq {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.30);
            backdrop-filter: blur(10px);
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        /* Frosted dark-glass cards so the moving background shines through cleanly */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(11, 17, 32, 0.78) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 12px !important;
        }
        [data-testid="stMetric"] {
            background: rgba(11, 17, 32, 0.78);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.22);
            padding: 14px 16px;
            border-radius: 12px;
        }
        [data-testid="stMetricValue"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stMetricDelta"] * {
            color: #38BDF8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inject full-viewport (100vw x 100vh) fixed rotating video background into parent document
    components.html(
        f"""
        <script>
        (function() {{
          const doc = window.parent.document;
          let bg = doc.getElementById('rmti-fullpage-bg');
          if (!bg) {{
            bg = doc.createElement('div');
            bg.id = 'rmti-fullpage-bg';
            bg.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:0;background:#0B1120;overflow:hidden;pointer-events:none;';
            bg.innerHTML = `
              <video id="rmti-bg-onc" autoplay loop muted playsinline
                style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right center;opacity:1;transition:opacity 1.5s ease-in-out;">
                <source src="{oncology_mp4}" type="video/mp4">
                <source src="{fallback_oncology}" type="video/mp4">
              </video>
              <video id="rmti-bg-dis" autoplay loop muted playsinline
                style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right center;opacity:0;transition:opacity 1.5s ease-in-out;">
                <source src="{disaster_mp4}" type="video/mp4">
                <source src="{fallback_disaster}" type="video/mp4">
              </video>
              <div style="position:absolute;inset:0;background:linear-gradient(90deg, rgba(11,17,32,0.95) 0%, rgba(11,17,32,0.84) 38%, rgba(11,17,32,0.36) 72%, rgba(11,17,32,0.14) 100%);"></div>
              <div style="position:absolute;inset:0;background:linear-gradient(180deg, rgba(11,17,32,0.45) 0%, rgba(11,17,32,0.15) 45%, rgba(11,17,32,0.88) 100%);"></div>
            `;
            doc.body.prepend(bg);

            let showOnc = true;
            setInterval(() => {{
              const vO = doc.getElementById('rmti-bg-onc');
              const vD = doc.getElementById('rmti-bg-dis');
              if (!vO || !vD) return;
              showOnc = !showOnc;
              vO.style.opacity = showOnc ? '1' : '0';
              vD.style.opacity = showOnc ? '0' : '1';
            }}, 9000);
          }}
        }})();
        </script>
        """,
        height=0,
    )

    # Visual Science Style Left-Aligned Hero Copy over the Full-Page Rotating Video
    st.markdown(
        """
        <div class="hero-wrap">
          <div class="hero-pills">
            <span class="hero-pill">Risk Intelligence • RMTI</span>
            <span class="hero-pill blue">Disaster Science</span>
            <span class="hero-pill red">Clinical Oncology</span>
            <span class="hero-pill">Deterministic FHIR API</span>
          </div>
          <p class="hero-lead">
            The Risk Mechanism Theory Index applies hazard–exposure–vulnerability–resilience assessment from
            disaster-risk reduction to clinical oncology, giving evidence-based triage across liver, lung,
            breast cancer, and urban climate resilience.
          </p>
          <div class="hero-title">Quantify systemic risk.<br>Before it fragments care.</div>
          <div class="hero-eq">
            <span>R = <span style="color:#38BDF8;">L</span> · <span style="color:#F87171;">E</span> · <span style="color:#FBBF24;">V</span> · (1 − <span style="color:#34D399;">ρ</span>)</span>
            <span style="color:#64748B;">|</span>
            <span style="color:#CBD5E1;font-weight:500;">Live Rotating 3D Oncology &amp; Disaster Models</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Primary Hero Action Buttons
    c1, c2, c3, _ = st.columns([1.6, 1.8, 1.8, 3.8])
    if c1.button("Explore the tools", type="primary", use_container_width=True, key="hero_explore"):
        if "calc" in PAGES:
            st.switch_page(PAGES["calc"])
    if c2.button("Disaster case studies", use_container_width=True, key="hero_disaster"):
        if "urban" in PAGES:
            st.switch_page(PAGES["urban"])
    if c3.button("Oncology case studies", use_container_width=True, key="hero_oncology"):
        if "liver" in PAGES:
            st.switch_page(PAGES["liver"])

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # 4-Column Metric Strip
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Unified framework", "R = L·E·V·(1−ρ)", "Disaster & Oncology")
    m2.metric("Cancer cohorts", "Liver, Lung, Breast", "BCLC & ALBI calibrated")
    m3.metric("Urban resilience", "Six African cities", "Flood & heat stress")
    m4.metric("Clinical integration", "HL7 FHIR R4", "Deterministic tiers 1–4")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.subheader("Everything in one place")

    cards = [
        ("RMTI Calculator", "Score any asset or cohort, model an investment, rank a portfolio.", "calc"),
        ("HCC Surveillance Calculator", "Triage surveillance for a patient or the six published cohorts.", "hccs"),
        ("HCC Treatment Calculator", "Evidence-gated regimen matching for stage 0 to D.", "hcct"),
        ("Cohort Sandbox", "Rank a synthetic or uploaded cohort and test scenarios.", "sandbox"),
        ("Interactive Tumor Models", "Rotate liver, lung, and breast models through stages 1 to 4.", "models"),
        ("Live Risk Matrix", "Tier maps that redraw as you move the levers.", "live"),
        ("4D Risk Matrix", "Tier surfaces in 3D, animated across Exposure.", "m4d"),
        ("Case Studies and Videos", "Liver, lung, breast videos with captions, HCC pathway, six African cities.", "library"),
        ("Developer API", "Deterministic scoring for EHR and dashboard integration.", "api"),
    ]

    for row_start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, (title, desc, page_key) in zip(cols, cards[row_start:row_start + 3]):
            with col.container(border=True):
                st.markdown(f"**{title}**")
