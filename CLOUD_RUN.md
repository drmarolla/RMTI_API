# Cloud Run: exact steps (public, stateless layer)

Checked 25 Oct 2026 against Google's gcloud reference for the `--add-volume`, `--add-volume-mount` and `--set-secrets` flags.
I could not run gcloud for you: test every step once in a throwaway project first. This layer takes **no patient data**.

## 0. Variables
```bash
export PROJECT_ID=your-project-id
export REGION=us-central1            # a European region if your audience needs it
export BUCKET=${PROJECT_ID}-rmti-proposals
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

## 1. Secrets, bucket, service account
```bash
openssl rand -hex 32 | gcloud secrets create rmti-api-key   --data-file=-     # clients send X-API-Key
openssl rand -hex 32 | gcloud secrets create rmti-admin-key --data-file=-     # reviewers send X-Admin-Key
gcloud storage buckets create gs://$BUCKET --location=$REGION --uniform-bucket-level-access --public-access-prevention
gcloud iam service-accounts create rmti-run --display-name "RMTI Cloud Run"
SA=rmti-run@${PROJECT_ID}.iam.gserviceaccount.com
for s in rmti-api-key rmti-admin-key; do
  gcloud secrets add-iam-policy-binding $s --member serviceAccount:$SA --role roles/secretmanager.secretAccessor; done
gcloud storage buckets add-iam-policy-binding gs://$BUCKET --member serviceAccount:$SA --role roles/storage.objectUser
```

## 2. Deploy the API (from the rmti-platform folder)
```bash
gcloud run deploy rmti-api --source . --region $REGION --service-account $SA \
  --allow-unauthenticated --max-instances 3 --memory 512Mi \
  --set-env-vars RMTI_ROLE=api,RMTI_PROPOSALS=/mnt/proposals \
  --set-secrets RMTI_API_KEYS=rmti-api-key:latest,RMTI_ADMIN_KEYS=rmti-admin-key:latest \
  --add-volume name=proposals,type=cloud-storage,bucket=$BUCKET \
  --add-volume-mount volume=proposals,mount-path=/mnt/proposals
```
`--allow-unauthenticated` only opens the door to the service URL. The application still requires `X-API-Key` on every
route except `/health`, and `X-Admin-Key` for proposals. To make scoring public for a teaching demo, remove the
`RMTI_API_KEYS` line; keep `RMTI_ADMIN_KEYS`, so the proposal routes stay locked.

## 3. Deploy the UI (no secrets, no vault, no volume)
```bash
gcloud run deploy rmti-app --source . --region $REGION --service-account $SA \
  --allow-unauthenticated --max-instances 3 --memory 1Gi --session-affinity --timeout 3600 \
  --set-env-vars RMTI_ROLE=ui
```
Do **not** set `RMTI_ENABLE_VAULT` here: the encrypted vault is SQLite and must not sit on Cloud Run's ephemeral disk or a
Cloud Storage mount. Streamlit needs WebSockets: open the printed URL and use every tab before you share it.

## 4. Verify
```bash
API=$(gcloud run services describe rmti-api --region $REGION --format 'value(status.url)')
KEY=$(gcloud secrets versions access latest --secret rmti-api-key)
ADM=$(gcloud secrets versions access latest --secret rmti-admin-key)
curl -s $API/health                                   # registry stamp appears
curl -si -H "X-API-Key: $KEY" $API/v1/registry | head -20          # X-RMTI-Registry header present, problems: []
curl -s  -H "X-API-Key: $KEY" "$API/v1/registry/ladder-check?source=kawaguchi2010"
curl -s -X POST $API/v1/registry/proposals -H "X-API-Key: $KEY" -H "X-Admin-Key: $ADM" -H 'Content-Type: application/json' \
  -d '{"target":"rho_bio_ladder","reason":"Face-validity check shows compression at ECOG 3-4","author":"rev01","payload":{}}'
gcloud storage ls gs://$BUCKET/                                     # the proposal file is there and survives a redeploy
```

## 5. Updating the registry (evidence, cohorts, constants)
1. Edit with `python registry.py add-evidence ...` or `register-cohort ...` (or a reviewed change to the parameter file).
2. `python registry.py validate && python -m pytest -q tests`
3. Commit, then redeploy both services with the same commands as steps 2 and 3. The `X-RMTI-Registry` header changes, which proves
   which revision answered. After pre-registration run `python registry.py lock`; a later change to a constant then fails validation.
4. Rollback: `gcloud run services update-traffic rmti-api --region $REGION --to-revisions REVISION=100`

## 6. Cost and limits
Scale-to-zero keeps small research use inside the free tier (confirm current limits on Google's pricing page). A cold start
takes a few seconds. Cloud Storage mounts use container memory while writing; proposals are tiny. Set a budget alert.

The interactive docs page (`/docs`) stays open and lists routes only; it holds no data.
