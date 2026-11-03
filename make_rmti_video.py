"""
tools/make_rmti_video.py  --  RMTI demo video (MP4, 1280x720, YouTube-ready) + SRT captions + timing JSON

Scenes: title -> limits -> how R = L*E*V*(1-rho) works -> fixed tiers
        -> ONCOLOGY case study (Faria et al. cohort: V from published ALBI-grade COUNTS; L, E, rho illustrative)
        -> DISASTER case studies (Pacific Palisades, Altadena, Lilongwe: published rubric values, calculator v2.3.0)
        -> close with name, title and disclaimers.

Reads NO patient data and no files except rmti_cases.py (aggregate counts and published rubric values).

    pip install matplotlib numpy pillow imageio-ffmpeg     # or have ffmpeg on PATH
    python tools/make_rmti_video.py --out rmti_demo.mp4            # also writes rmti_demo.srt and rmti_demo_timings.json
    python tools/make_rmti_video.py --preview preview_frames       # PNG of each scene's last frame, no encoding

Research prototype. Not validated, not a medical device.
"""
import argparse, json, os, re, shutil, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import rmti_cases as K                      # noqa: E402
from video_narration import NARRATION       # noqa: E402

NAME, TITLE, ORCID = "Prof. Dr. Cesar Marolla", "Developer of the Risk Mechanism Theory Index (RMTI)", "ORCID 0000-0001-8498-7380"
DEMO_URL = "oncoclastics.streamlit.app"
FPS = 20
W, H = 1280, 720
CMAP = LinearSegmentedColormap.from_list("rho", ["#b3261e", "#e8a317", "#1b7f5c"])   # vulnerable -> resilient
TIER_COL = ["#7F8FA6", "#4A6FA5", "#C9A227", "#C2662D", "#9B2C2C"]                    # same palette as the app
TIER_EDGES = [(0, .05), (.05, .15), (.15, .35), (.35, .60), (.60, 5)]
TIER_NAMES = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
BAR_COL = ["#b3261e", "#e8a317", "#1b7f5c"]                                           # R0 / R now / R after
INK, TEAL, DARK = "#0b3b40", "#37474f", "#0b3b40"
FOOT = ("Research prototype · not validated · not a medical device · not for patient-care or emergency decisions · "
        "R is a relative index, not a probability")

CONCEPT = dict(L=0.30, E=0.65, V=0.55, rho_now=0.20, rho_after=0.50)
CASESETS = {
    "onc": dict(cases=K.ONCOLOGY_CASES, ymax=0.20, dz=[0.05, -0.09],
                title="Oncology · Faria et al. cohort: HCC (n=29) vs cirrhosis (n=25)"),
    "dis": dict(cases=K.DISASTER_CASES, ymax=0.62, dz=[0.05, -0.09, 0.05],
                title="Disaster science · Pacific Palisades · Altadena · Lilongwe"),
}


# ================================================================== drawing helpers
def new_axes(fig, dark=False):
    fig.clf()
    fig.patch.set_facecolor(DARK if dark else "white")
    a = fig.add_axes([0, 0, 1, 1]); a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
    return a


def chrome(a, dark=False):
    sub = "#9fb8bb" if dark else "#78909c"
    a.text(0.985, 0.968, "DEMO MODE · NO PATIENT DATA", ha="right", va="top", fontsize=9.5, weight="bold", color="#7c2d12",
           bbox=dict(boxstyle="round,pad=0.4", fc="#fff7ed", ec="#b45309"))
    a.text(0.5, 0.043, FOOT, ha="center", fontsize=8.5, color=sub)
    a.text(0.5, 0.018, f"{NAME} · RMTI · Apache-2.0 · independent academic work", ha="center", fontsize=8.5, color=sub)


def wrap(a, text, x, y, width, size, color=INK, weight="normal", dy=0.055, mono=False):
    for line in textwrap.wrap(text, width) or [""]:
        a.text(x, y, line, fontsize=size, color=color, weight=weight, va="top", family="monospace" if mono else None)
        y -= dy
    return y


def cube(ax):
    for p in (0, 1):
        for q in (0, 1):
            ax.plot([0, 1], [p, p], [q, q], color="#cfd8dc", lw=0.8)
            ax.plot([p, p], [0, 1], [q, q], color="#cfd8dc", lw=0.8)
            ax.plot([p, p], [q, q], [0, 1], color="#cfd8dc", lw=0.8)


