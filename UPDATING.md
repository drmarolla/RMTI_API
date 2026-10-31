# Updating the evidence, cohorts and calculators

New papers, cohorts and retrospective datasets can be added at any time. The design separates what may change quickly
from what must not.

| Layer | How it changes | Effect on scores |
|---|---|---|
| Evidence entries (`lung_evidence.json`) | `python registry.py add-evidence entry.json` | None. Version and hash change |
| Cohort metadata (`cohorts.json`) | `python registry.py register-cohort cohort.json` (flags probable overlap with an existing cohort) | None |
| Support report for a dataset | `POST /v1/registry/ladder-support`, or the upload box in the Lung tab | None. Nothing is stored |
| Model constants: L anchors, ρ_bio ladder (`lung_parameters.json`) | A proposal, human review, then a new registry version | Yes, so it is a release, never automatic |
| Equations and tiers | Not updatable here. A new engine version | Yes |

## Rules
1. **Data never changes a constant by itself.** A cohort produces a report. A person proposes a change
   (`POST /v1/registry/proposals`, admin key), the change is reviewed, and it ships as a new registry version.
2. **Pre-registration.** After you choose the L anchors, v_lo/v_hi and ρ_bio values, run `python registry.py lock`.
   From then on `validate` (and CI) fails if those values change without a new lock, so a quiet edit cannot happen.
3. **Only peer-reviewed sources go in `evidence`.** Abstracts, theses and secondary analyses go in `supplementary`.
   A source whose numbers you could not read is marked `pending_verification` and cannot support any claim.
4. **Independence.** Registering a cohort from the same centre and overlapping years as an existing one is flagged:
   two papers from one centre are not two pieces of evidence.
5. **Traceability.** Every API response carries `X-RMTI-Registry: <version>+<hash>`. Quote it with any number.

## Adding a source
1. Write `entry.json` with: id, status, cite, design, findings, use, limits, verified (`full_text`, `abstract`,
   `abstract_partial`, `snippet`), and optionally supports, cancer_scope, n.
2. `python registry.py add-evidence entry.json` (add `--supplementary` for abstracts and secondary analyses).
3. `python registry.py validate`. CI repeats it.

## Checking a new cohort against the ladder
Upload rows with `ecog` (0–4), `time` (>0) and `event` (0/1). For each adjacent step the report gives events, a crude
rate ratio with a 95% interval and a verdict: separates, inconclusive, reversed, sparse, or no data. A dataset that
pools ECOG 3 and 4 or has few events at ECOG 4 cannot calibrate those steps; keep them provisional.

## After a registry change that alters a constant
Run in the repository, in this order, and ship only if every check passes:
```
python tools/build_lung_workbook.py
python /path/to/xlsx/scripts/recalc.py calculators/RMTI_Lung_Calculator_v2.4.0.xlsx   # fills cached values; check_workbooks needs them
python tools/check_workbooks.py && python tools/check_lung_sandbox.py && python tools/check_release.py
```
The lung sandbox page carries its own copy of the ladder; `check_lung_sandbox.py` fails if it differs from the registry.

## Deployment note
The registry is part of the image. In production, update it by committing the JSON and redeploying (the audit trail is
git). The proposals folder (`data/proposed`) must sit on a mounted volume, as `data/` already does in
`docker-compose.yml`; on Cloud Run use a Cloud Storage volume or a database instead, because container disks are lost.
Set `RMTI_ADMIN_KEYS` to enable proposals; with no key set they are disabled, not open.

## Switching the lung ladder (A or B) and what the lock covers
`python tools/set_lung_ladder.py A|B` changes the active ladder in the registry and the lung sandbox together; rebuild the workbook, recalculate it and
run the checks afterwards. It is refused once locked. `python tools/registry.py lock` now hashes the parameter file and the engine files that hold the V range,
consequence ladder and tiers (`core/rmti_core.py`, `dynamic/rmti_dynamic.py`, `oncology/rmti_lung.py`, `oncology/lung_evidence.py`); line endings are normalised.
See `PREREGISTRATION_lung.md` in the repository docs.
