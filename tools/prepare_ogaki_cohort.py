#!/usr/bin/env python3
"""
Convert the Ogaki baseline workbook (IDENTIFIABLE: it holds date of birth and exact dates) into the de-identified file the sandbox reads.
RUN THIS ON YOUR OWN COMPUTER. The workbook never needs to leave it; only the output file is ever uploaded, and only if your data agreement allows.

    python tools/prepare_ogaki_cohort.py  Anton_Ogaki_baseline_050225.xlsx  cohort_data/ogaki_2025.csv  --salt "a long private phrase"  [--include-tumour] [--check]

What it does
  - drops the date of birth, every date and the original ID; patient_id becomes OG + 8 hex characters of SHA-256(salt + ID). Keep the salt private;
    with the same salt the same patient always gets the same code, so the file can be regenerated when the workbook is updated.
  - builds the sandbox columns: etiology, age_years, male, albumin_g_l, bilirubin_umol_l, platelets_1e9_l (Plt_10^3_mm3), time_years, cause.
  - time and cause are INFERRED, because the workbook's data dictionary does not define them. Please have the data owner confirm:
        HCC = Yes  ->  cause 1, time = (HCC diagnosis date - study entry) / 365.25
        HCC = No   ->  time = Years_to_FU, cause 2 if Outcome = dead (death without HCC), else 0 (censored)
        HCC found within --prevalent-days (default 30) of entry is treated as already present and excluded; so are patients under 18.
    With these rules the 2025 extract reproduces the bundled 3,101 / 376 HCC / 413 deaths exactly.
  - --include-tumour adds max_diameter_cm, n_nodules and vp for patients who developed HCC (blank for everyone else; '-' in the workbook becomes blank). Early_HCC is
    NOT included: it is coded Yes or '-', so 'not early' cannot be told from 'not recorded'. AFP, AFP-L3 and DCP are
    NOT included: the dictionary gives no timing for them and they are filled for every patient, so they look like baseline values, not values at diagnosis.
  - writes <output>.meta.json so the app lists the file as a bundled cohort.
No tumour LOCATION exists in this workbook, so none can be output.
"""
import argparse, hashlib, json, os, sys, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REQ = ["ID", "Age_at_entry", "Gender", "Etiology", "ALB_g_L", "Tbil_umol_L", "Plt_10^3_mm3", "Date_studyentry", "HCC_Dx_day_detection_day", "Years_to_FU", "HCC", "Outcome"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--salt", required=True, help="private phrase used to pseudonymise IDs (keep it; do not commit it)")
    ap.add_argument("--prevalent-days", type=int, default=30)
    ap.add_argument("--include-tumour", action="store_true")
    ap.add_argument("--check", action="store_true", help="score the result with the sandbox engine and print a summary (run from the repo)")
    a = ap.parse_args()
    if len(a.salt) < 8:
        sys.exit("Use a longer --salt (at least 8 characters): short salts are easy to brute-force for sequential IDs.")
    d = pd.read_excel(a.input, sheet_name=0)
    d.columns = [str(c).strip() for c in d.columns]
    miss = [c for c in REQ if c not in d.columns]
    if miss:
        sys.exit("Missing columns in the workbook: %s" % miss)
    num = lambda c: pd.to_numeric(d[c], errors="coerce")
    entry, dx = pd.to_datetime(d["Date_studyentry"], errors="coerce"), pd.to_datetime(d["HCC_Dx_day_detection_day"], errors="coerce")
    hcc = d["HCC"].astype(str).str.strip().str.lower().eq("yes")
    dead = d["Outcome"].astype(str).str.strip().str.lower().eq("dead")
    t = np.where(hcc, (dx - entry).dt.days / 365.25, num("Years_to_FU"))
    cause = np.where(hcc, 1, np.where(dead, 2, 0))
    f = pd.DataFrame({"age": num("Age_at_entry"), "male": d["Gender"].astype(str).str.strip().str.upper().map({"M": 1, "F": 0}),
                      "alb": num("ALB_g_L"), "bil": num("Tbil_umol_L"), "plt": num("Plt_10^3_mm3"), "t": t, "cause": cause,
                      "et": d["Etiology"].astype(str).str.strip()})
    steps, keep = [("rows in workbook", len(d))], pd.Series(True, index=d.index)

    def drop(label, bad):
        nonlocal keep
        n = int((keep & bad).sum()); keep &= ~bad; steps.append((label, n))
    drop("missing age, sex, albumin, bilirubin, platelets or follow-up time", f[["age", "male", "alb", "bil", "plt", "t"]].isna().any(axis=1) | ~np.isfinite(f["t"]))
    drop("age under 18", f["age"] < 18)
    drop("follow-up time not positive", f["t"] <= 0)
    drop("HCC within %d days of entry (treated as already present)" % a.prevalent_days, (f["cause"] == 1) & (f["t"] * 365.25 <= a.prevalent_days))
    k = f[keep]
    code = ["OG" + hashlib.sha256((a.salt + str(i)).encode()).hexdigest()[:8] for i in d.loc[keep, "ID"]]
    if len(set(code)) != len(code):
        sys.exit("Pseudonym collision: use a different --salt.")
    out = pd.DataFrame({"patient_id": code, "etiology": k["et"].values, "age_years": k["age"].round(1).values, "male": k["male"].astype(int).values,
                        "albumin_g_l": k["alb"].values, "bilirubin_umol_l": k["bil"].values, "platelets_1e9_l": k["plt"].round(0).values,
                        "time_years": k["t"].round(4).values, "cause": k["cause"].astype(int).values})
    if a.include_tumour:
        case = (out["cause"] == 1).values
        tum = pd.DataFrame(index=range(len(out)))
        tum["max_diameter_cm"] = pd.to_numeric(d.loc[keep, "Max_Diameter_in_cm"], errors="coerce").values
        tum["n_nodules"] = pd.to_numeric(d.loc[keep, "Number_of_nodules"], errors="coerce").values
        tum["vp"] = pd.to_numeric(d.loc[keep, "Vp"], errors="coerce").values
        tum.loc[~case, :] = np.nan
        out = pd.concat([out, tum], axis=1)
    out.to_csv(a.output, index=False, encoding="utf-8")
    meta = {"id": "ogaki_2025", "disease": "hcc", "label": "Ogaki cohort (Japan), 2025 extract",
            "description": "%d patients; cause 1 = incident HCC (%d), 2 = death without HCC (%d), 0 = censored. Pseudonymised. time and cause inferred from dates (see tools/prepare_ogaki_cohort.py); confirm with the data owner." %
                           (len(out), int((out.cause == 1).sum()), int((out.cause == 2).sum()))}
    json.dump(meta, open(os.path.splitext(a.output)[0] + ".meta.json", "w"), indent=1)
    print("\nRows kept / removed")
    for lab, n in steps:
        print("  %-70s %6d" % (lab, n))
    print("  %-70s %6d\n" % ("rows written", len(out)))
    print("HCC %d | deaths without HCC %d | censored %d | person-years %.0f | columns written: %s" % (
        (out.cause == 1).sum(), (out.cause == 2).sum(), (out.cause == 0).sum(), out.time_years.sum(), ", ".join(out.columns)))
    print("Written:", a.output, "(+ .meta.json). No date, date of birth or original ID is in it. Keep the workbook and the salt OFF GitHub.")
    if a.check:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        import sandbox as B
        r = B.run("hcc", records=out.to_dict("records"))
        print("\nCheck with the sandbox engine: tiers", {x["tier"]: x["patients_now"] for x in r["tiers"] if x["patients_now"]},
              "| Harrell C %.3f" % r["outcomes"]["c_index"])


if __name__ == "__main__":
    main()
