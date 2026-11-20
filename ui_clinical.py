# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Clinical-grade UI pieces shared by the calculator pages.

    import ui_clinical as uc
    uc.kpi_cards([dict(title="R now", value="0.0858", tone="red"), ...])   # cards that wrap, never truncate
    uc.interpretation_box(L, E, V, rho, rho_after, posture_now=..., posture_after=...)
    uc.evidence_expander()                                                    # methodology, tiers, sources, limits

Every builder with the suffix _html returns a plain string, so it can be tested without Streamlit.
Nothing here invents evidence: sources come from the repo's own registry and case-study files.
"""
from __future__ import annotations

import html as _h
import re
import urllib.parse

RED, RED_D, BLUE_A, BLUE_D, BLUE_L, SKY, INK = "#d9262c", "#b81e24", "#1d6fd0", "#0f4fa8", "#6cb4f5", "#eaf4ff", "#0b2545"

# Fixed RMTI tier bands (the same for every case): R < 0.05, 0.15, 0.35, 0.60, then 1.0.
EDGES = (0.05, 0.15, 0.35, 0.60)
TIER_NAME = ["Low", "Moderate", "High", "Severe", "Critical"]
TIER_BG = ["#eaf4ff", "#b9d9f7", "#f3c0c2", "#d9262c", "#8f1519"]
TIER_FG = [INK, INK, INK, "#ffffff", "#ffffff"]
RHO_CEILING = 0.95


def _e(x) -> str:
    return _h.escape(str(x))


def tier_no(r: float) -> int:
    return 1 + sum(r >= e for e in EDGES)


def tier_band(t: int) -> tuple[float, float | None]:
    """(lower, upper) of tier t; upper is None for the open-ended top tier."""
    lo = 0.0 if t == 1 else EDGES[t - 2]
    return lo, (EDGES[t - 1] if t <= 4 else None)


def tier_chip_html(t: int) -> str:
    return (f'<span class="rm-tc" style="background:{TIER_BG[t - 1]};color:{TIER_FG[t - 1]}">'
            f'Tier {t} · {TIER_NAME[t - 1]}</span>')


# ------------------------------------------------------------------ KPI cards
_TONE = {"red": RED, "blue": BLUE_A, "deep": BLUE_D, "light": BLUE_L}


def kpi_html(items) -> str:
    """items: dict(title, value, sub=None, delta=None, tone='red'|'blue'|'deep'|'light', raw_value=False).
    value is escaped unless raw_value=True (used for tier chips built by this module)."""
    out = []
    for i in items:
        c = _TONE.get(i.get("tone", "red"), RED)
        val = i["value"] if i.get("raw_value") else _e(i["value"])
        delta = f'<div class="d">{_e(i["delta"])}</div>' if i.get("delta") else ""
        sub = f'<div class="s">{_e(i["sub"])}</div>' if i.get("sub") else ""
        out.append(f'<div class="rm-kpi" style="--c:{c}"><div class="t">{_e(i["title"])}</div><div class="v">{val}</div>{delta}{sub}</div>')
    return f'<div class="rm-kpis">{"".join(out)}</div>'


def tier_pair_html(t_now: int, t_after: int) -> str:
    return f'<div class="rm-tier-pair">{tier_chip_html(t_now)}<span class="ar">→</span>{tier_chip_html(t_after)}</div>'


def kpi_cards(items) -> None:
    import streamlit as st
    st.markdown(kpi_html(items), unsafe_allow_html=True)


# ------------------------------------------------------------------ interpretation
def interpret(L: float, E: float, V: float, rho: float, rho_after: float) -> dict:
    """Numbers behind the plain-language reading. Pure function."""
    lev = L * E * V
    R, R2 = lev * (1 - rho), lev * (1 - rho_after)
    t1, t2 = tier_no(R), tier_no(R2)
    ratio = (1 - rho_after) / (1 - rho) if rho < 1 else 1.0
    out = dict(R=R, R_after=R2, tier_now=t1, tier_after=t2, ratio=ratio, reduction_pct=(1 - ratio) * 100, lev=lev,
               next_tier=None, rho_needed=None, reachable=None)
    if t2 > 1 and lev > 0:
        edge = EDGES[t2 - 2]                      # R must fall below the lower edge of the current tier
        need = 1 - edge / lev                     # rho must exceed this
        out.update(next_tier=t2 - 1, next_edge=edge, rho_needed=need, reachable=need < RHO_CEILING)
    return out


def interpretation_html(L, E, V, rho, rho_after, posture_now=None, posture_after=None) -> str:
    d = interpret(L, E, V, rho, rho_after)
    R, R2, t1, t2 = d["R"], d["R_after"], d["tier_now"], d["tier_after"]
    pct = d["reduction_pct"]
    ps = []
    if abs(rho_after - rho) < 1e-9:
        ps.append(f"ρ is unchanged at {rho:.2f}, so R stays at <b>{R:.4f}</b>.")
    else:
        verb, move = ("fall", "Raising") if pct > 0 else ("rise", "Lowering")
        ps.append(f"{move} <b>ρ</b> (resilience: for cancer care, how fully surveillance and follow-up are delivered; for disasters, how prepared "
                  f"the system is) from {rho:.2f} to {rho_after:.2f} makes R {verb} from {R:.4f} to {R2:.4f}: <b class='n'>a {abs(pct):.0f}% "
                  f"{'reduction' if pct > 0 else 'increase'}</b>. R scales with (1 − ρ), so R is multiplied by "
                  f"(1 − {rho_after:.2f}) ÷ (1 − {rho:.2f}) = {d['ratio']:.3f}.")
    lo, hi = tier_band(t2)
    band = f"R of {lo:.2f} or more" if hi is None else f"R from {lo:.2f} up to, but not including, {hi:.2f}"
    if t1 == t2:
        ps.append(f"Both values sit in <b>Tier {t2} · {TIER_NAME[t2 - 1]}</b> ({band}), so the tier does not change. "
                  f"The score moved, but not far enough to cross a band.")
    else:
        ps.append(f"The tier moves from <b>Tier {t1} · {TIER_NAME[t1 - 1]}</b> to <b>Tier {t2} · {TIER_NAME[t2 - 1]}</b> ({band} after the change).")
    if d["next_tier"]:
        nt, edge = d["next_tier"], d["next_edge"]
        if d["reachable"]:
            ps.append(f"With these L, E and V, reaching <b>Tier {nt} · {TIER_NAME[nt - 1]}</b> (R below {edge:.2f}) would need ρ above "
                      f"<b>{d['rho_needed']:.2f}</b>.")
        else:
            ps.append(f"With these L, E and V, <b>Tier {nt} · {TIER_NAME[nt - 1]}</b> (R below {edge:.2f}) cannot be reached by raising ρ alone "
                      f"(it would need ρ above {d['rho_needed']:.2f}, past the model's ceiling of {RHO_CEILING:.2f}); L, E or V would also have to fall.")
    if posture_now or posture_after:
        if posture_now and posture_after and posture_now != posture_after:
            ps.append(f"Engine wording for the tier now: “{_e(posture_now)}”. After the change: “{_e(posture_after)}”.")
        else:
            ps.append(f"Engine wording for this tier: “{_e(posture_now or posture_after)}”.")
    cav = ("How to read this: R is a relative index on a fixed scale, for ranking and what-if comparison. It is not the probability that a person "
           "will develop cancer and it does not replace clinical judgement. A change in ρ stands for a change in how fully surveillance and care "
           "are delivered; it says nothing about the tumour biology.")
    return (f'<div class="rm-interp"><h4>What this means</h4>{"".join(f"<p>{p}</p>" for p in ps)}<div class="cav">{cav}</div></div>')


def interpretation_box(L, E, V, rho, rho_after, posture_now=None, posture_after=None) -> None:
    import streamlit as st
    st.markdown(interpretation_html(L, E, V, rho, rho_after, posture_now, posture_after), unsafe_allow_html=True)


# ------------------------------------------------------------------ evidence
FOUNDATION = dict(
    cite="Marolla C. Oncoclastics: definition note, version 1.0.0. Zenodo; 2026.",
    doi="10.5281/zenodo.24254220",
    note="Defines oncoclastics and the use of the RMTI equation for cancer trajectories. This is the author's own formulation.")

# Published case-study sources used as data anchors (same entries as the case-study animation).
CASE_SOURCES = [
    dict(cite="Lau-Min KS et al. JAMA Netw Open 2025;8(12):e2551665.",
         what="4198 patients on systemic therapy for HCC (Flatiron database, 2011–2023): survival, second-line use, liver function."),
    dict(cite="Sabakhtarishvili G et al. JTO Clin Res Rep 2025;6:100899.",
         what="3647 low-dose CT screening participants (one US center, 2021–2023): stage at diagnosis, screened versus usual care."),
    dict(cite="O’Shaughnessy J et al. Breast Cancer Res Treat 2026;219:19.",
         what="5041 women with HR+/HER2− metastatic breast cancer after endocrine therapy (Flatiron, 2015–2024): survival by line of therapy."),
]
METHODS = [
    dict(cite="Johnson PJ, Berhane S, Kagebayashi C, et al. Assessment of liver function in patients with hepatocellular carcinoma: "
              "a new evidence-based approach, the ALBI grade. J Clin Oncol 2015;33(6):550-558.", doi="10.1200/JCO.2014.57.9151",
         what="Source of the ALBI grade, the liver-function measure behind V in the HCC calculator."),
    dict(cite="Fan R, Papatheodoridis G, Sun J, et al. aMAP risk score predicts hepatocellular carcinoma development in patients with chronic "
              "hepatitis. J Hepatol 2020;73(6):1368-1378.", doi="10.1016/j.jhep.2020.07.025",
         what="Source of the aMAP score, the basis of L (aMAP-ref) in the HCC calculator."),
]
DATASETS = [dict(cite="Faria et al. cohort, Harvard Dataverse.", doi="10.7910/DVN/A81UVO",
                 what="Published ALBI grade counts used to set V in the two HCC example cases.")]

LIMITS = [
    "RMTI is a research prototype. The equation and the tier bands have not been validated against patient outcomes.",
    "Parameters (α, β, κ·H, λ, anchors) are uncalibrated placeholders.",
    "Published figures belong to the cited studies; mapping them onto L, E, V and ρ is illustrative.",
    "R is a relative rubric index, not a probability, forecast or actuarial figure.",
    "Not a medical device. Not for patient-care, emergency, safety or engineering decisions.",
]


def pubmed_url(cite: str) -> str:
    return "https://pubmed.ncbi.nlm.nih.gov/?term=" + urllib.parse.quote(cite[:200])


def doi_url(doi: str) -> str:
    return "https://doi.org/" + doi


_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s;,)]+")


def find_doi(text: str) -> str | None:
    m = _DOI_RE.search(text or "")
    return m.group(0).rstrip(".") if m else None


def cite_link(cite: str) -> str:
    """doi.org link when the citation carries a DOI, otherwise a PubMed search (labelled as a search)."""
    d = find_doi(cite)
    if d:
        return f'<a href="{doi_url(d)}" target="_blank">doi:{_e(d)}</a>'
    return f'<a href="{pubmed_url(cite)}" target="_blank">Search PubMed</a>'


def registry_items() -> list[dict]:
    """Peer-reviewed sources listed in the platform's evidence registry (empty list if unavailable)."""
    try:
        import registry as R
        ev = R.load().get("evidence")
        items = ev.get("evidence") if isinstance(ev, dict) else ev
        return [i for i in (items or []) if isinstance(i, dict) and i.get("cite")]
    except Exception:  # noqa: BLE001
        return []


