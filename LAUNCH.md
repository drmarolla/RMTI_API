# Launch the Oncoclastics API: step by step

You need: this folder, a Google account with billing enabled (the free tier covers light use), and about 20 minutes.
Not tested by me: Docker and `gcloud` are not available in my environment. I tested the same start script the container runs
(`start.sh`, role `api`, port from `$PORT`, production mode, API key). Expect to fix a small thing on the first real deploy.

## 0. Test on your own computer first (5 minutes)
```
pip install -r requirements.txt
RMTI_ROLE=api PORT=8000 RMTI_API_KEYS=my-test-key ./start.sh        # Windows: use WSL, or: set the variables, then: uvicorn api:app --port 8000
```
Open http://localhost:8000/docs . Try it:
```
curl -X POST http://localhost:8000/v1/hcc/patient -H "X-API-Key: my-test-key" -H "Content-Type: application/json" \
  -d '{"age_years":55,"male":1,"albumin_g_l":33,"bilirubin_umol_l":30,"platelets_1e9_l":150}'
```
Expected: `"status":"CLEAN: L and V use disjoint variables"`, `"R":0.133`, `"tier":"2 Moderate"`.

## 1. One-time Google Cloud setup
1. Create a project at https://console.cloud.google.com and enable billing.
2. Install the `gcloud` CLI (https://cloud.google.com/sdk/docs/install), then:
```
gcloud auth login
export PROJECT_ID=your-project-id
export REGION=us-central1            # pick a European region if your users need it
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

## 2. Create your API key (kept in Secret Manager, never in the code)
```
openssl rand -hex 32 | gcloud secrets create oncoclastics-api-key --data-file=-
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding oncoclastics-api-key \
  --member serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com --role roles/secretmanager.secretAccessor
```
Read the key when you need it: `gcloud secrets versions access latest --secret oncoclastics-api-key`

## 3. Deploy (run inside this folder)
```
gcloud run deploy oncoclastics-api --source . --region $REGION --allow-unauthenticated \
  --max-instances 3 --memory 512Mi \
  --set-env-vars RMTI_ROLE=api,RMTI_ENV=production \
  --set-secrets RMTI_API_KEYS=oncoclastics-api-key:latest
```
`--allow-unauthenticated` only lets requests reach the service; the app itself demands `X-API-Key` on every route except `/health`
(and `/docs`, which shows the schema only). If you omit the key, production mode refuses to serve. It prints a `https://...run.app` address.

## 4. Check it is live
```
API=$(gcloud run services describe oncoclastics-api --region $REGION --format 'value(status.url)')
KEY=$(gcloud secrets versions access latest --secret oncoclastics-api-key)
curl -s $API/health
curl -s -o /dev/null -w "%{http_code}\n" $API/v1/registry                    # expect 401 without a key
curl -s -X POST $API/v1/hcc/patient -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"age_years":55,"male":1,"albumin_g_l":33,"bilirubin_umol_l":30,"platelets_1e9_l":150}'
```
Interactive docs: `$API/docs`.

## 5. Your own address (api.yourdomain.org)
Buy the domain first (see the trademark and domain notes in the earlier review). Then in the Cloud Run console open the service,
choose **Manage custom domains** (availability varies by region; check Google's current page), verify the domain, and add the DNS records it shows
at your registrar. HTTPS is issued for you. If your region does not offer it, put Cloudflare in front of the `run.app` address instead.

## 6. Let a website call it (optional)
Browsers block cross-site calls unless you allow the site. Add its exact address:
```
gcloud run services update oncoclastics-api --region $REGION --update-env-vars "RMTI_CORS_ORIGINS=https://www.yourdomain.org"
```
Do not put the API key inside a public web page; anyone can read it. Call the API from your own server code, or keep public pages
as static calculators (your existing GitHub Pages sites compute in the browser and need no API).

## Updating later
Change the code, then repeat step 3 (same command). Roll back in the Cloud Run console under **Revisions**.

## Rules while it is live
- Research prototype, not validated, not a medical device. Do not send identifiable patient data. The pseudonymised cohort files are **not** for the API.
- Rotate the key if it leaks: create a new secret version and redeploy.
- Cost control: `--max-instances 3` caps scale; set a billing budget alert in the Google console.
- Other routes: `/v1/lung/inputs`, `/v1/hcc/patient`, `/v1/snapshot`, `/v1/oncoclastics/two-sense`, `/v1/registry`. Every response carries `X-RMTI-Registry`.

## Alternative: any Linux server with Docker (also gives the login web app)
```
cp .env.example .env     # set RMTI_DOMAIN, RMTI_INVITE_CODE, RMTI_API_KEYS to long random values; point DNS at the server
docker compose up -d --build        # Caddy gets the HTTPS certificate; API docs at https://<RMTI_DOMAIN>/api/docs
```
API only, no Caddy: `docker build -t oncoclastics-api . && docker run -p 8000:8000 -e RMTI_ROLE=api -e PORT=8000 -e RMTI_ENV=production -e RMTI_API_KEYS=<key> oncoclastics-api`
See `DEPLOY.md` and `CLOUD_RUN.md` for the full private-instance and proposals options.
