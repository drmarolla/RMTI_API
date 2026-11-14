"""
storyboards.py  --  the three narrated RMTI videos. Every number in the narration is computed from rmti_cases.py (no typing of results).

  explained   : the equation, the four levers in both domains, tiers, sensitivity, expected loss
  liver       : HCC surveillance: published cohorts (HBV, viral / alcohol / cured-HCV cirrhosis), three levers, ALBI from Faria et al.
  flood_heat  : flood and heat in Lilongwe, Lagos, Bamako: published rubric cases and four lever what-ifs
"""
from rmti_video_engine import *   # noqa: F401,F403
import rmti_cases as K

CONCEPT = dict(L=0.30, E=0.65, V=0.55, rho_now=0.20, rho_after=0.50, label="example")
LIMITS_TEXT = ("A reminder before we start. RMTI is a research prototype: not validated, not a medical device, and not for patient-care "
               "or emergency decisions. Everything here uses illustrative values, published rows, or aggregate counts. No patient data appears.")


def f2(x): return f"{x:.2f}"
def f3(x): return f"{x:.3f}"


def common_open(kicker, text):
    return [seg("title", text, one(dict(kind="title", kicker=kicker)), 5),
            seg("limits", LIMITS_TEXT, one(dict(kind="bullets", title="Before we start: the limits", width=78, items=[
                ("p", "Research prototype: not validated against real outcomes."),
                ("p", "Not a medical device. Not for patient-care or emergency decisions."),
                ("p", "R is a relative, rubric-based index, not a probability, forecast or loss estimate."),
                ("p", "Parameters are uncalibrated placeholders; after-values are scenarios, not observations."),
                ("p", "Illustrative values, published rows and aggregate counts only. No patient data.")])), 6)]


