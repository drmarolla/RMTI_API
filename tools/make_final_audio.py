#!/usr/bin/env python3
"""Mix your narration with the Adagio bed; the music dips automatically while you speak.

  Single take:   python tools/make_final_audio.py liver_narration.mp3 static/adagio_bed_134s.mp3 rmti_liver_audio.mp3
  Scene clips:   python tools/make_final_audio.py CLIPS_DIR            static/adagio_bed_134s.mp3 rmti_liver_audio.mp3
                 (CLIPS_DIR holds 01.mp3 ... 08.mp3; each starts at its scene time)

Needs ffmpeg on the PATH. The single-take mode starts your voice 2 s after the music and keeps 5 s of music after you finish.
"""
import subprocess
import sys
from pathlib import Path

STARTS = [0, 16, 32, 60, 74, 88, 106, 122]      # scene starts (s), medium-slow animation
TOTAL = 134
DUCK = "sidechaincompress=threshold=0.02:ratio=10:attack=40:release=700:makeup=1"


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def run(cmd):
    subprocess.run(cmd, check=True)


def single(voice, bed, out):
    total = duration(voice) + 2 + 5
    fc = (f"[0:a]highpass=f=70,loudnorm=I=-16:LRA=7:TP=-1.5,aformat=sample_rates=44100:channel_layouts=stereo,"
          f"adelay=2000|2000,apad=whole_dur={total:.2f},atrim=0:{total:.2f},asplit=2[v][sc];"
          f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.2f},aformat=sample_rates=44100:channel_layouts=stereo,"
          f"volume=-2dB,afade=t=out:st={total - 5:.2f}:d=5[m];"
          f"[m][sc]{DUCK}[d];[v][d]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[out]")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(voice), "-i", str(bed), "-filter_complex", fc, "-map", "[out]", "-b:a", "192k", str(out)])


def scenes(clips_dir, bed, out):
    clips = [Path(clips_dir) / f"{i + 1:02d}.mp3" for i in range(8)]
    missing = [str(c) for c in clips if not c.exists()]
    if missing:
        sys.exit("Missing clips: " + ", ".join(missing))
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-i", str(bed)]
    parts = [f"[{i}:a]highpass=f=70,aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(s * 1000)}|{int(s * 1000)}[c{i}]"
             for i, s in enumerate(STARTS)]
    parts.append("".join(f"[c{i}]" for i in range(8)) + f"amix=inputs=8:normalize=0,loudnorm=I=-16:LRA=7:TP=-1.5,"
                 f"apad=whole_dur={TOTAL},atrim=0:{TOTAL},asplit=2[v][sc]")
    parts.append(f"[8:a]atrim=0:{TOTAL},aformat=sample_rates=44100:channel_layouts=stereo,volume=-2dB[m]")
    parts.append(f"[m][sc]{DUCK}[d]")
    parts.append("[v][d]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[out]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", "-b:a", "192k", str(out)]
    run(cmd)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    voice, bed, out = sys.argv[1:]
    (scenes if Path(voice).is_dir() else single)(voice, bed, out)
    print("wrote", out)
