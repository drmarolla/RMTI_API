# Upload guide: RMTI API upgrade (portal, widget, narrated videos, Lever Lab)

Research prototype. Not validated, not a medical device. Nothing in this bundle contains patient data.

## 1. Upload to GitHub (about 5 minutes)
1. Unzip `oncoclastics_upload.zip` on your computer.
2. Open your repository on github.com, click **Add file → Upload files**.
3. Select **everything inside the unzipped folder** (the loose files and the `pages`, `media`, `tools`, `tests` folders) and drag it into the page. GitHub keeps the folder structure.
4. Scroll down, write a commit message such as "RMTI API upgrade: portal, widget, narrated videos, Lever Lab", choose **Commit directly to main**.

Files with the same name are replaced automatically. Replaced: `api.py`, `app.py.py`, `pages/3_4D_Risk_Matrix.py`. Everything else is new.

## 2. Streamlit app
Open **Manage app** (bottom right) → ⋮ → **Reboot app**. Wait about a minute, hard-refresh (Ctrl+Shift+R). The sidebar should now show:
`app` · HCC Calculator · Cohort Sandbox · 4D Risk Matrix · RMTI Step by Step · **Case Studies and Videos**.

## 3. The API (Cloud Run or Docker), only when you want the new portal live
Same command as before (see `LAUNCH.md` step 3): `gcloud run deploy oncoclastics-api --source . ...`
Then check (replace `$API`):
```
curl -s -o /dev/null -w "%{http_code}\n" $API/              # 200  developer portal
curl -s -o /dev/null -w "%{http_code}\n" $API/docs          # 200  themed reference
curl -s -o /dev/null -w "%{http_code}\n" "$API/widget?case=lilongwe"   # 200  embeddable viewer
curl -s -o /dev/null -w "%{http_code}\n" $API/v1/registry   # 401  still needs the key
```
The portal, docs and widget carry no data, so they are public. Every `/v1` route still needs `X-API-Key`.

## 4. Optional settings
| Setting | Where | Effect |
|---|---|---|
| `RMTI_DEMO_MODE=0` | environment variable, private instance only | switches the banner to "Private mode" and shows CSV upload. Leave unset on the public site. |
| `RMTI_APP_URL` | API environment variable | address the portal links to as "Live demo" (default `https://oncoclastics.streamlit.app`) |

## 5. Regenerating the videos (optional)
```
pip install matplotlib numpy pillow imageio-ffmpeg
python tools/make_videos.py all                     # offline basic voice (works with no internet)
python tools/make_videos.py all --voice edge        # natural neural voice: pip install edge-tts (needs internet)
python tools/make_videos.py liver --voice piper     # local neural voice: pip install piper-tts, set PIPER_MODEL
```
Captions are a separate track (`.srt` / `.vtt` and a soft track inside the MP4): off by default, toggle in the player. Upload the `.srt` to YouTube as captions.
The `edge` and `piper` voices were not tested in the environment that built this bundle.

## 6. Data safety checklist
- Public site: synthetic, illustrative or published aggregate values only. CSV upload is hidden while demo mode is on.
- Keep `.env`, `data/` and `*.db` out of GitHub (add to `.gitignore`); real keys belong in Streamlit Secrets / Secret Manager.
- Never record a live or private instance for video. These videos were rendered offline from `rmti_cases.py`.
