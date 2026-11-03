"""Narration text for the RMTI demo video: single source for the voice-over script, SRT captions and YouTube description."""

NARRATION = {
    "title":  "This is the Risk Mechanism Theory Index, or RMTI. I'm Cesar Marolla, its developer.",
    "limits": "First, the limits. RMTI is a research prototype: not validated, not a medical device, and not for patient-care "
              "or emergency decisions. This video uses only illustrative or published aggregate values, never patient data.",
    "c0": "RMTI scores risk as a single product of four bounded factors.",
    "c1": "L is likelihood: how probable the hazard is.",
    "c2": "E is exposure: the share of people or assets reached.",
    "c3": "V is vulnerability: how badly those reached are hurt.",
    "c4": "Multiplied together, that is the raw risk, before any resilience.",
    "c5": "Rho, resilience, absorbs a share of it, leaving the residual risk R.",
    "c6": "Raise resilience, and R falls. That is what an intervention is meant to do.",
    "tiers": "The score maps to five fixed tiers, with the same thresholds for every patient, city and year.",
    "onc_intro": "First, oncology: surveillance for hepatocellular carcinoma. Our published case study is the Faria et al. cohort.",
    "albi_a": "From measured albumin and bilirubin, each person gets an ALBI grade. We use only the group counts.",
    "albi_b": "Weighting the grade anchors by those counts gives vulnerability: 0.52 for the cancer cohort, 0.48 for cirrhosis.",
    "onc_a": "L, E and rho are illustrative working values, the same for both groups, so only V comes from the published data.",
    "onc_b": "Each cohort travels through the cube: likelihood, exposure, vulnerability.",
    "onc_c1": "With today's resilience, both land in tier 2, Moderate.",
    "onc_c2": "Under the improved-surveillance scenario, both fall to tier 1, Low.",
    "onc_take": "What this does not show: Faria's data supply only V. They cannot validate L, E or rho, or predict who develops cancer. "
                "This demonstrates the arithmetic, not clinical evidence.",
    "dis_intro": "Now disaster science. Three cases: the Palisades and Eaton fires of January 2025, and Lilongwe, Malawi, for flooding.",
    "dis_a": "These are the published rubric values in the calculator, not damage or casualty estimates.",
    "dis_b": "The two Los Angeles fires share likelihood, but differ in exposure and vulnerability.",
    "dis_c1": "Today, Lilongwe scores Severe, Altadena High, and Palisades Moderate.",
    "dis_c2": "Under scenario targets, Lilongwe and Altadena each fall one tier; Palisades stays Moderate.",
    "dis_take": "Resilience-after values are scenario targets, not observed results. R is a relative rubric index, not a forecast, "
                "an engineering assessment, or a loss estimate.",
    "close": "RMTI: one equation, two domains. I'm Cesar Marolla. The code is open under Apache 2.0, the demo uses no patient data, "
             "and nothing here is medical or engineering advice.",
}
