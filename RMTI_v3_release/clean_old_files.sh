#!/usr/bin/env bash
# Removes stale duplicates only. Review with: bash clean_old_files.sh --dry-run
set -u
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
rm_() { for p in "$@"; do [ -e "$p" ] && { echo "remove: $p"; [ $DRY = 0 ] && git rm -rq --ignore-unmatch -- "$p" && rm -rf -- "$p"; }; done; }
rm_ "Home.py" "Home (1).py" "app.py.py" "app.py (1).py" "streamlit_app.py" "streamlit_app (2).py" \
    "PASTE_oncoclastic_style.py.txt" "PASTE_streamlit_app.py.txt" "portal (1).py" \
    oncoclasticsAPIupdate oncoclastics_FINAL "oncoclastics_animation_update (1)" oncoclastics_fixpack \
    "oncoclastics_home_fix (1)" oncoclastics_override oncoclastics_redesign "oncoclastics_site_v2 (1)" oncoclastics_upload_v2_1
while IFS= read -r f; do rm_ "$f"; done < <(find . -maxdepth 1 -type f \( -name '*(1)*' -o -name '*(2)*' \) ! -name '*.zip' ! -name '*.mp3' ! -name '*.mp4' | sed 's|^\./||')
echo "done. Dry run: $DRY"
