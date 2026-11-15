SITE UPDATE: oncoclastics definition, soft red / light-blue / white look, Johnson case study
1. Unzip. GitHub > Add file > Upload files. Drag in EVERYTHING from the zip, including the hidden .streamlit folder
   (enable "Hidden items" in File Explorer), the pages folder, docs, animation, and the .py files. Commit.
   If you already have .streamlit/config.toml with other settings, keep them and copy the [theme] block into it.
2. share.streamlit.io > your app > Settings > Main file path = Home.py > Save. Manage app > Reboot app.
3. Check: / (first page: definition of oncoclastics, no bottom logo), /Johnson_Case_Study, /Risk_Calculator (logo at the bottom).
To use your official logo: add assets/rmti_logo.svg (SVG with xmlns). Pages not in this zip need two lines after st.set_page_config:
    import oncoclastic_style as ui
    ui.apply()