def cube_axes(fig, rect, azim):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_zlim(0, 1); ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("L likelihood", labelpad=8); ax.set_ylabel("E exposure", labelpad=8); ax.set_zlabel("V vulnerability", labelpad=4)
    for t in (ax.xaxis, ax.yaxis, ax.zaxis):
        t.set_ticks([0, 0.5, 1])
    ax.view_init(elev=22, azim=-58 + azim)
    cube(ax)
    return ax


def rho_key(fig):
    cax = fig.add_axes([0.535, 0.25, 0.010, 0.34])
    cax.imshow(np.linspace(1, 0, 100)[:, None], cmap=CMAP, aspect="auto", extent=[0, 1, 0, 1])
    cax.set_xticks([]); cax.yaxis.tick_right(); cax.set_yticks([0, 1]); cax.set_yticklabels(["ρ = 0", "ρ = 1"], fontsize=8)
    cax.set_title("resilience", fontsize=8)


def path_pos(u, L, E, V):
    w = [(0, 0, 0), (L, 0, 0), (L, E, 0), (L, E, V)]
    i = int(min(np.floor(u), 2)); f = u - i
    p = [w[i][j] + (w[i + 1][j] - w[i][j]) * f for j in range(3)]
    return p, w[: i + 1] + [tuple(p)]


def clip01(x):
    return float(np.clip(x, 0, 1))


# ================================================================== scene renderers (state dict -> RGBA bytes)
def r_title(fig, s):
    a = new_axes(fig, dark=True); chrome(a, dark=True)
    a.text(0.07, 0.72, "Risk Mechanism Theory Index", fontsize=38, weight="bold", color="white")
    a.text(0.07, 0.62, "R = L · E · V · (1 − ρ)", fontsize=30, color="#9bd1d6")
    a.text(0.07, 0.51, "One equation, two domains: oncology and disaster science", fontsize=19, color="#d0e3e5")
    a.add_patch(plt.Rectangle((0.07, 0.17), 0.006, 0.17, color="#e8a317"))
    a.text(0.09, 0.31, NAME, fontsize=26, weight="bold", color="white", va="top")
    a.text(0.09, 0.245, TITLE, fontsize=15, color="#d0e3e5", va="top")
    a.text(0.09, 0.195, ORCID, fontsize=12, color="#9fb8bb", va="top")


def r_bullets(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.90, s["title"], fontsize=27, weight="bold", color=INK, va="top")
    y = 0.78
    for kind, text in s["items"]:
        if kind == "h":
            a.text(0.05, y, text, fontsize=17, weight="bold", color="#b45309", va="top"); y -= 0.065
        else:
            a.text(0.06, y, "•", fontsize=17, color=TEAL, va="top")
            y = wrap(a, text, 0.085, y, s.get("width", 82), 16, TEAL, dy=0.052) - 0.02


def r_section(fig, s):
    a = new_axes(fig); chrome(a)
    a.add_patch(plt.Rectangle((0.05, 0.40), 0.006, 0.30, color="#e8a317"))
    a.text(0.07, 0.69, s["kicker"], fontsize=17, color="#b45309", weight="bold", va="top")
    y = wrap(a, s["title"], 0.07, 0.63, 44, 31, INK, "bold", dy=0.085)
    for t in s["lines"]:
        y = wrap(a, t, 0.07, y - 0.01, 90, 15, TEAL, dy=0.05)


def r_tiers(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.90, "Five fixed tiers of residual risk R", fontsize=27, weight="bold", color=INK, va="top")
    labels = ["R < 0.05", "0.05 – 0.15", "0.15 – 0.35", "0.35 – 0.60", "R ≥ 0.60"]
    for i in range(5):
        x = 0.05 + i * 0.185
        a.add_patch(plt.Rectangle((x, 0.42), 0.17, 0.26, color=TIER_COL[i]))
        a.text(x + 0.085, 0.60, TIER_NAMES[i].split()[0], fontsize=30, color="white", weight="bold", ha="center", va="center")
        a.text(x + 0.085, 0.52, TIER_NAMES[i].split()[1], fontsize=15, color="white", ha="center", va="center")
        a.text(x + 0.085, 0.45, labels[i], fontsize=12, color="white", ha="center", va="center")
    a.text(0.05, 0.33, "The same thresholds apply to every patient, city and year.", fontsize=17, color=TEAL)
    a.text(0.05, 0.26, "A tier is a reading of a research framework for discussion, not a clinical or engineering decision.",
           fontsize=13, color="#78909c")


