"""
tools/check_voice_folder.py  --  check your own voice recordings before building the videos

    python tools/check_voice_folder.py voice

Expects  voice/<video>/<scene id>.mp3|wav|m4a  (video folders: explained, liver, flood_heat). For every scene it reports:
  found / missing, length, speaking pace (words per second), loudness, and warnings for clipping, very quiet takes,
  and pace that is far too fast or too slow. Fix or re-record only the flagged scenes, then build the videos.
Needs ffmpeg (or `pip install imageio-ffmpeg`). Research prototype. No patient data.
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice_backends as VB
from storyboards import BOARDS


def probe(path):
    ff = VB._ffmpeg()
    r = subprocess.run([ff, "-hide_banner", "-i", path, "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True)
    err = r.stderr
    d = re.search(r"time=(\d+):(\d+):([\d.]+)", err)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", err); peak = re.search(r"max_volume: (-?[\d.]+) dB", err)
    return dur, float(mean.group(1)) if mean else None, float(peak.group(1)) if peak else None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = sys.argv[1]; missing = flagged = total = 0
    for key, (stem, fn) in BOARDS.items():
        print(f"\n== {key}  ({stem})")
        print(f"{'scene':<10}{'status':<9}{'length':>8}{'words/s':>9}{'mean dB':>9}{'peak dB':>9}  notes")
        for sg in fn():
            total += 1
            p = VB.find_audio(root, sg["id"], key)
            if not p:
                missing += 1; print(f"{sg['id']:<10}{'MISSING':<9}"); continue
            dur, mean, peak = probe(p); words = len(sg["text"].split()); wps = words / dur if dur else 0; notes = []
            if peak is not None and peak > -1.0:
                notes.append("clipping risk: record a little softer or move back from the mic")
            if mean is not None and mean < -34:
                notes.append("very quiet: move closer or raise the input level")
            if wps and wps > 3.4:
                notes.append("very fast: slow down")
            if wps and wps < 1.4:
                notes.append("very slow or long silences: trim")
            if dur < 1.0:
                notes.append("almost empty file")
            flagged += bool(notes)
            print(f"{sg['id']:<10}{'ok':<9}{dur:>7.1f}s{wps:>9.2f}{mean if mean is not None else float('nan'):>9.1f}{peak if peak is not None else float('nan'):>9.1f}  {'; '.join(notes)}")
    print(f"\n{total} scenes: {total - missing} found, {missing} missing, {flagged} with warnings.")
    if not missing:
        print("Ready to build:  python tools/make_videos.py all --audio-dir " + root)


if __name__ == "__main__":
    main()
