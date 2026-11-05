"""
rmti_video_engine.py  --  scene renderers, voice-over, captions and MP4 muxing for the RMTI videos.

Reads NO patient data. All numbers come from rmti_cases.py (published rows, aggregate counts, illustrative values).
Output per video: <name>.mp4 (H.264 + AAC voice + a soft English caption track that is OFF by default),
                  <name>.srt and <name>.vtt (captions as separate files for YouTube / web players).

Research prototype. Not validated, not a medical device.
"""
import json, os, re, shutil, subprocess, sys, textwrap, wave
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import rmti_cases as K          # noqa: E402
import voice_backends as VB     # noqa: E402

NAME = "Dr. Cesar Marolla"
ROLE = "Core logic created and formulated by Dr. Cesar Marolla"
TAGLINE = "Quantifying systemic risk in disaster science and oncology"
API_TITLE = "Risk Mechanism Theory Index (RMTI) API"
ORCID = "ORCID 0000-0001-8498-7380"
DEMO_URL = "oncoclastics.streamlit.app"
FPS, W, H = 20, 1280, 720
CMAP = LinearSegmentedColormap.from_list("rho", ["#b3261e", "#e8a317", "#1b7f5c"])
TIER_COL = ["#7F8FA6", "#4A6FA5", "#C9A227", "#C2662D", "#9B2C2C"]
TIER_EDGES = [(0, .05), (.05, .15), (.15, .35), (.35, .60), (.60, 5)]
TIER_NAMES = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
BAR_COL = ["#b3261e", "#e8a317", "#1b7f5c"]
INK, SLATE, DARK, TEAL = "#0b3b40", "#37474f", "#0b3b40", "#0b5c63"
FOOT = ("Research prototype · not validated · not a medical device · not for patient-care or emergency decisions · "
        "R is a relative index, not a probability")
LEVER_LABEL = {"L": "L  likelihood", "E": "E  exposure", "V": "V  vulnerability", "rho": "ρ  resilience"}


# ======================================================================= helpers
def clip01(x): return float(np.clip(x, 0, 1))
def ease(t):
    t = clip01(t); return t * t * (3 - 2 * t)
def N(sec): return int(round(sec * FPS))


def new_axes(fig, dark=False):
    fig.clf(); fig.patch.set_facecolor(DARK if dark else "white")
    a = fig.add_axes([0, 0, 1, 1]); a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
    return a


def chrome(a, dark=False):
    sub = "#9fb8bb" if dark else "#78909c"
    a.text(0.985, 0.968, "DEMO MODE · NO PATIENT DATA", ha="right", va="top", fontsize=9.5, weight="bold", color="#7c2d12",
           bbox=dict(boxstyle="round,pad=0.4", fc="#fff7ed", ec="#b45309"))
    a.text(0.5, 0.043, FOOT, ha="center", fontsize=8.5, color=sub)
    a.text(0.5, 0.018, f"{NAME} · RMTI · Apache-2.0 · independent academic work", ha="center", fontsize=8.5, color=sub)


def wrap(a, text, x, y, width, size, color=INK, weight="normal", dy=0.055):
    for line in textwrap.wrap(text, width) or [""]:
        a.text(x, y, line, fontsize=size, color=color, weight=weight, va="top"); y -= dy
    return y


def head(a, t, sub=None):
    a.text(0.04, 0.955, t, fontsize=20 if len(t) <= 52 else 16.5, weight="bold", color=INK, va="top")
    if sub:
        a.text(0.04, 0.893, sub, fontsize=13.5, color=SLATE, va="top")


def cube_axes(fig, rect, azim=0):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_zlim(0, 1); ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("L likelihood", labelpad=8); ax.set_ylabel("E exposure", labelpad=8); ax.set_zlabel("V vulnerability", labelpad=4)
    for t in (ax.xaxis, ax.yaxis, ax.zaxis):
        t.set_ticks([0, 0.5, 1])
    ax.view_init(elev=22, azim=-58 + azim)
    for p in (0, 1):
        for q in (0, 1):
            ax.plot([0, 1], [p, p], [q, q], color="#cfd8dc", lw=0.8); ax.plot([p, p], [0, 1], [q, q], color="#cfd8dc", lw=0.8)
            ax.plot([p, p], [q, q], [0, 1], color="#cfd8dc", lw=0.8)
    return ax


def rho_key(fig, rect=(0.535, 0.25, 0.010, 0.34)):
    cax = fig.add_axes(list(rect))
    cax.imshow(np.linspace(1, 0, 100)[:, None], cmap=CMAP, aspect="auto", extent=[0, 1, 0, 1])
    cax.set_xticks([]); cax.yaxis.tick_right(); cax.set_yticks([0, 1]); cax.set_yticklabels(["ρ = 0", "ρ = 1"], fontsize=8)
    cax.set_title("resilience", fontsize=8)