def r_concept(fig, s):
    a = new_axes(fig); chrome(a)
    L, E, V = CONCEPT["L"], CONCEPT["E"], CONCEPT["V"]
    fin = (L, L * E, L * E * V, L * E * V, L * E * V * (1 - CONCEPT["rho_now"]), L * E * V * (1 - CONCEPT["rho_after"]))
    labels = ["L", "L·E", "L·E·V", "R₀\n(ρ = 0)", "R\n(ρ now)", "R\n(ρ after)"]
    cols = ["#607d8b"] * 3 + BAR_COL
    t1, _, t2 = s["title"].partition("\n")
    a.text(0.04, 0.955, t1, fontsize=20, weight="bold", color=INK, va="top")
    a.text(0.04, 0.885, t2, fontsize=14, color=TEAL, va="top")
    ax = cube_axes(fig, [0.02, 0.08, 0.55, 0.74], 0)
    p, pts = path_pos(s["u"], L, E, V)
    xs, ys, zs = zip(*pts)
    ax.plot(xs, ys, zs, color="#607d8b", lw=3.5)
    ax.scatter([p[0]], [p[1]], [p[2]], s=220, c=[s["rho"]], cmap=CMAP, vmin=0, vmax=1, edgecolors="#263238", linewidths=1.6, depthshade=False)
    rho_key(fig)
    bx = fig.add_axes([0.66, 0.16, 0.32, 0.60])
    vals = [fin[k] * clip01(s["rev"] - k) for k in range(6)]
    bx.bar(range(6), vals, color=cols)
    for k, v in enumerate(vals):
        if v > 1e-9:
            bx.text(k, v + 0.015, f"{v:.3f}", ha="center", fontsize=10)
    bx.set_ylim(0, 1); bx.set_xticks(range(6)); bx.set_xticklabels(labels, fontsize=8.5)
    bx.set_title("Running product", fontsize=12); bx.spines[["top", "right"]].set_visible(False)


def r_albi(fig, s):
    a = new_axes(fig); chrome(a)
    a.text(0.05, 0.93, "From ALBI grades to vulnerability V", fontsize=26, weight="bold", color=INK, va="top")
    a.text(0.05, 0.855, f"Faria et al. cohort · Harvard Dataverse · doi:{K.FARIA_DOI} · aggregate grade counts only, no patient-level records",
           fontsize=11.5, color="#546e7a", va="top")
    gcol = ["#9ccfd3", "#4A9aa3", "#0b5c63"]
    anchors = K.ALBI_ANCHORS
    rows = [("HCC cohort", K.FARIA_COUNTS["HCC cohort"]), ("Cirrhosis cohort", K.FARIA_COUNTS["Cirrhosis cohort"])]
    bx = fig.add_axes([0.20, 0.50, 0.72, 0.26])
    for r, (name, cnt) in enumerate(rows):
        n = sum(cnt); left = 0
        for g in range(3):
            if cnt[g]:
                bx.barh(1 - r, cnt[g] / n, left=left, color=gcol[g], height=0.55, edgecolor="white")
                bx.text(left + cnt[g] / n / 2, 1 - r, f"{cnt[g]}", ha="center", va="center", color="white", fontsize=14, weight="bold")
            left += cnt[g] / n
    bx.set_yticks([1, 0]); bx.set_yticklabels([f"{n}\n(n={sum(c)})" for n, c in rows], fontsize=12)
    bx.set_xlim(0, 1); bx.set_xticks([]); bx.spines[["top", "right", "bottom"]].set_visible(False)
    for g in range(3):
        a.add_patch(plt.Rectangle((0.20 + g * 0.24, 0.42), 0.018, 0.03, color=gcol[g]))
        a.text(0.225 + g * 0.24, 0.435, f"ALBI grade {g + 1}  ·  V anchor {anchors[g + 1]:.2f}", fontsize=12, color=TEAL, va="center")
    if s["formula"]:
        y = 0.33
        for name, cnt in rows:
            n = sum(cnt)
            v = K.v_from_counts(*cnt)
            expr = " + ".join(f"{cnt[g]}×{anchors[g + 1]:.2f}" for g in range(3))
            a.text(0.05, y, f"{name}:  V = ({expr}) ÷ {n}  =", fontsize=14, color=TEAL, va="center", family="monospace")
            a.text(0.80, y, f"{v:.3f}", fontsize=28, weight="bold", color="#0b5c63", va="center")
            y -= 0.10
        a.text(0.05, 0.11, "ALBI: Johnson et al., J Clin Oncol 2015;33:550–558. Small cohorts, shown to demonstrate the arithmetic only.",
               fontsize=11, color="#78909c")


