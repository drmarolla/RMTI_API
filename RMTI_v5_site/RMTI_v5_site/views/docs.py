"""Documentation pages (no source code is shown anywhere on this site)."""
import pandas as pd
import streamlit as st

import content
from engine import core, ENGINE_VERSION
from rmti_ui import card, disclaimer, page_header


def method():
    page_header("Method and tiers", "One bounded equation, four levers and five fixed decision tiers.", "Documentation")
    st.markdown("""
## The equation
**R = L · E · V · (1 − ρ)** &nbsp; where every term lies between 0 and 1.

The inherent risk is IR = L · E · V. Resilience ρ is the share of that risk the system absorbs, so the residual score is R = IR · (1 − ρ).
""")
    c = st.columns(4, gap="medium")
    for col, (t, b) in zip(c, [("L · Likelihood", "How likely the hazard or event is within the planning horizon."),
                               ("E · Exposure", "The share of people and assets inside the hazard footprint."),
                               ("V · Vulnerability", "How fragile the system is when a hazard arrives."),
                               ("ρ · Resilience", "The share of inherent risk that coping capacity absorbs.")]):
        col.markdown(card(t, b), unsafe_allow_html=True)
    st.markdown("## Four design rules")
    st.markdown("**Monotonic:** more resilience always lowers R; more exposure or vulnerability always raises it.  **Bounded:** R stays in [0, 1].  "
                "**Reproducible:** identical inputs give identical outputs.  **Severity-aware:** the EAL layer multiplies likelihood by consequence.")
    st.markdown("## Fixed decision tiers")
    post = core.TIER_POSTURE
    st.dataframe(pd.DataFrame([("Tier 1 - Low", "R < 0.05", post["Tier 1 - Low"]), ("Tier 2 - Moderate", "0.05 to 0.15", post["Tier 2 - Moderate"]),
                               ("Tier 3 - High", "0.15 to 0.35", post["Tier 3 - High"]), ("Tier 4 - Severe", "0.35 to 0.60", post["Tier 4 - Severe"]),
                               ("Tier 5 - Critical", "R ≥ 0.60", post["Tier 5 - Critical"])], columns=["Tier", "R band", "General posture"]),
                 hide_index=True, width="stretch")
    st.markdown("## Further layers")
    st.markdown("""
- **Expected Annual Loss index:** EAL = L · C · (1 − ρ), with consequence C from five fixed levels (0.10, 0.30, 0.50, 0.75, 1.00). It is an index, not a monetary value.
- **Log-normalised exposure:** E_log compresses population size so very large cities do not dominate on population alone.
- **Per-capita equity rate:** EAL divided by population, reported per million residents.
- **Sensitivity:** a 1% change in L, E or V changes R by 1%. A 1% change in ρ changes R by −ρ/(1−ρ) percent.
""")
    st.caption(f"Engine version {ENGINE_VERSION}. The scoring engine runs on the server and its source code is not published on this site.")
    disclaimer()


def steps():
    page_header("Step by step", "Assess, quantify, treat.", "Documentation")
    a, b, c = st.columns(3, gap="medium")
    a.markdown(card("1 · Assess", "Choose the system or patient group. Rate L, E, V and ρ from published data or a documented rubric, and record how strong the evidence is."), unsafe_allow_html=True)
    b.markdown(card("2 · Quantify", "Enter the four levers in a calculator. Read the inherent risk, the residual score R, its tier, EAL and the per-capita rate."), unsafe_allow_html=True)
    c.markdown(card("3 · Treat", "Model an investment or treatment by raising ρ. Compare R before and after, and rank multiple assets by tier, then EAL."), unsafe_allow_html=True)
    st.markdown("## Choosing the inputs")
    st.markdown("""
1. **L:** convert an annual incidence or return period to a 0–1 likelihood using a documented anchor table, or take it from a validated score.
2. **E:** the share of people or assets inside the footprint. For a population-anchored value use the log-normalised E_log.
3. **V:** for liver disease, the ALBI grade anchors (grade 1 = 0.35, grade 2 = 0.60, grade 3 = 0.85). For infrastructure, a composite of fragility, governance and inequality.
4. **ρ:** the share of inherent risk absorbed by current coping capacity, from an advisory ladder, and a second value for the planned investment.
5. **C:** the consequence level of a failure or a missed tumour, from 1 (insignificant) to 5 (severe).
""")
    st.markdown("## Limits to keep in mind")
    st.markdown("Scores are only as good as their inputs. Two analysts working from weak data can differ. The tier thresholds are fixed but not independently recalibrated here, "
                "and the clinical applications are not validated against prospective outcomes.")
    disclaimer()


def references():
    page_header("References and disclaimer", None, "Documentation")
    st.markdown("""
- Marolla C. (2026). *From Narrative to Algorithm: A Risk Mechanism Theory Index for Urban Infrastructure Investment in Sub-Saharan Africa.* Int J Management and Data Analytics 6(1):354-388. https://doi.org/10.68485/ijmada.20266156
- Marolla C. (2018). *Information and Communication Technology for Sustainable Development.* CRC Press. Chapter 9. https://doi.org/10.1201/9781351045230
- Marolla C. (2025). Enhancing urban resilience to California wildfires. Int J Management and Data Analytics 5(1):60-77.
- Johnson PJ, Kalyuzhnyy A, Boswell E, Toyoda H. (2024). Progression of chronic liver disease to hepatocellular carcinoma: implications for surveillance and management. BJC Reports. https://doi.org/10.1038/s44276-024-00050-0
- World Bank (2023). *Climate resilient investment in Sub-Saharan Africa compendium volume.*
- Case-study sources: Lau-Min et al., JAMA Network Open 2025 (liver); Sabakhtarishvili et al., JTO Clinical and Research Reports 2025 (lung); O'Shaughnessy et al., Breast Cancer Research and Treatment 2026 (breast).
""")
    st.markdown("## Disclaimer")
    st.markdown("This is a research prototype. It is uncalibrated against outcomes, uses synthetic or published aggregate values in its examples, is not a medical device, "
                "and must not be used for clinical, diagnostic or emergency decisions. Treatment decisions stay with clinicians.")
    st.markdown("**Competing interest.** The RMTI Calculator is distributed through a paid professional education course at Harvard Division of Continuing Education; the author receives financial benefit from it.")
    st.caption("Licence: Apache-2.0 for the framework code. © Cesar Marolla.")
    disclaimer()
