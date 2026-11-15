#!/usr/bin/env python3
"""Assemble the final audio for one RMTI video: scene narration clips + Adagio bed, music ducked under the voice.

    python tools/assemble_audio.py CLIPS_DIR media/audio/adagio_bed_134s.mp3 rmti_liver_audio.mp3

CLIPS_DIR holds 01.mp3 ... 08.mp3 (one clip per scene; scene 3 may be one clip). Needs ffmpeg on the PATH.
Scene start times in seconds match the medium-slow animation (title 16 s, ..., closing 12 s; total 134 s).
"""
import subprocess
import sys
from pathlib import Path

STARTS = [0, 16, 32, 60, 74, 88, 106, 122]
TOTAL = 134


def main(clips_dir, bed, out):
    clips = [Path(clips_dir) / f"{i + 1:02d}.mp3" for i in range(8)]
    missing = [str(c) for c in clips if not c.exists()]
    if missing:
        sys.exit("Missing clips: " + ", ".join(missing))
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-i", str(bed)]
    parts = []
    for i, st in enumerate(STARTS):
        ms = int(st * 1000)
        parts.append(f"[{i}:a]highpass=f=70,aformat=sample_rates=44100:channel_layouts=stereo,adelay={ms}|{ms}[c{i}]")
    parts.append("".join(f"[c{i}]" for i in range(8)) + f"amix=inputs=8:normalize=0,loudnorm=I=-16:LRA=7:TP=-1.5,"
                 f"apad=whole_dur={TOTAL},atrim=0:{TOTAL},asplit=2[v][sc]")
    parts.append(f"[8:a]atrim=0:{TOTAL},aformat=sample_rates=44100:channel_layouts=stereo,volume=-2dB[m]")
    parts.append("[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=40:release=700:makeup=1[d]")
    parts.append("[v][d]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[out]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", "-b:a", "192k", str(out)]
    subprocess.run(cmd, check=True)
    print("wrote", out)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
