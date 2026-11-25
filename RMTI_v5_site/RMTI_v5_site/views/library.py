"""Case study library: separated into Oncology Case Studies and Disaster Science Case Studies."""
import streamlit as st

import content
from engine import core
from rmti_ui import disclaimer, page_header
from views import home

ONCOLOGY_CARDS = [
    ("liver", "Liver cancer · HCC", "From tumor events to trajectory", "Lau-Min et al., JAMA Netw Open 2025. Four tumor stages, ALBI-based vulnerability, second-line delivery as resilience, and the surveillance guidance behind HCC screening."),
    ("lung", "Lung cancer", "From tumor events to trajectory", "Sabakhtarishvili et al., JTO Clin Res Rep 2025. Screening delivery moves stage 4 at diagnosis from 35–44% to 13%."),
    ("breast", "Breast cancer", "From tumor events to trajectory", "O'Shaughnessy et al., Breast Cancer Res Treat 2026, with the GBD 2023 global burden data for context."),
    ("johnson", "HCC progression", "Pathway matters for surveillance", "Johnson et al., BJC Reports 2024. 2,592 patients followed for a median 13 years: cirrhosis is not an obligatory step to HCC."),
]

DISASTER_CARDS = [
    ("urban", "Six African cities", "Urban infrastructure & climate resilience", "Marolla, IJMADA 2026. Live recomputation of Tables 4 to 6 across Bamako, Lagos, Lilongwe, and partner cities under flood and heat stress."),
]

MEDIA_CARDS = [
    ("videos", "Video library", "Narrated walkthroughs", "Every narrated framework and domain video in the repository, with closed captions."),
]


def _render_card_grid(cards):
    for i in range(0, len(cards), 3):
        cols = st.columns(3, gap="large")
        for col, (key, tag, title, body) in zip(cols, cards[i:i + 3]):
            with col:
                chips = ""
                if key in content.CASES:
                    c = content.CASES[key]
                    chips = (
                        '<span class="r">▶ 3D Studio Animation + Captions</span>'
                        f'<span class="r">R {c["r_before"]:.3f} → {c["r_after"]:.3f}</span>'
                        f'<span class="r">{core.tier(c["r_before"]).split(" - ")[1]} → {core.tier(c["r_after"]).split(" - ")[1]}</span>'
                    )
                elif key == "urban":
                    chips = '<span class="r">▶ 3D Studio Animation</span><span class="r">6 Cities · Tables 4–6</span>'
                st.markdown(f'<div class="lib"><div class="tag">{tag}</div><h3>{title}</h3><p>{body}</p>{chips}</div>', unsafe_allow_html=True)
                if st.button("Open", key=f"lib_{key}", width="stretch", type="primary"):
                    st.switch_page(home.PAGES[key])
        st.write("")


def render():
    page_header(
        "Case studies",
        "Worked examples organized across Clinical Oncology and Disaster Science—each opening with its bright-studio 3D animation, followed by quantitative RMTI scoring, trajectories, and peer-reviewed sources.",
        "Case studies",
    )

    st.subheader("Oncology Case Studies")
    st.caption("Solid-tumor progression, screening delivery, ALBI reserve, and trajectory modeling across liver, lung, and breast cohorts.")
    _render_card_grid(ONCOLOGY_CARDS)

    st.divider()

    st.subheader("Disaster Science Case Studies")
    st.caption("Urban climate hazard, infrastructure exposure, health-system vulnerability, and resilience investment prioritization.")
    _render_card_grid(DISASTER_CARDS)

    st.divider()

    st.subheader("Narrated Walkthroughs & Media Archive")
    _render_card_grid(MEDIA_CARDS)

    st.info("The same case studies are available to developers through the API: GET /v1/cases and GET /v1/cases/{slug}.")
    disclaimer()
