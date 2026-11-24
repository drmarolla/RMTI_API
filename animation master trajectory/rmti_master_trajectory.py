#!/usr/bin/env python3
# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""
rmti_master_trajectory.py -- RMTI HCC case-study video, 1920x1080, split screen.

    left  45% (864 px)   the five Google Flow 3D clips, looped / trimmed with FFmpeg
    right 55% (1056 px)  light-mode clinical cards rendered by Manim, numbers from rmti_core

Run from the repo root:
    python animations/rmti_master_trajectory.py                  # full render
    python animations/rmti_master_trajectory.py --plan-only      # probe audio + clips, print the timeline
    python animations/rmti_master_trajectory.py --skip-manim     # layout test: blank right panel

Nothing is hardcoded about duration. The narration length comes from ffprobe (mutagen as a fallback)
at run time; the five beats are BEAT_WEIGHTS of that length; each clip gets
`-stream_loop -1 -t <its beat>`. Clip files are found by glob, so the hash suffixes never matter.
Every number on screen comes from core.rmti_core / oncology.rmti_hcc / dynamic.rmti_trajectory; no
scoring math lives in this file. Research prototype: synthetic and published aggregate values only.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT_W, OUT_H, FPS = 1920, 1080, 30
LEFT_W = round(OUT_W * 0.45)              # 864
RIGHT_W = OUT_W - LEFT_W                  # 1056
FADE = 0.5                                # seconds, fade in/out on every left clip

AUDIO_EXACT = "rmti_liver cancer _brit voice 2.mp3"
AUDIO_GLOB = "rmti_liver*brit*voice*.mp3"
# pathological sequence: (file number, filename stem as committed). Matched by glob "<n>. <stem>*.mp4".
CLIPS = [(1, "Camera_pushing_toward_glowing_liver", "glowing liver"),
         (3, "Cells_proliferating", "fibrosis and proliferation"),
         (2, "Camera_pushing_into_liver_tumor", "early HCC core"),
         (5, "Tumor_invading_portal_vein", "portal vein invasion"),
         (4, "Tumor_cells_traveling", "intravasation and metastasis")]
# share of the narration given to each beat: equations, cube, sweeps, ALBI cohorts, trajectory.
BEAT_WEIGHTS = (0.17, 0.20, 0.22, 0.15, 0.26)

# ----------------------------------------------------------------------------------------------- engine
def find_engine_dir() -> Path:
    cands = [os.environ.get("RMTI_PYTHON_DIR"), REPO / "RMTI_v5_site" / "rmti_python", REPO / "rmti_python", REPO]
    for c in filter(None, cands):
        if (Path(c) / "core" / "rmti_core.py").exists():
            return Path(c)
    raise FileNotFoundError("core/rmti_core.py not found. Set RMTI_PYTHON_DIR to the folder that contains core/.")


def load_engine():
    d = find_engine_dir()
    lock = d / "core" / "CORE_SHA256.txt"
    if lock.exists():
        want = lock.read_text().split()[0].strip().lower()
        got = hashlib.sha256((d / "core" / "rmti_core.py").read_bytes()).hexdigest()
        if got != want:
            raise RuntimeError(f"rmti_core.py hash mismatch: file {got[:12]}..., CORE_SHA256.txt {want[:12]}...")
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
    from core import rmti_core as core
    from oncology import rmti_hcc as hcc
    from dynamic.rmti_trajectory import run_trajectory
    return core, hcc, run_trajectory


