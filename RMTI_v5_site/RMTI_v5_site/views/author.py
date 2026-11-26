import streamlit as st
from rmti_ui import disclaimer, page_header

SCHOLAR_URL = "".join(["https://scholar.", "://google.com", chr(38), "hl=en"])
LINKS = [
    ("Google Scholar", SCHOLAR_URL),
    ("ORCID", "".join(["https://orcid.", "org/0000-0001-8498-7380"])),
    ("Biography", "".join(["https://cesar-marolla.", "owlstown.net/"])),
    ("LinkedIn", "".join(["https://www.linkedin.", "com/in/cesarmarolla/"])),
    ("Harvard ENVR E-241", "".join(["https://coursebrowser.dce.", "harvard.edu/course/risk-by-design-building-resilience-into-urban-infrastructure/"])),
]


ITEMS = [
    ("Books", "#1E3A5F", [
        ("Urban Megacity Health Risks", "2019", "CRC Press", "https://taylorfrancis.com"),
        ("ICT for Sustainable Development", "2018", "CRC Press", "https://taylorfrancis.com"),
        ("Sub-Saharan Urban Resilience Compendium", "2023", "World Bank", "https://worldbank.org"),
    ]),
    ("Articles", "#0284C7", [
        ("From Narrative to Algorithm (RMTI)", "2026", "IJMADA 6(1)", "https://ijmada.com"),
        ("California Wildfires & Urban Resilience", "2025", "IJMADA", SCHOLAR_URL),
        ("Urban Flood & Continuity Systems", "2024", "Cambridge", SCHOLAR_URL),
        ("Urban Environmental Health Resilience", "2024", "Harvard DASH", "https://harvard.edu"),
    ]),
    ("Preprints", "#DC2626", [
        ("RMTI for HCC Surveillance Triage", "2026", "SSRN 7427450", "https://ssrn.com"),
        ("RMTI for Urban Infrastructure", "2026", "SSRN 7707038", "https://ssrn.com"),
    ]),
]


def publications_page():
    page_header("Books, Peer-Reviewed Work & Preprints", "Selected monographs, World Bank reports, and articles.", "Publications & Author")
    tabs = st.tabs([f"{grp} ({len(rows)})" for grp, _, rows in ITEMS])
    for tab, (_, clr, rows) in zip(tabs, ITEMS):
        with tab:
            for title, yr, venue, url in rows:
                with st.container(border=True):
                    c1, c2 = st.columns((4.5, 1.1))
                    c1.markdown(f'<span style="background:{clr};color:#FFF;font-size:11px;font-weight:800;padding:2px 8px;border-radius:4px;">{yr}</span> **{title}** — *{venue}*', unsafe_allow_html=True)
                    c2.link_button("Open", url, use_container_width=True, type="primary")
    disclaimer

def bio_page():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#FFFFFF 0%,#F8FAFC 100%);border:1px solid #E2E8F0;border-left:6px solid #0284C7;border-radius:14px;padding:22px 26px;margin-bottom:16px;box-shadow:0 4px 16px rgba(15,23,42,0.04);">
      <div style="font-size:11px;font-weight:800;letter-spacing:0.9px;color:#0284C7;">PRINCIPAL INVESTIGATOR &amp; ARCHITECT · RISK MECHANISM THEORY INDEX (RMTI)</div>
      <div style="font-size:28px;font-weight:900;color:#0F172A;margin:4px 0 8px 0;">Prof. Dr. Cesar Marolla, PhD, ALM</div>
      <div style="font-size:14.5px;color:#334155;line-height:1.65;">
        Quantitative risk scientist, educator, and author with over 20 years of experience bridging urban infrastructure resilience, disaster-risk reduction, and clinical oncology triage. Correspondence: cesar.marolla@alumni.harvard.edu
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(LINKS))
    for col, (lbl, url) in zip(cols, LINKS):
        col.link_button(lbl, url, use_container_width=True, type="primary")

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Risk Research", "20+ Years", "Urban & Health Systems")
    k2.metric("Graduate Teaching", "Harvard & Nalanda", "ENVR E-241 & MBA")
    k3.metric("Global Advisory", "World Bank Group", "Sub-Saharan Africa")
    k4.metric("Invited Forums", "UN & Harvard Medical", "Global Health Symposia")

    st.write("")
    left, right = st.columns((1.1, 1.0), gap="large")
    with left:
        st.subheader("Academic & Advisory Appointments")
        for org, role, desc in [
            ("Harvard University (DCE)", "Instructor · ENVR E-241: Risk by Design (2026–Present)", "Teaches quantitative Risk Mechanism Design using World Bank and MIT-Jameel urban shock models."),
            ("World Bank Group", "Lead Author · Sub-Saharan Africa Urban Resilience", "Authored the urban infrastructure resilience compendium and validated RMTI across six African cities."),
            ("Nalanda University", "Visiting Professor · Sustainable Urbanization MBA", "Delivers graduate instruction on disaster governance, extreme-weather adaptation, and equitable health systems."),
        ]:
            with st.container(border=True):
                st.markdown(f"**{org}** — *{role}*")
                st.write(desc)

        st.subheader("Education & Credentials")
        with st.container(border=True):
            st.markdown(
                "- **PhD**, Computing, Engineering & Built Environment — Glasgow Caledonian University\n"
                "- **ALM**, Sustainability & Environmental Management — Harvard University\n"
                "- **Executive Certificate**, Sustainability Leadership — Harvard T.H. Chan School of Public Health\n"
                "- **BSc (Cum Laude)** — Columbia College"
            )

    with right:
        st.subheader("Honors, Keynotes & Arts")
        for ttl, desc in [
            ("Derek Bok Civic Prize Award (2013)", "Awarded by the Harvard Commencement Committee for community service and civic impact."),
            ("U.S. Department of Defense Commendations (2004–2005)", "Commander's Challenge Coin (395th QM BN) and U.S. Army Central Command certificates (Qatar & Kuwait)."),
            ("International Scientific Keynotes", "Speaker at UN global forums, Harvard Medical School, Harvard Global Health Institute, and University of Miami."),
            ("Parallel Musical Career — Guitarist & Composer", "Featured in Guitar Encyclopedia (2004); released Rhythm of Fire (Columbia/Sony), recorded with Berlin and London Philharmonic musicians, and toured for Armed Forces Entertainment / USO."),
        ]:
            with st.container(border=True):
                st.markdown(f"**{ttl}**")
                st.write(desc)

    disclaimer()

