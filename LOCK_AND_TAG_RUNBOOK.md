# Runbook: lock the lung parameters and tag the release (dry-run verified 25 Oct 2026)

Run this on a **copy** first. The hashes below come from the dry run with the shipped placeholders; yours will differ as soon as you confirm or change a
placeholder (L anchors, V range, C ladder, ρ_care values), which is expected. Do not lock until `docs/PREREGISTRATION_lung.md` section 10 is ticked.

## Prerequisites
Python (package requires >=3.8; this dry run used 3.12, the lower bound is untested here) with `pandas numpy openpyxl pyyaml`; Node is not needed. Git. A spreadsheet application (Excel or LibreOffice) to recalculate one workbook.
Bash shown; in PowerShell use `$env:RMTI_REGISTRY_DIR = "$PWD\rmti-python\oncology\registry"` and `Remove-Item Env:RMTI_REGISTRY_DIR`.

## Steps
```bash
git checkout v2.4-rho-bio-ladder-B                      # or apply v2.4-ladderB-repo.patch to a 2.3.1 checkout
python tools/set_lung_ladder.py A                       # A = primary (2.3.1 values); B stays defined as the sensitivity ladder
python tools/build_lung_workbook.py                     # regenerates the lung workbook from the registry
#  open calculators/RMTI_Lung_Calculator_v2.4.0.xlsx in Excel or LibreOffice, let it recalculate, save, close.
#  (Cached values are needed by check_workbooks.py. Expected: 1,041 formulas and 0 errors.)
(cd rmti-python && python -m unittest discover -s tests -t .)
for t in check_release check_workbooks check_cohort check_oncology_sandbox check_lung_sandbox; do python tools/$t.py; done
export RMTI_REGISTRY_DIR="$PWD/rmti-python/oncology/registry"      # absolute path
python tools/registry.py lock                           # hashes the parameter file AND the engine files holding V, C and the tiers
python tools/registry.py validate                       # expect: OK: registry 2026.10.4+... consistent
cp rmti-python/oncology/registry/* ../rmti-platform/rmti_engine/oncology/registry/     # platform gets the same registry and lock file
unset RMTI_REGISTRY_DIR
(cd ../rmti-platform && python registry.py validate && python -m pytest -q tests)
git add -A && git commit -m "Pre-registration lock: ladder A primary, B sensitivity"
git tag prereg-lung-YYYYMMDD && git push && git push --tags
```
Then paste `prereg_lock.json` (registry version, parameter hash, four code hashes) and the commit hash into the registration, and register **before** opening any outcome data.

## What the dry run showed
| Step | Result |
|---|---|
| Checks after switching to A | 67 package tests OK; release, workbook, cohort, both sandbox checks OK; workbook 1,041 formulas, 0 errors |
| `lock` | parameter hash c98c6b8e…92b3 (shipped placeholders); four engine-file hashes recorded |
| Platform with the same registry | `validate` OK; 52 tests pass **with the lock in place** |
| Add evidence after the lock | Allowed: registry 2026.10.4 → 2026.10.5, still consistent, constants hash unchanged |
| Edit `rmti_lung.py` after the lock | `PROBLEMS: LOCKED engine code changed … rmti_lung.py`, exit 1 |
| Edit a locked parameter (L anchor) | `PROBLEMS: LOCKED parameters were changed …`, exit 1 |
| `set_lung_ladder.py B` after the lock | `ERROR: parameters are locked …`, exit 1 |

## Rules that follow
New evidence and cohorts can still be added after the lock; they change the registry version and never a score. Anything that changes a constant needs a new
major version, a stated reason, and results reported for both versions. The lock is not a substitute for the git tag: it does not cover
`oncoclastics/rmti_oncoclastics.py`, the workbooks or the sandbox pages.

## If something fails
`ERROR: registry file not found`: set `RMTI_REGISTRY_DIR` to an **absolute** path (a relative path breaks as soon as you change directory).
`LOCKED engine code changed` with no edit by you: check line endings were not rewritten by an editor (the hash normalises CRLF, so a real difference remains),
or that the platform copy of an engine file differs from the repository's.
