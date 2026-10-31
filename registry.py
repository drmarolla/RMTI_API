"""RMTI registry: versioned, validated, hash-stamped evidence, parameters and cohort metadata.

Design rules (they are what keep the platform trustworthy while it keeps growing):
  1. New evidence and new cohorts can be added at any time. Adding them changes the registry version and hash,
     never a score.
  2. Model constants (L anchors, rho_bio ladder, tiers) are NEVER updated automatically from data. A cohort can
     produce a SUPPORT REPORT for the ladder (ladder_support) and a human proposes a change (propose), which is
     reviewed, then released as a new registry version. Once `locked` (pre-registration), constants change only
     through a new major version with a stated reason.
  3. Every API response carries X-RMTI-Registry: <version>+<hash12>, so any number can be traced to the
     evidence and parameter set that produced it.
  4. Patient-level data is never stored here. Cohort entries hold metadata only.

CLI:  python registry.py validate | hash | add-evidence FILE.json [--supplementary] | lock | register-cohort FILE.json | set-active-ladder A|B
"""
import hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REG_DIR = os.environ.get("RMTI_REGISTRY_DIR") or os.path.join(HERE, "rmti_engine", "oncology", "registry")
FILES = {"evidence": "lung_evidence.json", "parameters": "lung_parameters.json", "cohorts": "cohorts.json"}
LOCK_FILE = os.path.join(REG_DIR, "prereg_lock.json")
PROPOSAL_DIR = os.environ.get("RMTI_PROPOSALS", os.path.join(HERE, "data", "proposed"))

STATUSES = {"peer-reviewed", "peer-reviewed (editorial)", "draft, unpublished", "conference-abstract",
            "secondary-analysis", "preprint", "thesis"}
VERIFIED = {"full_text", "abstract", "abstract_partial", "snippet", "as_released_v2.4.0"}
REQUIRED = ("id", "status", "cite", "design", "findings", "use", "limits", "verified")
VERSION_RE = re.compile(r"^\d{4}\.\d{1,2}\.\d+$")
EVIDENCE_GRADES = {"strong", "moderate", "weak", "reference"}


def _path(kind):
    return os.path.join(REG_DIR, FILES[kind])


