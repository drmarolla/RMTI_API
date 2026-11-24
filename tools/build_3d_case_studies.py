import glob
import itertools
import shutil
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RAW_DIR = Path("assets/raw")
OUT_DIR = Path("assets/videos")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_duration(media_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    return float(subprocess.check_output(cmd).decode().strip())


def find_file(pattern: str) -> Path:
    matches = sorted(glob.glob(str(RAW_DIR / pattern)))
    if not matches:
        raise FileNotFoundError(f"Missing file matching: {RAW_DIR / pattern}")
    return Path(next(iter(matches)))


def render_animated_hud_frames(stage_idx: int, mode: str, n_frames: int, frame_dir: Path):
    """Render animated axes, moving risk curves, and clean citation pill (512x720)."""
    frame_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 1.0

    v1_meta = [
        (
            "STAGE 1 / FIBROSIS (F1-F3)",
            "Baseline Hepatic Reserve",
            "R = L · E · V · (1 - ρ) = 0.025",
            "Tier 1: Low Urgency (ALBI Grade 1)",
            "Marolla (2026) SSRN: 7427450 | Johnson et al. ALBI",
        ),
        (
            "STAGE 2 / CIRRHOSIS (F4)",
            "10x Surge in HCC Likelihood",
            "R = 0.90 · 0.70 · 0.55 · (1 - 0.10) = 0.312",
            "Tier 3: High Urgency (Untreated HBV)",
            "Fan et al. aMAP | Sharma et al. THRI | Table 1",
        ),
        (
            "STAGE 3 / EARLY HCC (BCLC 0/A)",
            "Resilience Interception Window",
            "ρ: 0.10 -> 0.65 cuts R by 30%-56%",
            "Intercepted at BCLC 0/A (>70% 5-Yr Survival)",
            "Singal et al. (2022) | RHO_ANCHORS_HCC (0.15-0.65)",
        ),
        (
            "STAGE 4 / PORTAL INVASION (BCLC B/C)",
            "ALBI Reserve Decompensation",
            "R = 0.90 · 0.75 · 0.85 · (1 - 0.15) = 0.488",
            "Tier 4: Severe Escalation (V = 0.522 vs 0.480)",
            "Faria et al. Harvard Dataverse (n=54, p=0.025)",
        ),
        (
            "STAGE 5 / METASTASIS (BCLC D)",
            "Expected Annual Loss Tie-Breaker",
            "EAL = L · C · (1 - ρ) = 0.200",
            "Within-Tier Reversal: Patient B Escalates First",
            "Marolla (2026) Governance | HL7 FHIR R4",
        ),
    ]

    v2_meta = [
        (
            "TIME-INDEXED TRAJECTORY | t = 0 -> 3",
            "From Snapshot to R(t)",
            "R(t) = L(t) · E · V*(t) · [1 - ρ(t)]",
            "Unrounded IR_raw, R_raw, EAL_raw (ΔR ~ 0.001)",
            "Marolla (2026) Snapshot to Trajectory | RMTI-Py v2.5",
        ),
        (
            "STEADY-STATE FILTER (α=0.41, β=0.09)",
            "Diverging Patient Trajectories",
            "V*(t) separates Patient B vs. Patient A",
            "+0.015 to +0.022 AUROC Gain (N = 2,000)",
            "Synthetic Landmark Validation (2-Yr HCC Horizon)",
        ),
    ]

    stages_list = v1_meta if mode == "v1" else v2_meta
    badge_txt, title_txt, eq_txt, outcome_txt, cite_txt = next(itertools.islice(stages_list, stage_idx, stage_idx + 1))

    for f in range(n_frames):
        prog = f / max(1, n_frames - 1)
        fig = plt.figure(figsize=(5.12, 7.20), dpi=100, facecolor="#F8FAFC")

        fig.text(
            0.05, 0.945, badge_txt, fontsize=9.0, fontweight="bold", color="#1D4ED8",
            bbox=dict(boxstyle="round,pad=0.32", facecolor="#EFF6FF", edgecolor="none"),
        )
        fig.text(0.05, 0.892, title_txt, fontsize=14.0, fontweight="bold", color="#0F172A")
        fig.text(
            0.05, 0.835, eq_txt, fontsize=10.5, fontweight="bold", color="#B91C1C",
            bbox=dict(boxstyle="round,pad=0.40", facecolor="#FFFFFF", edgecolor="#CBD5E1"),
        )

        ax = fig.add_axes([0.14, 0.38, 0.80, 0.39], facecolor="#FFFFFF")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, linestyle="--", alpha=0.35, color="#CBD5E1")

        if mode == "v1" and stage_idx in (0, 1, 2):
            rho_x = np.linspace(0.0, 0.80, 100)
            L_curr = (
                0.15 + 0.75 * min(1.0, prog * 1.4)
                if stage_idx == 1
                else (0.15 if stage_idx == 0 else 0.90)
            )
            E_curr = 0.60 if stage_idx == 0 else 0.70
            V_curr = 0.35 if stage_idx == 0 else 0.55
            r_curve = L_curr * E_curr * V_curr * (1.0 - rho_x)

            ax.plot(rho_x, r_curve, color="#1D4ED8", linewidth=2.5, label="R = L·E·V·(1-ρ)")
            rho_pt = 0.20 if stage_idx < 2 else (0.10 + 0.55 * prog)
            r_pt = L_curr * E_curr * V_curr * (1.0 - rho_pt)
            ax.scatter([rho_pt], [r_pt], color="#B91C1C", s=80, zorder=5)
            ax.annotate(
                f"R = {r_pt:.3f}", (rho_pt, r_pt),
                xytext=(8, 8), textcoords="offset points",
                fontsize=9.5, fontweight="bold", color="#B91C1C",
            )
            ax.axhline(0.15, color="#D97706", linestyle=":", linewidth=1.3, label="High Tier (0.15)")
            ax.set_xlim(0, 0.80)
            ax.set_ylim(0, 0.40)
            ax.set_xlabel("System Resilience (ρ)", fontsize=9.0, color="#475569")
            ax.set_ylabel("Residual Risk (R)", fontsize=9.0, color="#475569")
            ax.legend(loc="upper right", fontsize=7.5, frameon=True)

        elif mode == "v1" and stage_idx in (3, 4):
            labels = ["Fibrosis\n(G1)", "HBV\n(ρ=0.65)", "Invasion\n(ALBI 3)", "Pt A\n(EAL)", "Pt B\n(EAL)"]
            targets = [0.025, 0.191, 0.488, 0.072, 0.200]
            colors = ["#94A3B8", "#1D4ED8", "#B91C1C", "#64748B", "#0F766E"]
            curr_vals = [v * min(1.0, prog * 1.25) for v in targets]
            bars = ax.bar(labels, curr_vals, color=colors, width=0.50)
            for bar, val in zip(bars, curr_vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:.3f}",
                    ha="center", fontsize=8.0, fontweight="bold", color="#0F172A",
                )
            ax.set_ylim(0, 0.58)
            ax.set_ylabel("Risk / EAL Index", fontsize=9.0, color="#475569")
            ax.tick_params(axis="x", labelsize=7.5)

        else:
            t_full = np.array([0.0, 1.0, 2.0, 3.0])
            r_b = np.array([0.072, 0.115, 0.152, 0.178])
            r_a = np.array([0.072, 0.048, 0.031, 0.022])
            max_t = 3.0 * prog
            t_vis = np.linspace(0, max(0.05, max_t), 60)
            ax.plot(t_vis, np.interp(t_vis, t_full, r_b), color="#B91C1C", linewidth=2.6, label="Patient B (V↑, ρ flat)")
            ax.plot(t_vis, np.interp(t_vis, t_full, r_a), color="#1D4ED8", linewidth=2.6, label="Patient A (V↓, ρ↑)")
            ax.axhline(0.15, color="#B91C1C", linestyle="--", alpha=0.5, linewidth=1.1)
            ax.axhline(0.05, color="#0F766E", linestyle="--", alpha=0.5, linewidth=1.1)
            ax.set_xlim(0, 3.1)
            ax.set_ylim(0, 0.21)
            ax.set_xticks(list(range(4)))
            ax.set_xticklabels(["t=0", "t=1 (6m)", "t=2 (12m)", "t=3 (18m)"], fontsize=8.0)
            ax.set_ylabel("Time-Indexed R(t)", fontsize=9.0, color="#475569")
            ax.legend(loc="upper left", fontsize=7.5, frameon=True)

        fig.text(
            0.05, 0.255, outcome_txt, fontsize=9.8, fontweight="bold", color="#0F172A",
            bbox=dict(boxstyle="round,pad=0.40", facecolor="#FFFFFF", edgecolor="#94A3B8"),
        )
        fig.text(
            0.05, 0.155, f"Ref: {cite_txt}\nMarolla 2026 | RMTI-Py v2.5 (Apache-2.0)",
            fontsize=8.0, color="#475569",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#F1F5F9", edgecolor="none"),
        )

        fig.savefig(frame_dir / f"hud_{f:04d}.png", dpi=100)
        plt.close(fig)