def r_case(fig, s):
    cs = CASESETS[s["set"]]
    cases = cs["cases"]; ev = [K.evaluate(c) for c in cases]
    a = new_axes(fig); chrome(a)
    a.text(0.04, 0.955, cs["title"], fontsize=19, weight="bold", color=INK, va="top")
    a.text(0.04, 0.895, s["sub"], fontsize=13.5, color=TEAL, va="top")
    ax = cube_axes(fig, [0.01, 0.10, 0.52, 0.72], s["azim"])
    marks = ["o", "s", "^"]
    rho_c = [c["rho_now"] * s["g1"] + (c["rho_after"] - c["rho_now"]) * s["g2"] for c in cases]
    if s["u"] > 0:
        for i, c in enumerate(cases):
            p, pts = path_pos(s["u"], c["L"], c["E"], c["V"])
            xs, ys, zs = zip(*pts)
            ax.plot(xs, ys, zs, color="#90a4ae", lw=2.5)
            ax.scatter([p[0]], [p[1]], [p[2]], s=190, c=[rho_c[i]], cmap=CMAP, vmin=0, vmax=1, marker=marks[i],
                       edgecolors="#263238", linewidths=1.6, depthshade=False)
            ax.text(p[0], p[1], p[2] + cs["dz"][i], c["label"], fontsize=10, weight="bold", ha="center", color=INK)
    rho_key(fig)
    # bars with tier shading
    bx = fig.add_axes([0.625, 0.36, 0.29, 0.43])
    ymax = cs["ymax"]
    for (lo, hi), col, nm in zip(TIER_EDGES, TIER_COL, TIER_NAMES):
        if lo < ymax:
            bx.axhspan(lo, min(hi, ymax), color=col, alpha=0.13, lw=0)
            bx.text(1.02, (lo + min(hi, ymax)) / 2, "T" + nm, transform=bx.get_yaxis_transform(), fontsize=7.5, va="center", color=col)
    n = len(cases)
    for i, e in enumerate(ev):
        hs = [e["R0"] * s["g0"], e["R_now"] * s["g1"], e["R_after"] * s["g2"]]
        gs = [s["g0"], s["g1"], s["g2"]]
        for j in range(3):
            bx.bar(i + (j - 1) * 0.27, hs[j], width=0.25, color=BAR_COL[j], label=["R₀ (ρ = 0)", "R now", "R after"][j] if i == 0 else None)
            if gs[j] > 0.05:
                bx.text(i + (j - 1) * 0.27, hs[j] + ymax * 0.012, f"{hs[j]:.3f}", ha="center", fontsize=7, rotation=90, va="bottom")
    tl = []
    for i, e in enumerate(ev):
        t = cases[i]["label"]
        if s["g1"] >= 0.999:
            t += "\nT" + e["tier_now"][0] + (" → T" + e["tier_after"][0] if s["g2"] >= 0.999 else "")
        tl.append(t)
    bx.set_xticks(range(n)); bx.set_xticklabels(tl, fontsize=8.5)
    bx.set_xlim(-0.6, n - 0.4); bx.set_ylim(0, ymax); bx.tick_params(axis="y", labelsize=8)
    bx.set_title("Risk R by stage", fontsize=11); bx.spines[["top", "right"]].set_visible(False)
    bx.legend(loc="upper left", fontsize=7.5, frameon=False)
    # inputs table
    lines = [f"{'case':<10}{'L':>7}{'E':>7}{'V':>7}   ρ now→after"]
    for c in cases:
        lines.append(f"{c['label']:<10}{c['L']:>7.3f}{c['E']:>7.3f}{c['V']:>7.3f}   {c['rho_now']:.2f}→{c['rho_after']:.2f}")
    a.text(0.595, 0.285, "\n".join(lines), fontsize=9, family="monospace", color=TEAL, va="top", linespacing=1.5)
    a.text(0.595, 0.285 - 0.025 * (len(lines) + 1.3), s["note"], fontsize=8.5, color="#78909c", va="top", wrap=True)