# ============================================================================ 1. explained
def sb_explained():
    c = CONCEPT; r0 = c["L"] * c["E"] * c["V"]; rn = r0 * (1 - c["rho_now"]); ra = r0 * (1 - c["rho_after"])
    out = common_open("VIDEO 1 · RMTI EXPLAINED",
                      "Welcome. This is the Risk Mechanism Theory Index, RMTI, created and formulated by Dr. Cesar Marolla to quantify systemic risk in "
                      "disaster science and in oncology. In the next few minutes you will see how one equation turns a hazard, the people exposed, how "
                      "fragile they are, and how well a system copes, into a single bounded score.")
    out.append(seg("why", "Why an index? Risk decisions are often made from narrative: the loudest voice, or the most recent event. RMTI moves from narrative "
                          "to algorithm. Four inputs, each between zero and one, each with a stated meaning and source. And the same fixed thresholds for every "
                          "patient, every city and every year, so a score can be compared, audited and challenged.",
                   one(dict(kind="bullets", title="Why an index? From narrative to algorithm", width=80, items=[
                       ("p", "Risk choices are often made from narrative: the loudest voice, the latest event."),
                       ("p", "RMTI makes them an auditable calculation: four inputs between 0 and 1, each with a stated meaning and source."),
                       ("p", "The same fixed thresholds apply to every patient, city and year, so scores can be compared and challenged.")])), 6))
    kf = [(0, 0.0, 0, "R = L · E · V · (1 − ρ)\nFour bounded factors multiply into one residual-risk score",
           "The equation multiplies four bounded factors: likelihood, exposure, vulnerability, and resilience, which enters as one minus rho.",
           "surveillance of a cancer, for example hepatocellular carcinoma", "a hazard meeting a city, for example a flood or a heat event"),
          (1, 0.0, 1, f"Step 1 · L, likelihood = {c['L']:.2f}\nHow probable the hazard is, per year",
           "L is likelihood: how probable the hazard is in a year. In oncology it comes from a validated risk score, such as aMAP for liver cancer, and is not "
           "re-derived. In disaster science it is the annual probability that a flood, fire or heat event materially strikes.",
           "L: annual cancer probability from a validated risk score", "L: annual probability the hazard materially strikes"),
          (2, 0.0, 2, f"Step 2 · × E, exposure = {c['E']:.2f}\nWho or what is in harm's way.  L·E = {c['L']*c['E']:.3f}",
           "E is exposure: who or what is in harm's way. For liver surveillance it is the share of the at-risk population inside the programme's footprint. "
           "For a city it is the share of people and assets inside the hazard zone.",
           "E: share of the at-risk population in the surveillance footprint", "E: share of people and assets in the hazard zone"),
          (3, 0.0, 3, f"Step 3 · × V, vulnerability = {c['V']:.2f}\nHow badly those exposed are hurt.  L·E·V = {r0:.3f}",
           "V is vulnerability: how badly those exposed are hurt. For the liver it is reserve, taken from the ALBI grade, which uses albumin and bilirubin. "
           "For a city it reflects housing, services, poverty and governance.",
           "V: liver reserve from the ALBI grade (albumin, bilirubin)", "V: sensitivity given housing, services, poverty, governance"),
          (3, 0.0, 4, f"Step 4 · Inherent risk R₀ = {r0:.3f}\nWhat the score would be if nothing cushioned it",
           "Multiply L, E and V and you get the inherent risk: the score if nothing cushioned it.", "", ""),
          (3, c["rho_now"], 5, f"Step 5 · × (1 − ρ), ρ = {c['rho_now']:.2f}\nResilience absorbs {100*c['rho_now']:.0f}% of it.  R = {rn:.3f}",
           "Resilience, rho, is the fraction of that inherent risk the system absorbs. Because it enters as one minus rho, more resilience always means less "
           "residual risk.", "ρ: surveillance effectiveness (uptake, test quality, access to cure)", "ρ: coping capacity (warning, infrastructure, health care)"),
          (3, c["rho_after"], 6, f"Step 6 · An improved state, ρ = {c['rho_after']:.2f}\nR = {ra:.3f}  ({ra - rn:+.3f})",
           "And that is where action lives. Improve surveillance quality, early warning or infrastructure, raise rho, and the residual risk R falls.", "", "")]
    for k, (u, rho, rev, title, text, onc, dis) in enumerate(kf):
        st = []
        if k:
            u0, r0_, rev0 = kf[k - 1][0], kf[k - 1][1], kf[k - 1][2]
            for q in range(1, N(0.8) + 1):
                t = ease(q / (N(0.8) + 1))
                st.append((dict(kind="concept", c=c, u=u0 + (u - u0) * t, rho=r0_ + (rho - r0_) * t, rev=rev0 + (rev - rev0) * t, title=title, onc=onc, dis=dis), 1))
        st.append((dict(kind="concept", c=c, u=u, rho=rho, rev=rev, title=title, onc=onc, dis=dis), 1))
        out.append(seg(f"c{k}", text, st, 3.5))
    out.append(seg("tiers", "R lands in one of five fixed tiers: low, moderate, high, severe and critical. Each tier carries a posture. For liver surveillance, it runs from "
                            "usual-care monitoring at tier one to an immediate, resourced pathway at tier five. For cities, from baseline monitoring to an immediate, "
                            "system-level response.", one(dict(kind="tiers")), 8))
    base, d = K.tornado(c)
    items = [("L  likelihood", d["L"], False, "often set by nature or biology"), ("E  exposure", d["E"], True, "who is in harm's way"),
             ("V  vulnerability", d["V"], True, "how badly they are hurt"), ("ρ  resilience", d["rho"], True, "how well the system copes")]
    order = sorted(items, key=lambda x: -abs(x[1]))
    out.append(tornado_segment("levers",
        "Which lever matters most? Move each factor by ten points in the risk-reducing direction and see how far R falls. In this example "
        f"{order[0][0].split()[1]} moves it most, by {abs(order[0][1]):.3f}, followed by {order[1][0].split()[1]}, {order[2][0].split()[1]} and {order[3][0].split()[1]}. "
        "But equal steps are not equal efforts, and likelihood is often set by nature or biology, so programmes mostly act through exposure, vulnerability and resilience.",
        items, "Which lever moves R most?", f"One illustrative case: L 0.30, E 0.65, V 0.55, ρ 0.20, R = {base:.3f}. Each lever moves by 0.10 in the risk-reducing direction.",
        "Equal absolute steps, so results depend on where each input starts. An illustrative step, not an intervention effect size."))
    pa = dict(label="Patient A", L=0.30, E=0.60, V=0.50, rho=0.20, C=2, text="A: post-SVR hepatitis C, preserved reserve. A missed tumour would present early and be curable (C = 2, minor).")
    pb = dict(label="Patient B", L=0.25, E=0.60, V=0.55, rho=0.20, C=5, text="B: alcohol-related, marginal reserve. A missed tumour would present advanced and non-curative (C = 5, severe).")
    Ra, Rb = K.r_score(pa["L"], pa["E"], pa["V"], pa["rho"]), K.r_score(pb["L"], pb["E"], pb["V"], pb["rho"])
    Ea, Eb = pa["L"] * 0.3 * 0.8, pb["L"] * 1.0 * 0.8
    base_e = dict(kind="eal", title="R is not the whole story: consequence matters", sub="Same tier, different stakes (RMTI-HCC calculator, worked example)", patients=[pa, pb],
                  foot="Same tier, but EAL ranks B first: more to lose if surveillance is slow.")
    est = [(dict(base_e, g1=ease(q / N(1.5)), g2=0), 1) for q in range(1, N(1.5) + 1)] + [(dict(base_e, g1=1, g2=ease(q / N(1.5))), 1) for q in range(1, N(1.5) + 1)]
    out.append(seg("eal", "R measures residual risk, not how bad a miss would be. A second layer, expected annual loss, multiplies likelihood by consequence and by one minus rho. "
                          f"Take two liver patients in the same tier. Patient A has R of {Ra:.3f} and would be caught early and cured. Patient B has R of {Rb:.3f} and would present advanced. "
                          f"R ranks A first, but EAL is {Eb:.2f} for B against {Ea:.3f} for A, nearly three times higher. Within a tier, EAL shows who has the most to lose if surveillance is slow.", est, 6))
    out.append(seg("domains", "One engine, two domains. The same three indicator families feed E, V and rho. In disaster science, hazards, climate change and urbanisation raise exposure; poverty, "
                              "governance and pollution raise vulnerability; and risk-management strategy, infrastructure, and health and water security supply resilience. "
                              "In liver cancer, the size of the at-risk population feeds exposure; reduced liver reserve, metabolic disease and fibrosis progression feed vulnerability; "
                              "and surveillance uptake, test quality, access to cure and care coordination feed resilience.",
                   one(dict(kind="bullets", title="One engine, two domains: what feeds E, V and ρ", width=96, size=13, items=[
                       ("h", "Disaster science (indicator backbone)"),
                       ("p", "E ← natural and man-made hazards, climate change, accelerated urbanism, health hazards"),
                       ("p", "V ← poverty and inequality, governance and rule of law, pollution and land degradation, fiscal stability"),
                       ("p", "ρ ← risk-management strategy, infrastructure quality (ICT, energy, urban), hospital capacity, water and food security"),
                       ("h", "Oncology (HCC surveillance)"),
                       ("p", "E ← size of the at-risk cirrhosis population, surveillance footprint, competing hazards"),
                       ("p", "V ← reduced liver reserve (ALBI), metabolic comorbidity, FIB-4 trajectory and fibrosis progression, access barriers"),
                       ("p", "ρ ← surveillance uptake and adherence, ultrasound and AFP quality, access to curative therapy, care coordination")])), 10))
    out.append(seg("close", "That is RMTI: one bounded equation, four levers, five fixed tiers, and two domains. Next, see it applied: liver cancer surveillance, and flood and heat "
                            "risk in African cities. Thank you. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, the demo uses no patient data, and nothing here is medical "
                            "or engineering advice.", one(dict(kind="close")), 8))
    return out


