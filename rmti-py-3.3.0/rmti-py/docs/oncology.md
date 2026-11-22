# Oncology (HCC) workflow

There is **no satellite component** for HCC. The spatial analogue of a hazard footprint is the *surveillance footprint*.

| Urban | HCC |
|---|---|
| Hazard footprint (flood polygon) | Reach of surveillance-capable centres |
| E_sel = share of assets in footprint | E = share of **at-risk persons** within reach (`hcc_geo.access_exposure`) |
| V from rubric | V from ALBI grade (`hcc.albi_score/albi_grade`) |
| ρ from capital package | ρ from surveillance-adequacy ladder (`hcc.RHO`, `hcc_geo.rho_from_uptake`) |
| C from consequence scale | C from BCLC stage if missed (`hcc.C_BCLC`) |

* **Registry triage:** `hcc.score_table(df)` scores thousands of patients vectorised (tier, then EAL priority; optional improved-surveillance scenario).
* **District maps:** `access_exposure` → `score_zones` → `webmap.risk_map`.
* **Uncertainty / portfolios:** the same `simulate_rmti` and `optimize_portfolio` apply (e.g. choose among surveillance programmes under a budget).

Caveats: not validated against incident-HCC outcomes; the radius is straight-line, not travel time; L is a rubric-scaled value supplied by you (see FINDINGS #6);
`rho_from_uptake` interpolates published anchors (an assumption); sample data are synthetic; not for individual patient decisions.
