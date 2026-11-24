import streamlit as st

from rmti_ui import card, disclaimer, kpi

PAGES = {}   # filled by app.py


def go(key):
    if st.button("Open", key=f"open_{key}", width="stretch"):
        st.switch_page(PAGES[key])


def render():
    with st.container(border=True, key="hero"):
        left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<span class="pill">Risk intelligence · RMTI</span>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title">Quantify systemic risk.<br>Before it fragments care.</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-sub">The Risk Mechanism Theory Index applies hazard–exposure–vulnerability–resilience assessment '
                        'from disaster-risk reduction to clinical oncology, giving evidence-based triage across liver, lung and breast cancer.</div>',
                        unsafe_allow_html=True)
            b1, b2, _ = st.columns([1.2, 1.4, 0.5])
            if b1.button("Explore the tools", type="primary", width="stretch"):
                st.switch_page(PAGES["calc"])
            if b2.button("Watch the case study", width="stretch"):
                st.switch_page(PAGES["liver"])
        with right:
            st.markdown("""
<div class="diagram"><svg viewBox="0 0 280 210" width="100%" style="max-width:380px" role="img" aria-label="R equals L times E times V times one minus rho">
<ellipse cx="140" cy="100" rx="108" ry="74" fill="none" stroke="#CBD5E1" stroke-dasharray="4 4"/>
<ellipse cx="140" cy="100" rx="66" ry="46" fill="none" stroke="#CBD5E1" stroke-dasharray="4 4"/>
<circle cx="140" cy="100" r="26" fill="#BE123C"/><text x="140" y="107" text-anchor="middle" fill="#fff" font-weight="700" font-size="18">R</text>
<text x="140" y="140" text-anchor="middle" fill="#0F172A" font-size="11">Risk</text>
<circle cx="52" cy="40" r="19" fill="#2563EB"/><text x="52" y="46" text-anchor="middle" fill="#fff" font-weight="700" font-size="14">L</text>
<text x="52" y="72" text-anchor="middle" fill="#475569" font-size="11">Likelihood</text>
<circle cx="228" cy="40" r="19" fill="#BE123C"/><text x="228" y="46" text-anchor="middle" fill="#fff" font-weight="700" font-size="14">E</text>
<text x="228" y="72" text-anchor="middle" fill="#475569" font-size="11">Exposure</text>
<circle cx="52" cy="160" r="19" fill="#0F172A"/><text x="52" y="166" text-anchor="middle" fill="#fff" font-weight="700" font-size="14">V</text>
<text x="52" y="192" text-anchor="middle" fill="#475569" font-size="11">Vulnerability</text>
<circle cx="228" cy="160" r="19" fill="#93C5FD"/><text x="228" y="166" text-anchor="middle" fill="#0F172A" font-weight="700" font-size="14">ρ</text>
<text x="228" y="192" text-anchor="middle" fill="#475569" font-size="11">Resilience</text></svg>
<span class="formula">R = L · E · V · (1 − ρ)</span></div>""", unsafe_allow_html=True)
    st.write("")
    c = st.columns(4, gap="medium")
    for col, (n, l, a) in zip(c, [("4", "Levers in one unified framework", "red"), ("3", "Cancer sites: liver, lung, breast", "blue"),
                                  ("6", "Cities reproduced from the published paper", "navy"), ("5", "Fixed decision tiers, identical everywhere", "sky")]):
        col.markdown(kpi(n, l, a), unsafe_allow_html=True)
    st.write("")
    st.markdown("## Everything in one place")
    tiles = [("calc", "RMTI Calculator", "Score any asset or cohort, model an investment, rank a portfolio."),
             ("hccs", "HCC Surveillance Calculator", "Triage surveillance for a patient or the six published cohorts."),
             ("hcct", "HCC Treatment Calculator", "Evidence-gated regimen matching for stage 2 to 4 (sandbox)."),
             ("sandbox", "Cohort Sandbox", "Rank a synthetic or uploaded cohort and test scenarios."),
             ("models", "Interactive Tumor Models", "Rotate liver, lung and breast models through stages 1 to 4."),
             ("live", "Live Risk Matrix", "Tier maps that redraw as you move the levers."),
             ("m4d", "4D Risk Matrix", "Tier surfaces in 3D, animated across Exposure."),
             ("library", "Case Studies and Videos", "Liver, lung and breast videos with captions, HCC pathway, six African cities."),
             ("api", "Developer API", "Deterministic scoring for EHR and dashboard integration.")]
    for i in range(0, len(tiles), 3):
        cols = st.columns(3, gap="medium")
        for col, (k, t, b) in zip(cols, tiles[i:i + 3]):
            with col:
                st.markdown(card(t, b), unsafe_allow_html=True)
                go(k)
        st.write("")
    disclaimer()
