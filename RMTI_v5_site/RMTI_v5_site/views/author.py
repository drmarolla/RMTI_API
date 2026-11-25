"""Publications, Books, Preprints, and Author Biography / CV views."""
import streamlit as st
import publications_data as pub
from rmti_ui import disclaimer, page_header


def _render_pub_cards(items, badge_color="#0284C7"):
    for item in items:
        with st.container(border=True):
            c1, c2 = st.columns([4.5, 1.2])
            with c1:
                st.markdown(
                    f'<span style="background:{badge_color};color:#FFFFFF;font-size:11px;font-weight:800;'
                    f'padding:2px 8px;border-radius:4px;text-transform:uppercase;">{item["domain"]} · {item["year"]}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"#### {item['title']}")
                st.caption(item["venue"])
                st.write(item["summary"])
            with c2:
                st.write("")
                if item.get("url"):
                    st.link_button("Read Publication", item["url"], use_container_width=True, type="primary")
                if item.get("secondary_url"):
                    st.link_button("Google Books", item["secondary_url"], use_container_width=True)


def publications_page():
    page_header(
        "Books, Peer-Reviewed Papers & Preprints",
        "Published monographs, World Bank technical compendiums, peer-reviewed journal articles, and working preprints by Dr. Cesar Marolla.",
        "Publications & Author",
    )
    t1, t2, t3 = st.tabs([
        f"Books & Compendiums ({len(pub.BOOKS_AND_MONOGRAPHS)})",
        f"Peer-Reviewed Articles & Chapters ({len(pub.PEER_REVIEWED_AND_CHAPTERS)})",
        f"Preprints & Foundational Theory ({len(pub.PREPRINTS_AND_WORKING_PAPERS)})",
    ])
    with t1:
        _render_pub_cards(pub.BOOKS_AND_MONOGRAPHS, "#1E3A5F")
    with t2:
        _render_pub_cards(pub.PEER_REVIEWED_AND_CHAPTERS, "#0284C7")
    with t3:
        _render_pub_cards(pub.PREPRINTS_AND_WORKING_PAPERS, "#DC2626")
    st.info("All entries load from `publications_data.py`. Append new items there at any time.")
    disclaimer()


def bio_page():
    P = pub.PROFILE
    page_header(P["name"], P["tagline"], "Publications & Author")
    cols = st.columns(len(P["links"]))
    for col, (label, url) in zip(cols, P["links"]):
        col.link_button(label, url, use_container_width=True)
    st.write("")
    with st.container(border=True):
        st.subheader("Research & Interdisciplinary Overview")
        st.write(P["summary"])
        st.caption(f"Academic Correspondence: {P['email']}")
    st.subheader("Academic & Institutional Leadership")
    acols = st.columns(3, gap="medium")
    for col, appt in zip(acols, P["appointments"]):
        with col.container(border=True):
            st.markdown(f"**{appt['org']}**")
            st.caption(appt["role"])
            st.write(appt["detail"])
    st.write("")
    cl, cr = st.columns(2, gap="large")
    with cl:
        st.subheader("Education & Executive Credentials")
        for deg, inst in P["education"]:
            with st.container(border=True):
                st.markdown(f"**{deg}**")
                st.caption(inst)
    with cr:
        st.subheader("Honors & Commendations")
        for title, desc in P["honors"]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(desc)
    disclaimer()
