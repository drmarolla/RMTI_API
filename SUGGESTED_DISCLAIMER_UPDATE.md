# Suggested update to DISCLAIMER.md (your decision; not applied automatically)

`DISCLAIMER.md` currently says the repository "contains no real patient data" and that sandboxes "run entirely locally; nothing is uploaded". With the Ogaki cohort bundled and the app hosted on Streamlit Cloud, both statements would be untrue. For a tool that asks to be trusted, the disclaimer should match reality. Suggested replacements (edit to fit your agreements):

**Your data** (replaces the paragraph of that name)
> The hosted app processes files you upload on the server for your session and does not save them; hosting infrastructure still handles them in transit and in memory. Do not enter patient names or any identifying information in any field, saved-case name or spreadsheet cell. Uploading real patient data requires ethics approval and a data-use agreement, which you must hold.

**Human-subjects and animal research** (replaces the paragraph of that name)
> This repository contains one pseudonymised retrospective cohort (the Ogaki cohort, 3,101 patients) in `cohort_data/`, included for validation and demonstration under [state the ethics approval or waiver reference and the data-use agreement here]. Patient-level rows are not displayed or downloadable in the app. No other human-subjects or animal data are included. Any further use of real patient data requires its own ethics review (IRB/REC) and data-use agreement obtained by the investigators; none is granted or implied by this repository's licence.
