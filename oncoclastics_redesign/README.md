# Oncoclastics redesign: drop-in guide

## What is in this folder
| File | Purpose |
|---|---|
| `.streamlit/config.toml` | Base theme (colors, light mode, minimal toolbar) |
| `ui/theme.py` | Design system: CSS, animated hero, count-up KPIs, icon cards, equation banner, nav, footer |
| `Home.py` | Redesigned landing page that uses the module and includes a live lever lab with sensitivity chart |

## Install into your private repo (5 minutes)
1. Copy `ui/` and `.streamlit/config.toml` into the **root** of your repo (next to `app.py`).
2. Replace your Home page with `Home.py` (or paste its contents into `app.py`).
3. On **every** other page, add right after `st.set_page_config(...)`:
   ```python
   from ui.theme import inject_theme, top_nav, demo_banner, footer
   inject_theme()
   top_nav(active="Risk Calculator")
   demo_banner()
   # ... your existing page code ...
   footer()
   ```
4. Open `ui/theme.py` and edit the `NAV` list so the paths match your actual file names in `/pages`
   (a wrong path only shows plain text, it never crashes the page).
5. Commit and push; Streamlit Cloud redeploys automatically.

No new packages needed (Streamlit + pandas only). Everything is HTML/CSS/SVG, so it works on Community Cloud.

## Notes
- The KPI numbers on the home page are placeholders; replace them with your real figures.
- Count-up animation uses CSS `@property` (Chrome, Edge, Safari 16.4+, Firefox 128+); older browsers just show the final number.
- All motion switches off for users with "reduce motion" enabled.
- The code was syntax-checked but not run in a live Streamlit session here, so expect small tweaks on first deploy.

## Next upgrades (ask and I will build them)
- Restyle each calculator page: grouped inputs in cards, result "gauge", downloadable PDF report.
- Plotly charts with one shared color theme for the 4D matrix and cohort sandbox.
- Case-study gallery with filters (domain, year, evidence level) and a card per study.
- Developer Portal: copy-paste API snippets (Python, curl) with live example responses.
