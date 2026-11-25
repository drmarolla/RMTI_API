"""Case studies: liver, lung, breast (3D studio animations + stages + trajectory), Johnson HCC pathway, six-city validation, video library."""
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import TIER_COLORS, core, short
from rmti_ui import add_tier_bands, badge, card, disclaimer, page_header, style_fig

RAW_VIDEOS = (
    "https://raw."
    "githubusercontent"
    ".com/"
    "drmarolla/RMTI_API/main/assets/videos"
)

STUDIO_CLIPS = {
    "liver": ("case_liver.mp4", "Clinical Oncology · Hepatocellular Carcinoma (HCC)", "3D Hepatic Vasculature & BCLC Stage Trajectory"),
    "lung": ("case_lung.mp4", "Clinical Oncology · Non-Small Cell Lung Cancer", "3D Bronchial Tree & Screening Interception Trajectory"),
    "breast": ("case_breast.mp4", "Clinical Oncology · HR-Positive Breast Cancer", "3D Mammary Ductal-Lobular & Systemic Therapy Trajectory"),
    "urban": ("case_african_cities.mp4", "Disaster Science · Six Sub-Saharan African Cities", "3D Urban Flood, Heat & Infrastructure Resilience Model"),
}


def _studio_hero_video(key):
    """Render bright white-studio 3D animation matching the Pathway 3D aesthetic."""
    if key not in STUDIO_CLIPS:
        return
    filename, domain_tag, subtitle = STUDIO_CLIPS[key]
    video_url = f"{RAW_VIDEOS}/{filename}"
    accent = "#0284C7" if key == "urban" else "#DC2626"
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
          body {{ background: transparent; }}
          .studio-card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
          }}
          .studio-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            background: #F8FAFC;
            border-bottom: 1px solid #E2E8F0;
          }}
          .tag {{
            font-size: 11.5px;
            font-weight: 800;
            letter-spacing: 0.4px;
            text-transform: uppercase;
            color: {accent};
          }}
          .sub {{
            font-size: 12.5px;
            font-weight: 600;
            color: #475569;
          }}
          video {{
            width: 100%;
            max-height: 480px;
            object-fit: contain;
            background: #FFFFFF;
            display: block;
          }}
        </style>
        </head>
        <body>
          <div class="studio-card">
            <div class="studio-bar">
              <span class="tag">{domain_tag}</span>
              <span class="sub">{subtitle}</span>
            </div>
            <video autoplay loop muted playsinline controls>
              <source src="{video_url}" type="video/mp4">
            </video>
          </div>
        </body>
        </html>
        """,
        height=540,
    )


def _video(key, label):
    _studio_hero_video(key)
    f = content.find_media(key)
    if f:
        cap = content.find_captions(f)
        if cap:
            with open(cap, "rb") as fh:
                st.download_button("Download closed captions (.vtt)", fh.read(), os.path.basename(cap), "text/vtt", key=f"vtt_{key}")


def _refs(key):
    rows = []
    for cite, url, kind in content.CASES[key]["refs"]:
        link = f' <a href="{url}" target="_blank">open</a>' if url else ""
        rows.append(f'<div class="card" style="margin-bottom:.6rem"><p><b>{kind}</b> · {cite}{link}</p></div>')
    st.markdown("".join(rows), unsafe_allow_html=True)


def _gbd_tab():
    g = content.GBD_BREAST
    st.markdown("**Global context, GBD 2023** (Lancet Oncology 2026;27:302-326). Females, all ages.")
    a, b, c3, d4 = st.columns(4)
    a.metric("Incident cases, 2023", f"{g['cases_m']:.2f} million")
    b.metric("Deaths, 2023", f"{g['deaths_k']:,} thousand")
    c3.metric("DALYs, 2023", f"{g['dalys_m']:.1f} million")
    d4.metric("Forecast cases, 2050", f"{g['cases_2050_m']:.2f} million", f"{g['deaths_2050_m']:.2f} million deaths", delta_color="off")
    fig = go.Figure()
    fig.add_bar(x=g["groups"], y=g["asir"], name="Incidence (ASIR)", marker_color="#93C5FD")
    fig.add_bar(x=g["groups"], y=g["asmr"], name="Mortality (ASMR)", marker_color="#BE123C")
    fig.update_layout(barmode="group", yaxis_title="Age-standardised rate per 100,000", title="Where incidence is highest, mortality is not: 2023 by World Bank income group")
    st.plotly_chart(style_fig(fig, 420), width="stretch")
    st.markdown("Between 1990 and 2023 the age-standardised mortality rate fell by 29.9% in high-income countries and rose by 99.3% in low-income countries. "
                "That gap is a resilience gap: the same disease, delivered through very different systems. It is the pattern the ρ term is built to capture.")


def _hcc_guidance_tab():
    G = content.HCC_GUIDE
    st.markdown("**Surveillance guidance in brief**, summarised from the 2023 AASLD guidance as presented in the University of Washington Hepatitis C Online lesson.")
    cols = st.columns(3, gap="medium")
    for i, (t, b) in enumerate(G["facts"]):
        cols[i % 3].markdown(card(t, b), unsafe_allow_html=True)
        if i % 3 == 2:
            st.write("")
    st.dataframe(pd.DataFrame(G["tests"], columns=["Test", "Sensitivity", "Specificity"]), hide_index=True, width="stretch")
    st.markdown("**How RMTI reads this.** Residual risk R = L · E · V · (1 − ρ). The guidance sets who is eligible and how often to test; "
                "the surveillance-delivery gap (ρ), the share of at-risk patients actually reached (E) and liver reserve (V) decide how much of the likelihood (L) is left. "
                "Use the HCC Surveillance Calculator to test an improvement scenario.")


def case_page(key):
    c = content.CASES[key]
    page_header(f"{c['title']}: from tumor events to trajectory", f"Published case study: {c['study']}. {c['finding']}", "Oncology case studies")
    names = ["3D Animation & captions", "Tumor stages", "RMTI assessment", "Trajectory"] + (["Surveillance guidance"] if key == "liver" else []) + (["Global burden"] if key == "breast" else []) + ["Sources"]
    tabs = st.tabs(names)
    it = iter(tabs)
    with next(it):
        _video(key, c["title"].lower())
        f = content.find_media(key)
        if f and content.find_captions(f):
            with st.expander("Read the transcript"):
                st.markdown("\n\n".join(l.strip() for l in open(content.find_captions(f), encoding="utf-8").read().split("\n") if l.strip() and "-->" not in l and not l.strip().isdigit() and l.strip() != "WEBVTT"))
    with next(it):
        cols = st.columns(4, gap="medium")
        for col, (name, text) in zip(cols, c["stages"]):
            col.markdown(card(name, text), unsafe_allow_html=True)
        st.caption("Explore these stages in 3D under Interactive models.")
    with next(it):
        st.markdown("**How the published data map onto the levers (illustrative)**")
        st.dataframe(pd.DataFrame(c["mapping"], columns=["Lever", "Published data used"]), hide_index=True, width="stretch")
        a, b = st.columns(2)
        a.metric("R at first review", f"{c['r_before']:.3f}")
        a.markdown(badge(core.tier(c["r_before"])), unsafe_allow_html=True)
        b.metric("R after improvement", f"{c['r_after']:.3f}", f"{(c['r_after'] / c['r_before'] - 1) * 100:.0f}%", delta_color="inverse")
        b.markdown(badge(core.tier(c["r_after"])), unsafe_allow_html=True)
        st.caption(f"In this synthetic example R falls {c['change']}. It is an illustration, not a prediction. Treatment decisions stay with clinicians.")
    with next(it):
        st.markdown("**Build your own trajectory (illustrative).** Hold L and E, then update vulnerability and resilience at each review cycle.")
        g1, g2 = st.columns([1, 2.2], gap="large")
        with g1:
            L = st.slider("L", 0.0, 1.0, 0.5, 0.01, key=f"{key}L")
            E = st.slider("E", 0.0, 1.0, 0.5, 0.01, key=f"{key}E")
        pts = []
        with g2:
            cols = st.columns(4)
            for i, col in enumerate(cols):
                v = col.slider(f"V cycle {i + 1}", 0.0, 1.0, round(0.60 - 0.04 * i, 2), 0.01, key=f"{key}V{i}")
                r = col.slider(f"ρ cycle {i + 1}", 0.0, 0.95, round(0.20 + 0.12 * i, 2), 0.01, key=f"{key}R{i}")
                pts.append(core.score(L, E, v, r)["R_raw"])
        fig = go.Figure()
        add_tier_bands(fig)
                cycles = list(range(1, 5))
        fig.add_trace(go.Scatter(x=cycles, y=pts, mode="lines+markers", line=dict(color="#0F172A", width=4), marker=dict(size=13)))
        fig.update_layout(xaxis=dict(title="Review cycle", dtick=1), yaxis_title="Residual risk R", yaxis_range=[0, max(0.4, max(pts) * 1.2)], showlegend=False)
        st.plotly_chart(style_fig(fig, 360), width="stretch")
    if key == "liver":
        with next(it):
            _hcc_guidance_tab()
    if key == "breast":
        with next(it):
            _gbd_tab()
    with next(it):
        _refs(key)
    disclaimer()


def johnson_page():
    J = content.JOHNSON
    page_header("HCC progression: the pathway matters for surveillance",
                "Johnson and colleagues (BJC Reports, 2024) followed 2,592 patients with chronic liver disease and no prior cirrhosis at Ogaki Municipal Hospital, Japan (median follow-up 13.2 years).",
                "Oncology case studies")
    k0, k1, k2, k3 = st.columns(4, gap="medium")
    k0.metric("HCC developed", f"{J['hcc']}", f"{J['hcc'] / J['n']:.0%} of cohort", delta_color="off")
    k1.metric("Never passed through cirrhosis", f"{J['no_cirrhosis']}", "28% of HCC", delta_color="off")
    k2.metric("HBV that skipped cirrhosis", f"{J['hbv_direct']} of {J['hbv_total']}", "69%", delta_color="off")
    k3.metric("HCC per 1,000 patient-years", f"{J['rate_noncirr']} vs {J['rate_cirr']}", "non-cirrhotic vs cirrhotic", delta_color="off")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure(go.Bar(x=["Passed through cirrhosis", "Remained non-cirrhotic"], y=[J["via_cirrhosis"], J["no_cirrhosis"]],
                               marker_color=["#1E3A5F", "#BE123C"], text=[J["via_cirrhosis"], J["no_cirrhosis"]], textposition="outside"))
        fig.update_layout(title="Pathway to HCC (n = 172)", yaxis_title="Patients")
        st.plotly_chart(style_fig(fig, 400), width="stretch")
    with c2:
        fig = go.Figure(go.Bar(x=["Hepatitis B", "Hepatitis C"], y=[J["hbv_direct"] / J["hbv_total"] * 100, J["hcv_noncirr"] / J["hcv_total"] * 100],
                               marker_color=["#BE123C", "#93C5FD"], text=[f"{J['hbv_direct']}/{J['hbv_total']}", f"{J['hcv_noncirr']}/{J['hcv_total']}"], textposition="outside"))
        fig.update_layout(title="HCC without cirrhosis, by aetiology", yaxis_title="% of HCC cases", yaxis_range=[0, 85])
        st.plotly_chart(style_fig(fig, 400), width="stretch")
    st.markdown("""
