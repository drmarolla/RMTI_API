# Replace the whole site (clean start)

1. Unzip RMTI_v4_site.zip on your computer.
2. In your GitHub repo, create a NEW branch or a new repo (cleanest), and upload the CONTENTS of the unzipped folder to the repo ROOT
   (app.py must sit at the top level, not inside a folder).
3. Copy your existing .mp4 files into the repo root or `media/`.
4. share.streamlit.io > Create app > pick the repo > Main file path: `app.py` > Python 3.12 (3.14 also works) > Deploy.
   Streamlit does not let you edit the main file path later, so create a new app and delete the old one.
5. Optional: Settings > Secrets: RMTI_API_KEYS = "yourkey:research:Lab A".