# ============================================================================ 2. liver
def sb_liver():
    cs = K.LIVER_CASES; hbv, viral, alc, hcv = cs; ev = [K.evaluate(c) for c in cs]; hs = K.LIVER_EXTRA["hbv_suppressed"]
    out = common_open("VIDEO 2 · CASE STUDIES · LIVER CANCER (HCC) SURVEILLANCE",
                      "Case studies, part one: liver cancer. We use RMTI as a triage layer for hepatocellular carcinoma surveillance. The question is: which patient groups "
                      "need surveillance first, and which lever moves each group the most?")
    out.append(seg("map", "Here is how the inputs map to the liver. L comes from a validated risk score. E is the share of the at-risk population in the surveillance footprint. "
                          "V is liver reserve, from the ALBI grade. And rho is surveillance effectiveness, on a published ladder from none, at 0.15, to optimised, at 0.65.",
                   one(dict(kind="bullets", title="How the four inputs map to the liver", width=92, size=14, items=[
                       ("p", "L ← annual HCC probability from a validated score (for example aMAP); not re-derived here"),
                       ("p", "E ← share of the at-risk population in the active surveillance footprint"),
                       ("p", "V ← liver-reserve sensitivity to a missed diagnosis, from the ALBI grade (anchors 0.35 · 0.60 · 0.85)"),
                       ("p", "ρ ← surveillance effectiveness: none 0.15 · usual care 0.20 · outreach 0.45 · specialist 0.50 · optimised 0.65"),
                       ("p", "C ← severity if a tumour is missed, anchored to BCLC stage at detection (used for the EAL layer)")])), 8))
    cs_texts = [
        "Four published cohort rows from the RMTI HCC calculator: untreated hepatitis B, active viral cirrhosis, alcohol-related cirrhosis, and cured hepatitis C cirrhosis. "
        "The after values for resilience are back-solved to match the published table, so they are scenarios, not observations.",
        "Each group travels the cube: likelihood, exposure, vulnerability. Notice how far out untreated hepatitis B sits on likelihood.",
        f"With today's surveillance, untreated hepatitis B is the only group in tier 3, high, with R of {ev[0]['R_now']:.2f}. The three cirrhosis groups sit in tier 2, moderate.",
        f"After the improvement package, cured hepatitis C falls to tier 1, low. But untreated hepatitis B stays in tier 3, high, even though its R falls by "
        f"{100 * (1 - ev[0]['R_after'] / ev[0]['R_now']):.0f} percent."]
    out += case_segments("liv", cs, 0.40, [0.05, 0.05, 0.05, -0.11], "Liver (HCC) · four published cohorts", cs_texts,
                         ["Inputs: published cohort rows, RMTI-HCC calculator v2.3.0 (Table 2)", "Each cohort travels the cube: L → E → V",
                          "ρ now  →  HBV untreated: tier 3 High · the three cirrhosis groups: tier 2 Moderate", "ρ after (scenario)  →  HCV cured: tier 1 Low · HBV untreated: still tier 3 High"],
                         "ρ-after values for Table 2 are back-solved to reproduce the published R-after column: scenarios, not observations.")
    P = K.POSTURE_HCC
    nt = K.to_next_tier(hbv)
    out.append(sweep_segment("lv_rho",
        f"Lever one: resilience. Walk untreated hepatitis B up the surveillance ladder. None, usual care, outreach, specialist: R falls, but stays in tier 3. Only optimised surveillance, "
        f"ultrasound plus AFP with reliable access to cure, at 0.65, brings R to {K.r_with(hbv, rho=0.65):.2f}, below 0.15, into tier 2.",
        hbv, "rho", 0.10, 0.70, "Lever 1 · surveillance quality (ρ): untreated hepatitis B", "Published ladder rungs marked; all other inputs held fixed",
        [(0.15, "none"), (0.20, "usual"), (0.45, "outreach"), (0.50, "specialist"), (nt["need"]["rho"], "tier 3→2"), (0.65, "optimised")], P, 5.0))
    out.append(threshold_segment("lv_thr",
        f"Which single lever would be enough to leave tier 3? Resilience needs to reach at least {nt['need']['rho']:.2f}, which the optimised rung exceeds. Vulnerability would have to fall to "
        f"{nt['need']['V']:.2f}, below the lowest ALBI anchor of 0.35, so reserve alone cannot do it. Exposure would need to fall to {nt['need']['E']:.2f}, or likelihood to {nt['need']['L']:.2f}.",
        hbv, "What would it take to leave tier 3? Untreated hepatitis B", f"R now {nt['R']:.3f}; target R below {nt['target']:.2f}. One lever at a time, the others fixed.",
        "Single-lever what-ifs, not a plan: combinations of levers need less of each.", floors={"V": 0.35}, rho_top=True))
    out.append(sweep_segment("lv_L",
        f"Lever two: treat the cause. In the published table, untreated hepatitis B carries a likelihood of 0.90, and suppressed hepatitis B {hs['L']:.2f}. Move only that lever, "
        f"holding the other inputs of the untreated group, and R falls from {K.r_with(hbv):.2f} to {K.r_with(hbv, L=hs['L']):.2f}, from tier 3 to tier 2.",
        hbv, "L", 0.90, 0.20, "Lever 2 · treat the cause (L): untreated to suppressed hepatitis B", "Published L values marked; E, V and ρ held at the untreated group's values",
        [(0.90, "untreated HBV"), (hs["L"], "suppressed HBV")], P, 4.0))
    out.append(sweep_segment("lv_V",
        f"Lever three: liver reserve. In the framework, fibrosis progression and decompensation raise vulnerability. Using the ALBI anchors as a what-if on the active viral cirrhosis group: "
        f"at grade one, R is {K.r_with(viral, V=0.35):.3f}; at grade two, {K.r_with(viral, V=0.60):.3f}; at grade three, {K.r_with(viral, V=0.85):.3f}, crossing into tier 3. This is a what-if sweep, not patient data.",
        viral, "V", 0.35, 0.85, "Lever 3 · liver reserve (V): active viral cirrhosis", "ALBI grade anchors marked; a what-if sweep, not patient data",
        [(0.35, "ALBI 1"), (0.60, "ALBI 2"), (0.85, "ALBI 3")], P, 4.5))
    out.append(seg("alb_a", "To ground V in real measurements, we use the Faria et al. cohort from Harvard Dataverse. From measured albumin and bilirubin, each person has an ALBI grade, "
                            "and we use only the group counts, never patient-level records.", one(dict(kind="albi", formula=False)), 6))
    out.append(seg("alb_b", f"Weighting the grade anchors by those counts gives vulnerability: {K.v_from_counts(*K.FARIA_COUNTS['HCC cohort']):.2f} for the cancer cohort and "
                            f"{K.v_from_counts(*K.FARIA_COUNTS['Cirrhosis cohort']):.2f} for cirrhosis. A real measurement, feeding one lever.", one(dict(kind="albi", formula=True)), 6))
    base, d = K.tornado(hbv)
    items = [("L  likelihood", d["L"], True, "treat the cause"), ("E  exposure", d["E"], True, "surveillance footprint"), ("V  vulnerability", d["V"], True, "preserve reserve"), ("ρ  resilience", d["rho"], True, "surveillance quality")]
    order = sorted(items, key=lambda x: -abs(x[1]))
    out.append(tornado_segment("lv_tor",
        f"Putting the levers side by side for untreated hepatitis B, each moved by ten points, from largest to smallest: {order[0][0].split()[1]}, {order[1][0].split()[1]}, "
        f"{order[2][0].split()[1]} and {order[3][0].split()[1]}. R falls by {abs(order[0][1]):.3f} at most. The ranking depends on the group, which is why RMTI is run per cohort.",
        items, "Which lever moves R most? Untreated hepatitis B", f"R now = {base:.3f}. Each lever moves by 0.10 in the risk-reducing direction.", "Illustrative equal steps, not intervention effect sizes."))
    out.append(seg("take", "What this shows and does not show. The arithmetic and the levers are RMTI's own, applied to published rows. But fibrosis-stage inputs are not in the current calculators, so "
                           "ALBI anchors stand in, the after values are scenarios, and nothing here is validated against incident cancer. Surveillance decisions rest with clinicians and guidelines.",
                   one(dict(kind="bullets", title="Reading the liver examples", width=86, items=[
                       ("h", "What it shows"),
                       ("p", "Untreated HBV is the only cohort in tier 3, and stays there after the improvement package."),
                       ("p", "Three levers can move it: surveillance quality (ρ), treating the cause (L), preserving reserve (V)."),
                       ("h", "What it does not show"),
                       ("p", "Fibrosis-stage inputs (F0–F4) are not in the current calculators; ALBI anchors are a stand-in."),
                       ("p", "After-values are scenarios. Nothing is validated against incident HCC or patient outcomes.")])), 10))
    out.append(seg("close", "That is RMTI on the liver: one equation, three levers you can pull, and a clear view of what each would take. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, "
                            "the demo uses no patient data, and nothing here is medical advice.", one(dict(kind="close", title="RMTI · liver case studies")), 7))
    return out


