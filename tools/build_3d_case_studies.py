import glob
import subprocess
from pathlib import Path

RAW_DIR = Path("assets/raw")
OUT_DIR = Path("assets/videos")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_font() -> str:
    """Locate an installed TrueType font on Linux/macOS/Windows for FFmpeg drawtext."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return f":fontfile={path}"
    return ""


FONT_ARG = find_font()


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
    return Path(matches[0])


def esc(txt: str) -> str:
    """Escape text safely for FFmpeg drawtext filter with expansion=none."""
    clean = txt.replace("'", "\u2019")
    return clean.replace("\\", "\\\\").replace(":", "\\:")


def build_split_screen_video(stages: list[dict], audio: Path | None, output_mp4: Path):
    total_sec = get_duration(audio) if audio else 60.0
    seg_sec = total_sec / len(stages)
    temp_segments = []

    for idx, stg in enumerate(stages):
        seg_out = OUT_DIR / f"_tmp_{output_mp4.stem}_{idx}.mp4"

        # Left 660x720 = 3D Google Flow Organ Video; Right 620x720 = Clean Clinical Math HUD (#F8FAFC)
        vf = (
            "[0:v]scale=660:720:force_original_aspect_ratio=increase,crop=660:720,fps=24[left];"
            "color=c=#F8FAFC:s=620x720:r=24[right];"
            "[left][right]hstack=inputs=2,"
            # Top Header Banner
            "drawbox=x=680:y=28:w=572:h=44:color=#EFF6FF:t=fill,"
            f"drawtext=text='{esc(stg['badge'])}'{FONT_ARG}:expansion=none:x=696:y=42:fontsize=15:fontcolor=#1D4ED8,"
            # Stage Title
            f"drawtext=text='{esc(stg['title'])}'{FONT_ARG}:expansion=none:x=680:y=92:fontsize=23:fontcolor=#0F172A,"
            # Progression Flow Arrows Bar
            "drawbox=x=680:y=138:w=572:h=42:color=#0F172A:t=fill,"
            f"drawtext=text='{esc(stg['flow'])}'{FONT_ARG}:expansion=none:x=694:y=151:fontsize=13:fontcolor=#38BDF8,"
            # Core Equation Card with Centered Multiplication Dots (·)
            "drawbox=x=680:y=200:w=572:h=88:color=#FFFFFF:t=fill,"
            "drawbox=x=680:y=200:w=572:h=88:color=#CBD5E1:t=2,"
            f"drawtext=text='{esc(stg['eq_sym'])}'{FONT_ARG}:expansion=none:x=700:y=216:fontsize=22:fontcolor=#0F172A,"
            f"drawtext=text='{esc(stg['eq_num'])}'{FONT_ARG}:expansion=none:x=700:y=252:fontsize=19:fontcolor=#B91C1C,"
            # Moving Metrics & Trajectory Column Box
            "drawbox=x=680:y=308:w=572:h=245:color=#FFFFFF:t=fill,"
            "drawbox=x=680:y=308:w=572:h=245:color=#CBD5E1:t=2,"
            f"drawtext=text='{esc(stg['line1'])}'{FONT_ARG}:expansion=none:x=700:y=328:fontsize=16:fontcolor=#0F172A,"
            f"drawtext=text='{esc(stg['line2'])}'{FONT_ARG}:expansion=none:x=700:y=368:fontsize=16:fontcolor=#1D4ED8,"
            f"drawtext=text='{esc(stg['line3'])}'{FONT_ARG}:expansion=none:x=700:y=408:fontsize=16:fontcolor=#0F766E,"
            f"drawtext=text='{esc(stg['line4'])}'{FONT_ARG}:expansion=none:x=700:y=448:fontsize=16:fontcolor=#B91C1C,"
            f"drawtext=text='{esc(stg['outcome'])}'{FONT_ARG}:expansion=none:x=700:y=498:fontsize=18:fontcolor=#0F172A,"
            # Citation Footer
            "drawbox=x=680:y=575:w=572:h=110:color=#F1F5F9:t=fill,"
            f"drawtext=text='{esc(stg['cite1'])}'{FONT_ARG}:expansion=none:x=696:y=592:fontsize=14:fontcolor=#475569,"
            f"drawtext=text='{esc(stg['cite2'])}'{FONT_ARG}:expansion=none:x=696:y=620:fontsize=14:fontcolor=#475569,"
            f"drawtext=text='Marolla 2026 | RMTI-Py v2.5 | Apache-2.0'{FONT_ARG}:expansion=none:x=696:y=652:fontsize=13:fontcolor=#1D4ED8,"
            "format=yuv420p"
        )

        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(stg["clip"]),
            "-t", f"{seg_sec:.3f}",
            "-filter_complex", vf,
            "-c:v", "libx264", "-crf", "26", "-preset", "medium",
            "-an", str(seg_out),
        ], check=True)
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


if __name__ == "__main__":
    # --- VIDEO 1: 4-Stage Liver Progression & Cohort Triage ---
    v1_audio = find_file("*brit voice*.mp3")
    v1_stages = [
        {
            "clip": find_file("1.*glowing_liver*.mp4"),
            "badge": "STAGE 1 / FIBROSIS (F1-F3)  •  BASELINE SNAPSHOT",
            "title": "Preserved Hepatic Reserve",
            "flow": "[1. Fibrosis] -> 2. Cirrhosis -> 3. Early HCC -> 4. Invasion -> 5. Metastasis",
            "eq_sym": "R  =  L  ·  E  ·  V  ·  (1 - ρ)",
            "eq_num": "R  =  0.15  ·  0.60  ·  0.35  ·  (1 - 0.20)  =  0.025",
            "line1": "Likelihood (L): 0.15   (Low annual hazard)",
            "line2": "Exposure (E):   0.60   (Active clinic footprint)",
            "line3": "Vulnerability (V): 0.35 (ALBI Grade 1 preserved)",
            "line4": "Resilience (ρ): 0.20   (Usual care surveillance)",
            "outcome": "Result: R = 0.025  ->  TIER 1: LOW URGENCY",
            "cite1": "Source: Marolla (2026) SSRN: 7427450 | RMTI-Py v2.2.1",
            "cite2": "ALBI Liver Reserve Scale: Grade 1 = 0.35 (Johnson et al.)",
        },
        {
            "clip": find_file("3.*Cells_proliferating*.mp4"),
            "badge": "STAGE 2 / CIRRHOSIS (F4)  •  INCIDENCE SURGE",
            "title": "Up to 10x Jump in HCC Likelihood",
            "flow": "1. Fibrosis -> [2. Cirrhosis] -> 3. Early HCC -> 4. Invasion -> 5. Metastasis",
            "eq_sym": "R  =  L  ·  E  ·  V  ·  (1 - ρ)",
            "eq_num": "R  =  0.90  ·  0.70  ·  0.55  ·  (1 - 0.10)  =  0.312",
            "line1": "Untreated HBV Cohort (~12.8%/yr): L jumps 0.15 -> 0.90",
            "line2": "Pearl MASLD Cohort (~5.0%/yr):   L = 0.65, R = 0.156",
            "line3": "Population Exposure (E): 0.60 -> 0.70",
            "line4": "Ad-Hoc Resilience (ρ = 0.10): 90% hazard unbuffered",
            "outcome": "Result: R = 0.312  ->  TIER 3: HIGH URGENCY",
            "cite1": "Upstream Scores: Fan et al. aMAP; Sharma et al. THRI",
            "cite2": "Table 1 & Table 2 Cohorts (Marolla 2026, SSRN: 7427450)",
        },
        {
            "clip": find_file("2.*liver_tumor*.mp4"),
            "badge": "STAGE 3 / EARLY HCC (BCLC 0/A)  •  INTERCEPTION WINDOW",
            "title": "Resilience Upgrade Cuts Risk 30%-56%",
            "flow": "1. Fibrosis -> 2. Cirrhosis -> [3. Early HCC] -> 4. Invasion -> 5. Metastasis",
            "eq_sym": "R  =  L  ·  E  ·  V  ·  (1 - ρ)",
            "eq_num": "R  =  0.90  ·  0.70  ·  0.55  ·  (1 - 0.65)  =  0.121",
            "line1": "Resilience Ladder (ρ): 0.10 (Ad-hoc)  ->  0.65 (US + AFP)",
            "line2": "Untreated HBV: R drops 0.312 -> 0.191  (-39% Risk)",
            "line3": "Pearl MASLD:   R drops 0.156 -> 0.068  (-56% Risk)",
            "line4": "Investment Efficiency Index (IEI): > 1.00 (High Yield)",
            "outcome": "Result: Intercepted at BCLC 0/A (>70% 5-Yr Survival)",
            "cite1": "Singal et al. (2022) Surveillance Uptake (<20% baseline)",
            "cite2": "RHO_ANCHORS_HCC: 0.15 to 0.65 (core/rmti_core.py)",
        },
        {
            "clip": find_file("5.*portal_vein*.mp4"),
            "badge": "STAGE 4 / PORTAL VEIN INVASION (BCLC B/C)",
            "title": "Capsule Breach & ALBI Decompensation",
            "flow": "1. Fibrosis -> 2. Cirrhosis -> 3. Early HCC -> [4. Invasion] -> 5. Metastasis",
            "eq_sym": "R  =  L  ·  E  ·  V  ·  (1 - ρ)",
            "eq_num": "R  =  0.90  ·  0.75  ·  0.85  ·  (1 - 0.15)  =  0.488",
            "line1": "Faria et al. Cohort (n=54): HCC V=0.522 vs Cirrhosis 0.480",
            "line2": "Mortality Gap: 34.5% (HCC) vs 8.0% (Cirrhosis), p = 0.025",
            "line3": "ALBI Grade 3 Progression: Vulnerability V -> 0.85",
            "line4": "Curative Resection & Ablation Window Foreclosed",
            "outcome": "Result: R = 0.488  ->  TIER 4: SEVERE ESCALATION",
            "cite1": "Faria et al. Harvard Dataverse Cohort (doi:10.7910/DVN)",
            "cite2": "Lau-Min et al., JAMA Network Open (2025) Systemic Cohort",
        },
        {
            "clip": find_file("4.*Tumor_cells_traveling*.mp4"),
            "badge": "STAGE 5 / METASTASIS (BCLC D)  •  EXPECTED ANNUAL LOSS",
            "title": "Consequence Tie-Breaker: EAL Index",
            "flow": "1. Fibrosis -> 2. Cirrhosis -> 3. Early HCC -> 4. Invasion -> [5. Metastasis]",
            "eq_sym": "EAL  =  L  ·  C  ·  (1 - ρ)",
            "eq_num": "EAL  =  0.25  ·  1.00  ·  (1 - 0.20)  =  0.200",
            "line1": "Patient A (BCLC A, C=0.30): R = 0.072 | EAL = 0.072",
