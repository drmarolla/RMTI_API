# RMTI Video Series: Narration Scripts, Delivery Notes and YouTube Descriptions

By Dr. Cesar Marolla · Research prototype · Synthetic, illustrative and published aggregate data only · No patient data

## How to use this document

Each video has a timed voice-over script with a delivery note for every scene, then a paste-ready YouTube description with chapters and disclaimers. Times match the delivered videos. If you regenerate the videos with a different voice or your own recording, scene lengths adjust to the audio automatically and a new chapters file is written next to each video (use that file for the description).

Voice options, from basic to most expressive: the built-in offline voice (drafts only); OpenAI gpt-4o-mini-tts, which accepts the delivery notes below as acting directions; ElevenLabs; the free Edge neural voices; or your own recording. The command lines are in UPLOAD_GUIDE.md. Say "rho" for ρ and spell RMTI as letters.

## Video 1 · RMTI explained

Length 5:03 · 15 scenes

### Voice-over script (timed, with delivery notes)

**0:00 · Title** *(warm, welcoming and confident, like opening a keynote; slight smile in the voice)* Welcome. This is the Risk Mechanism Theory Index, RMTI, created and formulated by Dr. Cesar Marolla to quantify systemic risk in disaster science and in oncology. In the next few minutes you will see how one equation turns a hazard, the people exposed, how fragile they are, and how well a system copes, into a single bounded score.

**0:23 · The limits** *(calm, clear and serious; slow down on 'not validated', 'not a medical device' and 'no patient data')* A reminder before we start. RMTI is a research prototype: not validated, not a medical device, and not for patient-care or emergency decisions. Everything here uses illustrative values, published rows, or aggregate counts. No patient data appears.

**0:42 · Why an index** *(thoughtful and persuasive; build from the problem to the solution)* Why an index? Risk decisions are often made from narrative: the loudest voice, or the most recent event. RMTI moves from narrative to algorithm. Four inputs, each between zero and one, each with a stated meaning and source. And the same fixed thresholds for every patient, every city and every year, so a score can be compared, audited and challenged.

**1:06 · The equation** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* The equation multiplies four bounded factors: likelihood, exposure, vulnerability, and resilience, which enters as one minus rho.

**1:17 · L, likelihood** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* L is likelihood: how probable the hazard is in a year. In oncology it comes from a validated risk score, such as aMAP for liver cancer, and is not re-derived. In disaster science it is the annual probability that a flood, fire or heat event materially strikes.

**1:35 · E, exposure** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* E is exposure: who or what is in harm's way. For liver surveillance it is the share of the at-risk population inside the programme's footprint. For a city it is the share of people and assets inside the hazard zone.

**1:49 · V, vulnerability** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* V is vulnerability: how badly those exposed are hurt. For the liver it is reserve, taken from the ALBI grade, which uses albumin and bilirubin. For a city it reflects housing, services, poverty and governance.

**2:04 · Inherent risk** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* Multiply L, E and V and you get the inherent risk: the score if nothing cushioned it.

**2:11 · Resilience** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* Resilience, rho, is the fraction of that inherent risk the system absorbs. Because it enters as one minus rho, more resilience always means less residual risk.

**2:23 · Improved state** *(clear, patient teacher; curious and encouraging; land each key term as it appears)* And that is where action lives. Improve surveillance quality, early warning or infrastructure, raise rho, and the residual risk R falls.

**2:33 · Fixed tiers** *(measured and precise; steady rhythm through the five tiers)* R lands in one of five fixed tiers: low, moderate, high, severe and critical. Each tier carries a posture. For liver surveillance, it runs from usual-care monitoring at tier one to an immediate, resourced pathway at tier five. For cities, from baseline monitoring to an immediate, system-level response.

**2:54 · Levers** *(curious and analytical; let the comparison build; honest about uncertainty)* Which lever matters most? Move each factor by ten points in the risk-reducing direction and see how far R falls. In this example likelihood moves it most, by 0.029, followed by vulnerability, exposure and resilience. But equal steps are not equal efforts, and likelihood is often set by nature or biology, so programmes mostly act through exposure, vulnerability and resilience.

