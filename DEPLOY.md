# Deployment guide (checked 23 Oct 2026; prices and limits change, confirm on each provider's page)

Nothing here is hosted for you. You choose the addresses.

## Recommended layout: one code base, one API contract, three layers

| Layer | Purpose | Data allowed | Host | Cost |
|---|---|---|---|---|
| 1. Static sandboxes | Public teaching calculators (Oncoclastics, Disaster Science) | none | **GitHub Pages**: keep your two live sites | free |
| 2. Public Python app and API | Trajectories, cohort ranking, validation demo, REST docs | synthetic or de-identified only | **Google Cloud Run** (scale to zero) | free tier: 2M requests, 180,000 vCPU-s, 360,000 GiB-s per month |
| 3. Private practitioner instance | Login, encrypted saved cases | pseudonymous cases, after approvals | institution VM first; else **DigitalOcean Droplet + Volume** with a signed BAA | about the price of a small VM plus a support plan |

Why these, for cancer and disaster science:
- Disaster Science traffic is spiky around events and carries no patient data, so scale-to-zero, stateless and free fits (layers 1 and 2).
- Oncoclastics with saved cases needs a persistent disk, a signed BAA or DPA, and region control, so it belongs on a VM you control (layer 3), not on serverless.
- Google's BAA covers Cloud Run, but Cloud Run's filesystem is ephemeral, so the encrypted vault must not run there. Keep `RMTI_ENABLE_VAULT` unset on Cloud Run.

Not recommended for this project:
- **Fly.io**: no free tier for new accounts; HIPAA needs a $99/month add-on on top of compute.
- **Render free tier**: sleeps after 15 minutes (about a minute to wake) and wipes local files, which would delete a SQLite vault.
- **Cloudflare Workers**: free plan is 100,000 requests per day with 10 ms CPU and 128 MB memory, which cannot run Streamlit or pandas. It suits static pages or a JavaScript port of the scoring math; static assets are free and unlimited.

## Layer 2: Google Cloud Run (public, stateless)
One image, two services (UI and API). From this folder, with the `gcloud` CLI signed in to a project with billing enabled
(a free-tier region such as us-central1; for GDPR-sensitive audiences pick a European region and check its free-tier terms):
```bash
gcloud run deploy rmti-api --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars RMTI_ROLE=api --max-instances 3 --memory 512Mi
gcloud run deploy rmti-app --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars RMTI_ROLE=ui --max-instances 3 --memory 1Gi --session-affinity --timeout 3600
```
Each command prints a `https://...run.app` address; map your own domain in the Cloud Run console if you want one. The UI calls the engine in-process,
so the API service is for programmatic users (docs at `/docs`). Set `RMTI_API_KEYS` on the API service if you do not want it open.
Untested by me: Streamlit on Cloud Run relies on WebSockets and session affinity, so test it before announcing the link.

## Layer 3: private instance with login (Docker Compose + HTTPS)
1. Choose the host: your institution's approved VM, or a DigitalOcean Droplet with a Volume (a Droplet is a covered product once you sign
   DigitalOcean's BAA, which also requires a Standard or Premium support plan; contact their sales). On Google Cloud, use a Compute Engine VM with a persistent disk.
2. `cp .env.example .env`; set `RMTI_DOMAIN`, `RMTI_INVITE_CODE`, `RMTI_API_KEYS` to long random values. Point DNS at the server.
3. `docker compose up -d --build`. Caddy obtains the HTTPS certificate. App at `https://<RMTI_DOMAIN>`, API docs at `https://<RMTI_DOMAIN>/api/docs`.
4. Give approved practitioners the invite code through a separate channel. They register with a pseudonymous username and a password of 12 or more characters.
5. Back up `data/` (ciphertext only) and test a restore.

## Before any real patient data is entered (the software cannot do this for you)
- Ethics or IRB approval, data-use agreement, and a data-protection impact assessment where GDPR applies.
- A signed BAA or DPA with the host, data residency, retention and deletion policy, breach-response plan.
- Institutional single sign-on or MFA if required, patching schedule, no logging of request bodies at any proxy.
- The model is an unvalidated research prototype: nothing in the app is a basis for patient-care decisions.
