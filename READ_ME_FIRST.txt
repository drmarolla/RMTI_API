UPDATE: bottom signature, self-introduction in the scripts, Adagio music bed, voice sample
1. Unzip. GitHub > Add file > Upload files. Drag in: oncoclastic_style.py, animation, narration, media, tools. Commit. Reboot the app.
   (oncoclastic_style.py replaces the old one: new bottom signature; the RMTI logo above it on every page after the first.)
2. Voice clone: ElevenLabs > Voices > Add a new voice > Instant Voice Clone > upload media/audio/my_voice_clone_sample.mp3
   (or your original), confirm it is your own voice, name it, then tell Claude the name.
3. Listen to media/audio/ducking_demo.mp3: your voice over the Adagio bed, music dips while you speak.
4. When the 8 narration clips per video exist (01.mp3 ... 08.mp3):
   python tools/assemble_audio.py CLIPS_DIR media/audio/adagio_bed_134s.mp3 rmti_liver_audio.mp3
