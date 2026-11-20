# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Single router for the whole site: grouped sidebar navigation, one disclaimer bar, one "Request API access" button, shared Plotly look.

Entry points (app.py.py and streamlit_app.py) just call rmti_nav.run(). With st.navigation the pages/ folder is not scanned,
so no raw file name (app.py) ever shows in the sidebar, and there is no second horizontal menu on any page.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
ORCID = "https://orcid.org/0000-0001-8498-7380"

# group -> [(file, title, material icon, url_path, shows the Evidence & Methodology panel)]
GROUPS = {
    "Overview": [
        ("Home.py", "Home", ":material/home:", None, False),
    ],
    "Clinical Calculators": [
        ("pages/0_Risk_Calculator.py", "Risk Calculator", ":material/calculate:", "Risk_Calculator", True),
        ("pages/1_HCC_Calculator.py", "HCC Calculator", ":material/medical_services:", "HCC_Calculator", True),
        ("pages/2_Cohort_Sandbox.py", "Cohort Sandbox", ":material/groups:", "Cohort_Sandbox", True),
    ],
    "Interactive Models": [
        ("pages/7_Live_Risk_Matrix.py", "Live Risk Matrix", ":material/tune:", "Live_Risk_Matrix", True),
        ("pages/3_4D_Risk_Matrix.py", "4D Risk Matrix", ":material/view_in_ar:", "4D_Risk_Matrix", True),
        ("pages/6_Live_4D_Lab.py", "Live 4D Lab", ":material/science:", "Live_4D_Lab", True),
        ("pages/7_Liver_Progression_4D.py", "Liver Progression 4D", ":material/timeline:", "Liver_Progression_4D", True),
    ],
    "Documentation & API": [
        ("pages/4_RMTI_Step_by_Step.py", "RMTI Step by Step", ":material/stairs:", "RMTI_Step_by_Step", False),
        ("pages/5_Case_Studies_and_Videos.py", "Case Studies & Videos", ":material/video_library:", "Case_Studies_and_Videos", False),
        ("pages/8_Johnson_Case_Study.py", "Johnson Case Study", ":material/menu_book:", "Johnson_Case_Study", False),
        ("pages/6_Developer_Portal.py", "Developer Portal", ":material/api:", "Developer_Portal", False),
    ],
}


def contact_email() -> str:
    """Set RMTI_CONTACT_EMAIL (environment variable or Streamlit secret) to enable the 'Send by email' button. Nothing is invented."""
    v = os.environ.get("RMTI_CONTACT_EMAIL", "").strip()
    if not v:
        try:
            v = str(st.secrets.get("RMTI_CONTACT_EMAIL", "")).strip()
        except Exception:  # noqa: BLE001  (no secrets file)
            v = ""
    return v


def access_request_text(name, org, email, role, use_case, scope) -> str:
    return (f"RMTI API access request\nName: {name}\nOrganisation: {org}\nEmail: {email}\nRole: {role}\n"
            f"Intended use: {use_case}\nScope: {scope}\n"
            "I confirm I will send only synthetic or published aggregate values, no patient-identifiable data.")


def _access_form() -> None:
    st.markdown("**Request API access.** Keys are issued by the maintainer after a short review. Nothing is sent from this page "
                "until you choose how to send it.")
    c1, c2 = st.columns(2)
    name = c1.text_input("Full name", key="rq_name")
    org = c2.text_input("Institution or company", key="rq_org")
    email = c1.text_input("Work email", key="rq_email")
    role = c2.selectbox("Role", ["Clinician", "Researcher", "Hospital IT / integrator", "Public health / emergency management", "Student", "Other"], key="rq_role")
    scope = st.multiselect("Endpoints needed", ["Snapshot", "Trajectory", "Cohort", "Validate", "HCC / lung inputs", "Two-sense", "FHIR RiskAssessment", "Registry"],
                           default=["Snapshot"], key="rq_scope")
    use_case = st.text_area("What will you build or study?", key="rq_use", height=90)
    ok = st.checkbox("I will not send patient-identifiable data to this service.", key="rq_ok")
    ready = bool(name and org and email and "@" in email and use_case and ok)
    if not ready:
        st.caption("Fill in every field and tick the box to continue.")
        return
    text = access_request_text(name, org, email, role, use_case, ", ".join(scope) or "Snapshot")
    st.code(text, language="text")
    to = contact_email()
    cols = st.columns(2)
    if to:
        url = f"mailto:{to}?subject={urllib.parse.quote('RMTI API access request')}&body={urllib.parse.quote(text)}"
        cols[0].link_button("Send by email", url, type="primary", use_container_width=True)
    else:
        cols[0].caption("Copy the text above (button at the top right of the box).")
    cols[1].link_button("Contact the author (ORCID)", ORCID, use_container_width=True)


def _open_access_dialog() -> None:
    dlg = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dlg is None:
        _access_form()
        return
    dlg("Request API access", width="large")(_access_form)()


def cta() -> None:
    """Persistent top-right button on every page. CSS (.st-key-rm_cta) pins it to the header."""
    with st.container(key="rm_cta"):
        if st.button("Request API access", key="rm_cta_btn"):
            _open_access_dialog()


def install_plot_theme() -> None:
    """Every st.plotly_chart gets the shared scientific look (fonts >= 13 px, visible grid, room on the right)."""
    cur = st.plotly_chart
    if getattr(cur, "_rm_wrapped", False):
        return

    def wrapped(fig, *a, **k):
        try:
            import ui_plot
            fig = ui_plot.style(fig)
        except Exception:  # noqa: BLE001
            pass
        return cur(fig, *a, **k)

    wrapped._rm_wrapped = True
    st.plotly_chart = wrapped


def run() -> None:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    orig = getattr(st, "_rmti_set_page_config", None) or st.set_page_config
    st._rmti_set_page_config = orig
    orig(page_title="Oncoclastics · RMTI", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")
    st.set_page_config = lambda *a, **k: None          # pages call it again; make that harmless

    import oncoclastic_style as ui
    import ui_clinical as uc

    st.session_state["rmti_nav"] = True                 # tells demo_mode / style.strip to stay quiet: the bar below is the only notice
    install_plot_theme()

    nav, evidence = {}, set()
    for group, items in GROUPS.items():
        pages = []
        for rel, title, icon, url, ev in items:
            if not (REPO / rel).exists():
                continue
            kw = {"default": True} if url is None else {"url_path": url}
            pages.append(st.Page(str(REPO / rel), title=title, icon=icon, **kw))
            if ev:
                evidence.add(title)
        if pages:
            nav[group] = pages

    pg = st.navigation(nav)
    with st.sidebar:
        st.caption(f"RMTI engine {ui.ENGINE_VERSION} · research prototype")
    is_home = pg.title == "Home"
    ui.apply(first_page=is_home)
    ui.disclaimer_bar()
    cta()
    pg.run()
    if pg.title in evidence:
        try:
            uc.evidence_expander()
        except Exception as e:  # noqa: BLE001
            st.caption(f"Evidence panel unavailable: {e}")
    ui.apply(first_page=is_home)                        # after the page, so the shared look wins over a page's own colours