def build_video(clips: list[Path], mode: str, audio: Path | None, output_mp4: Path):
    total_sec = get_duration(audio) if audio else 70.0
    seg_sec = total_sec / len(clips)
    fps_hud = 8
    n_frames = max(16, int(seg_sec * fps_hud))
    temp_segments = []

    for idx, clip in enumerate(clips):
        frame_dir = OUT_DIR / f"_frames_{output_mp4.stem}_{idx}"
        render_animated_hud_frames(idx, mode, n_frames, frame_dir)
        seg_out = OUT_DIR / f"_tmp_{output_mp4.stem}_{idx}.mp4"

        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(clip),
            "-framerate", str(fps_hud), "-i", str(frame_dir / "hud_%04d.png"),
            "-t", f"{seg_sec:.3f}",
            "-filter_complex",
            "[0:v]scale=768:720:force_original_aspect_ratio=increase,crop=768:720,fps=24[left];"
            "[1:v]fps=24[right];"
            "[left][right]hstack=inputs=2,format=yuv420p",
            "-c:v", "libx264", "-crf", "26", "-preset", "medium",
            "-an", str(seg_out),
        ], check=True)

        shutil.rmtree(frame_dir, ignore_errors=True)
        temp_segments.append(seg_out)

    concat_txt = OUT_DIR / f"_concat_{output_mp4.stem}.txt"
    concat_txt.write_text("\n".join(f"file '{p.name}'" for p in temp_segments))

    if audio:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-i", str(audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(output_mp4),
        ], check=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-c:v", "copy", str(output_mp4),
        ], check=True)

    for p in temp_segments:
        p.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    print(f"Built {output_mp4} ({total_sec:.1f}s)")