def path_pos(u, L, E, V):
    w = [(0, 0, 0), (L, 0, 0), (L, E, 0), (L, E, V)]
    i = int(min(np.floor(u), 2)); f = u - i
    p = [w[i][j] + (w[i + 1][j] - w[i][j]) * f for j in range(3)]
    return p, w[: i + 1] + [tuple(p)]


def tier_bands(bx, ymax, labels=True):
    for (lo, hi), col, nm in zip(TIER_EDGES, TIER_COL, TIER_NAMES):
        if lo < ymax:
            bx.axhspan(lo, min(hi, ymax), color=col, alpha=0.13, lw=0)
            if labels:
                bx.text(1.02, (lo + min(hi, ymax)) / 2, "T" + nm, transform=bx.get_yaxis_transform(), fontsize=7.5, va="center", color=col)


# ======================================================================= renderers (state dict -> draws on fig)
def r_title(fig, s):
    a = new_axes(fig, True); chrome(a, True)
    a.text(0.07, 0.86, s["kicker"], fontsize=13, weight="bold", color="#e8a317", va="top")
    y = wrap(a, API_TITLE, 0.07, 0.80, 40, 35, "white", "bold", dy=0.085)
    a.text(0.07, y - 0.005, ROLE, fontsize=17, color="#d0e3e5", va="top")
    a.text(0.07, y - 0.065, TAGLINE, fontsize=15, color="#9bd1d6", va="top")
    a.text(0.07, y - 0.15, "R = L · E · V · (1 − ρ)", fontsize=28, color="white", va="top")
    a.add_patch(plt.Rectangle((0.07, 0.10), 0.006, 0.12, color="#e8a317"))
    a.text(0.09, 0.215, NAME, fontsize=22, weight="bold", color="white", va="top")
    a.text(0.09, 0.165, "Developer of the Risk Mechanism Theory Index (RMTI)", fontsize=13, color="#d0e3e5", va="top")
    a.text(0.09, 0.125, ORCID, fontsize=11, color="#9fb8bb", va="top")


def r_bullets(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.90, s["title"], fontsize=26, weight="bold", color=INK, va="top")
    y = 0.79
    for kind, text in s["items"]:
        if kind == "h":
            a.text(0.05, y, text, fontsize=16, weight="bold", color="#b45309", va="top"); y -= 0.06
        else:
            a.text(0.06, y, "•", fontsize=15, color=SLATE, va="top")
            y = wrap(a, text, 0.085, y, s.get("width", 88), s.get("size", 14.5), SLATE, dy=0.046) - 0.016


def r_section(fig, s):
    a = new_axes(fig); chrome(a)
    a.add_patch(plt.Rectangle((0.05, 0.38), 0.006, 0.32, color="#e8a317"))
    a.text(0.07, 0.69, s["kicker"], fontsize=16, color="#b45309", weight="bold", va="top")
    y = wrap(a, s["title"], 0.07, 0.63, 46, 30, INK, "bold", dy=0.082)
    for t in s["lines"]:
        y = wrap(a, t, 0.07, y - 0.01, 95, 14.5, SLATE, dy=0.048)


def r_tiers(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.92, "Five fixed tiers of residual risk R, each with a posture", fontsize=24, weight="bold", color=INK, va="top")
    labels = ["R < 0.05", "0.05 – 0.15", "0.15 – 0.35", "0.35 – 0.60", "R ≥ 0.60"]
    for i in range(5):
        x = 0.05 + i * 0.185
        a.add_patch(plt.Rectangle((x, 0.66), 0.17, 0.17, color=TIER_COL[i]))
        a.text(x + 0.085, 0.77, TIER_NAMES[i].split()[0], fontsize=26, color="white", weight="bold", ha="center", va="center")
        a.text(x + 0.085, 0.715, TIER_NAMES[i].split()[1], fontsize=13, color="white", ha="center", va="center")
        a.text(x + 0.085, 0.678, labels[i], fontsize=10.5, color="white", ha="center", va="center")
        wrap(a, K.POSTURE_HCC[i + 1], x, 0.60, 21, 9.5, SLATE, dy=0.036)
        wrap(a, K.POSTURE_DISASTER[i + 1], x, 0.36, 21, 9.5, SLATE, dy=0.036)
    a.text(0.05, 0.635, "Liver (HCC) surveillance posture", fontsize=11, color="#b45309", weight="bold", va="top")
    a.text(0.05, 0.395, "Disaster and infrastructure posture", fontsize=11, color="#b45309", weight="bold", va="top")
    wrap(a, "The same thresholds apply to every patient, city and year. A tier is a reading of a research framework for discussion, "
            "not a clinical or engineering decision.", 0.05, 0.20, 120, 11.5, "#78909c", dy=0.04)