# ============================================================================ 3. flood and heat
def sb_flood_heat():
    cs = K.FLOOD_HEAT_CASES; lil, lag, bam = cs; ev = [K.evaluate(c) for c in cs]; P = K.POSTURE_DISASTER
    out = common_open("VIDEO 3 · CASE STUDIES · FLOOD AND HEAT IN AFRICAN CITIES",
                      "Case studies, part two: disaster science. We apply the same equation to flood and heat risk in three African cities: Lilongwe in Malawi, Lagos in Nigeria, and Bamako in Mali.")
    out.append(seg("map", "Here is how the inputs map to a city, using the RMTI indicator backbone. Exposure is raised by hazards, climate change and urbanisation. Vulnerability is raised by poverty, "
                          "governance and pollution. Resilience comes from risk-management strategy, infrastructure, and health and water security.",
                   one(dict(kind="bullets", title="How the inputs map to a city (RMTI indicator backbone)", width=92, size=14, items=[
                       ("p", "E ← natural and man-made hazards, climate change, accelerated urbanism, health hazards"),
                       ("p", "V ← poverty and inequality, governance and rule of law, pollution and land degradation, fiscal stability"),
                       ("p", "ρ ← risk-management strategy, ICT, energy and urban infrastructure quality, hospital capacity, water and food security"),
                       ("p", "L ← annual probability that the hazard materially strikes (analyst rubric, 1–5 band midpoints)")])), 8))
    out.append(seg("levers", "What can each lever mean on the ground? These are illustrative examples, not evidence-based effect sizes. For flood: keep people out of the floodplain, which acts on exposure; "
                             "improve housing and keep services running, which acts on vulnerability; and build early warning, drainage and emergency health capacity, which raises resilience. "
                             "For heat: reduce the share of people in the hottest neighbourhoods, improve housing and tackle energy poverty, and build cooling centres, heat-health plans and reliable power.",
                   one(dict(kind="bullets", title="Levers in practice: illustrative examples (not effect sizes)", width=96, size=13.5, items=[
                       ("h", "Flood"),
                       ("p", "E: zoning and relocation out of the floodplain  ·  V: housing standards, service continuity  ·  ρ: early warning, drainage and pumping, emergency health capacity"),
                       ("h", "Heat"),
                       ("p", "E: fewer people in the hottest neighbourhoods  ·  V: housing quality, energy poverty, support for older and poorer residents  ·  ρ: cooling centres, heat-health plans, reliable power")])), 10))
    cs_texts = [
        "Published rubric values from the disaster calculator: Lilongwe, pluvial and river flood; Lagos, coastal and pluvial flood; and Bamako, a multi-hazard case of drought, flood and heat. "
        "These are rubric scores, not damage or casualty estimates.",
        "Each city travels the cube. All three combine high likelihood with high exposure and vulnerability.",
        f"With today's resilience, all three land in tier 4, severe: R of {ev[0]['R_now']:.2f} for Lilongwe, {ev[1]['R_now']:.2f} for Lagos, and {ev[2]['R_now']:.2f} for Bamako.",
        "Under scenario resilience targets, all three fall to tier 3, high. These after values are targets, not observed results."]
    out += case_segments("fh", cs, 0.62, [0.07, -0.12, 0.16], "Flood and heat · Lilongwe · Lagos · Bamako", cs_texts,
                         ["Inputs: published rubric values (disaster calculator v2.3.0)", "Each city travels the cube: L → E → V", "ρ now  →  all three: tier 4 Severe",
                          "ρ after (scenario)  →  all three: tier 3 High"],
                         "Rubric scores, not damage or casualty estimates. ρ-after values are scenario targets, not observations.")
    nl = K.to_next_tier(lil)
    out.append(sweep_segment("fh_rho",
        f"Lever one, resilience, for Lilongwe. The calculator's target pathway is 0.43 to 0.53 by 2027 to 2030. R drops below the severe threshold of 0.35 once resilience passes about "
        f"{nl['need']['rho']:.2f}, and the target pathway goes well beyond it.", lil, "rho", 0.25, 0.60, "Lever 1 · resilience (ρ): Lilongwe flood", "Target pathway 0.43–0.53 by 2027–2030 (calculator); all other inputs fixed",
        [(0.25, "now"), (nl["need"]["rho"], "leaves Severe"), (0.43, "target low"), (0.53, "target high")], P, 4.5))
    out.append(sweep_segment("fh_E",
        f"Lever two, exposure, shows why inputs must be audited. For Lagos the published rubric uses exposure 0.65, but the population-based helper gives about 0.98. Same city, same equation: "
        f"R would rise from {K.r_with(lag):.2f} to {K.r_with(lag, E=0.98):.2f}, still severe but close to critical. Sensitivity like this is exactly what an auditable index should expose.",
        lag, "E", 0.50, 1.00, "Lever 2 · exposure (E): Lagos flood, and why inputs are audited", "Rubric E used in the calculator vs the population-derived helper (about 0.98)",
        [(0.65, "rubric used"), (0.98, "population helper")], P, 4.5))
    nb = K.to_next_tier(bam)
    out.append(sweep_segment("fh_V",
        f"Lever three, vulnerability, for Bamako, where drought, flood and heat combine. At vulnerability 0.75, R is {K.r_with(bam):.2f}. Housing quality, service continuity and support for the poorest "
        f"would move this lever. R drops below 0.35 once vulnerability falls to about {nb['need']['V']:.2f}.", bam, "V", 0.50, 0.90, "Lever 3 · vulnerability (V): Bamako drought, flood and heat",
        "Illustrative what-if on one input; all others fixed", [(0.75, "now"), (nb["need"]["V"], "leaves Severe")], P, 4.5))
    out.append(threshold_segment("fh_thr",
        f"For Bamako, which single lever would be enough to leave tier 4? Resilience at least {nb['need']['rho']:.2f}; vulnerability at most {nb['need']['V']:.2f}; exposure at most {nb['need']['E']:.2f}; "
        f"or likelihood at most {nb['need']['L']:.2f}. Likelihood is the hardest to move, because it is set largely by climate. Realistic plans combine levers.",
        bam, "What would it take to leave tier 4? Bamako", f"R now {nb['R']:.3f}; target R below {nb['target']:.2f}. One lever at a time, the others fixed.",
        "Single-lever what-ifs, not a plan: combinations of levers need less of each."))
    base, d = K.tornado(bam)
    items = [("L  likelihood", d["L"], False, "set largely by climate"), ("E  exposure", d["E"], True, "land use, settlement"), ("V  vulnerability", d["V"], True, "housing, services, poverty"), ("ρ  resilience", d["rho"], True, "warning, infrastructure, health")]
    order = sorted(items, key=lambda x: -abs(x[1]))
    out.append(tornado_segment("fh_tor",
        f"Side by side for Bamako, each lever moved by ten points, from largest to smallest: {order[0][0].split()[1]}, {order[1][0].split()[1]}, {order[2][0].split()[1]} and {order[3][0].split()[1]}. "
        "The grey bar is likelihood: it moves R, but a city cannot choose it. The blue bars are the levers a programme can pull.",
        items, "Which lever moves R most? Bamako", f"R now = {base:.3f}. Each lever moves by 0.10 in the risk-reducing direction.", "Illustrative equal steps, not intervention effect sizes."))
    out.append(seg("take", "What this shows and does not show. The arithmetic and the levers are RMTI's own, applied to published rubric values. The after values are scenario targets, R is a relative rubric index, "
                           "and none of this is a forecast, an engineering assessment, or a loss estimate. Investment decisions need local data and professional assessment.",
                   one(dict(kind="bullets", title="Reading the flood and heat examples", width=86, items=[
                       ("h", "What it shows"),
                       ("p", "All three cities sit in tier 4 today; scenario resilience targets move each to tier 3."),
                       ("p", "Single-lever what-ifs show how far each input would need to move, and how sensitive R is to an audited input such as exposure."),
                       ("h", "What it does not show"),
                       ("p", "After-values are scenario targets. R is a relative rubric index, not a forecast or loss estimate."),
                       ("p", "Not an engineering assessment. Rubric scores, not damage or casualty estimates.")])), 10))
    out.append(seg("close", "That is RMTI on flood and heat: one equation, four levers, and a clear view of what each would take to leave a tier. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, "
                            "the demo uses no patient data, and nothing here is engineering advice.", one(dict(kind="close", title="RMTI · flood and heat case studies")), 7))
    return out


