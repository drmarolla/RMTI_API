# Findings while consolidating the source materials

Items to resolve before publishing (paper, preprint, archive, JOSS).

## A. Errors / inconsistencies that affect published claims

1. **IJMADA Table 8, ρ rows are inconsistent with the paper's own elasticity.**
   The ρ rows scale R by ±10% (e.g. Lagos 0.336 / 0.411), which is the elasticity of L, E, V (=1).
   For ρ the elasticity is −ρ/(1−ρ) = −0.25 at ρ=0.20 (stated in the same section).
   Correct values for ρ±10%: Bamako 0.418 / 0.398, Lagos 0.384 / 0.365, Lilongwe 0.434 / 0.406 —
   **no tier changes**. The statement that Lagos flips under "a 10% overestimate of ρ" is wrong;
   ρ must rise ~0.052 (+26% relative) to flip Lagos. The L/E/V rows are correct.
   `rmti.boundary_margins` computes both exactly; `tests/test_core.py` pins the numbers.
2. **HCC Vulnerability anchors vs. worked patients.** ALBI anchors are 0.35/0.60/0.85, but the A/B example uses
   V=0.50 (ALBI 1) and V=0.55 (ALBI 2–3). Either the example V values are rubric-based, or the anchors differ.
   The preprint's R=0.066 for patient B cannot be reproduced from the stated anchors.
3. **ALBI counts.** The archived code uses {1:9, 2:19, 3:1} → V=0.53; preprint Table 1a (35/62/4 %) and V=0.52
   are reproduced by {10, 18, 1}. The package uses the latter. **Verify against the Dataverse file.**
4. **Preprint text vs. Table 1.** Text: "ρ raised by 0.35–0.45" and "30–44% reduction"; Table 1 has Δρ from +0.15
   (active viral) to +0.35, and reductions of −30% to −45%.
5. **Table numbering.** The archived README/code refer to "Table 2/3"; the preprint calls them Table 1/2.

6. **L is a rubric-scaled value, not an annual probability.** In the HCC preprint, ~12.8%/yr incidence maps to L = 0.90 and
   ~1.06%/yr to L = 0.15, yet the text calls L the "annualized HCC likelihood". The mapping from incidence (or an aMAP/THRI
   output) to L is not specified. Publish it explicitly, otherwise R cannot be reproduced from a validated score.

## B. Licensing / disclosure

7. The Excel workbook footer says *"Proprietary; not for redistribution"*; the preprint says CC BY 4.0 and the
   code is Apache-2.0. Pick one per artefact and state it.
8. The IJMADA paper declares a financial interest (paid Harvard DCE course); the HCC preprint says "no competing
   interests". JOSS requires COI disclosure — align the statements.
9. `CITATION.cff` (HCC archive) still has TODOs (repository URL, release date) and no ORCID.

## C. Not reviewed
`RMTI_HCC_Dr_Marolla_Zenodo.docx` and the Windows `.lnk` shortcut were not used.