**3:22 · Expected annual loss** *(thoughtful; slow slightly on the numbers; a human tone when saying 'who has the most to lose')* R measures residual risk, not how bad a miss would be. A second layer, expected annual loss, multiplies likelihood by consequence and by one minus rho. Take two liver patients in the same tier. Patient A has R of 0.072 and would be caught early and cured. Patient B has R of 0.066 and would present advanced. R ranks A first, but EAL is 0.20 for B against 0.072 for A, nearly three times higher. Within a tier, EAL shows who has the most to lose if surveillance is slow.

**3:59 · Two domains** *(steady and informative; separate the two domains with a short pause)* One engine, two domains. The same three indicator families feed E, V and rho. In disaster science, hazards, climate change and urbanisation raise exposure; poverty, governance and pollution raise vulnerability; and risk-management strategy, infrastructure, and health and water security supply resilience. In liver cancer, the size of the at-risk population feeds exposure; reduced liver reserve, metabolic disease and fibrosis progression feed vulnerability; and surveillance uptake, test quality, access to cure and care coordination feed resilience.

**4:39 · Closing** *(warm, sincere and reassuring; end with a gentle, confident sign-off)* That is RMTI: one bounded equation, four levers, five fixed tiers, and two domains. Next, see it applied: liver cancer surveillance, and flood and heat risk in African cities. Thank you. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, the demo uses no patient data, and nothing here is medical or engineering advice.

### Title options

RMTI explained: one equation for oncology and disaster risk (Dr. Cesar Marolla)

R = L·E·V·(1−ρ): the four levers of the Risk Mechanism Theory Index

### YouTube description (copy and paste)

Research prototype · NOT validated · NOT a medical device · NOT for patient-care or emergency decisions. No patient data is used or shown.

The Risk Mechanism Theory Index (RMTI), created and formulated by Dr. Cesar Marolla, scores systemic risk with one bounded equation: R = L · E · V · (1 − ρ). This 5-minute explainer shows what each lever means for cancer surveillance and for disaster science, how R lands on five fixed tiers, which lever moves R most, and why expected annual loss (EAL) ranks cases within a tier.

CHAPTERS

0:00 Introduction and limits

0:42 Why an index? Narrative to algorithm

1:06 How R = L·E·V·(1−ρ) works

2:33 The five fixed tiers

2:54 Which lever matters most?

3:22 Beyond R: expected annual loss

3:59 One engine, two domains

4:39 Closing

SOURCES AND DATA

• RMTI-HCC calculator v2.3.0 and RMTI disaster science calculator v2.3.0 (worked examples)

• Live demo and API portal: [add link]

• Paper or archive record: [add link]

• Code (Apache-2.0): [add link]

IMPORTANT LIMITS

R is a relative, rubric-based index, not a probability, forecast, engineering assessment or loss estimate. Parameters are uncalibrated placeholders and nothing here has been validated against real outcomes. RMTI does not diagnose, stage or predict outcomes for any person, and it is not a basis for patient-care or emergency decisions; those rest with treating clinicians, current guidelines and qualified professionals. Examples are teaching illustrations, and after-values are scenarios, not observations. No patient data is used or shown.

ABOUT

Dr. Cesar Marolla, creator of RMTI · ORCID 0000-0001-8498-7380. Independent academic work, not an official product of the World Bank Group, Harvard University or any other institution. Released under Apache-2.0 and provided "as is", without warranty. Narration: synthetic voice; captions available.

#RMTI #RiskManagement #Oncology #DisasterScience #Resilience #OpenScience

### Tags

RMTI, Risk Mechanism Theory Index, risk index, systemic risk, oncology, hepatocellular carcinoma, disaster risk, resilience, expected annual loss, open science

## Video 2 · Liver cancer (HCC) case studies

Length 5:00 · 16 scenes

### Voice-over script (timed, with delivery notes)

