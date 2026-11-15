# How the Streamlit app is laid out

Streamlit Cloud runs one **main file** from the repository root and builds the page menu from the `pages/` folder next to it.

```
Home.py                    <- Main file path (share.streamlit.io > app > Settings)
developer_portal.html      <- shown by Home.py, must sit next to Home.py
app.py.py                  <- original calculator, run by pages/0_Risk_Calculator.py
7_Live_Risk_Matrix.py      <- run by pages/7_Live_Risk_Matrix.py
media/                     <- .mp4 case videos (+ same-named .vtt captions); Home.py also finds .mp4 in the root
pages/
  0_Risk_Calculator.py     -> /Risk_Calculator
  1_HCC_Calculator.py      -> /HCC_Calculator
  2_Cohort_Sandbox.py      -> /Cohort_Sandbox
  3_4D_Risk_Matrix.py      -> /4D_Risk_Matrix
  4_RMTI_Step_by_Step.py   -> /RMTI_Step_by_Step
  5_Case_Studies_and_Videos.py -> /Case_Studies_and_Videos
  6_Live_4D_Lab.py, 7_Liver_Progression_4D.py, 7_Live_Risk_Matrix.py
  Home.py                  <- stub that redirects to the root Home.py
```

Rules of thumb
- `Home.py` must stay in the root. A copy inside `pages/` becomes an ordinary page.
- A file's menu URL is its name without the number and `.py` (`3_4D_Risk_Matrix.py` -> `/4D_Risk_Matrix`).
- After changing the Main file path or moving files: Manage app > Reboot app.
- Open the site with `?debug=1` to list the videos the home page found.
