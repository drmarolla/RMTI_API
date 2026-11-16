FINAL PACKAGE: oncoclastics site v3 (replaces every earlier zip)
1. Copy the CONTENTS of this zip into the repository ROOT (GitHub Desktop: Fetch origin > Repository > Show in Explorer >
   paste, replace files > commit "Site v3" > Push origin). Include the hidden .streamlit folder.
2. Add your narration to the static folder, named exactly: static/narration_liver.mp3, narration_lung.mp3, narration_breast.mp3
   (download them from the ElevenLabs flow; they are in your voice "My voice conversational"). Commit and push.
3. share.streamlit.io > your app > Settings > Main file path = streamlit_app.py > Save > Manage app > Reboot app.
4. Open the first page, scroll to "From tumor events to trajectory", press "Sound on": your voice drives the scenes, Adagio dips under it.
   (Optional: a mixed audio file for a video: python tools/make_final_audio.py static/narration_liver.mp3 static/adagio_bed_134s.mp3 out.mp3)
5. Delete stray files from the repo root: Home (1).py, RMTI_Animation.py, UPLOAD_ANIMATION.md, ADD_ANIMATION.txt, ADD_VIDEO_README.txt,
   README_FIRST.txt, the folders named oncoclastics_* (1), oncoclasticsaudio.zip, and loose copies of *.vtt, *.mp3,
   RMTI_narration_script.pdf, assemble_audio.py, JOHNSON_CASE_STUDY.md, ONCOCLASTICS_DEFINITION.md, 8_Johnson_Case_Study.py, 0_Risk_Calculator.py.
If something looks wrong after the reboot, send a screenshot of the first page.