**0:00 · Title** *(warm, welcoming and confident, like opening a keynote; slight smile in the voice)* Case studies, part one: liver cancer. We use RMTI as a triage layer for hepatocellular carcinoma surveillance. The question is: which patient groups need surveillance first, and which lever moves each group the most?

**0:16 · The limits** *(calm, clear and serious; slow down on 'not validated', 'not a medical device' and 'no patient data')* A reminder before we start. RMTI is a research prototype: not validated, not a medical device, and not for patient-care or emergency decisions. Everything here uses illustrative values, published rows, or aggregate counts. No patient data appears.

**0:35 · Input mapping** *(clear, structured, friendly)* Here is how the inputs map to the liver. L comes from a validated risk score. E is the share of the at-risk population in the surveillance footprint. V is liver reserve, from the ALBI grade. And rho is surveillance effectiveness, on a published ladder from none, at 0.15, to optimised, at 0.65.

**0:56 · Cohorts: inputs** *(explanatory and grounded; precise about what is published and what is a scenario)* Four published cohort rows from the RMTI HCC calculator: untreated hepatitis B, active viral cirrhosis, alcohol-related cirrhosis, and cured hepatitis C cirrhosis. The after values for resilience are back-solved to match the published table, so they are scenarios, not observations.

**1:18 · Cohorts: travel the cube** *(building, with visible momentum as the points travel)* Each group travels the cube: likelihood, exposure, vulnerability. Notice how far out untreated hepatitis B sits on likelihood.

**1:28 · Cohorts: today** *(matter-of-fact with quiet emphasis on the tier names)* With today's surveillance, untreated hepatitis B is the only group in tier 3, high, with R of 0.31. The three cirrhosis groups sit in tier 2, moderate.

**1:39 · Cohorts: after** *(matter-of-fact with quiet emphasis on the tier names)* After the improvement package, cured hepatitis C falls to tier 1, low. But untreated hepatitis B stays in tier 3, high, even though its R falls by 39 percent.

**1:52 · Lever 1: resilience** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever one: resilience. Walk untreated hepatitis B up the surveillance ladder. None, usual care, outreach, specialist: R falls, but stays in tier 3. Only optimised surveillance, ultrasound plus AFP with reliable access to cure, at 0.65, brings R to 0.12, below 0.15, into tier 2.

**2:16 · Single-lever thresholds** *(careful and exact; read each threshold clearly)* Which single lever would be enough to leave tier 3? Resilience needs to reach at least 0.57, which the optimised rung exceeds. Vulnerability would have to fall to 0.26, below the lowest ALBI anchor of 0.35, so reserve alone cannot do it. Exposure would need to fall to 0.34, or likelihood to 0.43.

**2:41 · Lever 2: treat the cause** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever two: treat the cause. In the published table, untreated hepatitis B carries a likelihood of 0.90, and suppressed hepatitis B 0.20. Move only that lever, holding the other inputs of the untreated group, and R falls from 0.31 to 0.07, from tier 3 to tier 2.

**3:03 · Lever 3: liver reserve** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever three: liver reserve. In the framework, fibrosis progression and decompensation raise vulnerability. Using the ALBI anchors as a what-if on the active viral cirrhosis group: at grade one, R is 0.067; at grade two, 0.115; at grade three, 0.164, crossing into tier 3. This is a what-if sweep, not patient data.

**3:30 · ALBI grades** *(explanatory and grounded; precise about what is published and what is a scenario)* To ground V in real measurements, we use the Faria et al. cohort from Harvard Dataverse. From measured albumin and bilirubin, each person has an ALBI grade, and we use only the group counts, never patient-level records.

**3:46 · V from counts** *(building, with visible momentum as the points travel)* Weighting the grade anchors by those counts gives vulnerability: 0.52 for the cancer cohort and 0.48 for cirrhosis. A real measurement, feeding one lever.

**3:58 · Side by side** *(curious and analytical; let the comparison build; honest about uncertainty)* Putting the levers side by side for untreated hepatitis B, each moved by ten points, from largest to smallest: vulnerability, exposure, likelihood and resilience. R falls by 0.057 at most. The ranking depends on the group, which is why RMTI is run per cohort.

