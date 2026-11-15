"""
liver_progression.py  --  RMTI time-indexed trajectory (HCC) as animation frames for a rotating 3D liver.

The numbers come from the unchanged RMTI time-indexed engine (dynamic.rmti_dynamic.run_trajectory):
    V*(t) from the filtered allostatic-load indicator y(t);  rho(t) from surveillance delivery;
    R(t) = L * E * V*(t) * (1 - rho(t)),  tier and posture from the shared core.
Frames interpolate linearly between cycles and recompute R with the same formula, so cycle frames equal the engine's R.

VISUAL ENCODING (illustrative, not a medical model):
  * liver surface and colour follow V*(t) through display bands F0-F4 (smooth -> nodular). The engine has no fibrosis-stage input,
    so a band is a display bin of V*(t), not a METAVIR score and not a diagnosis.
  * the sphere on the right lobe is a risk glyph: its VOLUME is proportional to R(t) and its colour is the tier.
    It is not a tumour volume and not a growth forecast.
Research prototype. Synthetic or de-identified values only; no patient data, no imaging.
"""
import os, re, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rmti_engine"))
from core.rmti_core import tier as core_tier                                   # noqa: E402
from dynamic.rmti_dynamic import HCC_PARAMS, TrajectoryParams, run_trajectory, tier_changes   # noqa: E402
from oncology.rmti_hcc import HCC_TIER_POSTURE                                  # noqa: E402

DISCLAIMER = ("Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions. "
              "The liver is a stylised model, not an image of a patient. Surface and colour encode V*(t); the sphere's volume encodes R(t). "
              "Neither is a fibrosis stage, a tumour size or a forecast. Synthetic or de-identified values only.")
EQUATION = "R(t) = L * E * V*(t) * (1 - rho(t))"
BANDS = [(0.20, "F0 · smooth, healthy-appearing"), (0.40, "F1 · early change"), (0.60, "F2 · moderate change"),
         (0.80, "F3 · advanced change"), (1.01, "F4 · nodular, cirrhosis-like")]
TIER_HEX = ["#9fb3c8", "#4d78a8", "#e8a0a3", "#d9262c", "#8f1519"]
R_REF = 0.60                       # R at which the glyph reaches full size (the tier 4/5 boundary)

PRESETS = {
    "Progression, then surveillance rescue": dict(L=0.75, E=0.80, C=5, rho0=0.20,
        y=[1.0, 1.4, 1.9, 2.6, 3.4, 3.9, 3.5, 3.0], delivery=[0.40, 0.40, 0.45, 0.50, 0.70, 0.85, 0.90, 0.90]),
    "Sustained surveillance (stable)": dict(L=0.30, E=0.60, C=5, rho0=0.45,
        y=[1.5, 1.4, 1.6, 1.5, 1.4, 1.5, 1.4, 1.5], delivery=[0.80] * 8),
    "Missed visits, then progression": dict(L=0.75, E=0.80, C=5, rho0=0.20,
        y=[1.2, 1.5, None, None, 2.8, 3.6, 4.2, 4.6], delivery=[0.50, 0.30, 0.10, 0.10, 0.30, 0.40, 0.40, 0.40]),
}


def tier_number(label):
    return int(re.search(r"\d", label).group())


def stage_fraction(V, p=HCC_PARAMS):
    return float(min(1.0, max(0.0, (V - p.v_lo) / (p.v_hi - p.v_lo))))


def stage_band(f):
    for upper, name in BANDS:
        if f < upper:
            return name


def glyph_radius(R, r_max=0.30):
    """Sphere volume proportional to R: radius = r_max * (R / R_REF)^(1/3), capped at r_max."""
    return float(r_max * min(1.0, max(0.0, R) / R_REF) ** (1.0 / 3.0))


def _params(overrides=None):
    return TrajectoryParams(**{**HCC_PARAMS.__dict__, **(overrides or {})})


def engine_rows(L, E, C, rho0, observations, delivery, params=None):
    return run_trajectory(L, E, C, rho0, list(observations), list(delivery), _params(params), HCC_TIER_POSTURE)


def manifest(L, E, C, rho0, observations, delivery, params=None, sub=10, turns=1.0):
    if not 1 <= sub <= 30:
        raise ValueError("sub must be between 1 and 30")
    if not 0 <= turns <= 4:
        raise ValueError("turns must be between 0 and 4")
    p = _params(params)
    rows = run_trajectory(L, E, C, rho0, list(observations), list(delivery), p, HCC_TIER_POSTURE)
    n = len(rows)
    total = (n - 1) * sub + 1
    frames = []
    for k in range(total):
        if n == 1:
            i, w = 0, 0.0
            a = b = rows[0]
        else:
            c = k / sub
            i = min(int(c), n - 2)
            w = c - i
            a, b = rows[i], rows[i + 1]
        V = a["V"] + (b["V"] - a["V"]) * w
        rho = a["rho"] + (b["rho"] - a["rho"]) * w
        R = L * E * V * (1 - rho)                                   # the RMTI formula, same as the engine's score()
        tl = core_tier(R)
        f = stage_fraction(V, p)
        frames.append(dict(k=k, cycle=round(k / sub, 4), is_cycle=(k % sub == 0), V=round(V, 5), rho=round(rho, 5), R=round(R, 6),
                           tier=tl, tier_no=tier_number(tl), stage_f=round(f, 4), stage_band=stage_band(f),
                           glyph_radius=round(glyph_radius(R), 4), azimuth_deg=round(360.0 * turns * k / max(total - 1, 1), 2)))
    return dict(equation=EQUATION, inputs=dict(L=L, E=E, C=C, rho0=rho0, observations=list(observations), delivery=list(delivery)),
                params=p.__dict__, cycles=rows, sub=sub, turns=turns, frame_count=len(frames), frames=frames,
                tier_changes=tier_changes(rows), disclaimer=DISCLAIMER)