def r_concept(fig, s):
    a = new_axes(fig); chrome(a)
    c = s["c"]; L, E, V = c["L"], c["E"], c["V"]
    fin = (L, L * E, L * E * V, L * E * V, L * E * V * (1 - c["rho_now"]), L * E * V * (1 - c["rho_after"]))
    labels = ["L", "L·E", "L·E·V", "R₀\n(ρ = 0)", "R\n(ρ now)", "R\n(ρ after)"]
    cols = ["#607d8b"] * 3 + BAR_COL
    t1, _, t2 = s["title"].partition("\n")
    head(a, t1, t2)
    ax = cube_axes(fig, [0.02, 0.22, 0.55, 0.60])
    p, pts = path_pos(s["u"], L, E, V); xs, ys, zs = zip(*pts)
    ax.plot(xs, ys, zs, color="#607d8b", lw=3.5)
    ax.scatter([p[0]], [p[1]], [p[2]], s=220, c=[s["rho"]], cmap=CMAP, vmin=0, vmax=1, edgecolors="#263238", linewidths=1.6, depthshade=False)
    rho_key(fig, (0.585, 0.30, 0.010, 0.30))
    bx = fig.add_axes([0.68, 0.30, 0.30, 0.46])
    vals = [fin[k] * clip01(s["rev"] - k) for k in range(6)]
    bx.bar(range(6), vals, color=cols)
    for k, v in enumerate(vals):
        if v > 1e-9:
            bx.text(k, v + 0.015, f"{v:.3f}", ha="center", fontsize=9)
    bx.set_ylim(0, 1); bx.set_xticks(range(6)); bx.set_xticklabels(labels, fontsize=8)
    bx.set_title("Running product", fontsize=11); bx.spines[["top", "right"]].set_visible(False)
    if s.get("onc"):
        a.text(0.04, 0.175, "Oncology  ", fontsize=11.5, color="#b45309", weight="bold", va="top")
        a.text(0.135, 0.175, s["onc"], fontsize=11.5, color=SLATE, va="top")
        a.text(0.04, 0.125, "Disaster  ", fontsize=11.5, color="#b45309", weight="bold", va="top")
        a.text(0.135, 0.125, s["dis"], fontsize=11.5, color=SLATE, va="top")


def r_albi(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.93, "From ALBI grades to vulnerability V", fontsize=25, weight="bold", color=INK, va="top")
    a.text(0.05, 0.855, f"Faria et al. cohort · Harvard Dataverse · doi:{K.FARIA_DOI} · aggregate grade counts only, no patient-level records",
           fontsize=11.5, color="#546e7a", va="top")
    gcol = ["#9ccfd3", "#4A9aa3", "#0b5c63"]; an = K.ALBI_ANCHORS
    rows = [("HCC cohort", K.FARIA_COUNTS["HCC cohort"]), ("Cirrhosis cohort", K.FARIA_COUNTS["Cirrhosis cohort"])]
    bx = fig.add_axes([0.20, 0.50, 0.72, 0.26])
    for r, (nm, cnt) in enumerate(rows):
        n = sum(cnt); left = 0
        for g in range(3):
            if cnt[g]:
                bx.barh(1 - r, cnt[g] / n, left=left, color=gcol[g], height=0.55, edgecolor="white")
                bx.text(left + cnt[g] / n / 2, 1 - r, f"{cnt[g]}", ha="center", va="center", color="white", fontsize=14, weight="bold")
            left += cnt[g] / n
    bx.set_yticks([1, 0]); bx.set_yticklabels([f"{nm}\n(n={sum(c)})" for nm, c in rows], fontsize=12)
    bx.set_xlim(0, 1); bx.set_xticks([]); bx.spines[["top", "right", "bottom"]].set_visible(False)
    for g in range(3):
        a.add_patch(plt.Rectangle((0.20 + g * 0.24, 0.42), 0.018, 0.03, color=gcol[g]))
        a.text(0.225 + g * 0.24, 0.435, f"ALBI grade {g + 1}  ·  V anchor {an[g + 1]:.2f}", fontsize=12, color=SLATE, va="center")
    if s["formula"]:
        y = 0.33
        for nm, cnt in rows:
            n = sum(cnt); v = K.v_from_counts(*cnt)
            expr = " + ".join(f"{cnt[g]}×{an[g + 1]:.2f}" for g in range(3))
            a.text(0.05, y, f"{nm}:  V = ({expr}) ÷ {n}  =", fontsize=14, color=SLATE, va="center", family="monospace")
            a.text(0.80, y, f"{v:.3f}", fontsize=28, weight="bold", color=TEAL, va="center"); y -= 0.10
        a.text(0.05, 0.11, "ALBI: Johnson et al., J Clin Oncol 2015;33:550–558. Small cohorts, shown to demonstrate the arithmetic only.", fontsize=11, color="#78909c")


