# Add the RMTI animation to GitHub and Streamlit

Files in this package:
- `animation/index.html` – the animation (single file, no dependencies)
- `streamlit_pages/RMTI_Animation.py` – Streamlit page that embeds it

## GitHub (GitHub Desktop, as in UPLOAD_INSTRUCTIONS.md)
1. Copy the `animation` folder into the root of your local `RMTI-time-indexed` folder.
2. GitHub Desktop → Changes shows `animation/index.html`. Summary: `Add RMTI cancer animation`. Commit to main, then Push origin.
3. Pages is already on (main / root), so after a minute it is live at
   https://drmarolla.github.io/RMTI-time-indexed/animation/
4. Optional: add a card or link for it in the root `index.html`.

## Streamlit
1. Copy `streamlit_pages/RMTI_Animation.py` into your Streamlit app's `pages/` folder (or paste its body into an existing page).
2. Commit and push; Streamlit Cloud redeploys automatically. Locally: `streamlit run <your_app>.py`.
3. "Live" mode needs step 3 above to be online. "Local file" mode reads `animation/index.html` from the repository, so adjust `LOCAL` if your layout differs.

## Notes
- The root-layout check in `tools/check_release.py` and the "17 entries" rule in UPLOAD_INSTRUCTIONS.md describe the 2.2.1 archive. Run the check after adding the folder, and update it if it flags `animation/`.
- Zenodo archives only published releases, so the new folder is not in the 2.2.1 record. Make a new release if you want it archived and citable.
