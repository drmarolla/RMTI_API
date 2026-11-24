# Deploy RMTI v5 (read this first)

Your live site still showed the OLD app because Streamlit was pointed at `RMTI_v3_release/app.py`.
Streamlit Cloud cannot change the main file of an existing app, so you create a new app.

1. In GitHub (repo `RMTI_API`, branch `main`): Add file > Upload files > drag the whole **RMTI_v5_site** folder
   (unzip first; the folder must contain app.py, media/, views/, rmti_python/ ...). Commit.
2. https://share.streamlit.io : open your current app > Settings > Delete app (this frees the name `risk-mechanism-theory-index`).
3. Create app > Deploy a public app from GitHub:
   - Repository: drmarolla/RMTI_API    Branch: main
   - **Main file path: RMTI_v5_site/app.py**
   - App URL: risk-mechanism-theory-index
   - Advanced settings > Python 3.12
4. Deploy. First build takes 2 to 4 minutes.

The app finds its own videos in RMTI_v5_site/media (and in the repo root). Large .mp4 files over 25 MB need git upload instead of the web page.
When you record your voice: ffmpeg -i media/rmti_liver_case_study.mp4 -i liver_voice.mp3 -c:v copy -c:a aac -shortest out.mp4
(then replace the file; keep the .vtt next to it so the closed captions still show).
If your recording is longer or shorter, send me the timings or edit media/*_timing.json and I will re-render to match.