def r_case(fig, s):
    cases = s["cases"]; ev = [K.evaluate(c) for c in cases]
    a = new_axes(fig); chrome(a); head(a, s["title"], s["sub"])
    ax = cube_axes(fig, [0.01, 0.10, 0.52, 0.72], s["azim"])
    marks = ["o", "s", "^", "D"]
    rho_c = [c["rho_now"] * s["g1"] + (c["rho_after"] - c["rho_now"]) * s["g2"] for c in cases]
    if s["u"] > 0:
        for i, c in enumerate(cases):
            p, pts = path_pos(s["u"], c["L"], c["E"], c["V"]); xs, ys, zs = zip(*pts)
            ax.plot(xs, ys, zs, color="#90a4ae", lw=2.5)
            ax.scatter([p[0]], [p[1]], [p[2]], s=190, c=[rho_c[i]], cmap=CMAP, vmin=0, vmax=1, marker=marks[i], edgecolors="#263238", linewidths=1.6, depthshade=False)
            ax.text(p[0], p[1], p[2] + s["dz"][i], c["label"], fontsize=10, weight="bold", ha="center", color=INK)
    rho_key(fig)
    bx = fig.add_axes([0.625, 0.36, 0.29, 0.43]); ymax = s["ymax"]; tier_bands(bx, ymax)
    n = len(cases); wdt = 0.8 / 3
    for i, e in enumerate(ev):
        hs = [e["R0"] * s["g0"], e["R_now"] * s["g1"], e["R_after"] * s["g2"]]; gs = [s["g0"], s["g1"], s["g2"]]
        for j in range(3):
            x = i + (j - 1) * wdt
            bx.bar(x, hs[j], width=wdt * 0.92, color=BAR_COL[j], label=["R₀ (ρ = 0)", "R now", "R after"][j] if i == 0 else None)
            if gs[j] > 0.05:
                bx.text(x, hs[j] + ymax * 0.012, f"{hs[j]:.3f}", ha="center", fontsize=6.5 if n > 3 else 7, rotation=90, va="bottom")
    tl = []
    for i, e in enumerate(ev):
        t = cases[i]["label"]
        if s["g1"] >= 0.999:
            t += "\nT" + e["tier_now"][0] + (" → T" + e["tier_after"][0] if s["g2"] >= 0.999 else "")
        tl.append(t)
    bx.set_xticks(range(n)); bx.set_xticklabels(tl, fontsize=8); bx.set_xlim(-0.6, n - 0.4); bx.set_ylim(0, ymax)
    bx.tick_params(axis="y", labelsize=8); bx.spines[["top", "right"]].set_visible(False)
    bx.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=7.5, frameon=False)
    lines = [f"{'case':<14}{'L':>6}{'E':>6}{'V':>6}  ρ now→after"]
    for c in cases:
        lines.append(f"{c['label']:<14}{c['L']:>6.3f}{c['E']:>6.2f}{c['V']:>6.3f}  {c['rho_now']:.2f}→{c['rho_after']:.2f}")
    a.text(0.595, 0.285, "\n".join(lines), fontsize=8.5, family="monospace", color=SLATE, va="top", linespacing=1.5)
    a.text(0.595, 0.285 - 0.025 * (len(lines) + 1.3), s["note"], fontsize=8.5, color="#78909c", va="top", wrap=True)