def _li(label: str, body: str) -> str:
    return f'<li><span class="stt">{_e(label)}</span>{body}</li>'


def evidence_html() -> dict:
    """The HTML for each section of the evidence expander."""
    f = FOUNDATION
    foundation = '<ul class="rm-refs">' + _li("author", f'{_e(f["cite"])} <a href="{doi_url(f["doi"])}" target="_blank">doi:{_e(f["doi"])}</a><br>'
                                              f'<span style="color:#3f5f86">{_e(f["note"])}</span>') + "</ul>"
    cases = '<ul class="rm-refs">' + "".join(
        _li("published", f'{_e(c["cite"])} <a href="{pubmed_url(c["cite"])}" target="_blank">Search PubMed</a><br><span style="color:#3f5f86">{_e(c["what"])}</span>')
        for c in CASE_SOURCES)
    cases += "".join(_li("dataset", f'{_e(d["cite"])} <a href="{doi_url(d["doi"])}" target="_blank">doi:{_e(d["doi"])}</a><br><span style="color:#3f5f86">{_e(d["what"])}</span>')
                     for d in DATASETS) + "</ul>"
    methods = '<ul class="rm-refs">' + "".join(
        _li("method", f'{_e(m["cite"])} <a href="{doi_url(m["doi"])}" target="_blank">doi:{_e(m["doi"])}</a><br>'
                      f'<span style="color:#3f5f86">{_e(m["what"])}</span>') for m in METHODS) + "</ul>"
    reg = registry_items()
    registry = ""
    if reg:
        registry = '<ul class="rm-refs">' + "".join(
            _li(i.get("status", "source"),
                f'{_e(i["cite"])} {cite_link(i["cite"])}'
                + (f'<br><span style="color:#3f5f86"><b>Limits:</b> {_e(str(i["limits"])[:240])}</span>' if i.get("limits") else ""))
            for i in reg) + "</ul>"
    return dict(foundation=foundation, cases=cases, methods=methods, registry=registry, n_registry=len(reg))