**4:19 · What it shows and does not** *(serious, careful and humble; slow down on what the work does NOT show)* What this shows and does not show. The arithmetic and the levers are RMTI's own, applied to published rows. But fibrosis-stage inputs are not in the current calculators, so ALBI anchors stand in, the after values are scenarios, and nothing here is validated against incident cancer. Surveillance decisions rest with clinicians and guidelines.

**4:42 · Closing** *(warm, sincere and reassuring; end with a gentle, confident sign-off)* That is RMTI on the liver: one equation, three levers you can pull, and a clear view of what each would take. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, the demo uses no patient data, and nothing here is medical advice.

### Title options

Liver cancer (HCC) surveillance with RMTI: HBV, cirrhosis and three levers (case studies)

Which lever moves liver cancer risk most? RMTI on HBV, viral, alcohol and cured-HCV cirrhosis

### YouTube description (copy and paste)

Research prototype · NOT validated · NOT a medical device · NOT for patient-care or emergency decisions. No patient data is used or shown.

Case studies on hepatocellular carcinoma (HCC) surveillance with the Risk Mechanism Theory Index, created and formulated by Dr. Cesar Marolla. We run four published cohort rows (untreated hepatitis B, active viral cirrhosis, alcohol-related cirrhosis, cured hepatitis C cirrhosis), then pull three levers on them: surveillance quality (ρ), treating the cause (L) and liver reserve (V), and ask what a single lever would need to reach to leave tier 3. Vulnerability is grounded in the Faria et al. cohort using aggregate ALBI-grade counts only (n = 29 HCC, n = 25 cirrhosis; V = 0.52 and 0.48). After-values are scenarios back-solved to a published table, not observations. Fibrosis-stage inputs are not in the current calculators, so ALBI anchors stand in.

CHAPTERS

0:00 Introduction and limits

0:35 How the inputs map to the liver

0:56 Four published cohorts

1:52 Lever 1: surveillance quality (ρ)

2:16 What would it take to leave tier 3?

2:41 Lever 2: treat the cause (L)

3:03 Lever 3: liver reserve (V)

3:30 ALBI grades and the Faria et al. cohort

3:58 Which lever moves R most?

4:19 What this does and does not show

4:42 Closing

SOURCES AND DATA

• RMTI-HCC calculator v2.3.0, Table 2 (published cohort rows)

• Faria et al. cohort, Harvard Dataverse, doi:10.7910/DVN/A81UVO (aggregate ALBI-grade counts only)

• ALBI score: Johnson et al., J Clin Oncol 2015;33:550–558

• Live demo and API portal: [add link]

• Paper or archive record: [add link]

• Code (Apache-2.0): [add link]

IMPORTANT LIMITS

R is a relative, rubric-based index, not a probability, forecast, engineering assessment or loss estimate. Parameters are uncalibrated placeholders and nothing here has been validated against real outcomes. RMTI does not diagnose, stage or predict outcomes for any person, and it is not a basis for patient-care or emergency decisions; those rest with treating clinicians, current guidelines and qualified professionals. Examples are teaching illustrations, and after-values are scenarios, not observations. No patient data is used or shown.

ABOUT

Dr. Cesar Marolla, creator of RMTI · ORCID 0000-0001-8498-7380. Independent academic work, not an official product of the World Bank Group, Harvard University or any other institution. Released under Apache-2.0 and provided "as is", without warranty. Narration: synthetic voice; captions available.

#RMTI #HCC #LiverCancer #Hepatology #Oncology #OpenScience

### Tags

RMTI, hepatocellular carcinoma, HCC surveillance, hepatitis B, cirrhosis, ALBI score, liver cancer, risk triage, surveillance, open science

## Video 3 · Flood and heat case studies

Length 4:50 · 15 scenes

### Voice-over script (timed, with delivery notes)

**0:00 · Title** *(warm, welcoming and confident, like opening a keynote; slight smile in the voice)* Case studies, part two: disaster science. We apply the same equation to flood and heat risk in three African cities: Lilongwe in Malawi, Lagos in Nigeria, and Bamako in Mali.

