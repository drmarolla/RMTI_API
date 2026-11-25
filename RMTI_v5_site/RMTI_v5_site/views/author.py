"""Books, Peer-Reviewed Papers, Preprints, and Author Biography / CV."""
import streamlit as st
from rmti_ui import disclaimer, page_header

PROFILE = {
    "name": "Cesar Marolla, PhD, ALM",
    "tagline": "Risk Mechanism Theory Index (RMTI) · Disaster-Risk Reduction, Climate Resilience & Clinical Oncology Triage",
    "email": "cesar.marolla@alumni.harvard.edu",
    "links": [
        ("Academic Website", "https://owlstown.net"),
        ("Google Scholar", "https://google.com"),
        ("Harvard DASH", "https://harvard.edu"),
        ("ORCID", "https://orcid.org"),
        ("LinkedIn", "https://linkedin.com"),
    ],
    "summary": (
        "Dr. Cesar Marolla is a researcher, educator, and systems risk architect bridging disaster-risk reduction, "
        "urban infrastructure resilience, and quantitative clinical oncology triage. He is the creator of the Risk "
        "Mechanism Theory Index (RMTI), decomposing systemic risk across likelihood (L), exposure (E), vulnerability (V), and resilience (ρ)."
    ),
    "appointments": [
        ("Harvard University", "Instructor, Division of Continuing Education", "Teaching ENVR E-241: Risk by Design: Building Resilience into Urban Infrastructure."),
        ("Nalanda University", "Visiting Professor, Sustainable Urbanization & Development MBA", "Graduate instruction on resilient urban systems, climate adaptation, and sustainable development."),
        ("World Bank Group", "Lead Author & Consultant, Sub-Saharan Africa Urban Investment Resilience Program", "Authored engineering and investment resilience frameworks for infrastructure project design across Sub-Saharan Africa."),
    ],
    "education": [
        ("PhD", "Glasgow Caledonian University"),
        ("ALM (Master of Liberal Arts)", "Harvard University"),
        ("BSc (Cum Laude)", "Columbia College"),
        ("Executive Education Certificate — Sustainability Leadership", "Harvard T.H. Chan School of Public Health"),
    ],
    "honors": [
        ("Derek Bok Civic Award (2013)", "Harvard University (Commencement Committee) — Recognized for outstanding public impact, creative community initiatives, and civic achievement."),
        ("Commander's Challenge Coin & Commendation (2004)", "U.S. Department of Defense (395th QM BN) — Awarded by Lt. Colonel L. Smith for exceptional civilian performance during the Global War on Terror (GWOT)."),
    ],
}

BOOKS = [
    ("Climate Health Risks in Megacities: Sustainable Management and Strategic Planning", "2019", "CRC Press / Taylor & Francis", "Disaster & Climate Health", "https://taylorfrancis.com", "Compounding climate hazards, urban air pollution (1–10 ppb), and health-system vulnerability in megacities."),
    ("Information and Communication Technology for Sustainable Development", "2018", "CRC Press / Taylor & Francis", "Systems & Digital Resilience", "https://taylorfrancis.com", "Sustainability assessments, digital infrastructure governance, and operational resilience frameworks."),
    ("Climate Resilient Investment in Sub-Saharan Africa Compendium Volume", "2023", "World Bank Group (Lead Author & Consultant)", "Infrastructure Resilience", "https://worldbank.org", "Technical compendium operationalizing climate-resilient infrastructure project design across Sub-Saharan Africa."),
]
PAPERS = [
    ("From Narrative to Algorithm: A Risk Mechanism Theory Index for Urban Infrastructure Investment in Sub-Saharan Africa", "2026", "IJMADA 6(1): 354–388", "Disaster Science & RMTI", "https://ijmada.com", "Formalizes the deterministic RMTI scoring algorithm and EAL tie-breaker across six Sub-Saharan African cities."),
    ("California Wildfires: A Holistic Systemic Management Approach to Urban Resilience", "2025", "Cambridge University Press", "Disaster Science", "https://cambridge.org", "Systemic wildfire degradation, psychological health threats, and integrated risk-governance strategies."),
    ("Urban Flood Resilience: Risk and Business Continuity Management Systems Strategic Approach", "2024", "Cambridge University Press", "Disaster Science", "https://cambridge.org", "Integrates ISO business continuity management with urban hydrological flood resilience planning."),
    ("ICT Transformation in Healthcare: A Risk-Based Approach for Climate Adaptation in LMICs", "2024", "Cambridge University Press", "Digital Health", "https://cambridge.org", "Risk-based health IT framework to buffer LMIC healthcare delivery systems against climate surges."),
    ("Urban Climate Health Risks and Resilience", "2024", "Harvard DASH Repository", "Climate Health", "https://harvard.edu", "Evaluates clinical and public-health system vulnerabilities driven by urban heat islands."),
    ("The Dynamics of Global Risks: Sociopolitical Risks in Strategic Management and Policy Decisions", "2023", "Developments in Managing and Exploiting Risk (OAPEN)", "Risk Governance", "https://oapen.org", "Examines cascading sociopolitical and systemic hazards in strategic policy design."),
    ("Climate Change Impacts on Health: The Urban Poor in the World's Megacities", "2020", "Harvard DASH Repository", "Climate Equity", "https://harvard.edu", "Investigates disproportionate climate-health exposure among low-income urban populations."),
    ("Health in the Digital World", "2020", "Harvard DASH Repository", "Digital Health", "https://harvard.edu", "Analyzes health information technology adoption and digital resilience across clinical care systems."),
    ("Leading Through Uncertainty", "2018", "The Routledge Companion to Risk, Crisis and Security in Business", "Risk Management", "https://taylorfrancis.com", "Executive decision-making and institutional resilience under high-uncertainty hazard landscapes."),
]

