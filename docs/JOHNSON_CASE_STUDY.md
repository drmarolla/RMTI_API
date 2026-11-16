# Case study: chronic liver disease to HCC (work led by Dr. Philip J. Johnson)

Independent RMTI case study. Dr. Johnson and his co-authors did not review it and are not responsible for the mapping or calculations.

Studies used (figures quoted as reported):
- Johnson PJ, Kalyuzhnyy A, Boswell E, Toyoda H. Progression of chronic liver disease to hepatocellular carcinoma: implications for surveillance and management. BJC Reports 2024. doi:10.1038/s44276-024-00050-0
- Cucchetti A, et al., Johnson PJ. "Potentially curative therapies" for hepatocellular carcinoma: how many patients can actually be cured? Br J Cancer 2023;128:1665-1671. doi:10.1038/s41416-023-02188-z

Code: `rmti_johnson_case.py` (uses `rmti_elasticity.py` and `rmti_resilience_components.py`); tests: `python -m unittest -v test_rmti_johnson_case`. Streamlit page: `pages/8_Johnson_Case_Study.py`.

Illustrative defaults: L = 1 - exp(-rate x 10 years) from 5 and 31 cases per 1000 patient-years (0.049 and 0.267); E 0.60, V 0.50, rho_bio 0.30, rho_care 0.20 (low) and 0.70 (high). R falls by 62.5% when rho_care goes from 0.20 to 0.70 (R is proportional to 1 - rho_care); cirrhosis at high delivery still has about twice the R of non-cirrhotic disease at low delivery; delivery alone would need rho_care of about 0.85 to offset the difference in L. Placeholders, not findings.