# --- delivery directions (used by the 'openai' and 'elevenlabs' voices; printed in the voice script for a human narrator)
import re as _re
_DIR = [(r"^title$", "warm, welcoming and confident, like opening a keynote; slight smile in the voice"),
        (r"^limits$", "calm, clear and serious; slow down on 'not validated', 'not a medical device' and 'no patient data'"),
        (r"^(why)$", "thoughtful and persuasive; build from the problem to the solution"),
        (r"^c[0-6]$", "clear, patient teacher; curious and encouraging; land each key term as it appears"),
        (r"^tiers$", "measured and precise; steady rhythm through the five tiers"),
        (r"^(levers|lv_tor|fh_tor)$", "curious and analytical; let the comparison build; honest about uncertainty"),
        (r"^eal$", "thoughtful; slow slightly on the numbers; a human tone when saying 'who has the most to lose'"),
        (r"^domains$", "steady and informative; separate the two domains with a short pause"),
        (r"^(map|levers)$", "clear, structured, friendly"),
        (r"_a$|^liv_a$|^fh_a$|^dis_a$", "explanatory and grounded; precise about what is published and what is a scenario"),
        (r"_b$", "building, with visible momentum as the points travel"),
        (r"_c1$|_c2$", "matter-of-fact with quiet emphasis on the tier names"),
        (r"^(lv_rho|lv_L|lv_V|fh_rho|fh_E|fh_V)$", "engaged and explanatory; lift slightly on the key finding, then settle"),
        (r"^(lv_thr|fh_thr)$", "careful and exact; read each threshold clearly"),
        (r"^alb_", "grounded and careful; emphasise that only group counts are used"),
        (r"^take$", "serious, careful and humble; slow down on what the work does NOT show"),
        (r"^close$", "warm, sincere and reassuring; end with a gentle, confident sign-off")]