PREPRINTS = [
    ("The Risk Mechanism Theory Index (RMTI) as a Triage and Evidence-Grading Layer for Hepatocellular-Carcinoma Surveillance", "2026", "SSRN (7427450) & Research Square", "Clinical Oncology · HCC", "https://ssrn.com", "Computable, HL7 FHIR-compatible triage and surveillance-adequacy (ρ) grading model across HCC cohorts."),
    ("From Narrative to Algorithm: RMTI for Urban Infrastructure Investment in Sub-Saharan Africa (Preprint)", "2026", "SSRN (7707038)", "Disaster Science", "https://ssrn.com", "Working paper establishing mathematical derivation, sensitivity bounds, and equity-weighted EAL ranking."),
    ("Risk Mechanism Theory and its Relation to Risk Management and Sustainable Development", "Foundational", "ResearchGate Working Monograph", "Foundational Theory", "https://researchgate.net", "Foundational theoretical paper defining Risk Mechanism Theory and sustainable development."),
]


def _cards(items, color):
    for title, yr, venue, dom, url, desc in items:
        with st.container(border=True):
            c1, c2 = st.columns([4.5, 1.2])
            with c1:
                st.markdown(f'<span style="background:{color};color:#FFF;font-size:11px;font-weight:800;padding:2px 8px;border-radius:4px;">{dom} · {yr}</span>', unsafe_allow_html=True)
                st.markdown(f"#### {title}")
                st.caption(venue)
                st.write(desc)
            with c2:
                st.write("")
                st.link_button("Open", url, use_container_width=True, type="primary")


def publications_page():
    page_header("Books, Peer-Reviewed Papers & Preprints", "Monographs, World Bank compendiums, peer-reviewed articles, and preprints by Dr. Cesar Marolla.", "Publications & Author")
    t1, t2, t3 = st.tabs([f"Books & Compendiums ({len(BOOKS)})", f"Peer-Reviewed Articles & Chapters ({len(PAPERS)})", f"Preprints & Theory ({len(PREPRINTS)})"])
    with t1:
        _cards(BOOKS, "#1E3A5F")
    with t2:
        _cards(PAPERS, "#0284C7")
    with t3:
        _cards(PREPRINTS, "#DC2626")
    st.info("To add more books or papers later, simply add a new tuple line to BOOKS, PAPERS, or PREPRINTS in `views/author.py`.")
    disclaimer()


def bio_page():
    page_header(PROFILE["name"], PROFILE["tagline"], "Publications & Author")
    cols = st.columns(len(PROFILE["links"]))
    for col, (lbl, url) in zip(cols, PROFILE["links"]):
        col.link_button(lbl, url, use_container_width=True)
    st.write("")
    with st.container(border=True):
        st.subheader("Research & Interdisciplinary Overview")
        st.write(PROFILE["summary"])
        st.caption(f"Correspondence: {PROFILE['email']}")
    st.subheader("Academic & Institutional Leadership")
    acols = st.columns(3, gap="medium")
    for col, (org, role, det) in zip(acols, PROFILE["appointments"]):
        with col.container(border=True):
            st.markdown(f"**{org}**")
            st.caption(role)
            st.write(det)
    st.write("")
    cl, cr = st.columns(2, gap="large")
    with cl:
        st.subheader("Education & Executive Credentials")
        for deg, inst in PROFILE["education"]:
            with st.container(border=True):
                st.markdown(f"**{deg}**")
                st.caption(inst)
    with cr:
        st.subheader("Honors & Commendations")
        for ttl, desc in PROFILE["honors"]:
            with st.container(border=True):
                st.markdown(f"**{ttl}**")
                st.write(desc)
    disclaimer()
    with st.container(border=True):
        st.subheader("Research & Interdisciplinary Overview")
        st.write(PROFILE["summary"])
        st.caption(f"Correspondence: {PROFILE['email']}")
    st.subheader("Academic & Institutional Leadership")
    acols = st.columns(3, gap="medium")
    for col, (org, role, det) in zip(acols, PROFILE["appointments"]):
        with col.container(border=True):
            st.markdown(f"**{org}**")
            st.caption(role)
            st.write(det)
    st.write("")
    cl, cr = st.columns(2, gap="large")
    with cl:
        st.subheader("Education & Executive Credentials")
        for deg, inst in PROFILE["education"]:
            with st.container(border=True):
                st.markdown(f"**{deg}**")
                st.caption(inst)
    with cr:
        st.subheader("Honors & Commendations")
        for ttl, desc in PROFILE["honors"]:
            with st.container(border=True):
                st.markdown(f"**{ttl}**")
                st.write(desc)
    disclaimer()
