# Oncoclastics Platform (Streamlit + FastAPI), built on the RMTI engine

Interactive web interface and REST API around the RMTI time-indexed engine v2.4.0 (vendored unchanged in `rmti_engine/`).
**Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions.** See `DISCLAIMER.md`.

## Run locally
```bash
pip install -r requirements.txt
uvicorn api:app --port 8000          # API, docs at http://localhost:8000/docs
streamlit run app.py                 # UI at http://localhost:8501
RMTI_API_URL=http://localhost:8000 streamlit run app.py   # UI through the API instead of in-process
python -m unittest discover -s tests # service-layer tests
```
Docker: `docker build -t rmti . && docker run -p 8000:8000 -p 8501:8501 rmti`

## Terminology (RMTI v2.4.0)
**Oncoclastics** is the application of hazard-exposure-vulnerability-resilience assessment, as developed in disaster-risk reduction, to the fragmentation of cancer-related trajectories, in two named senses: **biological** (L, E, V, ρ_bio) and **care-system** (ρ_care). **Disaster Science** is the other domain. The vendored `rmti_engine/oncoclastics/` module is used unchanged. See its `TERMINOLOGY_NOTE.md`.

## Domains
Oncoclastics, with cancer-site modules HCC (published application) and lung cancer (proposed extension, `rmti_engine/oncology/rmti_lung.py` and `lung_evidence.py`, vendored from RMTI v2.4.0); and Disaster Science. API: `domain` = `oncoclastics` with optional `site` (`hcc` default, or `lung`), or `disaster_science`; the older keys `hcc`, `lung`, `disaster` still work.
Each domain keeps its own vocabulary and anchors; all scoring goes through the one shared core. Domains are not interchangeable: add a disease by writing a new module, not by reusing another disease's anchors.

## Secure practitioner workspace (private instances only)
`secure_store.py`: scrypt password hashing, per-user envelope encryption (Fernet), lockout, audit log of actions only, identifier refusal,
export and account deletion. Enable with `RMTI_ENABLE_VAULT=1` and `RMTI_INVITE_CODE`. See `DEPLOY.md` for hosting and the pre-use checklist.

## Layout
| File | Role |
|---|---|
| `rmti_engine/` | Your core, oncology (HCC), disaster_climate and dynamic modules, untouched |
| `service.py` | Framework-free functions: snapshot, trajectory, cohort ranking, validation metrics (C-index, AUC, Kaplan-Meier, tier table) |
| `fhir_export.py` | FHIR R4 RiskAssessment export (research use: status preliminary, tier not probability, pseudonymous subject) |
| `secure_store.py` | Encrypted per-practitioner workspace |
| `DEPLOY.md`, `docker-compose.yml`, `Caddyfile` | Hosting instructions and HTTPS setup |
| `api.py` | FastAPI: `GET /health`, `POST /v1/snapshot`, `/v1/trajectory`, `/v1/cohort/rank`, `/v1/validate`, `/v1/oncoclastics/two-sense`, `/v1/oncoclastics/trajectory`, `/v1/fhir/risk-assessment`; engine errors return HTTP 422 |
| `app.py` | Streamlit UI: Snapshot, Trajectory, Cohort ranking, Retrospective validation, About |
| `sample_data/` | Six published HCC cohorts (snapshot) and a synthetic serial cohort (validation) |

## API example
```bash
curl -X POST localhost:8000/v1/trajectory -H 'Content-Type: application/json' -d '{
 "domain":"hcc","L":0.30,"E":0.65,"C":3,"rho0":0.20,
 "observations":[2,1,null,0],"delivery":[0.40,0.55,0.70,0.75]}'
```

## Access modes (set by environment variables)
| Setting | Effect |
|---|---|
| none | Open sandbox. Use for the public link, synthetic or de-identified teaching data only |
| `RMTI_ACCESS_CODES="a,b"` | Streamlit asks for a shared code before showing anything |
| `RMTI_API_KEYS="k1,k2"` | Every `/v1/*` API call needs an `X-API-Key` header (`/health` stays open) |
| `RMTI_API_URL` | UI calls the API instead of the in-process engine |

Every CSV upload passes an identifier guard (refuses columns such as name, MRN, DOB, email, phone, address, ZIP, and cell values that look like emails, phone numbers or SSNs). It prevents accidents; it does not make real patient data safe.
Validation adds bootstrap 95% CIs (C-index final, baseline, and their difference), Wilson intervals by tier, and a logistic slope on log(R); `POST /v1/validate` exposes the same.

## Deploying for collaborators
Streamlit Community Cloud or any container host works for the synthetic sandbox. Before anyone enters real patient data:
ethics approval, data-use agreement, authentication (e.g. reverse proxy with SSO), HTTPS, no logging of request bodies, and a
privacy review. The app stores nothing server-side, but hosting it publicly does not make patient-data entry safe.

## Updating evidence, cohorts and parameters
See `UPDATING.md`. Evidence and cohort metadata are data (versioned, hashed, validated); model constants change only through a reviewed release; every API response carries `X-RMTI-Registry`.
## 4D Lab Live Motion Videos & Case Studies (`files 3D Lab live.zip`)
This archive contains live motion video demonstrations, closed-caption subtitle tracks, chapter markers, and Python scripts illustrating the RMTI modules across Oncoclastics and Disaster Science:

* **Module 1: RMTI Explained**
  * `rmti_1_explained.mp4` & `rmti_1_explained_CC.mp4` — Core framework overview (standard and burned-in closed captions)
  * `rmti_1_explained.srt` & `.vtt` — Subtitle tracks
  * `rmti_1_explained_chapters.py` — Chapter timestamp definitions
* **Module 2: Liver Case Studies (Oncoclastics / HCC)**
  * `rmti_2_liver_case_studies.mp4` & `rmti_2_liver_case_studies_CC.mp4` — Liver trajectory case study video
  * `rmti_2_liver_case_studies.srt` & `.vtt` — Subtitle tracks
  * `rmti_2_liver_case_studies_chapters.py` — Chapter timestamp definitions
* **Module 3: Flood & Heat Case Studies (Disaster Science)**
  * `rmti_3_flood_heat_case_studies.mp4` & `rmti_3_flood_heat_case_studies_CC.mp4` — Disaster science case study video
  * `rmti_3_flood_heat_case_studies.srt` & `.vtt` — Subtitle tracks
  * `rmti_3_flood_heat_case_studies_chapters.py` — Chapter timestamp definitions
* **Lab Script**
  * `6_Live_4D_Lab.py` — Main Python source script for the 4D Lab session

To use: download `files 3D Lab live.zip` from the repository root (or pull via Git LFS), extract the archive locally, and keep the `.srt`/`.vtt` files in the same folder as the `.mp4` videos for automatic caption loading.
