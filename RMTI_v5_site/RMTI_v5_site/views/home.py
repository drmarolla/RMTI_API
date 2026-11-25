"""Home view — Full-page dark cinematic video background + psychoacoustic ambient audio toggle + high-contrast RMTI cards."""
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

    st.markdown(
        """
        <style>
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: transparent !important;
        }
        [data-testid="stMain"], [data-testid="stAppViewContainer"] > .main {
            position: relative !important;
            z-index: 5 !important;
            background: transparent !important;
        }
        [data-testid="stSidebar"] {
            background: rgba(11, 17, 32, 0.92) !important;
            backdrop-filter: blur(14px);
            border-right: 1px solid rgba(148, 163, 184, 0.22);
            z-index: 6 !important;
        }
        [data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] p,
        [data-testid="stMain"] strong,
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] strong {
            color: #FFFFFF !important;
        }
        [data-testid="stMain"] [data-testid="stCaptionContainer"] p,
        [data-testid="stMain"] small {
            color: #CBD5E1 !important;
            opacity: 1 !important;
        }
        .hero-wrap {
            padding: 28px 4px 12px 4px;
            max-width: 680px;
        }
        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
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
            margin-bottom: 16px;
            max-width: 560px;
        }
        .hero-title {
            color: #FFFFFF !important;
            font-size: 50px;
            font-weight: 800;
            line-height: 1.06;
            letter-spacing: -0.03em;
            margin-bottom: 18px;
        }
        [data-testid="stMetric"] {
            background: rgba(11, 17, 32, 0.84) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.28) !important;
            padding: 14px 16px;
            border-radius: 12px;
        }
        [data-testid="stMetricLabel"] * {
            color: #94A3B8 !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetricValue"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(15, 23, 42, 0.86) !important;
            backdrop-filter: blur(14px);
            border: 1px solid rgba(148, 163, 184, 0.30) !important;
            border-radius: 12px !important;
            padding: 6px !important;
            transition: border-color 0.2s ease, transform 0.2s ease;
        }
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #38BDF8 !important;
        }
        [data-testid="stMain"] .stButton > button[kind="secondary"] {
            background: #F8FAFC !important;
            color: #0F172A !important;
            border: 1px solid #FFFFFF !important;
            font-weight: 700 !important;
            opacity: 1 !important;
            cursor: pointer !important;
        }
        [data-testid="stMain"] .stButton > button[kind="secondary"] * {
            color: #0F172A !important;
        }
        [data-testid="stMain"] .stButton > button[kind="secondary"]:hover {
            background: #0284C7 !important;
            border-color: #0284C7 !important;
            color: #FFFFFF !important;
        }
        [data-testid="stMain"] .stButton > button[kind="secondary"]:hover * {
            color: #FFFFFF !important;
        }
        [data-testid="stMain"] .stButton > button[kind="primary"] {
            background: #DC2626 !important;
            border-color: #DC2626 !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }
        [data-testid="stMain"] .stButton > button[kind="primary"] * {
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Full-viewport fixed rotating video background at z-index: -1
    components.html(
        f"""
        <script>
        (function() {{
          const doc = window.parent.document;
          let bg = doc.getElementById('rmti-fullpage-bg');
          if (!bg) {{
            bg = doc.createElement('div');
            bg.id = 'rmti-fullpage-bg';
            bg.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;background:#0B1120;overflow:hidden;pointer-events:none;';
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

    # Left-Aligned Hero Copy
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
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Equation Bar + Discreet Muted-By-Default Psychoacoustic Ambient Soundscape (64 BPM Major-9th Synth)
    components.html(
        """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
          body { background: transparent; overflow: hidden; }
          .bar {
            display: inline-flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 14px;
            background: rgba(15, 23, 42, 0.86);
            border: 1px solid rgba(148, 163, 184, 0.35);
            backdrop-filter: blur(10px);
            padding: 10px 18px;
            border-radius: 10px;
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 700;
          }
          .sound-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.95);
            color: #CBD5E1;
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
          }
          .sound-btn:hover { border-color: #38BDF8; color: #FFFFFF; }
