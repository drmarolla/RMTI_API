"""Case study library: one clear page that lists every case study, its sources and its video."""
import streamlit as st

import content
from engine import core
from rmti_ui import disclaimer, page_header
from views import home

CARDS = [
    ("liver", "Liver cancer · HCC", "From tumor events to trajectory", "Lau-Min et al., JAMA Netw Open 2025. Four tumor stages, ALBI-based vulnerability, second-line delivery as resilience, and the surveillance guidance behind HCC screening."),
    ("lung", "Lung cancer", "From tumor events to trajectory", "Sabakhtarishvili et al., JTO Clin Res Rep 2025. Screening delivery moves stage 4 at diagnosis from 35–44% to 13%."),
    ("breast", "Breast cancer", "From tumor events to trajectory", "O'Shaughnessy et al., Breast Cancer Res Treat 2026, with the GBD 2023 global burden data for context."),
    ("johnson", "HCC progression", "Pathway matters for surveillance", "Johnson et al., BJC Reports 2024. 2,592 patients followed for a median 13 years: cirrhosis is not an obligatory step to HCC."),
    ("urban", "Six African cities", "Infrastructure and health systems", "Marolla, IJMADA 2026. Tables 4 to 6 recomputed live and checked against the paper."),
    ("videos", "Video library", "Narrated walkthroughs", "Every video in the app folder, with closed captions where available."),
]


def render():
    page_header("Case studies", "Every worked example in one place. Each opens with its video, then the tumor stages, the RMTI assessment, the trajectory and the sources.", "Case studies")
    for i in range(0, len(CARDS), 3):
        cols = st.columns(3, gap="large")
        for col, (key, tag, title, body) in zip(cols, CARDS[i:i + 3]):
            with col:
                chips = ""
                if key in content.CASES:
                    c = content.CASES[key]
                    f = content.find_media(key)
                    chips = (f'<span class="r">{"▶ Video + captions" if f else "Video pending"}</span>'
                             f'<span class="r">R {c["r_before"]:.3f} → {c["r_after"]:.3f}</span><span class="r">{core.tier(c["r_before"]).split(" - ")[1]} → {core.tier(c["r_after"]).split(" - ")[1]}</span>')
                st.markdown(f'<div class="lib"><div class="tag">{tag}</div><h3>{title}</h3><p>{body}</p>{chips}</div>', unsafe_allow_html=True)
                if st.button("Open", key=f"lib_{key}", width="stretch", type="primary"):
                    st.switch_page(home.PAGES[key])
        st.write("")
    st.info("The same case studies are available to developers through the API: GET /v1/cases and GET /v1/cases/{slug}.")
    disclaimer()
