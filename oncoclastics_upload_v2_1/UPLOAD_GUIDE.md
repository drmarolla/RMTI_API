# Upload guide (version 2.1): RMTI API upgrade

Research prototype. Not validated, not a medical device. Nothing in this kit contains patient data.

## The short answer: upload the code kit now, add the videos later
`oncoclastics_upload_v2_1.zip` (small) holds the API portal, pages, tools and documents. Upload it now.
`oncoclastics_media_DRAFT_voice.zip` holds the three draft videos with the basic synthetic voice. **Hold it back** until your own voice is ready; until then the Case Studies page shows "This video is being prepared" and the Lever Lab works fully.

## Step 1. Delete the stray files from the repository root (2 minutes)
Open each file on github.com, click the three-dot menu, **Delete file**, commit. List: `DELETE_FROM_repo_root.txt`
(`3_4D_Risk_Matrix (1).py`, `3_4D_Risk_Matrix.py`, `4_RMTI_Step_by_Step (1).py`, `make_rmti_video.py`, `video_narration.py`, `test_cases.py`).

## Step 2. Upload each folder to its destination
Open the destination in GitHub (click through the folders), **Add file → Upload files**, drag in **the files inside** the kit folder, commit.
| Kit folder | Destination | What it does |
|---|---|---|
| `UPLOAD_TO_repo_root` | repository root | `api.py` (portal, themed docs, widget), `app.py.py`, `portal.py`, `rmti_cases.py`, `demo_mode.py`, `rmti_theme.py` |
| `UPLOAD_TO_pages` | `pages/` | the fixed 4D page (**this removes the red error**) and two new pages |
| `UPLOAD_TO_tools` | `tools/` | video engine, voices, reading-script maker, voice-folder checker |
| `UPLOAD_TO_tests` | `tests/` | case-data tests |
| `UPLOAD_TO_docs` | `docs/` (create: Add file → Create new file → `docs/README.md`) | narration scripts and YouTube descriptions (Markdown) |
`FOR_YOU_reading_scripts` is **not** for GitHub: it holds your three printable PDFs.

## Step 3. Reboot and check
**Manage app → ⋮ → Reboot app**, wait a minute, hard-refresh (Ctrl+Shift+R). Sidebar: app · HCC Calculator · Cohort Sandbox · 4D Risk Matrix · RMTI Step by Step · **Case Studies and Videos**. If a page still shows a red error, send me the first lines of the log from **Manage app**.

## Step 4. The API (only when you want the new portal live)
Redeploy as before (`LAUNCH.md` step 3). Then: `$API/` portal (200), `$API/docs` (200), `$API/widget?case=lilongwe` (200), `$API/v1/registry` (401 without a key).

## Record your own voice (recommended)
1. Print or open the PDF for a video (`FOR_YOU_reading_scripts`). Page 1 is the recording guide; each scene shows its delivery note, pronunciation hints and the file name to save as (for example `title.mp3`).
2. Record each scene as its own file (a phone voice recorder is fine). Save into `voice/explained/`, `voice/liver/` or `voice/flood_heat/`.
3. Check your folder before building: `python tools/check_voice_folder.py voice` (lists missing scenes, length, pace, loudness, clipping).
4. Build: `python tools/make_videos.py liver --audio-dir voice` (or send me the audio files in the chat and I will build the videos here). Scene lengths follow your voice; captions, chapters and the closing contact line are rebuilt.
5. Re-record any scene at any time: replace its file and build again.
```
pip install matplotlib numpy pillow imageio-ffmpeg reportlab
```
Other voices (natural, expressive) are still available: `--voice openai`, `elevenlabs`, `edge`, `piper`; audition with `--only title,limits`. Those paths were tested with mocked responses only. To rebuild the PDFs: `python tools/make_reading_scripts.py reading_scripts`.

## Captions
Every video comes in two forms: `name.mp4` has a caption track you switch on and off (CC button; VLC may show it by default, use the Subtitle menu), and `name_CC.mp4` has the captions always visible in a band under the picture. Upload the `.srt` to YouTube. Rebuild the captioned copies any time: `python tools/make_videos.py cc --out media`.

## Can everything be changed later?
Yes. On GitHub you can edit a file (pencil icon), delete it, or replace it by uploading a file with the same name. Every change is a saved version: open the file's **History** to compare or restore an earlier one. Streamlit redeploys after each commit (reboot the app if a page looks stale). Videos can be swapped by uploading the same file names. The narration document stays editable and can be exported to Word or PDF.
One caution: deleting a file does not erase it from GitHub's history. Never commit keys, `.env` files or any patient data; if that ever happens, change the key and tell me.

## Test before you upload (optional)
```
pip install -r requirements.txt
streamlit run app.py.py            # http://localhost:8501
uvicorn api:app --port 8000        # http://localhost:8000/   portal, /docs, /widget
```
## Data safety checklist
- Public site: synthetic, illustrative or published aggregate values only. CSV upload is hidden while demo mode is on (default).
- Real keys belong in Streamlit Secrets or Secret Manager, never in the repo. Never put a voice-service key in the repo.
- Never screen-record a live or private instance. These videos are rendered offline from `rmti_cases.py`.

Contact: cesar.marolla@alumni.harvard.edu