# ----------------------------------------------------------------------------------------------- numbers
def build_data() -> dict:
    """Everything shown on screen, computed by the engine. No scoring math here."""
    core, hcc, run_trajectory = load_engine()
    d = {"engine_version": core.__version__}
    base = dict(L=0.30, E=0.60, V=0.50, rho=0.20, C=2)           # Patient A of rmti_hcc.py, Part 3
    d["example"] = {**base, **core.score(base["L"], base["E"], base["V"], base["rho"], base["C"])}

    ranked = {r["name"]: r for r in hcc.rank_cohort_hcc(hcc._scoreable(hcc.PUBLISHED_COHORTS))}
    d["cohorts"] = []
    for name, c in hcc.PUBLISHED_COHORTS.items():
        r = ranked[name]
        d["cohorts"].append(dict(name=name, L=c["L"], E=c["E"], V=c["V"], rho_now=c["rho_now"], rho_after=c["rho_after"],
                                 R_now=r["R_now"], R_after=r["R_after"], pct=core.pct_reduction(c["rho_now"], c["rho_after"])))
    pcts = [core.pct_reduction(c["rho_now"], c["rho_after"]) for c in (*hcc.PUBLISHED_COHORTS.values(), *hcc.PEARL_COHORTS.values())]
    d["pct_min"], d["pct_max"] = min(pcts), max(pcts)
    u, o = core.RHO_ANCHORS_HCC["usual"], core.RHO_ANCHORS_HCC["optimised"]
    d["usual_to_opt"] = dict(rho_now=u, rho_after=o, pct=core.pct_reduction(u, o), iei=core.investment_efficiency(u, o))

    def R(**kw):
        k = {**base, **kw}
        s = core.score(k["L"], k["E"], k["V"], k["rho"], k["C"])
        return dict(R=s["R"], R_raw=s["R_raw"], tier=s["tier"])
    d["sweep_rho"] = [dict(label=k, x=v, **R(rho=v)) for k, v in sorted(core.RHO_ANCHORS_HCC.items(), key=lambda kv: kv[1])]
    d["sweep_L"] = [dict(label="", x=v, **R(L=v)) for v in (0.90, 0.55, 0.30, 0.25, 0.20)]    # mirrors content.HCC_L_ANCHORS
    d["sweep_V"] = [dict(label=f"ALBI {g}", x=v, **R(V=v)) for g, v in sorted(hcc.ALBI_V.items())]

    cohorts = {"HCC cohort": {1: 10, 2: 18, 3: 1}, "Cirrhosis cohort": {1: 12, 2: 13, 3: 0}}   # as rmti_hcc.py, Part 4
    d["albi"] = []
    for nm, g in cohorts.items():
        V = hcc.albi_cohort_v(g)
        d["albi"].append(dict(name=nm, grades=g, n=sum(g.values()), V=V, R=core.score(0.30, 0.60, V, 0.20, 2)["R"]))
    d["albi_anchors"] = dict(hcc.ALBI_V)

    scen = dict(A=dict(y=[4.0, 4.4, 5.1, 5.9, 6.8, 7.5, 8.0, 8.4, 8.6], rho=[.50, .50, .45, .40, .35, .30, .30, .25, .25]),
                B=dict(y=[4.0, 3.9, 3.6, 3.4, 3.3, 3.1, 3.0, 3.0, 2.9], rho=[.50, .50, .55, .58, .60, .62, .65, .65, .65]))
    d["alpha"], d["beta"] = 0.41, 0.09
    d["traj"] = {k: run_trajectory(v["y"], v["rho"], 0.25, 0.60, alpha=d["alpha"], beta=d["beta"]) for k, v in scen.items()}
    d["tier_cut"] = core.TIER[0][0]
    return d


# ----------------------------------------------------------------------------------------------- probing
def probe_duration(path) -> float:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        if str(path).lower().endswith(".mp3"):
            from mutagen.mp3 import MP3
            return float(MP3(str(path)).info.length)
        raise


def pick(raw: Path, exact: str | None, pattern: str, what: str) -> Path:
    if exact and (raw / exact).exists():
        return raw / exact
    hits = sorted(glob.glob(os.path.join(glob.escape(str(raw)), pattern)))
    if not hits:
        listing = "\n  ".join(sorted(p.name for p in raw.iterdir())) if raw.exists() else "(folder missing)"
        raise FileNotFoundError(f"No {what} matches '{pattern}' in {raw}. Files present:\n  {listing}")
    if len(hits) > 1:
        print(f"warning: {len(hits)} files match {pattern}; using {Path(hits[0]).name}", file=sys.stderr)
    return Path(hits[0])


def make_plan(raw: Path, weights) -> dict:
    audio = pick(raw, AUDIO_EXACT, AUDIO_GLOB, "narration")
    D = probe_duration(audio)
    w = [x / sum(weights) for x in weights]
    bounds = [0.0]
    for x in w:
        bounds.append(bounds[-1] + x * D)
    bounds[-1] = D
    clips = []
    for i, (n, stem, label) in enumerate(CLIPS):
        f = pick(raw, None, f"{n}. {stem}*.mp4", f"clip {n}")
        seg, cd = bounds[i + 1] - bounds[i], probe_duration(f)
        clips.append(dict(n=n, file=str(f), label=label, clip_seconds=cd, start=bounds[i], seconds=seg, loops=math.ceil(seg / cd)))
    return dict(audio=str(audio), duration=D, bounds=bounds, clips=clips)


