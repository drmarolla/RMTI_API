HOW TO UPDATE YOUR GITHUB REPO (drmarolla/oncoclastics)

1. Unzip this folder on your computer.
2. On GitHub open your repo. Click Add file > Upload files.
3. Drag these into the box (keep media/ as a folder):
     api.py                  (replaces your current api.py)
     portal.py               (replaces your current portal.py)
     developer_portal.html   (new)
     rmti_client.py          (new)
     CHANGELOG.md            (new)
     media/rmti-logo.svg     (new)
4. Write a commit message, for example "Add breast, new developer portal". Click Commit changes.
5. Redeploy. Streamlit Cloud updates itself. Your API host (Cloud Run or Docker) must be rebuilt and redeployed too.
6. Test: open your API address in a browser (the new portal appears), then run
   curl -X POST YOUR-API/v1/snapshot -H "X-API-Key: KEY" -H "Content-Type: application/json" \
     -d '{"domain":"oncoclastics","site":"breast","L":0.3,"E":0.65,"V":0.4,"rho_now":0.2}'

BREAST: the only change is in api.py. A list of allowed cancer sites was ["hcc","lung"]. It now says
Site = Literal["hcc","lung","breast"], and "breast" was added to Domain. service.py already handled breast.
Not changed: app.py (Streamlit). Send it if you want a Breast option in the Streamlit screens.