**0:13 · The limits** *(calm, clear and serious; slow down on 'not validated', 'not a medical device' and 'no patient data')* A reminder before we start. RMTI is a research prototype: not validated, not a medical device, and not for patient-care or emergency decisions. Everything here uses illustrative values, published rows, or aggregate counts. No patient data appears.

**0:32 · Input mapping** *(clear, structured, friendly)* Here is how the inputs map to a city, using the RMTI indicator backbone. Exposure is raised by hazards, climate change and urbanisation. Vulnerability is raised by poverty, governance and pollution. Resilience comes from risk-management strategy, infrastructure, and health and water security.

**0:54 · Levers** *(curious and analytical; let the comparison build; honest about uncertainty)* What can each lever mean on the ground? These are illustrative examples, not evidence-based effect sizes. For flood: keep people out of the floodplain, which acts on exposure; improve housing and keep services running, which acts on vulnerability; and build early warning, drainage and emergency health capacity, which raises resilience. For heat: reduce the share of people in the hottest neighbourhoods, improve housing and tackle energy poverty, and build cooling centres, heat-health plans and reliable power.

**1:29 · Cities: inputs** *(explanatory and grounded; precise about what is published and what is a scenario)* Published rubric values from the disaster calculator: Lilongwe, pluvial and river flood; Lagos, coastal and pluvial flood; and Bamako, a multi-hazard case of drought, flood and heat. These are rubric scores, not damage or casualty estimates.

**1:47 · Cities: travel the cube** *(building, with visible momentum as the points travel)* Each city travels the cube. All three combine high likelihood with high exposure and vulnerability.

**1:54 · Cities: today** *(matter-of-fact with quiet emphasis on the tier names)* With today's resilience, all three land in tier 4, severe: R of 0.42 for Lilongwe, 0.37 for Lagos, and 0.41 for Bamako.

**2:07 · Cities: scenario** *(matter-of-fact with quiet emphasis on the tier names)* Under scenario resilience targets, all three fall to tier 3, high. These after values are targets, not observed results.

**2:16 · Lever 1: resilience** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever one, resilience, for Lilongwe. The calculator's target pathway is 0.43 to 0.53 by 2027 to 2030. R drops below the severe threshold of 0.35 once resilience passes about 0.38, and the target pathway goes well beyond it.

**2:37 · Lever 2: exposure** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever two, exposure, shows why inputs must be audited. For Lagos the published rubric uses exposure 0.65, but the population-based helper gives about 0.98. Same city, same equation: R would rise from 0.37 to 0.56, still severe but close to critical. Sensitivity like this is exactly what an auditable index should expose.

**3:04 · Lever 3: vulnerability** *(engaged and explanatory; lift slightly on the key finding, then settle)* Lever three, vulnerability, for Bamako, where drought, flood and heat combine. At vulnerability 0.75, R is 0.41. Housing quality, service continuity and support for the poorest would move this lever. R drops below 0.35 once vulnerability falls to about 0.64.

**3:28 · Single-lever thresholds** *(careful and exact; read each threshold clearly)* For Bamako, which single lever would be enough to leave tier 4? Resilience at least 0.31; vulnerability at most 0.64; exposure at most 0.73; or likelihood at most 0.69. Likelihood is the hardest to move, because it is set largely by climate. Realistic plans combine levers.

**3:51 · Side by side** *(curious and analytical; let the comparison build; honest about uncertainty)* Side by side for Bamako, each lever moved by ten points, from largest to smallest: vulnerability, resilience, likelihood and exposure. The grey bar is likelihood: it moves R, but a city cannot choose it. The teal bars are the levers a programme can pull.

**4:10 · What it shows and does not** *(serious, careful and humble; slow down on what the work does NOT show)* What this shows and does not show. The arithmetic and the levers are RMTI's own, applied to published rubric values. The after values are scenario targets, R is a relative rubric index, and none of this is a forecast, an engineering assessment, or a loss estimate. Investment decisions need local data and professional assessment.

