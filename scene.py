"""
scene.py  --  time-indexed "scene manifests" for the RMTI cube: the same numbers the narrated videos animate, as JSON.

One source of truth for the API (scene_routes.py) and the live Streamlit page (pages/6_Live_4D_Lab.py).
Pure arithmetic on R = L * E * V * (1 - rho) using rmti_cases.py. No patient data, no imaging, no engine call.
R is a relative rubric index, not a probability, forecast or loss estimate. After-values are scenarios.

Frames walk the point through the bounded 0..1 cube (L, then E, then V), then raise resilience from 0 to rho_now,
then from rho_now to rho_after. Each frame carries the point position, the resilience shown (colour), and the running product.
"""
import rmti_cases as K

DISCLAIMER = ("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. "
              "R is a relative rubric index, not a probability. After-values are scenarios, not observations. Synthetic or published aggregate values only.")
PHASES = ("L", "E", "V", "resilience_now", "resilience_after")
BARS = ("L", "L·E", "L·E·V", "R0", "R_now", "R_after")


def _check(name, v, hi_open=False):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ValueError(f"{name} must be a number")
    if v < 0 or (v >= 1 if hi_open else v > 1):
        raise ValueError(f"{name} must be in [0, {'1)' if hi_open else '1]'}")
    return float(v)


def _cases():
    out = {}
    for c in K.FLOOD_HEAT_CASES + K.LIVER_CASES + list(K.LIVER_EXTRA.values()) + K.DISASTER_CASES + K.ONCOLOGY_CASES:
        out.setdefault(c["key"], c)            # first definition wins (flood/heat Lilongwe == disaster Lilongwe)
    return out


def _group(c):
    if c["key"] in {x["key"] for x in K.FLOOD_HEAT_CASES}:
        return "Flood and heat: African cities"
    if c["key"] in {x["key"] for x in K.LIVER_CASES} | set(K.LIVER_EXTRA):
        return "Liver cancer (HCC): published cohorts"
    if c["domain"] == "oncology":
        return "Liver cancer (HCC): Faria et al. (V from counts)"
    return "Wildfire: Los Angeles 2025"


def list_cases():
    rows = [dict(key=k, label=c["label"], name=c["name"], domain=c["domain"], group=_group(c)) for k, c in _cases().items()]
    order = {"Flood and heat: African cities": 0, "Liver cancer (HCC): published cohorts": 1}
    return sorted(rows, key=lambda r: (order.get(r["group"], 9), r["name"]))


def case_inputs(key):
    c = _cases().get(key)
    if c is None:
        raise KeyError(f"unknown case '{key}'")
    return dict(L=c["L"], E=c["E"], V=c["V"], rho_now=c["rho_now"], rho_after=c["rho_after"], label=c["label"],
                domain=c["domain"], source=c["source"])


def _frame(i, phase, u, pos, rho, product, R0, tiered):
    return dict(i=i, phase=phase, u=round(u, 4), pos=[round(p, 4) for p in pos], rho=round(rho, 4),
                product=round(product, 5), tier=(K.tier(product) if tiered else None))


def build(L, E, V, rho_now, rho_after, label="custom", domain="disaster", per_leg=12):
    L, E, V = _check("L", L), _check("E", E), _check("V", V)
    rho_now, rho_after = _check("rho_now", rho_now, True), _check("rho_after", rho_after, True)
    if domain not in ("disaster", "oncology"):
        raise ValueError("domain must be 'disaster' or 'oncology'")
    if not 2 <= per_leg <= 60:
        raise ValueError("per_leg must be between 2 and 60")
    R0 = L * E * V
    Rn, Ra = K.r_score(L, E, V, rho_now), K.r_score(L, E, V, rho_after)
    frames = []
    for leg, phase in enumerate(("L", "E", "V")):                      # point travels L -> E -> V
        for q in range(per_leg + (1 if leg == 0 else 0)):
            f = (q if leg == 0 else q + 1) / per_leg
            u = leg + f if leg else f
            if leg == 0:
                pos, prod = (L * f, 0, 0), L * f
            elif leg == 1:
                pos, prod = (L, E * f, 0), L * E * f
            else:
                pos, prod = (L, E, V * f), R0 * f
            frames.append(_frame(len(frames), phase, u, pos, 0.0, prod, R0, False))
    for phase, a, b in (("resilience_now", 0.0, rho_now), ("resilience_after", rho_now, rho_after)):
        for q in range(1, per_leg + 1):
            r = a + (b - a) * q / per_leg
            frames.append(_frame(len(frames), phase, 3.0, (L, E, V), r, R0 * (1 - r), R0, True))
    tn = K.tier_no(Rn)
    posture = (K.POSTURE_HCC if domain == "oncology" else K.POSTURE_DISASTER)[tn]
    case = dict(L=L, E=E, V=V, rho_now=rho_now, rho_after=rho_after)
    base, d = K.tornado(case)
    nt = K.to_next_tier(case)
    return dict(
        label=label, domain=domain, equation="R = L * E * V * (1 - rho)", inputs=dict(L=L, E=E, V=V, rho_now=rho_now, rho_after=rho_after),
        phases=list(PHASES), bars=list(BARS), per_leg=per_leg, frame_count=len(frames), frames=frames,
        summary=dict(R0=round(R0, 5), R_now=round(Rn, 5), R_after=round(Ra, 5), delta=round(Ra - Rn, 5),
                     tier_now=K.tier(Rn), tier_after=K.tier(Ra), posture_now=posture,
                     lever_steps_R_falls_by={k: round(-v, 5) for k, v in d.items()},
                     to_next_tier=None if nt is None else dict(target_below=nt["target"], need={k: (None if v is None else round(v, 4)) for k, v in nt["need"].items()},
                                                               feasible=nt["feasible"])),
        disclaimer=DISCLAIMER)


def scene_for_case(key, per_leg=12):
    c = case_inputs(key)
    s = build(c["L"], c["E"], c["V"], c["rho_now"], c["rho_after"], label=c["label"], domain=c["domain"], per_leg=per_leg)
    s["source"] = c["source"]; s["case_key"] = key
    return s


def bar_values(frame, inputs):
    """Running-product bar heights for one frame (same logic as the video's bar chart)."""
    L, E, V = inputs["L"], inputs["E"], inputs["V"]
    R0 = L * E * V; Rn = R0 * (1 - inputs["rho_now"])
    p, ph = frame["product"], frame["phase"]
    full = [L, L * E, R0, R0, Rn, 0.0]
    vals = [0.0] * 6
    if ph == "L": vals[0] = p
    elif ph == "E": vals[0], vals[1] = L, p
    elif ph == "V": vals[0], vals[1], vals[2] = L, L * E, p
    elif ph == "resilience_now": vals[:4] = full[:4]; vals[4] = p
    else: vals[:5] = full[:5]; vals[5] = p
    return vals