def r_sweep(fig, s):
    c, lever, lo, hi = s["case"], s["lever"], s["lo"], s["hi"]
    val = lo + (hi - lo) * s["t"]
    L, E, V, rho = (val if k == lever else K._val(c, k) for k in K.LEVERS)
    R = K.r_score(L, E, V, rho); tn = K.tier_no(R)
    a = new_axes(fig); chrome(a); head(a, s["title"], s["sub"])
    ax = cube_axes(fig, [0.01, 0.22, 0.50, 0.60], s.get("azim", 0))
    if lever != "rho":
        pl = [K._val(c, k) for k in ("L", "E", "V")]; a0, a1 = list(pl), list(pl); idx = ("L", "E", "V").index(lever); a0[idx] = lo; a1[idx] = hi
        ax.plot([a0[0], a1[0]], [a0[1], a1[1]], [a0[2], a1[2]], color="#90a4ae", lw=2.5, ls="--")
    ax.scatter([L], [E], [V], s=230, c=[rho], cmap=CMAP, vmin=0, vmax=1, edgecolors="#263238", linewidths=1.6, depthshade=False)
    ax.text(L, E, V + 0.07, c["label"], fontsize=10, weight="bold", ha="center", color=INK)
    rho_key(fig, (0.52, 0.30, 0.010, 0.30))
    bx = fig.add_axes([0.60, 0.30, 0.31, 0.46])
    xs, ys = K.sweep(c, lever, lo, hi); ymax = max(max(ys) * 1.18, 0.06); tier_bands(bx, ymax)
    bx.plot(xs, ys, color=TEAL, lw=2.6)
    for x, lab in s.get("marks", []):
        bx.axvline(x, ls=":", color="#78909c", lw=1); bx.text(x, ymax * 0.98, " " + lab, rotation=90, va="top", ha="right", fontsize=7.5, color=SLATE)
    bx.plot([val], [R], "o", ms=12, color=TIER_COL[tn - 1], mec="#263238", mew=1.4)
    bx.set_xlim(min(lo, hi), max(lo, hi)); bx.set_ylim(0, ymax); bx.set_xlabel(LEVER_LABEL[lever], fontsize=10); bx.set_ylabel("R", fontsize=10)
    bx.tick_params(labelsize=8); bx.spines[["top", "right"]].set_visible(False)
    a.text(0.04, 0.165, f"{LEVER_LABEL[lever].split()[0]} = {val:.2f}    →    R = {R:.3f}    ·    tier {K.tier(R)}", fontsize=15, weight="bold", color=TIER_COL[tn - 1], va="top")
    a.text(0.04, 0.118, s["postures"][tn], fontsize=11.5, color=SLATE, va="top")


def r_tornado(fig, s):
    a = new_axes(fig); chrome(a); head(a, s["title"], s["sub"])
    items = sorted(s["items"], key=lambda x: -abs(x[1])); mx = max(abs(d) for _, d, _, _ in items) * 1.35
    bx = fig.add_axes([0.30, 0.22, 0.60, 0.52])
    for i, (lab, d, act, note) in enumerate(items[::-1]):
        w = abs(d) * s["g"]
        bx.barh(i, w, color=TEAL if act else "#b0bec5", height=0.55)
        if s["g"] > 0.05:
            bx.text(w + mx * 0.01, i, f"R falls by {abs(d):.3f}", va="center", fontsize=11, color=INK)
        bx.text(-mx * 0.02, i, f"{lab}\n{note}", ha="right", va="center", fontsize=11, color=INK)
    bx.set_xlim(0, mx); bx.set_ylim(-0.6, len(items) - 0.4); bx.set_yticks([]); bx.set_xticks([])
    bx.spines[["top", "right", "left"]].set_visible(False)
    wrap(a, s["foot"], 0.30, 0.16, 85, 11, "#78909c", dy=0.04)


def r_threshold(fig, s):
    c = s["case"]; nt = K.to_next_tier(c)
    a = new_axes(fig); chrome(a); head(a, s["title"], s["sub"])
    rows = [("rho", "ρ  resilience", "at least", "#1b7f5c"), ("V", "V  vulnerability", "at most", "#b3261e"), ("E", "E  exposure", "at most", "#b3261e"), ("L", "L  likelihood", "at most", "#b3261e")]
    y = 0.74
    for k, lab, rel, col in rows:
        cur = K._val(c, k); need = nt["need"][k]; fl = s.get("floors", {}).get(k)
        ok = nt["feasible"][k] and (fl is None or (need >= fl if rel == "at most" else True))
        a.text(0.05, y, lab, fontsize=14, weight="bold", color=INK, va="center")
        a.plot([0.26, 0.70], [y, y], color="#cfd8dc", lw=4, solid_capstyle="round")
        for tx in (0, 0.5, 1):
            a.text(0.26 + 0.44 * tx, y - 0.04, f"{tx:g}", fontsize=8, color="#90a4ae", ha="center", va="top")
        a.plot([0.26 + 0.44 * cur], [y], "o", ms=13, color="#263238", zorder=5)
        a.text(0.26 + 0.44 * cur, y + 0.04, f"now {cur:.2f}", fontsize=9, ha="center", color="#263238")
        if s["g"] > 0 and need is not None and 0 <= need <= 1:
            pos = cur + (need - cur) * ease(s["g"])
            a.annotate("", xy=(0.26 + 0.44 * pos, y), xytext=(0.26 + 0.44 * cur, y), arrowprops=dict(arrowstyle="-|>", color=col, lw=2.5))
            if s["g"] >= 0.999:
                a.plot([0.26 + 0.44 * need], [y], "D", ms=11, color=col, zorder=6)
        if s["g"] >= 0.999:
            txt = f"{rel} {need:.2f}" if (need is not None and 0 <= need < 1.0001) else "not reachable alone"
            if fl is not None and rel == "at most" and need is not None and need < fl:
                txt += f"\nbelow the lowest ALBI anchor ({fl:.2f}):\nnot reachable on this lever alone"
            elif k == "rho" and need is not None and need > 0.65 and s.get("rho_top"):
                txt += "\nabove the top of the published ladder"
            a.text(0.73, y, txt, fontsize=11.5 if "\n" not in txt else 10.5, color=col if ok else "#78909c", va="center", weight="bold" if ok else "normal", linespacing=1.3)
        y -= 0.135
    wrap(a, s["foot"], 0.05, 0.145, 120, 11, "#78909c", dy=0.04)