def direction_for(seg_id):
    for pat, d in _DIR:
        if _re.search(pat, seg_id):
            return d
    return "clear and natural"


CHAPTERS = dict(
    explained=[("title", "Introduction and limits"), ("why", "Why an index? Narrative to algorithm"), ("c0", "How R = L·E·V·(1−ρ) works"), ("tiers", "The five fixed tiers"),
               ("levers", "Which lever matters most?"), ("eal", "Beyond R: expected annual loss"), ("domains", "One engine, two domains"), ("close", "Closing")],
    liver=[("title", "Introduction and limits"), ("map", "How the inputs map to the liver"), ("liv_a", "Four published cohorts"), ("lv_rho", "Lever 1: surveillance quality (ρ)"),
           ("lv_thr", "What would it take to leave tier 3?"), ("lv_L", "Lever 2: treat the cause (L)"), ("lv_V", "Lever 3: liver reserve (V)"),
           ("alb_a", "ALBI grades and the Faria et al. cohort"), ("lv_tor", "Which lever moves R most?"), ("take", "What this does and does not show"), ("close", "Closing")],
    flood_heat=[("title", "Introduction and limits"), ("map", "How the inputs map to a city"), ("levers", "Levers in practice for flood and heat"), ("fh_a", "Lilongwe, Lagos, Bamako: published cases"),
                ("fh_rho", "Lever 1: resilience (Lilongwe flood)"), ("fh_E", "Lever 2: exposure (Lagos)"), ("fh_V", "Lever 3: vulnerability (Bamako)"),
                ("fh_thr", "What would it take to leave tier 4?"), ("fh_tor", "Which lever moves R most?"), ("take", "What this does and does not show"), ("close", "Closing")])

BOARDS = dict(explained=("rmti_1_explained", sb_explained), liver=("rmti_2_liver_case_studies", sb_liver), flood_heat=("rmti_3_flood_heat_case_studies", sb_flood_heat))
