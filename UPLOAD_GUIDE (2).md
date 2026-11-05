# Upload guide (version 2): RMTI API upgrade

Research prototype. Not validated, not a medical device. Nothing in this kit contains patient data.

## Why the red error kept coming back
The fixed page files were uploaded to the **repository root** instead of the **`pages`** folder, so Streamlit kept running the old copy inside `pages/`.
In this kit every folder is named after where it must go: **`UPLOAD_TO_pages` goes into `pages`**, and so on. Do not drag all files in at once.

## Step 1. Delete the stray files from the repository root (2 minutes)
Open each file on github.com, click the **⋯** menu, **Delete file**, commit. The list is in `DELETE_FROM_repo_root.txt`:
`3_4D_Risk_Matrix (1).py`, `3_4D_Risk_Matrix.py`, `4_RMTI_Step_by_Step (1).py`, `make_rmti_video.py`, `video_narration.py`, `test_cases.py`.
(These are harmless copies in the wrong place; deleting them avoids confusion.)

## Step 2. Upload each folder to its destination
For each row: open the destination in GitHub (click through the folders), choose **Add file → Upload files**, drag in **the files inside** the kit folder, commit.
| Kit folder | Destination in the repository | What it does |
|---|---|---|
| `UPLOAD_TO_repo_root` | the main (root) page of the repo | `api.py` (portal, themed docs, widget), `app.py.py` (new header, Who uses what), `portal.py`, `rmti_cases.py`, `demo_mode.py`, `rmti_theme.py` |
| `UPLOAD_TO_pages` | `pages/` | the three fixed or new pages (**this replaces the buggy 4D page**) |
| `UPLOAD_TO_media` | `media/` (create it: **Add file → Create new file**, type `media/README.md`, commit; then upload) | 3 videos, 3 captioned copies, captions, chapters |
| `UPLOAD_TO_tools` | `tools/` | video engine, voices, storyboards |
| `UPLOAD_TO_tests` | `tests/` | case-data tests |
| `UPLOAD_TO_docs` | `docs/` (create the same way) | narration scripts and YouTube descriptions as Markdown |
Files with the same name are replaced automatically. If GitHub says "file already exists", that is fine; commit.

## Step 3. Reboot and check
**Manage app → ⋮ → Reboot app**, wait a minute, hard-refresh (Ctrl+Shift+R). The sidebar should show: app · HCC Calculator · Cohort Sandbox · 4D Risk Matrix · RMTI Step by Step · **Case Studies and Videos**.
If a page still shows a red error, open **Manage app** and send me the first lines of the log.

## Step 4. The API (only when you want the new portal live)
Redeploy as before (`LAUNCH.md` step 3). Then: `$API/` portal (200), `$API/docs` themed reference (200), `$API/widget?case=lilongwe` viewer (200), `$API/v1/registry` (401 without a key).

## Natural, expressive voice (the built-in voice is only for drafts)
Run these on your own computer (Python 3.10+). The built-in voice needs no setup; the others need internet and an account where noted.
```
pip install matplotlib numpy pillow imageio-ffmpeg
```
| Voice | Setup | Command | Emotion control |
|---|---|---|---|
| **OpenAI** (recommended) | `OPENAI_API_KEY=...` | `python tools/make_videos.py all --voice openai` | yes: each scene sends a written acting direction (warm, serious, curious...) |
| **ElevenLabs** | `ELEVENLABS_API_KEY=...` and `ELEVENLABS_VOICE_ID=...` (pick a voice you like) | `python tools/make_videos.py all --voice elevenlabs` | per-scene stability and style settings |
| **Edge neural** (free) | `pip install edge-tts`; optional `EDGE_VOICE=en-US-AriaNeural` | `python tools/make_videos.py all --voice edge` | natural pace and tone, no scene-level emotion |
| **Piper** (offline) | `pip install piper-tts`; `PIPER_MODEL=path/to/voice.onnx` | `python tools/make_videos.py all --voice piper` | natural, no emotion control |
| **Your own voice** (most authentic) | record or generate each scene with any tool | see below | whatever you perform |
Windows PowerShell: set a key with `$env:OPENAI_API_KEY="your-key"`; Mac/Linux: `export OPENAI_API_KEY=your-key`.

**Audition first** (cheap, two scenes): `python tools/make_videos.py liver --voice openai --only title,limits` writes `media/rmti_2_liver_case_studies_TEST.mp4`.

**Your own recording or any other tool**
1. `python tools/make_videos.py all --export-script voice_scripts` writes one text file per scene, plus a CSV with the delivery direction for each scene.
2. Record or generate audio per scene and save it as `voice/<video>/<scene id>.mp3` (video folders: `explained`, `liver`, `flood_heat`; scene ids are the text file names).
3. `python tools/make_videos.py all --audio-dir voice`. Scene lengths adapt to your audio; captions, chapters and timings are rebuilt.

The OpenAI, ElevenLabs, Edge and Piper code paths were tested with mocked responses only (no internet where this kit was built). Audition one scene first.

## Captions
Every video comes in two forms: `name.mp4` has a caption track you switch on and off in the player (CC button; VLC may show it by default: use the Subtitle menu), and `name_CC.mp4` has the captions **always visible in a band under the picture**. The Streamlit page lets visitors choose. Upload the `.srt` to YouTube as English captions. Regenerate the captioned copies any time: `python tools/make_videos.py cc --out media`.

## Test before you upload (optional)
```
pip install -r requirements.txt
streamlit run app.py.py            # http://localhost:8501
uvicorn api:app --port 8000        # http://localhost:8000/   portal, /docs, /widget
```
## Data safety checklist
- Public site: synthetic, illustrative or published aggregate values only. CSV upload is hidden while demo mode is on (default).
- Keep `.env`, `data/` and `*.db` out of GitHub; real keys belong in Streamlit Secrets or Secret Manager. Never put a voice-service key in the repo.
- Never screen-record a live or private instance. These videos were rendered offline from `rmti_cases.py`.