def r_eal(fig, s):
    a = new_axes(fig); chrome(a); head(a, s["title"], s["sub"])
    pats = s["patients"]
    bx = fig.add_axes([0.08, 0.22, 0.50, 0.52])
    for i, p in enumerate(pats):
        R = K.r_score(p["L"], p["E"], p["V"], p["rho"]); Cn = {1: .1, 2: .3, 3: .5, 4: .75, 5: 1.0}[p["C"]]; EAL = p["L"] * Cn * (1 - p["rho"])
        bx.bar(i - 0.2, R * s["g1"], 0.36, color="#4A6FA5", label="R (residual risk)" if i == 0 else None)
        bx.bar(i + 0.2, EAL * s["g2"], 0.36, color="#C2662D", label="EAL (L × C × (1 − ρ))" if i == 0 else None)
        if s["g1"] > .05: bx.text(i - 0.2, R * s["g1"] + 0.006, f"{R:.3f}", ha="center", fontsize=11)
        if s["g2"] > .05: bx.text(i + 0.2, EAL * s["g2"] + 0.006, f"{EAL:.3f}", ha="center", fontsize=11)
    bx.set_xticks(range(len(pats))); bx.set_xticklabels([p["label"] for p in pats], fontsize=11); bx.set_ylim(0, 0.25)
    bx.legend(frameon=False, fontsize=10, loc="upper left"); bx.spines[["top", "right"]].set_visible(False)
    y = 0.72
    for p in pats:
        y = wrap(a, p["text"], 0.62, y, 36, 11.5, SLATE, dy=0.04) - 0.03
    a.text(0.62, y - 0.01, s["foot"], fontsize=11, weight="bold", color="#b45309", va="top", wrap=True)


def r_close(fig, s):
    a = new_axes(fig, True); chrome(a, True)
    a.text(0.07, 0.82, s.get("title", "RMTI · one equation, two domains"), fontsize=32, weight="bold", color="white", va="top")
    a.text(0.07, 0.72, "R = L · E · V · (1 − ρ)", fontsize=25, color="#9bd1d6", va="top")
    a.add_patch(plt.Rectangle((0.07, 0.45), 0.006, 0.17, color="#e8a317"))
    a.text(0.09, 0.61, NAME, fontsize=25, weight="bold", color="white", va="top")
    a.text(0.09, 0.545, ROLE, fontsize=14, color="#d0e3e5", va="top")
    a.text(0.09, 0.495, ORCID, fontsize=12, color="#9fb8bb", va="top")
    y = 0.37
    for t in [f"Public demo (synthetic and published aggregate data only): {DEMO_URL}",
              "Open code under Apache-2.0 · Research prototype, not validated, not a medical device",
              "Independent academic work. Not an official product of the World Bank Group, Harvard University or any other institution.",
              "No patient data is used or shown. Nothing here is medical or engineering advice."]:
        y = wrap(a, t, 0.07, y, 108, 12.5, "#d0e3e5", dy=0.045)
    a.text(0.07, y - 0.015, "Contact: cesar.marolla@alumni.harvard.edu", fontsize=16, weight="bold", color="#ffd37a", va="top")


RENDER = dict(title=r_title, bullets=r_bullets, section=r_section, tiers=r_tiers, concept=r_concept, albi=r_albi, case=r_case,
              sweep=r_sweep, tornado=r_tornado, threshold=r_threshold, eal=r_eal, close=r_close)


# ======================================================================= storyboard helpers
def seg(id_, text, states, min_dur=3.0):
    return dict(id=id_, text=text, states=states, min=min_dur)


def one(state): return [(state, 1)]
def anim(make, n, hold_state=None):
    st = [(make(ease(q / n)), 1) for q in range(1, n + 1)]
    return st


