import glob
import subprocess
from pathlib import Path

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
    return Path(matches[0])


def assemble_video(clips: list[Path], audio: Path, output_mp4: Path):
    total_sec = get_duration(audio)
    seg_sec = total_sec / len(clips)
    temp_segments = []

    for idx, clip in enumerate(clips):
        seg_out = OUT_DIR / f"_tmp_{output_mp4.stem}_{idx}.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(clip),
            "-t", f"{seg_sec:.3f}",
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,fps=24,format=yuv420p",
            "-c:v", "libx264", "-crf", "28", "-preset", "medium",
            "-an", str(seg_out),
        ], check=True)
        temp_segments.append(seg_out)

    concat_txt = OUT_DIR / f"_concat_{output_mp4.stem}.txt"
    concat_txt.write_text("\n".join(f"file '{p.name}'" for p in temp_segments))

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output_mp4),
    ], check=True)

    for p in temp_segments:
        p.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    print(f"Built {output_mp4} ({total_sec:.1f}s)")


if __name__ == "__main__":
    # Video 1: 4-Stage Pathological Progression & Cohort Triage
    v1_audio = find_file("*brit voice*.mp3")
    v1_clips = [
        find_file("1.*glowing_liver*.mp4"),
        find_file("3.*Cells_proliferating*.mp4"),
        find_file("2.*liver_tumor*.mp4"),
        find_file("5.*portal_vein*.mp4"),
        find_file("4.*Tumor_cells_traveling*.mp4"),
    ]
    assemble_video(v1_clips, v1_audio, OUT_DIR / "video1_4stages_3d.mp4")

    # Video 2: Time-Indexed Trajectory R(t) (matches both .mp3 and .mp3.mp3)
    if list(RAW_DIR.glob("video2_trajectory_voice*.mp3")):
        v2_audio = find_file("video2_trajectory_voice*.mp3")
        v2_clips = sorted(RAW_DIR.glob("traj_clip_*.mp4"))
        assemble_video(v2_clips, v2_audio, OUT_DIR / "video2_trajectory_3d.mp4")