def r_close(fig, s):
    a = new_axes(fig, dark=True); chrome(a, dark=True)
    a.text(0.07, 0.80, "RMTI · one equation, two domains", fontsize=34, weight="bold", color="white", va="top")
    a.text(0.07, 0.70, "R = L · E · V · (1 − ρ)", fontsize=26, color="#9bd1d6", va="top")
    a.add_patch(plt.Rectangle((0.07, 0.43), 0.006, 0.17, color="#e8a317"))
    a.text(0.09, 0.59, NAME, fontsize=26, weight="bold", color="white", va="top")
    a.text(0.09, 0.525, TITLE, fontsize=15, color="#d0e3e5", va="top")
    a.text(0.09, 0.475, ORCID, fontsize=12, color="#9fb8bb", va="top")
    y = 0.36
    for t in [f"Public demo (synthetic and published aggregate data only): {DEMO_URL}",
              "Open code under Apache-2.0 · Research prototype, not validated, not a medical device",
              "Independent academic work. Not an official product of the World Bank Group, Harvard University or any other institution.",
              "No patient data is used or shown. Nothing here is medical or engineering advice."]:
        y = wrap(a, t, 0.07, y, 105, 12.5, "#d0e3e5", dy=0.045)


RENDER = dict(title=r_title, bullets=r_bullets, section=r_section, tiers=r_tiers, concept=r_concept, albi=r_albi,
              case=r_case, close=r_close)


# ================================================================== timeline
def N(sec):
    return int(round(sec * FPS))


def pad(states, n_total):
    cnt = sum(c for _, c in states)
    assert cnt <= n_total, f"segment overruns: {cnt} > {n_total}"
    return states[:-1] + [(states[-1][0], states[-1][1] + n_total - cnt)]


def ease(t):
    t = clip01(t)
    return t * t * (3 - 2 * t)