# ----------------------------------------------------------------------------------------------- geometry (procedural, no imaging)
def _smooth(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0, 1)
    return t * t * (3 - 2 * t)


def _grid(nt, npp):
    th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    ph = np.linspace(1e-3, np.pi - 1e-3, npp)
    return np.meshgrid(th, ph)


def _faces(nt, npp):
    i, j, k = [], [], []
    for a in range(npp - 1):
        for b in range(nt):
            b2 = (b + 1) % nt
            p00, p01, p10, p11 = a * nt + b, a * nt + b2, (a + 1) * nt + b, (a + 1) * nt + b2
            i += [p00, p01]; j += [p10, p10]; k += [p01, p11]
    return i, j, k


def _lerp_hex(stops, f):
    xs = [s[0] for s in stops]
    cols = np.array([[int(s[1][q:q + 2], 16) for q in (1, 3, 5)] for s in stops], float)
    rgb = [np.interp(f, xs, cols[:, c]) for c in range(3)]
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in rgb)


LIVER_COLORS = [(0.0, "#e9d5d6"), (0.25, "#e29698"), (0.50, "#c85a60"), (0.75, "#a8363c"), (1.0, "#7d1c22")]


def liver_color(f):
    return _lerp_hex(LIVER_COLORS, float(min(1.0, max(0.0, f))))


def liver_mesh(f, nt=40, npp=20):
    """Stylised liver surface for display fraction f in [0, 1]. Returns x, y, z, i, j, k, colour."""
    f = float(min(1.0, max(0.0, f)))
    TH, PH = _grid(nt, npp)
    a, b, c = 1.0, 0.62, 0.44
    x0, y0, z0 = a * np.sin(PH) * np.cos(TH), b * np.sin(PH) * np.sin(TH), c * np.cos(PH)
    nx, ny, nz = x0 / a ** 2, y0 / b ** 2, z0 / c ** 2
    nrm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2) + 1e-9
    nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
    x, y, z = x0.copy(), y0.copy(), z0.copy()
    left = 0.5 * (1 - np.tanh(3 * x0))                              # left lobe tapers
    sc = 1 - 0.42 * left * (0.5 + 0.5 * np.clip(-x0, 0, 1))
    y, z = y * sc, z * sc ** 1.2
    z = np.where(z < 0, z * 0.75, z)                                 # flatter underside
    z = z + 0.10 * np.exp(-(((x - 0.05) ** 2) + y ** 2) / 0.05) * (z < 0)    # shallow fissure
    undulate = 0.6 * np.sin(3 * TH + 0.8) * np.sin(2 * PH + 0.3) + 0.4 * np.sin(5 * TH + PH)
    nod = np.tanh(1.5 * (np.sin(6 * TH + 1.1) * np.sin(7 * PH + 0.6) + 0.5 * np.sin(9 * TH + 2 * PH)))
    amp_n = 0.050 * _smooth(0.20, 1.0, f) ** 1.2                      # nodularity grows with the display fraction
    amp_u = 0.012 + 0.02 * _smooth(0.10, 0.6, f)
    swell = 1 + 0.06 * np.exp(-((f - 0.35) / 0.2) ** 2) - 0.10 * _smooth(0.70, 1.0, f)     # swollen early, shrunken late
    d = amp_n * nod + amp_u * undulate
    X, Y, Z = (x + nx * d) * swell, (y + ny * d) * swell, (z + nz * d) * swell
    i, j, k = _faces(nt, npp)
    r3 = lambda A: np.round(A.ravel(), 3).tolist()                    # noqa: E731
    return r3(X), r3(Y), r3(Z), i, j, k, liver_color(f)


GLYPH_CENTER = (0.45, -0.02, 0.42)       # on the upper surface of the right lobe, so it protrudes


def sphere_mesh(radius, center=GLYPH_CENTER, nt=24, npp=12):
    TH, PH = _grid(nt, npp)
    r = max(radius, 1e-3)
    X, Y, Z = center[0] + r * np.sin(PH) * np.cos(TH), center[1] + r * np.sin(PH) * np.sin(TH), center[2] + r * np.cos(PH)
    i, j, k = _faces(nt, npp)
    r3 = lambda A: np.round(A.ravel(), 3).tolist()                    # noqa: E731
    return r3(X), r3(Y), r3(Z), i, j, k