def case_segments(prefix, cases, ymax, dz, title, texts, subs, note, b_secs=3.2):
    base = dict(kind="case", cases=cases, ymax=ymax, dz=dz, title=title, u=0, g0=0, g1=0, g2=0, azim=0, note=note)
    out = [seg(prefix + "_a", texts[0], one(dict(base, sub=subs[0])))]
    nB = N(b_secs)
    out.append(seg(prefix + "_b", texts[1], [(dict(base, sub=subs[1], u=3 * ease(q / nB), g0=clip01(3 * ease(q / nB) - 2)), 1) for q in range(1, nB + 1)]))
    full = dict(base, u=3, g0=1); n1 = N(2.0)
    out.append(seg(prefix + "_c1", texts[2], [(dict(full, sub=subs[2], g1=ease(q / n1)), 1) for q in range(1, n1 + 1)]))
    n2 = N(2.0); tot = N(5.0)
    out.append(seg(prefix + "_c2", texts[3], [(dict(full, g1=1, sub=subs[3], g2=ease(q / n2), azim=25 * ease(q / tot)), 1) for q in range(1, tot + 1)]))
    return out


def sweep_segment(id_, text, case, lever, lo, hi, title, sub, marks, postures, anim_s=4.0):
    base = dict(kind="sweep", case=case, lever=lever, lo=lo, hi=hi, title=title, sub=sub, marks=marks, postures=postures)
    n = N(anim_s)
    return seg(id_, text, [(dict(base, t=ease(q / n)), 1) for q in range(1, n + 1)])


def tornado_segment(id_, text, items, title, sub, foot, anim_s=1.6):
    base = dict(kind="tornado", items=items, title=title, sub=sub, foot=foot); n = N(anim_s)
    return seg(id_, text, [(dict(base, g=ease(q / n)), 1) for q in range(1, n + 1)])


def threshold_segment(id_, text, case, title, sub, foot, floors=None, rho_top=False, anim_s=2.0):
    base = dict(kind="threshold", case=case, title=title, sub=sub, foot=foot, floors=floors or {}, rho_top=rho_top); n = N(anim_s)
    return seg(id_, text, [(dict(base, g=0.0), 1)] + [(dict(base, g=ease(q / n)), 1) for q in range(1, n + 1)])


# ======================================================================= runner
def _ffmpeg():
    return VB._ffmpeg()


def srt_t(t, sep=","):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d}{sep}{ms:03d}"


def split_caption(text, maxlen=100):
    """Caption cues of at most two short lines: split at sentence ends, then at commas/colons for long sentences."""
    out = []
    text = re.sub(r"\b(Dr|Prof|al|vs|No)\.\s", lambda m: m.group(1) + ".\u00a7", text)   # abbreviations are not sentence ends
    for x in [y.replace("\u00a7", " ") for y in re.split(r"(?<=[.!?])\s+", text)]:
        while len(x) > maxlen:
            cands = [m.end() for m in re.finditer(r"[,;:] ", x[:maxlen + 12]) if 25 <= m.end() <= maxlen + 10]
            cut = max(cands) if cands else x.rfind(" ", 0, maxlen)
            out.append(x[:cut].strip()); x = x[cut:].strip()
        out.append(x)
    return [o for o in out if o]