def build_segments():
    seg = []

    def add(id_, dur, states):
        seg.append(dict(id=id_, dur=dur, states=pad(states, N(dur))))

    add("title", 6.5, [(dict(kind="title"), 1)])
    add("limits", 14, [(dict(kind="bullets", title="Before we start: the limits", width=78, items=[
        ("p", "Research prototype: not validated against real outcomes."),
        ("p", "Not a medical device. Not for patient-care or emergency decisions."),
        ("p", "R is a relative, rubric-based index, not a probability, forecast or loss estimate."),
        ("p", "Parameters are uncalibrated placeholders."),
        ("p", "This video uses illustrative or published aggregate values only. No patient data."),
    ]), 1)])

    # --- concept walk
    L, E, V = CONCEPT["L"], CONCEPT["E"], CONCEPT["V"]
    r0 = L * E * V
    rn, ra = r0 * (1 - CONCEPT["rho_now"]), r0 * (1 - CONCEPT["rho_after"])
    kf = [(0, 0.0, 0, "R = L · E · V · (1 − ρ)\nEvery factor is bounded between 0 and 1", 4.0),
          (1, 0.0, 1, f"Step 1 · L, likelihood = {L:.2f}\nHow probable the hazard is", 3.5),
          (2, 0.0, 2, f"Step 2 · × E, exposure = {E:.2f}\nShare reached or affected.  L·E = {L*E:.3f}", 4.0),
          (3, 0.0, 3, f"Step 3 · × V, vulnerability = {V:.2f}\nHow badly those reached are hurt.  L·E·V = {r0:.3f}", 4.0),
          (3, 0.0, 4, f"Step 4 · Raw risk R₀ = {r0:.3f}\nBefore any resilience is counted", 3.8),
          (3, CONCEPT["rho_now"], 5, f"Step 5 · × (1 − ρ), ρ = {CONCEPT['rho_now']:.2f}\nResilience absorbs {100*CONCEPT['rho_now']:.0f}%.  R = {rn:.3f}", 4.0),
          (3, CONCEPT["rho_after"], 6, f"Step 6 · Improved state, ρ = {CONCEPT['rho_after']:.2f}\nR = {ra:.3f}  ({ra-rn:+.3f})", 5.5)]
    move = 0.8
    for k, (u, rho, rev, title, hold) in enumerate(kf):
        st = []
        if k > 0:
            u0, rho0, rev0, _, _ = kf[k - 1]
            for q in range(1, N(move) + 1):
                t = ease(q / (N(move) + 1))
                st.append((dict(kind="concept", u=u0 + (u - u0) * t, rho=rho0 + (rho - rho0) * t, rev=rev0 + (rev - rev0) * t, title=title), 1))
        st.append((dict(kind="concept", u=u, rho=rho, rev=rev, title=title), 1))
        add(f"c{k}", hold + (move if k else 0), st)

    add("tiers", 7, [(dict(kind="tiers"), 1)])

    # --- oncology
    add("onc_intro", 7.5, [(dict(kind="section", kicker="ONCOLOGY  ·  HEPATOCELLULAR CARCINOMA (HCC) SURVEILLANCE",
                                 title="Case study: Faria et al. cohort",
                                 lines=[f"Published and public: Harvard Dataverse, doi:{K.FARIA_DOI}",
                                        "Only aggregate ALBI-grade counts are used (n = 29 HCC, n = 25 cirrhosis). No patient-level records.",
                                        "Question: how does vulnerability V, taken from real labs, move the RMTI score?"]), 1)])
    add("albi_a", 7, [(dict(kind="albi", formula=False), 1)])
    add("albi_b", 8, [(dict(kind="albi", formula=True), 1)])

    def case_segments(prefix, setname, a_dur, b_dur, c1_dur, c2_dur, sub_a, note, sub_c1, sub_c2):
        cs = CASESETS[setname]
        base = dict(kind="case", set=setname, u=0, g0=0, g1=0, g2=0, azim=0, note=note)
        add(prefix + "_a", a_dur, [(dict(base, sub=sub_a), 1)])
        stB = []
        nB = N(min(b_dur - 0.8, 3.2))
        for q in range(1, nB + 1):
            u = 3 * ease(q / nB)
            stB.append((dict(base, sub="Each case travels the cube: L → E → V", u=u, g0=clip01(u - 2)), 1))
        add(prefix + "_b", b_dur, stB)
        full = dict(base, u=3, g0=1)
        stC1 = []
        nC1 = N(2.0)
        for q in range(1, nC1 + 1):
            stC1.append((dict(full, sub=sub_c1, g1=ease(q / nC1)), 1))
        add(prefix + "_c1", c1_dur, stC1)
        stC2 = []
        nC2 = N(2.0)
        total2 = N(c2_dur)
        for q in range(1, total2 + 1):
            stC2.append((dict(full, g1=1, sub=sub_c2, g2=ease(q / nC2), azim=25 * ease(q / total2)), 1))
        add(prefix + "_c2", c2_dur, stC2)

    ev = [K.evaluate(c) for c in K.ONCOLOGY_CASES]
    case_segments("onc", "onc", 9.0, 4.5, 4.5, 6.0,
                  "Inputs: only V comes from published data",
                  "Only V is anchored to the Faria et al. counts; L, E and ρ are illustrative working values (same for both groups).",
                  f"ρ now = 0.20  →  R = {ev[0]['R_now']:.3f} (HCC) and {ev[1]['R_now']:.3f} (cirrhosis): tier 2 Moderate",
                  f"ρ after = 0.65 (scenario)  →  R = {ev[0]['R_after']:.3f} and {ev[1]['R_after']:.3f}: tier 1 Low")
    add("onc_take", 13, [(dict(kind="bullets", title="Reading the oncology example", width=84, items=[
        ("h", "What it shows"),
        ("p", f"The arithmetic: V from published counts moves R only slightly ({ev[0]['R_now']:.3f} vs {ev[1]['R_now']:.3f})."),
        ("p", "Under the scenario, both groups move from tier 2 Moderate to tier 1 Low."),
        ("h", "What it does not show"),
        ("p", "Faria's data supply V only. L, E and ρ are illustrative, so nothing is validated."),
        ("p", "No incident-HCC outcomes are used. This is not a risk prediction for any patient."),
    ]), 1)])

    # --- disaster science
    add("dis_intro", 8.5, [(dict(kind="section", kicker="DISASTER SCIENCE  ·  URBAN CLIMATE AND HAZARD RISK",
                                 title="Case studies: two wildfires and one flood city",
                                 lines=["Pacific Palisades and Altadena, California (Palisades and Eaton fires, January 2025)",
                                        "Lilongwe, Malawi (pluvial and river flooding), a sub-Saharan Africa worked example",
                                        "Published rubric inputs from the RMTI disaster calculator v2.3.0. No personal data."]), 1)])
    dv = [K.evaluate(c) for c in K.DISASTER_CASES]
    case_segments("dis", "dis", 7.0, 6.0, 5.0, 6.5,
                  "Inputs: published rubric values (calculator v2.3.0)",
                  "Rubric scores, not damage or casualty estimates. ρ-after values are scenario targets, not observations.",
                  "ρ now  →  Lilongwe: Severe · Altadena: High · Palisades: Moderate",
                  "ρ after (scenario)  →  Lilongwe: High · Altadena: Moderate · Palisades: Moderate")
    add("dis_take", 12, [(dict(kind="bullets", title="Reading the disaster examples", width=84, items=[
        ("h", "What it shows"),
        ("p", f"Lilongwe {dv[2]['R_now']:.2f} → {dv[2]['R_after']:.2f} (Severe → High); Altadena {dv[1]['R_now']:.2f} → {dv[1]['R_after']:.2f} (High → Moderate); "
              f"Palisades {dv[0]['R_now']:.2f} → {dv[0]['R_after']:.2f} (stays Moderate)."),
        ("h", "What it does not show"),
        ("p", "ρ after is a scenario target, not an observed result. R is a relative rubric index."),
        ("p", "Not a forecast, an engineering assessment, or a loss or casualty estimate."),
    ]), 1)])
    add("close", 13, [(dict(kind="close"), 1)])
    return seg