def _read(kind, default=None):
    p = _path(kind)
    if not os.path.exists(p):
        if default is None and kind != "cohorts":
            raise FileNotFoundError("registry file not found: %s (registry folder: %s; set RMTI_REGISTRY_DIR to an absolute path if it is wrong)" % (p, REG_DIR))
        return default
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _write(kind, obj):
    with open(_path(kind), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def load():
    return {k: _read(k, {"cohorts": []} if k == "cohorts" else None) for k in FILES}


def stamp():
    """'<version>+<hash12>' over evidence, parameters and cohorts: changes whenever any of them changes."""
    r = load()
    return "%s+%s" % (r["evidence"]["registry_version"], canonical_hash(r)[:12])


LOCK_EXCLUDE = ("registry_version",)     # a label that moves whenever evidence or cohorts are added; it is not a model constant


def lock_hash(pa):
    """Identity of the model constants: the parameter file without its version label, so adding evidence after pre-registration
    never breaks the lock, while any change to a ladder, anchor or flag does."""
    return canonical_hash({k: v for k, v in pa.items() if k not in LOCK_EXCLUDE})


def params_hash():
    return lock_hash(_read("parameters"))


def validate(reg=None):
    """Return a list of problems (empty list = consistent)."""
    reg = reg or load()
    bad = []
    ev, pa, co = reg["evidence"], reg["parameters"], reg["cohorts"]
    if not VERSION_RE.match(ev.get("registry_version", "")):
        bad.append("evidence registry_version must look like YYYY.M.N")
    if pa.get("registry_version") != ev.get("registry_version"):
        bad.append("parameters and evidence registry_version differ (%s v %s)" % (pa.get("registry_version"), ev.get("registry_version")))
    seen = set()
    for group in ("evidence", "supplementary"):
        for e in ev.get(group, []):
            miss = [k for k in REQUIRED if not e.get(k)]
            if miss:
                bad.append("%s: missing %s" % (e.get("id", "?"), ", ".join(miss)))
            if e.get("id") in seen:
                bad.append("duplicate evidence id " + str(e.get("id")))
            seen.add(e.get("id"))
            if e.get("status") not in STATUSES:
                bad.append("%s: unknown status %r" % (e.get("id"), e.get("status")))
            if e.get("verified") not in VERIFIED:
                bad.append("%s: unknown verified level %r" % (e.get("id"), e.get("verified")))
            if group == "evidence" and e.get("id") != "draft_rtp" and not str(e.get("status")).startswith("peer-reviewed"):
                bad.append("%s: only peer-reviewed sources may sit in 'evidence'; use 'supplementary'" % e.get("id"))
            if group == "supplementary" and str(e.get("status")).startswith("peer-reviewed"):
                bad.append("%s: peer-reviewed sources belong in 'evidence'" % e.get("id"))
            if e.get("pending_verification") and e.get("supports"):
                bad.append("%s: a source pending verification cannot support a claim" % e.get("id"))
            hr = e.get("adjusted_hr")
            if hr:
                lv = hr.get("levels", {})
                for key, x in lv.items():
                    if not (key.isdigit() and 0 <= int(key) <= 4 and x.get("lo", 9) <= x.get("hr", -1) <= x.get("hi", -9) and x["lo"] > 0):
                        bad.append("%s: adjusted_hr level %s needs 0 < lo <= hr <= hi" % (e.get("id"), key))
                if hr.get("reference_level") is None or str(hr["reference_level"]) in lv:
                    bad.append("%s: adjusted_hr needs a reference_level that is not itself listed" % e.get("id"))
                if e.get("verified") not in ("full_text",):
                    bad.append("%s: numeric hazard ratios require verified=full_text" % e.get("id"))
            if e.get("id") == "draft_rtp" and e.get("design") != "Not used.":
                bad.append("draft_rtp must stay 'Not used.'")
    ceilings = {pa.get("active_ladder", "A"): (pa.get("rho_bio_ladder", []), pa.get("rho_bio_ceiling", 0.70))}
    for nm, alt in pa.get("ladder_alternatives", {}).items():
        if nm in ceilings:
            bad.append("ladder name %r is used twice" % nm)
        ceilings[nm] = (alt.get("ladder", []), alt.get("ceiling", 0.70))
    for nm, (lad, ceil) in ceilings.items():
        if sorted(r.get("ecog") for r in lad) != [0, 1, 2, 3, 4]:
            bad.append("ladder %s must cover ECOG 0 to 4 exactly once" % nm)
            continue
        vals = [r["value"] for r in sorted(lad, key=lambda r: r["ecog"], reverse=True)]
        if not all(0 < v < 1 for v in vals) or vals != sorted(vals) or len(set(vals)) != len(vals):
            bad.append("ladder %s: rho_bio values must lie in (0,1) and rise strictly as ECOG falls" % nm)
        if not (0 < ceil < 1) or abs(max(vals) - ceil) > 1e-9:
            bad.append("ladder %s: the top value must equal its ceiling (%s)" % (nm, ceil))
        for r in lad:
            if r.get("evidence") not in EVIDENCE_GRADES:
                bad.append("ladder %s ECOG %s: evidence grade must be one of %s" % (nm, r.get("ecog"), sorted(EVIDENCE_GRADES)))
    a = pa.get("L_anchors", {})
    if not (0 < a.get("r_lo", 0) < a.get("r_hi", 0) <= 1):
        bad.append("L_anchors need 0 < r_lo < r_hi <= 1")
    if pa.get("locked"):
        lock = _read_lock()
        if lock is None:
            bad.append("parameters are locked but prereg_lock.json is missing")
        elif lock.get("params_sha256") != lock_hash(pa):
            bad.append("LOCKED parameters were changed after pre-registration (hash mismatch); a new major registry version with a stated reason is required")
        elif lock.get("code_sha256") and lock["code_sha256"] != code_hashes():
            changed = sorted(k for k in set(lock["code_sha256"]) | set(code_hashes()) if lock["code_sha256"].get(k) != code_hashes().get(k))
            bad.append("LOCKED engine code changed after pre-registration: %s; a new major version with a stated reason is required" % ", ".join(changed))
    ids = set()
    for c in co.get("cohorts", []):
        if not c.get("id") or c["id"] in ids:
            bad.append("cohort ids must be present and unique")
        ids.add(c.get("id"))
        for k in ("source_evidence_id", "centre", "period", "n", "cancer_scope", "ecog_levels_reported", "ecog_pooling"):
            if c.get(k) in (None, ""):
                bad.append("cohort %s: missing %s" % (c.get("id"), k))
    return bad


CODE_FILES = ("core/rmti_core.py", "dynamic/rmti_dynamic.py", "oncology/rmti_lung.py", "oncology/lung_evidence.py")


def _code_root():
    """The engine package that holds the registry (rmti-python/ in the repo, rmti_engine/ in the platform)."""
    return os.path.dirname(os.path.dirname(REG_DIR))


def code_hashes():
    """SHA-256 of the engine files that hold constants the parameter file does not (V range, consequence ladder, tiers).
    Line endings are normalised so a Windows checkout hashes the same as Linux."""
    out = {}
    for rel in CODE_FILES:
        path = os.path.join(_code_root(), rel)
        if os.path.exists(path):
            with open(path, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    return out


def _read_lock():
    if not os.path.exists(LOCK_FILE):
        return None
    with open(LOCK_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def _bump(ev, pa):
    """YYYY.M.N: N counts releases within the month; a new month restarts at 1."""
    y, m, n = ev["registry_version"].split(".")
    ny, nm = time.strftime("%Y"), str(int(time.strftime("%m")))
    new = "%s.%s.%d" % (y, m, int(n) + 1) if (y, m) == (ny, nm) else "%s.%s.1" % (ny, nm)
    ev["registry_version"] = pa["registry_version"] = new
    return new


def add_evidence(entry, supplementary=False):
    """Append a source; bump the registry version; refuse if the result does not validate. Scores never change."""
    reg = load()
    ev, pa = reg["evidence"], reg["parameters"]
    ev.setdefault("supplementary" if supplementary else "evidence", []).append(dict(entry, added=time.strftime("%Y-%m-%d")))
    _bump(ev, pa)
    problems = validate(dict(reg, evidence=ev, parameters=pa))
    if problems:
        raise ValueError("; ".join(problems))
    _write("evidence", ev)
    _write("parameters", pa)
    return ev["registry_version"]


def register_cohort(meta):
    """Record cohort METADATA (never patient data). Flags probable overlap with cohorts already registered, so two
    papers from the same centre and period are not counted as independent evidence."""
    reg = load()
    co, ev, pa = reg["cohorts"], reg["evidence"], reg["parameters"]
    flags = overlap_flags(meta, co.get("cohorts", []))
    co.setdefault("cohorts", []).append(dict(meta, overlap_flags=[f["with"] for f in flags], added=time.strftime("%Y-%m-%d")))
    _bump(ev, pa)
    problems = validate(dict(reg, cohorts=co, evidence=ev, parameters=pa))
    if problems:
        raise ValueError("; ".join(problems))
    _write("cohorts", co)
    _write("evidence", ev)
    _write("parameters", pa)
    return {"registry_version": ev["registry_version"], "overlap_flags": flags}


def _years(period):
    ys = [int(y) for y in re.findall(r"(?:19|20)\d{2}", str(period))]
    return (min(ys), max(ys)) if ys else None


def overlap_flags(meta, existing):
    out = []
    for c in existing:
        same_centre = meta.get("centre", "").strip().lower() == c.get("centre", "").strip().lower() and meta.get("centre")
        a, b = _years(meta.get("period")), _years(c.get("period"))
        years = bool(a and b and a[0] <= b[1] and b[0] <= a[1])
        if same_centre and years:
            out.append({"with": c["id"], "reason": "same centre and overlapping period: not independent evidence"})
    return out


def set_active_ladder(name):
    """Make ladder `name` the active rho_bio ladder (the other becomes an alternative). Refused once locked.
    The engine, sandbox page and workbook must then be regenerated (repo: tools/set_lung_ladder.py does the sandbox)."""
    pa, ev = _read("parameters"), _read("evidence")
    if pa.get("locked"):
        raise ValueError("parameters are locked: a new major registry version with a stated reason is required")
    cur = pa.get("active_ladder", "A")
    if name == cur:
        return ev["registry_version"]
    alts = pa.get("ladder_alternatives", {})
    if name not in alts:
        raise ValueError("unknown ladder %r; available: %s" % (name, sorted(list(alts) + [cur])))
    new = alts.pop(name)
    alts[cur] = {"ladder": pa["rho_bio_ladder"], "ceiling": pa["rho_bio_ceiling"], "name": pa.get("ladder_name", "")}
    pa["rho_bio_ladder"], pa["rho_bio_ceiling"], pa["ladder_name"], pa["active_ladder"] = new["ladder"], new["ceiling"], new.get("name", ""), name
    pa["ladder_alternatives"] = alts
    _bump(ev, pa)
    problems = validate(dict(load(), evidence=ev, parameters=pa))
    if problems:
        raise ValueError("; ".join(problems))
    _write("parameters", pa)
    _write("evidence", ev)
    return ev["registry_version"]


PREREG_LADDER_RE = re.compile(r"Primary ladder \(read by `registry\.py lock`\):\s*\**\s*([AB])\b")


def prereg_path():
    return os.environ.get("RMTI_PREREG_FILE") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "PREREGISTRATION_lung.md")


def prereg_ladder():
    """The primary ladder letter declared in the pre-registration document, or raise ValueError."""
    path = prereg_path()
    if not os.path.isfile(path):
        raise ValueError("pre-registration file not found (%s); set RMTI_PREREG_FILE or restore docs/PREREGISTRATION_lung.md" % path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = PREREG_LADDER_RE.search(text)
    if not m:
        raise ValueError("%s does not declare 'Primary ladder (read by `registry.py lock`): A|B'" % os.path.basename(path))
    return m.group(1), hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def lock():
    pa = _read("parameters")
    declared, prereg_sha = prereg_ladder()                       # raises before anything is written
    active = pa.get("active_ladder", "A")
    if active != declared:
        raise ValueError("REFUSED: the pre-registration declares ladder %s as primary but the registry's active ladder is %s. "
                         "Run `python tools/set_lung_ladder.py %s`, rebuild and re-run the checks, then lock." % (declared, active, declared))
    pa["locked"] = True
    _write("parameters", pa)
    with open(LOCK_FILE, "w", encoding="utf-8") as fh:
        json.dump({"params_sha256": lock_hash(pa), "code_sha256": code_hashes(), "registry_version": pa["registry_version"],
                   "active_ladder": pa.get("active_ladder", "A"), "prereg_sha256": prereg_sha, "locked_on": time.strftime("%Y-%m-%d")}, fh, indent=1)
    return lock_hash(pa)


def propose(change, author):
    """Queue a proposed change for human review. Does NOT alter the active registry."""
    if not isinstance(change, dict) or not change.get("target") or not change.get("reason"):
        raise ValueError("a proposal needs 'target' and a stated 'reason'")
    os.makedirs(PROPOSAL_DIR, exist_ok=True)
    pid = "%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), hashlib.sha1(json.dumps(change, sort_keys=True).encode()).hexdigest()[:6])
    with open(os.path.join(PROPOSAL_DIR, pid + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"id": pid, "author": author, "status": "pending-review", "registry_at_proposal": stamp(), "change": change}, fh, indent=1)
    return pid


def list_proposals():
    if not os.path.isdir(PROPOSAL_DIR):
        return []
    out = []
    for f in sorted(os.listdir(PROPOSAL_DIR)):
        if f.endswith(".json"):
            with open(os.path.join(PROPOSAL_DIR, f), encoding="utf-8") as fh:
                out.append(json.load(fh))
    return out


# ---------------------------------------------------------------------------------------------------------------
def ladder_face_validity(source_id=None, ladder=None):
    """Compare the ladder's implied risk multiplier with published adjusted hazard ratios.
    With care capacity held fixed, R scales with (1 - rho_bio) (rho = 1-(1-rho_bio)(1-rho_care)), so level k versus the
    reference level implies a multiplier (1 - rho_k) / (1 - rho_ref). It is a FACE-VALIDITY check, not calibration:
    R is not a hazard, values are assigned not estimated, and a survival hazard in patients with cancer is a different
    construct from reserve against lung-cancer-related harm. Use it to see where equal steps compress or stretch."""
    reg = load()
    pa = reg["parameters"]
    name = ladder or pa.get("active_ladder", "A")
    if name == pa.get("active_ladder", "A"):
        rows_ = pa["rho_bio_ladder"]
    elif name in pa.get("ladder_alternatives", {}):
        rows_ = pa["ladder_alternatives"][name]["ladder"]
    else:
        raise ValueError("unknown ladder %r" % name)
    lad = {r["ecog"]: r["value"] for r in rows_}
    out = []
    for e in reg["evidence"]["evidence"] + reg["evidence"].get("supplementary", []):
        hr = e.get("adjusted_hr")
        if not hr or (source_id and e["id"] != source_id):
            continue
        ref = int(hr["reference_level"])
        denom = 1 - lad[ref]
        max_mult = 1 / denom                               # a level with rho_bio = 0 cannot exceed this
        rows = []
        for k, x in sorted(hr["levels"].items(), key=lambda kv: int(kv[0])):
            implied = (1 - lad[int(k)]) / denom
            verdict = "within the 95% interval" if x["lo"] <= implied <= x["hi"] else \
                      ("ladder too steep (implied above the interval)" if implied > x["hi"] else
                       "ladder too shallow (implied below the interval)")
            if x["lo"] > max_mult:
                verdict += "; unreachable: even rho_bio = 0 gives at most %.2f" % max_mult
            rows.append({"ecog": int(k), "observed_hr": x["hr"], "ci95": [x["lo"], x["hi"]],
                         "ladder_implied": round(implied, 3), "verdict": verdict})
        out.append({"source": e["id"], "ladder": name, "reference_ecog": ref, "model": hr.get("model"),
                    "ladder_max_multiplier": round(max_mult, 3), "levels": rows})
    return out


# ---------------------------------------------------------------------------------------------------------------
# Does a new cohort support each step of the rho_bio ladder?  Descriptive, unadjusted, and honest about sparse cells.
def _km_median(time_, event):
    import numpy as np
    t, e = np.asarray(time_, float), np.asarray(event, int)
    s = 1.0
    for u in np.unique(t[e == 1]):
        s *= 1 - ((t == u) & (e == 1)).sum() / (t >= u).sum()
        if s <= 0.5:
            return float(u)
    return None


def ladder_support(df, ecog="ecog", time_col="time", event="event", min_events=10):
    """Per ECOG level: n, events, KM median, crude event rate; per adjacent step: rate ratio with 95% CI and a verdict.
    Crude exponential rate ratios (events / person-time): a screen for whether a dataset can inform a step, NOT an
    adjusted hazard ratio. Levels with fewer than min_events events are reported as 'sparse'."""
    import math
    import pandas as pd
    for c in (ecog, time_col, event):
        if c not in df.columns:
            raise ValueError("column %r not found; columns present: %s" % (c, ", ".join(map(str, df.columns))))
    d = df[[ecog, time_col, event]].dropna()
    d = d[d[ecog].isin([0, 1, 2, 3, 4])]
    if d.empty:
        raise ValueError("no rows with ECOG 0-4, a time and an event indicator")
    if (d[time_col] <= 0).any() or not d[event].isin([0, 1]).all():
        raise ValueError("time must be > 0 and event must be 0/1")
    levels = []
    for k in (0, 1, 2, 3, 4):
        g = d[d[ecog] == k]
        ev, pt = int(g[event].sum()), float(g[time_col].sum())
        levels.append({"ecog": k, "n": int(len(g)), "events": ev, "person_time": round(pt, 3),
                       "rate": (ev / pt) if pt > 0 else None, "km_median": _km_median(g[time_col], g[event]) if len(g) else None,
                       "sparse": ev < min_events})
    steps = []
    for a, b in zip(levels, levels[1:]):
        step = {"from": a["ecog"], "to": b["ecog"]}
        if not a["rate"] or not b["rate"] or a["events"] == 0 or b["events"] == 0:
            step.update(rate_ratio=None, ci95=None, verdict="no data")
        else:
            rr = b["rate"] / a["rate"]
            se = math.sqrt(1.0 / a["events"] + 1.0 / b["events"])
            lo, hi = rr * math.exp(-1.96 * se), rr * math.exp(1.96 * se)
            sparse = a["sparse"] or b["sparse"]
            verdict = "sparse (fewer than %d events in a level)" % min_events if sparse else \
                      ("separates" if lo > 1 else "reversed" if hi < 1 else "inconclusive")
            step.update(rate_ratio=round(rr, 3), ci95=[round(lo, 3), round(hi, 3)], verdict=verdict)
        steps.append(step)
    return {"levels": levels, "steps": steps,
            "supports_five_levels": all(s["verdict"] == "separates" for s in steps),
            "note": "Crude, unadjusted, exponential. A dataset that does not separate a step cannot calibrate it; "
                    "pooled or sparse levels mean the ladder must stay provisional there. Proposals go through propose()."}


def _main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        p = validate()
        print("OK: registry %s consistent" % stamp() if not p else "PROBLEMS:\n- " + "\n- ".join(p))
        sys.exit(1 if p else 0)
    elif cmd == "hash":
        print(stamp())
    elif cmd == "add-evidence":
        print("registry ->", add_evidence(json.load(open(sys.argv[2])), "--supplementary" in sys.argv))
    elif cmd == "register-cohort":
        print(json.dumps(register_cohort(json.load(open(sys.argv[2]))), indent=1))
    elif cmd == "set-active-ladder":
        print("active ladder ->", sys.argv[2], "registry", set_active_ladder(sys.argv[2]))
    elif cmd == "lock":
        print("locked, params sha256", lock())
    else:
        sys.exit("usage: registry.py validate|hash|add-evidence FILE [--supplementary]|register-cohort FILE|set-active-ladder A|B|lock")


if __name__ == "__main__":
    try:
        _main()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        sys.exit("ERROR: %s" % (exc.args[0] if exc.args else exc))
