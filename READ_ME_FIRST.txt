FIX THE STREAMLIT APP (override)
1. Unzip. GitHub > Add file > Upload files. Drag in: Home.py, READ_ME_FIRST.txt, the pages folder and the docs folder. Commit.
   This puts Home.py back in the repository root, replaces the misplaced pages/Home.py with a redirect stub,
   and adds pages/7_Live_Risk_Matrix.py (it runs the 7_Live_Risk_Matrix.py already in your root).
2. share.streamlit.io > your app > Settings > Main file path = Home.py > Save.
3. Manage app > Reboot app. Reload https://oncoclastics.streamlit.app
Optional tidy-up: in GitHub delete pages/6_Developer_Portal.py (the home page replaces it).
Videos: put your .mp4 files in media/ (or leave them in the root). Open the site with ?debug=1 to see what was found.
