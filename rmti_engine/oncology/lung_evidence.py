# Copyright 2026 Cesar Marolla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
lung_evidence.py -- evidence base and variable registry for the lung-cancer
Oncoclastics module (rmti_lung.py, RMTI v2.4.0).

Evidence hierarchy: peer-reviewed sources set every default. The manuscript in
preparation on risk versus treatment and prognosis is listed for transparency
only; no number from it appears in any default, example or anchor.
"""

import json
import os

_REGISTRY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry")


def _load(name):
    with open(os.path.join(_REGISTRY_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


# Source of truth is registry/lung_evidence.json (versioned, hashed, validated by registry.py).
# Add or correct a source with `python registry.py add-evidence ...`; do not edit this list by hand.
_REG = _load("lung_evidence.json")
REGISTRY_VERSION = _REG["registry_version"]
EVIDENCE = _REG["evidence"]                       # peer-reviewed sources (+ the unpublished draft, listed as unused)
EVIDENCE_SUPPLEMENTARY = _REG["supplementary"]    # conference abstracts, secondary analyses: shown, never used for defaults

# Variables each validated L tool already contains (E, V and rho must not reuse them).
# Only tools documented in the sources above are listed; add others after reading their papers.
L_TOOL_VARIABLES = {
    "UK Biobank model (Muller 2017)": ["age", "sex", "smoking_status", "cigarettes_per_day", "age_stopped_smoking",
                                       "smoking_difficulty", "previous_cancer", "family_history",
                                       "emphysema_bronchitis", "allergy_eczema", "fev1"],
    # 5-YEAR incidence model, usable as L (nyears=5, ever-smokers). Variables from the NCI lcmodels manual v4.1.1, LCRAT column.
    # Caution: LCRAT also contains BMI; the metabolic-syndrome V item uses obesity as one of its components, so do not count
    # an obesity criterion twice. "Lung disease" in LCRAT is COPD/emphysema, which blocks the COPD V item.
    "LCRAT (Katki 2016), 5-year incidence": ["age", "sex", "race_ethnicity", "education", "bmi", "years_smoked",
                                             "age_stopped_smoking", "cigarettes_per_day", "pack_years",
                                             "emphysema_bronchitis", "family_history"],
    "Other or custom tool (tick the variables)": [],
}

# Candidate indicators for V (accumulated cost of prior injury). Each names the variable it needs.
V_ITEMS = [
    dict(label="COPD, emphysema or chronic bronchitis", variable="emphysema_bronchitis",
         source="Muller 2017; Nguyen 2025 (respiratory comorbidity 7.9%)"),
    dict(label="Reduced lung function (FEV1 below a locally agreed threshold)", variable="fev1",
         source="Muller 2017"),
    dict(label="Two or more metabolic-syndrome components (IDF 2009)", variable="metabolic_syndrome",
         source="Robien and DiPietro 2024"),
    dict(label="Cardiovascular disease", variable="cardiovascular",
         source="Nguyen 2025 (most frequent comorbidity, 17.9%)"),
]

STRATA_SUGGESTED = [
    "smoking status (never, former, current)", "sex", "histology (adenocarcinoma, squamous, other)",
    "ECOG performance status (<2, >=2)", "stage (IIIA, IIIB, IIIC for stage III cohorts)",
    "driver-mutation status (positive, negative, untested)", "geography or ancestry of the development cohort",
]
