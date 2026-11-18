"""Redesigned landing page. Replace your current Home page (or app.py) with this."""
import pandas as pd
import streamlit as st

from ui.theme import (
    BLUE, TEAL, AMBER, CORAL, RED, INK,
    inject_theme, top_nav, hero, stats, strip, section, cards,
    equation_banner, demo_banner, callout, footer,
)

st.set_page_config(page_title="RMTI · Oncoclastics", page_icon="📊", layout="wide")
inject_theme()
top_nav(active="Home")

# ------------------------------------------------------------------ hero
hero(
    eyebrow="Oncology and disaster science",
    title="Quantify systemic risk. <br>Before it fragments care.",
    lead=(
        "The Risk Mechanism Theory Index (RMTI) brings hazard–exposure–vulnerability–resilience "
        "assessment from disaster-risk reduction into oncology: one equation, four levers, "
        "real case studies."
    ),
    cta_label="Explore the pathways",
    cta_href="#pathways",
)
demo_banner()

# ------------------------------------------------------------------ animated KPIs
# Replace the numbers with your real published figures.
stats([
    (4, "levers in one equation", "", BLUE),
    (2, "domains: oncology and disaster science", "", TEAL),
    (7, "interactive tools and calculators", "", AMBER),
    (3, "narrated case-study walkthroughs", "", RED),
])

strip("Built on", ["Disaster-risk reduction", "Hepatocellular carcinoma", "Cohort modelling", "Open Python / Streamlit"])

# ------------------------------------------------------------------ pathways
section("Platform", "Four ways in", "Pick the pathway that matches your question. Every tool runs on synthetic or published aggregate data.", anchor="pathways")
cards([
    dict(icon="calculator", title="Risk Calculator", text="Set the four levers and see the RMTI score, tier and expected loss instantly.", tag="Calculator", color=BLUE),
    dict(icon="liver", title="HCC Calculator", text="Chronic liver injury to hepatocellular carcinoma, including non-cirrhotic HCC.", tag="Oncology", color=RED),
    dict(icon="users", title="Cohort Sandbox", text="Simulate a synthetic cohort and watch the distribution of risk shift.", tag="Simulation", color=TEAL),
    dict(icon="cube", title="4D Risk Matrix", text="Hazard, exposure, vulnerability and resilience explored across time.", tag="Visual", color=AMBER),
    dict(icon="route", title="Step by Step", text="A guided walkthrough of the RMTI method with worked arithmetic.", tag="Learn", color=CORAL),
    dict(icon="book", title="Case Studies", text="Narrated 3D/4D videos: RMTI explained, liver cancer, flood and heat.", tag="Evidence", color=BLUE),
])

# ------------------------------------------------------------------ equation
section("The model", "One equation, four levers")
equation_banner()

# ------------------------------------------------------------------ live mini-lab
section("Try it", "Live lever lab", "Move a lever and watch the score and sensitivity update. Illustrative values only.")
left, right = st.columns([1, 1.25], gap="large")
with left:
    L = st.slider("L · Hazard", 0.0, 1.0, 0.60, 0.01)
    E = st.slider("E · Exposure", 0.0, 1.0, 0.70, 0.01)
    V = st.slider("V · Vulnerability", 0.0, 1.0, 0.50, 0.01)
    rho = st.slider("ρ · Resilience / care-system", 0.0, 1.0, 0.40, 0.01)


def rmti(l, e, v, r):
    return l * e * v * (1 - r)


R = rmti(L, E, V, rho)
tier = "Low" if R < 0.10 else "Moderate" if R < 0.25 else "High"

with right:
    m1, m2 = st.columns(2)
    m1.metric("RMTI score (R)", f"{R:.3f}")
    m2.metric("Tier", tier)

    # sensitivity: effect on R of a +/-20% change in each lever
    base = dict(L=L, E=E, V=V, rho=rho)
    rows = []
    for k in base:
        lo, hi = dict(base), dict(base)
        lo[k] = max(0.0, base[k] * 0.8)
        hi[k] = min(1.0, base[k] * 1.2)
        rows.append({"Lever": k, "−20 %": rmti(**lo) - R, "+20 %": rmti(**hi) - R})
    sens = pd.DataFrame(rows).set_index("Lever")
    st.caption("Change in R when each lever moves ±20 %")
    st.bar_chart(sens, color=[CORAL, BLUE], height=240)

callout(
    "<b>Why “oncoclastics”?</b> From <i>onco-</i> (tumour) and <i>-clastic</i> (broken): the "
    "fragmentation of cancer-related trajectories, whether biological or in the care system. "
    "The term is used here in its biological sense, with the care system entering through ρ."
)

footer()
