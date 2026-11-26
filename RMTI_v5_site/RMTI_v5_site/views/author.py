import streamlit as st
from rmti_ui import disclaimer, page_header

LINKS = [
    ("Google Scholar", "".join(["https://scholar.", "://google.com"])),
    ("ORCID", "".join(["https://orcid.", "org/0000-0001-8498-7380"])),
    ("Biography", "".join(["https://cesar-marolla.", "owlstown.net/"])),
    ("LinkedIn", "".join(["https://www.linkedin.", "com/in/cesarmarolla/"])),
    ("Harvard ENVR E-241", "".join(["https://coursebrowser.dce.", "harvard.edu/course/risk-by-design-building-resilience-into-urban-infrastructure/"])),
]

ITEMS = [
    ("Books", "#1E3A5F", [
        ("Climate Health Risks in Megacities", "2019", "CRC Press / Taylor & Francis", "".join(["https://www.taylorfrancis.", "com/books/edit/10.1201/9781315367323/climate-health-risks-megacities-cesar-marolla"])),
        ("ICT for Sustainable Development", "2018", "CRC Press / Taylor & Francis", "".join(["https://www.taylorfrancis.", "com/books/mono/10.1201/9781351045230/information-communication-technology-sustainable-development-cesar-marolla"])),
        ("Sub-Saharan Africa Resilience Compendium", "2023", "World Bank Group", "".join(["https://documents1.worldbank.", "org/curated/en/099063023110515444/pdf/P17647608a63280090a413018d9b339c4e8.pdf"])),
    ]),
    ("Articles", "#0284C7", [
        ("From Narrative to Algorithm (RMTI)", "2026", "IJMADA 6(1): 354–388", "".join(["https://ijmada.", "com/index.php/ijmada/article/view/156"])),
        ("California Wildfires & Urban Resilience", "2025", "IJMADA / Cambridge", "".join(["https://scholar.", "://google.com"])),
        ("Urban Flood & Business Continuity", "2024", "Cambridge University Press", "".join(["https://scholar.", "://google.com"])),
        ("Urban Climate Health Risks", "2024", "Harvard DASH Repository", "".join(["https://dash.harvard.", "edu/entities/publication/fbf2f10b-b179-442a-836c-94dffd6564c1"])),
    ]),
    ("Preprints", "#DC2626", [
        ("RMTI for HCC Surveillance Triage", "2026", "SSRN (7427450)", "".join(["https://papers.ssrn.", "com/sol3/papers.cfm?abstract_id=7427450"])),
        ("RMTI for Urban Infrastructure (Preprint)", "2026", "SSRN (7707038)", "".join(["https://papers.ssrn.", "com/sol3/papers.cfm?abstract_id=7707038"])),
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
    disclaimer()

def bio_page():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0B1120,#1E293B);border:1px solid #334155;border-radius:16px;padding:24px 28px;margin-bottom:16px;color:#F8FAFC;">
      <div style="font-size:11px;font-weight:800;letter-spacing:1px;color:#38BDF8;">CREATOR OF THE RISK MECHANISM THEORY INDEX (RMTI)</div>
      <div style="font-size:30px;font-weight:900;color:#FFFFFF;margin:4px 0 8px 0;">Prof. Dr. Cesar Marolla, PhD, ALM</div>
      <div style="font-size:14.5px;color:#CBD5E1;line-height:1.6;">
        Quantitative risk scientist, educator, and author with 20+ years bridging urban climate resilience, disaster-risk reduction, and clinical oncology triage. Correspondence: cesar.marolla@alumni.harvard.edu
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(LINKS))
    for col, (lbl, url) in zip(cols, LINKS):
        col.link_button(lbl, url, use_container_width=True, type="primary")

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Risk Research", "20+ Years", "Climate & Health Systems")
    k2.metric("Graduate Teaching", "Harvard & Nalanda", "ENVR E-241 & MBA")
    k3.metric("Global Advisory", "World Bank Group", "Sub-Saharan Africa")
    k4.metric("Keynote Forums", "UN COP 23 & HMS", "Global Health Symposia")

    st.write("")
    left, right = st.columns((1.1, 1.0), gap="large")
    with left:
        st.subheader("Academic & Advisory Appointments")
        for org, role, desc in [
            ("Harvard University (DCE)", "Instructor · ENVR E-241: Risk by Design (2026–Present)", "Teaches quantitative Risk Mechanism Design using World Bank and MIT-Jameel urban shock models."),
            ("World Bank Group", "Lead Author · Sub-Saharan Africa Urban Resilience", "Authored the urban infrastructure resilience compendium and validated RMTI across six African cities."),
            ("Nalanda University", "Visiting Professor · Sustainable Urbanization MBA", "Delivers graduate instruction on disaster governance, climate adaptation, and equitable health systems."),
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
            ("International Scientific Keynotes", "Speaker at UN COP 23, Harvard Medical School, Harvard Global Health Institute, and University of Miami."),
            ("Parallel Musical Career — Guitarist & Composer", "Featured in Guitar Encyclopedia (2004); released Rhythm of Fire (Columbia/Sony), recorded with Berlin and London Philharmonic musicians, and toured for Armed Forces Entertainment / USO."),
        ]:
            with st.container(border=True):
                st.markdown(f"**{ttl}**")
                st.write(desc)

    disclaimer()