**4:32 · Closing** *(warm, sincere and reassuring; end with a gentle, confident sign-off)* That is RMTI on flood and heat: one equation, four levers, and a clear view of what each would take to leave a tier. I'm Dr. Cesar Marolla. The code is open under Apache 2.0, the demo uses no patient data, and nothing here is engineering advice.

### Title options

Flood and heat risk with RMTI: Lilongwe, Lagos and Bamako (case studies)

What would it take to leave Severe? RMTI levers for flood and heat in African cities

### YouTube description (copy and paste)

Research prototype · NOT validated · NOT a medical device · NOT for patient-care or emergency decisions. No patient data is used or shown.

Case studies in disaster science with the Risk Mechanism Theory Index, created and formulated by Dr. Cesar Marolla. Using the published rubric values in the RMTI disaster calculator (v2.3.0), we score Lilongwe (pluvial and river flood), Lagos (coastal and pluvial flood) and Bamako (a multi-hazard case of drought, flood and heat), then run lever what-ifs: resilience for Lilongwe, exposure for Lagos (rubric 0.65 versus about 0.98 from the population helper) and vulnerability for Bamako, and show what a single lever would need to reach to leave tier 4. All three sit in tier 4 today; scenario resilience targets move each to tier 3. After-values are scenario targets, not observations. Heat appears only inside the Bamako multi-hazard case.

CHAPTERS

0:00 Introduction and limits

0:32 How the inputs map to a city

0:54 Levers in practice for flood and heat

1:29 Lilongwe, Lagos, Bamako: published cases

2:16 Lever 1: resilience (Lilongwe flood)

2:37 Lever 2: exposure (Lagos)

3:04 Lever 3: vulnerability (Bamako)

3:28 What would it take to leave tier 4?

3:51 Which lever moves R most?

4:10 What this does and does not show

4:32 Closing

SOURCES AND DATA

• RMTI disaster science calculator v2.3.0 (worked examples: Lilongwe, Lagos, Bamako)

• Live demo and API portal: [add link]

• Paper or archive record: [add link]

• Code (Apache-2.0): [add link]

IMPORTANT LIMITS

R is a relative, rubric-based index, not a probability, forecast, engineering assessment or loss estimate. Parameters are uncalibrated placeholders and nothing here has been validated against real outcomes. RMTI does not diagnose, stage or predict outcomes for any person, and it is not a basis for patient-care or emergency decisions; those rest with treating clinicians, current guidelines and qualified professionals. Examples are teaching illustrations, and after-values are scenarios, not observations. No patient data is used or shown.

ABOUT

Dr. Cesar Marolla, creator of RMTI · ORCID 0000-0001-8498-7380. Independent academic work, not an official product of the World Bank Group, Harvard University or any other institution. Released under Apache-2.0 and provided "as is", without warranty. Narration: synthetic voice; captions available.

#RMTI #DisasterScience #FloodRisk #HeatRisk #UrbanResilience #OpenScience

### Tags

RMTI, disaster risk, flood risk, heat risk, Lilongwe, Lagos, Bamako, urban resilience, climate adaptation, African cities, open science

## Before you publish

Confirm the Faria et al. dataset's licence and preferred citation on its Dataverse page. Only group counts from your workbook are used.

Fill in the [add link] placeholders. No repository, paper or portal address has been guessed.

YouTube asks whether content is altered or synthetic. Check its current wording when you upload; the description already states that the narration is a synthetic voice.

Upload the .srt file as English captions. The _CC video has captions burned into a band under the picture; the other file has a caption track you can switch on and off.

Watch each video once before publishing. Consider Unlisted first for a read-through of the wording.

## Recording your own voice

The scripts above are also available as three printable reading-script PDFs, one per video, with a one-page recording guide, a "Save as" file name for every scene, delivery notes and pronunciation hints.

## Contact

Add this line at the very end of each YouTube description:

Contact: cesar.marolla@alumni.harvard.edu

Cesar Marolla · cesar.marolla@alumni.harvard.edu