def tier_table_md() -> str:
    rows = ["| Tier | R range | Example |", "|---|---|---|"]
    ex = {1: "R = 0.031", 2: "R = 0.0858", 3: "R = 0.210", 4: "R = 0.450", 5: "R = 0.720"}
    for t in range(1, 6):
        lo, hi = tier_band(t)
        rng = f"{lo:.2f} to below {hi:.2f}" if hi is not None else f"{lo:.2f} and above"
        rows.append(f"| **{t} · {TIER_NAME[t - 1]}** | {rng} | {ex[t]} |")
    return "\n".join(rows)


def evidence_expander(title: str = "Clinical evidence and methodology", expanded: bool = False) -> None:
    import streamlit as st
    ev = evidence_html()
    with st.expander(title, expanded=expanded):
        t1, t2, t3, t4 = st.tabs(["How R is built", "Risk tiers", "Evidence base", "Limits"])
        with t1:
            st.latex(r"R = L \cdot E \cdot V \cdot (1-\rho)")
            st.markdown(
                "- **L, likelihood**: how likely the adverse trajectory is over the horizon (for liver cancer, progression from chronic injury).\n"
                "- **E, exposure**: the burden of insults acting on the patient or population.\n"
                "- **V, vulnerability**: how much harm the same exposure does (for example liver function, allostatic load).\n"
                "- **ρ, resilience**: how much of the care pathway holds (surveillance reached, follow-up completed). R scales with (1 − ρ).\n\n"
                "L, E, V and ρ each run from 0 to 1, so R also runs from 0 to 1. The formula is the same for every domain; "
                "only the inputs change (cancer site, or disaster hazard).")
        with t2:
            st.markdown("The tier bands are **fixed**, so one score means the same thing every time.")
            st.markdown(tier_table_md())
            st.markdown("**Worked example.** R = 0.0858 is at least 0.05 and below 0.15, so it is **Tier 2 · Moderate**. "
                        "Moving ρ from 0.20 to 0.50 with L = 0.30, E = 0.65 and V = 0.55 changes R from 0.0858 to 0.0536: a 38% reduction, still Tier 2.")
        with t3:
            st.markdown("**Foundation**")
            st.markdown(ev["foundation"], unsafe_allow_html=True)
            st.markdown("**Published sources behind the case studies**")
            st.markdown(ev["cases"], unsafe_allow_html=True)
            st.markdown("**Methods behind the inputs (HCC calculator)**")
            st.markdown(ev["methods"], unsafe_allow_html=True)
            if ev["registry"]:
                st.markdown(f"**Evidence registry** ({ev['n_registry']} peer-reviewed sources on lung risk tools)")
                st.markdown(ev["registry"], unsafe_allow_html=True)
            st.caption("DOI links point to the cited record. Where a citation has no DOI, the link is a PubMed search, not a verified identifier. "
                       "No independent peer-reviewed validation of RMTI itself exists yet: see Limits.")
        with t4:
            st.markdown("\n".join(f"- {x}" for x in LIMITS))