# ----------------------------------------------------------------------------------------------- FFmpeg
def run(cmd):
    print("+", " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def left_filter(i: int, seg: float, fit: str) -> str:
    fade = f"fade=t=in:st=0:d={FADE},fade=t=out:st={max(seg - FADE, 0):.3f}:d={FADE}"
    cover = f"scale={LEFT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={LEFT_W}:{OUT_H}"
    if fit == "blur":     # whole frame visible, blurred fill above and below
        return (f"[{i}:v]fps={FPS},split[a{i}][b{i}];[a{i}]{cover},boxblur=30:5[bg{i}];[b{i}]scale={LEFT_W}:-2[fg{i}];"
                f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,{fade}[v{i}]")
    return f"[{i}:v]fps={FPS},{cover},setsar=1,{fade}[v{i}]"


def build_left(plan, out: Path, fit: str):
    cmd, parts = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"], []
    for i, c in enumerate(plan["clips"]):
        cmd += ["-stream_loop", "-1", "-t", f"{c['seconds']:.3f}", "-i", c["file"]]
        parts.append(left_filter(i, c["seconds"], fit))
    chain = "".join(f"[v{i}]" for i in range(len(plan["clips"])))
    graph = ";".join(parts) + f";{chain}concat=n={len(plan['clips'])}:v=1:a=0[v]"
    run(cmd + ["-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "14", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", out])


def build_right(plan_path: Path, plan, out: Path, build: Path, skip: bool):
    if skip:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
             f"color=c=0xF8FAFC:s={RIGHT_W}x{OUT_H}:r={FPS}:d={plan['duration']:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
        return
    media = build / "media"
    env = {**os.environ, "RMTI_PLAN": str(plan_path)}
    cmd = [sys.executable, "-m", "manim", "render", "--format", "mp4", "-r", f"{RIGHT_W},{OUT_H}", "--fps", str(FPS),
           "--disable_caching", "--media_dir", str(media), "-o", "right_panel", str(Path(__file__).resolve()), "RMTIMaster"]
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, env=env)
    hits = glob.glob(str(media / "videos" / "**" / "right_panel.mp4"), recursive=True)
    if not hits:
        raise FileNotFoundError("Manim finished but right_panel.mp4 was not found under " + str(media))
    Path(hits[0]).replace(out)


def compose(left: Path, right: Path, audio: str, D: float, out: Path, max_bytes: int):
    """hstack + narration, H.264 + AAC. Capped CRF: the maxrate is derived from the size budget and
    lowered by 12% until the file fits, so the result is always under max_bytes."""
    abr = 128
    vk = int(max_bytes * 8 * 0.96 / D / 1000 - abr)
    if vk < 400:
        raise RuntimeError(f"{max_bytes / 1e6:.0f} MB for {D:.0f} s leaves only {vk} kbit/s for video")
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 8):
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", left, "-i", right, "-i", audio,
             "-filter_complex", f"[1:v]tpad=stop_mode=clone:stop_duration=3[r];[0:v][r]hstack=inputs=2:shortest=1[v]",
             "-map", "[v]", "-map", "2:a", "-t", f"{D:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
             "-maxrate", f"{vk}k", "-bufsize", f"{2 * vk}k", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", f"{abr}k", "-movflags", "+faststart", out])
        size = out.stat().st_size
        print(f"attempt {attempt}: video cap {vk} kbit/s -> {size / 1e6:.2f} MB (limit {max_bytes / 1e6:.2f} MB)")
        if size <= max_bytes:
            return size
        vk = int(vk * 0.88)
    raise RuntimeError("could not fit the video under the size limit")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(REPO / "assets" / "raw"))
    ap.add_argument("--out", default=str(REPO / "assets" / "videos" / "rmti_hcc_case_study.mp4"))
    ap.add_argument("--build", default=str(REPO / "build" / "rmti_master"))
    ap.add_argument("--max-mb", type=float, default=19.0, help="decimal MB; default 19 keeps it under 20 MB")
    ap.add_argument("--fit", choices=["cover", "blur"], default="cover", help="cover = crop to fill the left panel; blur = whole frame on a blurred fill")
    ap.add_argument("--weights", default=",".join(map(str, BEAT_WEIGHTS)), help="five comma-separated beat weights")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--skip-manim", action="store_true")
    a = ap.parse_args()

    weights = [float(x) for x in a.weights.split(",")]
    if len(weights) != 5:
        ap.error("--weights needs five values")
    build, out = Path(a.build), Path(a.out)
    build.mkdir(parents=True, exist_ok=True)
    plan = make_plan(Path(a.raw), weights)
    plan_path = build / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2))
    print(f"narration: {Path(plan['audio']).name}  {plan['duration']:.3f} s")
    for c in plan["clips"]:
        print(f"  clip {c['n']} {c['label']:<30} {c['start']:7.2f}-{c['start'] + c['seconds']:7.2f} s  "
              f"({c['seconds']:5.2f} s from a {c['clip_seconds']:.2f} s clip, {c['loops']} loop(s))  {Path(c['file']).name}")
    if a.plan_only:
        return
    left, right = build / "left.mp4", build / "right.mp4"
    build_left(plan, left, a.fit)
    build_right(plan_path, plan, right, build, a.skip_manim)
    size = compose(left, right, plan["audio"], plan["duration"], out, int(a.max_mb * 1e6))
    print(f"wrote {out}  {size / 1e6:.2f} MB  {OUT_W}x{OUT_H}  {plan['duration']:.2f} s")