# ================================================================== captions + timings
def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"


def write_meta(seg, base):
    t = 0.0; rows = []; cues = []; idx = 1
    for s in seg:
        text = NARRATION[s["id"]]
        words = len(text.split())
        rows.append(dict(id=s["id"], start=round(t, 2), end=round(t + s["dur"], 2), seconds=s["dur"], words=words,
                         words_per_sec=round(words / s["dur"], 2), narration=text))
        sents = re.split(r"(?<=[.!?:])\s+", text)
        a0, a1 = t + 0.3, t + s["dur"] - 0.2
        tot = sum(len(x) for x in sents); cur = a0
        for x in sents:
            d = (a1 - a0) * len(x) / tot
            cues.append(f"{idx}\n{srt_time(cur)} --> {srt_time(cur + d)}\n{x}\n"); idx += 1; cur += d
        t += s["dur"]
    json.dump(dict(total_seconds=round(t, 2), fps=FPS, segments=rows), open(base + "_timings.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(base + ".srt", "w", encoding="utf-8").write("\n".join(cues))
    fast = [r for r in rows if r["words_per_sec"] > 2.9]
    print(f"total {t:.1f}s ({int(t // 60)}:{int(t % 60):02d}); fastest narration {max(r['words_per_sec'] for r in rows)} words/s")
    if fast:
        print("WARNING narration too fast for:", [(r["id"], r["words_per_sec"]) for r in fast])
    return rows


# ================================================================== main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="rmti_demo.mp4")
    ap.add_argument("--preview", default=None, help="folder: save each scene's last frame as PNG, then exit")
    a = ap.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    seg = build_segments()
    base = os.path.splitext(a.out)[0]
    write_meta(seg, base)
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)

    def render(state):
        RENDER[state["kind"]](fig, state)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())
        assert buf.shape[:2] == (H, W), buf.shape
        return buf.tobytes()

    if a.preview:
        from PIL import Image
        os.makedirs(a.preview, exist_ok=True)
        for s in seg:
            Image.frombytes("RGBA", (W, H), render(s["states"][-1][0])).convert("RGB").save(os.path.join(a.preview, s["id"] + ".png"))
        print("previews in", a.preview)
        return

    ff = shutil.which("ffmpeg")
    if not ff:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart",
           "-metadata", "title=RMTI demo: oncology and disaster science (synthetic and published aggregate data)",
           "-metadata", "artist=Cesar Marolla", "-metadata", "comment=Research prototype. Not validated. Not a medical device. No patient data.",
           a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    done = 0; total = sum(sum(c for _, c in s["states"]) for s in seg)
    for s in seg:
        for state, count in s["states"]:
            b = render(state)
            for _ in range(count):
                proc.stdin.write(b)
            done += count
        print(f"{s['id']:<10} done ({done}/{total} frames)", flush=True)
    proc.stdin.close(); proc.wait()
    print("wrote", a.out, "+", base + ".srt", "+", base + "_timings.json")


if __name__ == "__main__":
    main()