**What the study shows.** Most HCC is detected in a cirrhotic liver, but cirrhosis is not an obligatory stage. Hepatitis B shows a direct route to HCC, 
and achieving a sustained virological response after cirrhosis has formed does not remove the risk. Patients on nucleoside analogues for hepatitis B 
mostly stayed below the cirrhosis threshold, whether or not they developed HCC.

**Why it matters for RMTI-HCC.** Surveillance reach (E) and surveillance adequacy (ρ) cannot be tied to cirrhosis status alone. 
The HCC Surveillance Calculator lets you test how risk tiers shift when more at-risk patients are reached.
""")
    st.caption("Source: Johnson PJ, Kalyuzhnyy A, Boswell E, Toyoda H. BJC Reports 2024. https://doi.org. Figures summarised in our own words.")
    disclaimer()


def urban_page():
    page_header("Urban infrastructure: six Sub-Saharan African cities",
                "Live recomputation of Tables 4 to 6 of Marolla (2026), checked against the published values.", "Disaster science case studies")
    _studio_hero_video("urban")
    st.write("")
    ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))}
                               for k, v in content.SIX_CITIES.items()})
    rows, ok_all = [], True
    for r in ranked:
        pub_now, pub_after = content.SIX_CITIES_PUBLISHED[r["name"]]
        ok = abs(r["R_now"] - pub_now) < 0.0015 and (pub_after is None or abs(r["R_after"] - pub_after) < 0.0015)
        ok_all &= ok
        rows.append({"Priority in tier": r["priority_in_tier"], "City": r["name"], "Asset": content.SIX_CITIES[r["name"]]["asset"],
                     "R now": r["R_now"], "Tier now": short(r["tier_now"]), "R after": r.get("R_after"), "Tier after": short(r["tier_after"]) if "tier_after" in r else "",
                     "Reduction %": r.get("risk_reduction_pct"), "EAL now": r["EAL_now"], "Equity /1M": r["equity_now_per_1M"], "Matches paper": "Yes" if ok else "No"})
    df = pd.DataFrame(rows)
    (st.success if ok_all else st.warning)("All published R values reproduced." if ok_all else "Some values differ from the paper.")
    st.dataframe(df, hide_index=True, width="stretch")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        add_tier_bands(fig)
        fig.add_bar(x=df["City"], y=df["R now"], name="R now", marker_color="#1E3A5F")
        fig.add_bar(x=df["City"], y=df["R after"], name="R after ($50M package)", marker_color="#93C5FD")
        fig.update_layout(barmode="group", yaxis_title="Residual risk R", yaxis_range=[0, 0.65], title="R against the five fixed tiers")
        st.plotly_chart(style_fig(fig, 460), width="stretch")
    with c2:
        d2 = df.sort_values("Equity /1M")
        fig = go.Figure(go.Bar(y=d2["City"], x=d2["Equity /1M"], orientation="h", marker_color="#2F5D50"))
        fig.update_layout(title="Per-capita equity rate (EAL per million residents)", xaxis_title="Equity rate")
        st.plotly_chart(style_fig(fig, 460), width="stretch")
    st.markdown("**One-way sensitivity, ±10% (primary cases).** Lagos is the only baseline that flips tier under a plausible 10% input error.")
    sens = []
    for city in ("Bamako", "Lagos", "Lilongwe"):
        p = content.SIX_CITIES[city]
        base = core.score(p["L"], p["E_sel"], p["V"], p["rho_now"], p["C"])["R_raw"]
        lo = base * 0.9
        hi = min(base * 1.1, 1.0)
        sens.append({"City": city, "R now": round(base, 3), "L, E or V −10%": f"{lo:.3f} ({short(core.tier(lo))})", "L, E or V +10%": f"{hi:.3f} ({short(core.tier(hi))})",
                     "Margin to boundary": round(base - 0.35, 3)})
    st.dataframe(pd.DataFrame(sens), hide_index=True, width="stretch")
    st.caption("Source: Marolla C. (2026). From Narrative to Algorithm. Int J Management and Data Analytics 6(1):354-388. https://doi.org. "
               "Scores are case-based demonstrations from World Bank AFRI-RES inputs and analyst judgement, not measured outcomes.")
    disclaimer()


def videos_page():
    page_header("Video library", "Narrated walkthroughs of the framework and the case studies.", "Case studies")
    known = {"rmti_1": "RMTI explained", "rmti_2": "Liver case studies", "rmti_3": "Flood and heat case studies"}
    vids = content.all_videos()
    if not vids:
        st.markdown('<div class="note">No videos found yet. Place .mp4 files in the repository root or the media/ folder and they will be listed here.</div>', unsafe_allow_html=True)
    for f in vids:
        name = os.path.basename(f)
        stem = name.rsplit(".", 1)[0]
        title = next((v for k, v in known.items() if name.lower().startswith(k)), stem.replace("_", " ").title())
        st.subheader(title)
        st.video(f)
    disclaimer()


def liver():
    case_page("liver")


def lung():
    case_page("lung")


def breast():
    case_page("breast")