# ----------------------------------------------------------------------------------------------- Manim scene
try:
    from manim import (BOLD, DOWN, LEFT, NORMAL, RIGHT, UL, UP, Axes, Create, DashedLine, Dot, FadeIn, FadeOut, GrowFromEdge,
                       LaggedStart, Line, MathTex, Polygon, Rectangle, RoundedRectangle, Scene, Text, VGroup, VMobject, Write, config)
    HAVE_MANIM = True
except ModuleNotFoundError:
    HAVE_MANIM = False

if HAVE_MANIM:
    config.pixel_width, config.pixel_height, config.frame_rate = RIGHT_W, OUT_H, FPS
    config.frame_height = 8.0
    config.frame_width = 8.0 * RIGHT_W / OUT_H
    config.background_color = "#F8FAFC"

    INK, MUTED, BORDER, CRIM, BLUE, SKY, WHITE = "#0F172A", "#475569", "#E2E8F0", "#BE123C", "#2563EB", "#93C5FD", "#FFFFFF"
    TIER_COL = ["#16A34A", "#CA8A04", "#EA580C", "#DC2626", "#7F1D1D"]
    FONT, CW = "Inter", 7.1                                   # CW = card width in scene units
    CENTER = np.array([0.0, -0.5, 0.0])

    def tcol(tier: str) -> str:
        return TIER_COL[int(tier.split()[1]) - 1]

    def T(s, size=24, color=INK, bold=False):
        return Text(s, font=FONT, font_size=size, color=color, weight=BOLD if bold else NORMAL)

    def card(w=CW, h=1.2):
        return RoundedRectangle(corner_radius=0.16, width=w, height=h, fill_color=WHITE, fill_opacity=1, stroke_color=BORDER, stroke_width=2)

    def tag(box, s, dx=0.3, dy=-0.28, size=17):
        return T(s, size, MUTED, True).move_to(box.get_corner(UL) + np.array([dx, dy, 0]), aligned_edge=LEFT)

    class RMTIMaster(Scene):
        def setup(self):
            p = os.environ.get("RMTI_PLAN")
            if p:
                plan = json.loads(Path(p).read_text())
            else:                                              # standalone preview, no audio probed
                D, b = 78.0, [0.0]
                for w in BEAT_WEIGHTS:
                    b.append(b[-1] + w * D / sum(BEAT_WEIGHTS))
                plan = dict(duration=D, bounds=b)
            self.D, self.bounds, self.d = plan["duration"], plan["bounds"], build_data()
            self.kicker = self.dots = None

        # --- timing: re-sync to the beat boundary after every beat so frame rounding never accumulates
        def now(self):
            try:
                return float(self.renderer.time)
            except Exception:
                return float(getattr(self, "time", 0.0))

        def hold(self, t):
            rem = t - self.now()
            if rem > 1.5 / FPS:
                self.wait(rem)

        def go(self, *anims, rt=0.8):
            self.play(*anims, run_time=max(rt, 0.15))

        def chrome(self):
            self.add(T("RMTI  ·  HCC surveillance case study", 20, MUTED, True).move_to([0, 3.75, 0]).align_on_border(LEFT, buff=0.35))
            self.add(T("Research prototype. Synthetic and published aggregate values. Not a medical device.", 15, MUTED).move_to([0, -3.78, 0]))

        def header(self, i, title, sub):
            new = VGroup(T(title, 34, INK, True), T(sub, 19, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            new.move_to([0, 3.0, 0]).align_on_border(LEFT, buff=0.35)
            dots = VGroup(*[Dot(radius=0.07, color=CRIM if k == i else BORDER) for k in range(5)]).arrange(RIGHT, buff=0.14)
            dots.move_to([0, 3.75, 0]).align_on_border(RIGHT, buff=0.35)
            old = [m for m in (self.kicker, self.dots) if m is not None]
            self.play(*[FadeOut(m) for m in old], FadeIn(new), FadeIn(dots), run_time=0.45)
            self.kicker, self.dots = new, dots

        def construct(self):
            b = self.bounds
            self.chrome()
            for i, fn in enumerate((self.beat_equations, self.beat_cube, self.beat_sweeps, self.beat_albi, self.beat_trajectory)):
                fn(i, b[i], b[i + 1])
                self.hold(b[i + 1])
            self.hold(self.D)

        def clear(self, group, t1):
            self.hold(t1 - 0.45)
            self.play(FadeOut(group), run_time=0.4)

        # (a) equations --------------------------------------------------------------------------------
        def beat_equations(self, i, t0, t1):
            B = t1 - t0
            self.header(i, "The equations", "Inherent risk, residual risk, expected annual loss")
            specs = [("INHERENT RISK  ·  Eq. (1)", r"IR = L \cdot E \cdot V"),
                     ("RESIDUAL RISK  ·  Eq. (2)", r"R = L \cdot E \cdot V \cdot (1-\rho)"),
                     ("EXPECTED ANNUAL LOSS  ·  Eq. (6)", r"EAL = L \cdot C \cdot (1-\rho)")]
            cards = []
            for lab, tex in specs:
                box = card(h=1.2)
                eq = MathTex(tex, font_size=42, color=INK).move_to(box.get_center() + DOWN * 0.15)
                cards.append(VGroup(box, tag(box, lab), eq))
            e = self.d["example"]
            ex = card(h=1.55)
            line1 = T(f"L {e['L']:.2f}   E {e['E']:.2f}   V {e['V']:.2f}   rho {e['rho']:.2f}   C {e['C']}", 23, MUTED).move_to(ex.get_center() + UP * 0.15)
            line2 = T(f"IR {e['IR']:.3f}    R {e['R']:.3f}    EAL {e['EAL']:.3f}    {e['tier']}", 27, tcol(e["tier"]), True).move_to(ex.get_center() + DOWN * 0.35)
            example = VGroup(ex, tag(ex, "WORKED EXAMPLE  ·  core.score()"), line1, line2)
            allg = VGroup(*cards, example).arrange(DOWN, buff=0.2).move_to(CENTER)
            for k, c in enumerate(cards):
                self.go(FadeIn(c[0]), FadeIn(c[1]), Write(c[2]), rt=min(1.3, 0.2 * B))
                self.hold(t0 + B * (0.22 + 0.2 * k))
            self.go(FadeIn(example, shift=UP * 0.15), rt=min(1.0, 0.15 * B))
            self.clear(allg, t1)

        # (b) cohort cube + surveillance reductions ----------------------------------------------------------
        def beat_cube(self, i, t0, t1):
            B, d = t1 - t0, self.d
            lo, hi = round(abs(d["pct_min"])), round(abs(d["pct_max"]))
            self.header(i, "Where a cohort sits", f"Surveillance cuts residual risk by {lo}% to {hi}%")
            s, org = 1.3, np.array([-2.15, 0.9, 0.0])
            P = lambda L, E, V: org + s * np.array([0.866 * (L - E), -0.5 * (L + E) + V, 0.0])
            corners = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
            edges = [(p, q) for p in corners for q in corners if p < q and sum(x != y for x, y in zip(p, q)) == 1]
            cube = VGroup()
            for p, q in edges:
                hidden = (0, 0, 0) in (p, q)
                ln = (DashedLine if hidden else Line)(P(*p), P(*q), stroke_color="#CBD5E1" if hidden else "#94A3B8", stroke_width=2)
                cube.add(ln)
            lab = VGroup(T("L", 24, CRIM, True).move_to(P(1, 0, 0) + [0.25, -0.1, 0]), T("E", 24, BLUE, True).move_to(P(0, 1, 0) + [-0.25, -0.1, 0]),
                         T("V", 24, INK, True).move_to(P(0, 0, 1) + [0, 0.25, 0]))
            self.go(FadeIn(cube), FadeIn(lab), rt=min(1.0, 0.12 * B))
            kr = lambda R: 0.2 * math.sqrt(max(R, 1e-6) / 0.312)
            dots, legend = VGroup(), VGroup()
            for c in d["cohorts"]:
                col = tcol(self.tier_of(c["R_now"]))
                dots.add(Dot(P(c["L"], c["E"], c["V"]), radius=kr(c["R_now"]), color=col, fill_opacity=0.85, stroke_color=WHITE, stroke_width=1.5))
                row = VGroup(Dot(radius=0.07, color=col), T(c["name"], 17, INK), T(f"R {c['R_now']:.3f} → {c['R_after']:.3f}", 17, MUTED))
                row[1].next_to(row[0], RIGHT, buff=0.12)
                row[2].next_to(row[1], RIGHT, buff=0.15)
                legend.add(row)
            legend.arrange(DOWN, aligned_edge=LEFT, buff=0.17).move_to([1.35, 1.1, 0]).align_on_border(RIGHT, buff=0.3)
            self.go(LaggedStart(*[FadeIn(x) for x in dots], lag_ratio=0.15), FadeIn(legend), rt=min(1.6, 0.18 * B))
            self.hold(t0 + 0.38 * B)
            shrink = [dt.animate.scale(kr(c["R_after"]) / kr(c["R_now"])) for dt, c in zip(dots, d["cohorts"])]
            self.go(*shrink, rt=min(1.4, 0.15 * B))                        # dot area is proportional to R
            rows = [(c["name"], c["pct"]) for c in d["cohorts"]] + [("Usual → optimised care", d["usual_to_opt"]["pct"])]
            title = T("Risk reduction when rho rises (usual → better surveillance)", 18, MUTED, True).move_to([0, -0.7, 0]).align_on_border(LEFT, buff=0.35)
            bars = VGroup()
            for k, (nm, pct) in enumerate(rows):
                y = -1.2 - 0.34 * k
                lab_t = T(nm, 18, INK, k == len(rows) - 1).move_to([-3.3, y, 0], aligned_edge=LEFT)
                w = 3.0 * abs(pct) / 60.0
                bar = Rectangle(width=w, height=0.22, fill_color=CRIM if k == len(rows) - 1 else BLUE, fill_opacity=1, stroke_width=0)
                bar.move_to([0.2 + w / 2, y, 0])
                val = T(f"−{abs(pct):.1f}%", 18, INK, True).move_to([0.2 + w + 0.12, y, 0], aligned_edge=LEFT)
                bars.add(VGroup(lab_t, bar, val))
            self.go(FadeIn(title), LaggedStart(*[FadeIn(r) for r in bars], lag_ratio=0.12), rt=min(1.8, 0.2 * B))
            u = d["usual_to_opt"]
            note = T(f"Investment efficiency at rho {u['rho_now']:.2f} → {u['rho_after']:.2f}:  IEI {u['iei']:.3f}", 18, MUTED).move_to([0, -3.5, 0]).align_on_border(LEFT, buff=0.35)
            self.go(FadeIn(note), rt=0.5)
            self.clear(VGroup(cube, lab, dots, legend, title, bars, note), t1)

        @staticmethod
        def tier_of(R):
            from core import rmti_core
            return rmti_core.tier(R)

        # (c) single-lever sweeps ----------------------------------------------------------------------------------
        def beat_sweeps(self, i, t0, t1):
            B, d = t1 - t0, self.d
            self.header(i, "One lever at a time", "Residual risk R as each term moves; the other terms stay fixed")
            sweeps = [("rho: surveillance effectiveness ladder, 0.15 → 0.65", d["sweep_rho"], lambda r: f"{r['label']} {r['x']:.2f}"),
                      ("L: likelihood suppression, 0.90 → 0.20", d["sweep_L"], lambda r: f"{r['x']:.2f}"),
                      ("V: ALBI grades 1 to 3 (liver reserve)", d["sweep_V"], lambda r: f"{r['label']} {r['x']:.2f}")]
            rmax = max(r["R_raw"] for _, rows, _ in sweeps for r in rows)
            panels = VGroup()
            for ttl, rows, lab in sweeps:
                box = card(h=1.85)
                g = VGroup(box, tag(box, ttl, size=17))
                n, slot = len(rows), 6.5 / len(rows)
                for k, r in enumerate(rows):
                    h = max(0.04, 0.85 * r["R_raw"] / rmax)
                    x = box.get_left()[0] + 0.3 + slot * (k + 0.5)
                    base_y = box.get_bottom()[1] + 0.5
                    bar = Rectangle(width=min(0.62, slot * 0.7), height=h, fill_color=tcol(r["tier"]), fill_opacity=0.9, stroke_width=0)
                    bar.move_to([x, base_y + h / 2, 0])
                    g.add(bar, T(f"{r['R']:.3f}", 16, INK, True).move_to([x, base_y + h + 0.17, 0]),
                          T(lab(r), 13, MUTED).move_to([x, base_y - 0.2, 0]))
                panels.add(g)
            panels.arrange(DOWN, buff=0.18).move_to(CENTER)
            for k, g in enumerate(panels):
                self.go(FadeIn(g[0]), FadeIn(g[1]), LaggedStart(*[GrowFromEdge(m, DOWN) if isinstance(m, Rectangle) else FadeIn(m) for m in g[2:]], lag_ratio=0.05), rt=min(1.6, 0.2 * B))
                self.hold(t0 + B * (0.3 + 0.25 * k))
            self.clear(panels, t1)

        # (d) Faria cohort ALBI weights ------------------------------------------------------------------------------
        def beat_albi(self, i, t0, t1):
            B, d = t1 - t0, self.d
            self.header(i, "Vulnerability from liver reserve", "Cohort-mean V from ALBI grade shares (Faria et al. dataset)")
            cols = {1: SKY, 2: BLUE, 3: CRIM}
            groups = VGroup()
            for c in d["albi"]:
                box = card(h=2.2)
                g = VGroup(box, tag(box, f"{c['name'].upper()}  ·  n = {c['n']}"))
                x0 = box.get_left()[0] + 0.3
                for gr in (1, 2, 3):
                    cnt = c["grades"][gr]
                    if not cnt:
                        continue
                    w = 6.5 * cnt / c["n"]
                    seg = Rectangle(width=w, height=0.5, fill_color=cols[gr], fill_opacity=1, stroke_color=WHITE, stroke_width=2)
                    seg.move_to([x0 + w / 2, box.get_center()[1] + 0.2, 0])
                    pct = T(f"G{gr}  {100 * cnt / c['n']:.0f}%", 15, WHITE if gr != 1 else INK, True).move_to(seg)
                    if w < 0.9:
                        pct = T(f"G{gr}", 13, INK, True).next_to(seg, DOWN, buff=0.06)
                    g.add(seg, pct)
                    x0 += w
                g.add(T(f"mean V = {c['V']:.3f}", 34, INK, True).move_to(box.get_center() + DOWN * 0.75 + LEFT * 1.6),
                      T(f"R = {c['R']:.3f}  (L 0.30, E 0.60, rho 0.20)", 19, MUTED).move_to(box.get_center() + DOWN * 0.75 + RIGHT * 1.9))
                groups.add(g)
            a = d["albi_anchors"]
            note = card(h=1.1)
            nt = VGroup(note, T(f"V = Σ share(grade) × anchor,   anchors  G1 {a[1]:.2f}   G2 {a[2]:.2f}   G3 {a[3]:.2f}", 20, INK).move_to(note.get_center()))
            allg = VGroup(*groups, nt).arrange(DOWN, buff=0.2).move_to(CENTER)
            for k, g in enumerate(groups):
                self.go(FadeIn(g, shift=UP * 0.15), rt=min(1.2, 0.18 * B))
                self.hold(t0 + B * (0.35 + 0.3 * k))
            self.go(FadeIn(nt), rt=0.6)
            self.clear(allg, t1)

        # (e) time-indexed trajectory --------------------------------------------------------------------------------
        def beat_trajectory(self, i, t0, t1):
            B, d = t1 - t0, self.d
            self.header(i, "The trajectory", "Two patients, same start, reviewed every 6 months")
            formula = MathTex(r"R(t) = L(t)\cdot E\cdot V^{*}(t)\cdot\left[1-\rho(t)\right]", font_size=36, color=INK).move_to([0, 1.85, 0])
            sub = T(f"V*(t) from an alpha-beta filter, alpha = {d['alpha']:.2f}, beta = {d['beta']:.2f}, 6-monthly cycles", 17, MUTED).move_to([0, 1.38, 0])
            A, Bp = d["traj"]["A"], d["traj"]["B"]
            top = 0.10
            ax = Axes(x_range=[0, 48, 12], y_range=[0, top, 0.05], x_length=6.0, y_length=2.7, tips=False,
                      axis_config={"color": MUTED, "stroke_width": 2, "include_numbers": False}).move_to([0.2, -0.45, 0])
            ticks = VGroup(*[T(s, 15, MUTED).next_to(ax.c2p(x, 0), DOWN, buff=0.12) for x, s in ((0, "0"), (12, "1 y"), (24, "2 y"), (36, "3 y"), (48, "4 y"))],
                           *[T(s, 15, MUTED).next_to(ax.c2p(0, y), LEFT, buff=0.12) for y, s in ((0, "0"), (0.05, "0.05"), (0.10, "0.10"))])
            cut = DashedLine(ax.c2p(0, d["tier_cut"]), ax.c2p(48, d["tier_cut"]), stroke_color="#94A3B8", stroke_width=2)
            cut_t = T("Tier 1 | Tier 2", 14, MUTED).next_to(ax.c2p(48, d["tier_cut"]), UP, buff=0.05).align_on_border(RIGHT, buff=0.4)
            self.go(FadeIn(formula), FadeIn(sub), FadeIn(ax), FadeIn(ticks), FadeIn(cut), FadeIn(cut_t), rt=min(1.4, 0.15 * B))
            self.hold(t0 + 0.3 * B)
            lns, dts, ends = [], VGroup(), VGroup()
            for rows, col, nm in ((A, CRIM, "Patient A"), (Bp, BLUE, "Patient B")):
                pts = [ax.c2p(r["month"], r["R_raw"]) for r in rows]
                ln = VMobject(stroke_color=col, stroke_width=5).set_points_as_corners(pts)
                lns.append(ln)
                dts.add(*[Dot(p, radius=0.055, color=col) for p in pts])
                ends.add(T(nm, 17, col, True).next_to(pts[-1], UP if col == CRIM else DOWN, buff=0.12))
            self.go(*[Create(l) for l in lns], rt=min(0.45 * B, 7.0))
            self.go(FadeIn(dts), FadeIn(ends), rt=0.6)
            self.hold(t0 + 0.72 * B)
            cards = VGroup()
            for rows, col, nm in ((A, CRIM, "Patient A"), (Bp, BLUE, "Patient B")):
                f, l = rows[0], rows[-1]
                box = card(w=3.45, h=1.4)
                cards.add(VGroup(box, tag(box, nm.upper(), 0.22, -0.26, 16), T(f"R {f['R_raw']:.3f} → {l['R_raw']:.3f}", 25, col, True).move_to(box.get_center() + UP * 0.08),
                                 T(f"{f['tier'].split(' - ')[0]} → {l['tier']}", 16, INK).move_to(box.get_center() + DOWN * 0.38),
                                 T(f"V* {f['V']:.2f} → {l['V']:.2f}   rho {f['rho']:.2f} → {l['rho']:.2f}", 14, MUTED).move_to(box.get_center() + DOWN * 0.62)))
            cards.arrange(RIGHT, buff=0.2).move_to([0, -2.9, 0])
            self.go(FadeIn(cards, shift=UP * 0.15), rt=0.8)
            self.clear(VGroup(formula, sub, ax, ticks, cut, cut_t, *lns, dts, ends, cards), t1)


if __name__ == "__main__":
    main()