def run(segments, out_mp4, backend="flite", voice_dir=None, preview=None, lead=0.35, tail=0.7, audio_dir=None, video_key=None):
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)

    def render(state):
        RENDER[state["kind"]](fig, state); fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba()); assert buf.shape[:2] == (H, W)
        return buf.tobytes()

    if preview:
        from PIL import Image
        os.makedirs(preview, exist_ok=True)
        for sg in segments:
            Image.frombytes("RGBA", (W, H), render(sg["states"][-1][0])).convert("RGB").save(os.path.join(preview, sg["id"] + ".png"))
        print("previews in", preview); return

    voice_dir = voice_dir or os.path.join(os.path.dirname(os.path.abspath(out_mp4)), "_voice"); os.makedirs(voice_dir, exist_ok=True)
    import hashlib
    for sg in segments:                                              # 1. voice for each segment
        if audio_dir:                                                # your own recording / audio from any tool
            src = VB.find_audio(audio_dir, sg["id"], video_key)
            if not src:
                raise FileNotFoundError(f"no audio file for segment '{sg['id']}' in {audio_dir} (expected {sg['id']}.mp3 or .wav)")
            key = hashlib.md5(f"{src}{os.path.getsize(src)}{os.path.getmtime(src)}".encode()).hexdigest()[:12]
            wav = os.path.join(voice_dir, f"{sg['id']}_f{key}.wav"); sg["wav"] = wav
            if not os.path.exists(wav):
                VB.import_audio(src, wav)
        else:
            key = hashlib.md5((backend + sg["text"] + str(sg.get("direction"))).encode()).hexdigest()[:12]
            wav = os.path.join(voice_dir, f"{sg['id']}_{key}.wav"); sg["wav"] = wav
            if not os.path.exists(wav):
                VB.synth(sg["text"], wav, backend=backend, direction=sg.get("direction"))
        sg["audio"] = VB.wav_seconds(wav)
        sg["dur"] = max(sg["min"], sg["audio"] + lead + tail, len(sg["states"]) / FPS)
        n = N(sg["dur"]); assert len(sg["states"]) <= n, (sg["id"], len(sg["states"]), n)
        sg["states"] = sg["states"][:-1] + [(sg["states"][-1][0], sg["states"][-1][1] + n - len(sg["states"]))]
    total = sum(N(sg["dur"]) for sg in segments) / FPS

    tmp_v = out_mp4 + ".video.mp4"                                    # 2. video frames
    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", tmp_v]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE); done = 0; tf = sum(N(sg["dur"]) for sg in segments)
    for sg in segments:
        for state, count in sg["states"]:
            b = render(state)
            for _ in range(count):
                proc.stdin.write(b)
        done += N(sg["dur"]); print(f"{sg['id']:<12} {done}/{tf}", flush=True)
    proc.stdin.close(); proc.wait()

    sr = 44100; mix = np.zeros(int(round(total * sr)), dtype=np.float32); t0 = 0.0; cues = []; idx = 1   # 3. audio track + captions
    for sg in segments:
        with wave.open(sg["wav"]) as w:
            assert w.getframerate() == sr
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        o = int((t0 + lead) * sr); mix[o:o + len(a)] += a
        sents = split_caption(sg["text"]); tot_c = sum(len(x) for x in sents); cur = t0 + lead
        for x in sents:
            d = sg["audio"] * len(x) / tot_c
            cues.append((idx, cur, cur + d, "\n".join(textwrap.wrap(x, 56)))); idx += 1; cur += d
        t0 += N(sg["dur"]) / FPS
    wav_out = out_mp4 + ".audio.wav"
    with wave.open(wav_out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    base = os.path.splitext(out_mp4)[0]
    open(base + ".srt", "w", encoding="utf-8").write("\n".join(f"{i}\n{srt_t(a)} --> {srt_t(b)}\n{t}\n" for i, a, b, t in cues))
    open(base + ".vtt", "w", encoding="utf-8").write("WEBVTT\n\n" + "\n".join(f"{srt_t(a, '.')} --> {srt_t(b, '.')}\n{t}\n" for i, a, b, t in cues))
    starts, acc = [], 0.0
    for sg in segments:
        starts.append(round(acc, 2)); acc += N(sg["dur"]) / FPS
    json.dump(dict(total_seconds=round(total, 1), voice=("own audio files" if audio_dir else backend),
                   segments=[dict(id=s["id"], start=st, seconds=round(s["dur"], 1), direction=s.get("direction"), text=s["text"]) for s, st in zip(segments, starts)]),
              open(base + "_timings.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", tmp_v, "-i", wav_out, "-i", base + ".srt", "-map", "0:v", "-map", "1:a", "-map", "2:s",   # 4. mux
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text", "-disposition:s:0", "0",
                    "-metadata:s:a:0", "language=eng", "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "title=English captions (toggle on/off)",
                    "-metadata", f"title={os.path.basename(base)} · RMTI (research prototype, no patient data)", "-metadata", "artist=Dr. Cesar Marolla",
                    "-movflags", "+faststart", out_mp4], check=True)
    for f in (tmp_v, wav_out):
        os.remove(f)
    print(f"wrote {out_mp4}  ({total:.0f}s, voice={'own files' if audio_dir else backend}) + .srt + .vtt + _timings.json")


def burn_captions(src_mp4, srt_path, out_mp4):
    """Always-visible captions in a dark band under the picture (never covers the graphics). Re-encodes video, copies audio."""
    d, n = os.path.dirname(os.path.abspath(srt_path)), os.path.basename(srt_path)
    style = "FontName=DejaVu Sans,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=0,Shadow=0,Alignment=2,MarginV=5"
    vf = f"scale=1138:640,pad=1280:720:71:0:color=0x0b3b40,subtitles={n}:force_style='{style}'"
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", os.path.abspath(src_mp4), "-vf", vf, "-map", "0:v", "-map", "0:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "22", "-preset", "veryfast", "-c:a", "copy", "-movflags", "+faststart", os.path.abspath(out_mp4)], cwd=d, check=True)
    print("wrote", out_mp4)


def chapters_text(timings_json, chapter_map):
    """YouTube chapters from a *_timings.json and [(segment id, title), ...]. First chapter is forced to 0:00."""
    d = json.load(open(timings_json, encoding="utf-8")); st = {x["id"]: x["start"] for x in d["segments"]}
    lines = []
    for i, (sid, title) in enumerate(chapter_map):
        if sid in st:
            t = 0 if i == 0 else int(st[sid]); lines.append(f"{t // 60}:{t % 60:02d} {title}")
    return "\n".join(lines)
