"""
tools/make_videos.py  --  build the narrated RMTI videos: MP4 with voice + soft caption track, burned-in-caption copy, .srt/.vtt, chapters

  python tools/make_videos.py all                                  # basic offline voice (drafts)
  python tools/make_videos.py all --voice openai                   # natural + emotional (OPENAI_API_KEY)  <- recommended for expressive delivery
  python tools/make_videos.py all --voice elevenlabs               # natural + emotional (ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)
  python tools/make_videos.py all --voice edge                     # natural, free (pip install edge-tts; EDGE_VOICE=en-US-AriaNeural)
  python tools/make_videos.py liver --audio-dir voice              # YOUR recording or audio from any tool: voice/liver/<segment id>.mp3
  python tools/make_videos.py all --export-script voice_scripts    # per-scene text + delivery directions, to paste into any voice tool
  python tools/make_videos.py liver --voice openai --only title,limits   # audition a voice on two scenes first
  python tools/make_videos.py cc --out media                       # only (re)make the burned-in-caption copies of existing videos
  python tools/make_videos.py all --preview prev                   # PNG of each scene, no voice, no encoding
Outputs per video in --out: <name>.mp4 (voice + caption track you can switch on/off), <name>_CC.mp4 (captions always visible in a band under the picture),
<name>.srt, <name>.vtt, <name>_timings.json, <name>_chapters.txt (paste into the YouTube description).
Research prototype. No patient data.
"""
import argparse, csv, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rmti_video_engine as E
from storyboards import BOARDS, CHAPTERS, direction_for

ap = argparse.ArgumentParser()
ap.add_argument("which", choices=["all", "cc"] + list(BOARDS))
ap.add_argument("--voice", default="flite", choices=["flite", "openai", "elevenlabs", "edge", "piper"])
ap.add_argument("--audio-dir", default=None, help="folder with your own audio: <dir>/<video>/<segment id>.mp3|wav|m4a")
ap.add_argument("--export-script", default=None, help="write per-scene voice scripts (text + delivery direction) into this folder and exit")
ap.add_argument("--out", default="media"); ap.add_argument("--preview", default=None); ap.add_argument("--no-cc", action="store_true")
ap.add_argument("--only", default=None, help="comma-separated segment ids: render just those scenes as <name>_TEST.mp4 (cheap way to audition a voice)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

if a.which == "cc":
    for mp4 in sorted(glob.glob(os.path.join(a.out, "rmti_[0-9]_*.mp4"))):
        if not mp4.endswith("_CC.mp4"):
            E.burn_captions(mp4, mp4[:-4] + ".srt", mp4[:-4] + "_CC.mp4")
    sys.exit()

for k in (BOARDS if a.which == "all" else [a.which]):
    stem, fn = BOARDS[k]
    segs = fn()
    for sg in segs:
        sg["direction"] = direction_for(sg["id"])
    if a.export_script:
        d = os.path.join(a.export_script, k); os.makedirs(d, exist_ok=True)
        with open(os.path.join(a.export_script, stem + "_voice_script.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["segment_id", "delivery_direction", "text"])
            for sg in segs:
                w.writerow([sg["id"], sg["direction"], sg["text"]])
                open(os.path.join(d, sg["id"] + ".txt"), "w", encoding="utf-8").write(sg["text"] + "\n")
        print("voice script for", k, "->", d); continue
    if a.only:
        keep = set(a.only.split(",")); segs = [sg for sg in segs if sg["id"] in keep]
        if not segs:
            sys.exit("no such segment id; see the CSV from --export-script")
        stem += "_TEST"
    out = os.path.join(a.out, stem + ".mp4")
    E.run(segs, out, backend=a.voice, preview=(os.path.join(a.preview, k) if a.preview else None), audio_dir=a.audio_dir, video_key=k)
    if a.preview or a.only:
        continue
    open(os.path.join(a.out, stem + "_chapters.txt"), "w", encoding="utf-8").write(E.chapters_text(os.path.join(a.out, stem + "_timings.json"), CHAPTERS[k]) + "\n")
    if not a.no_cc:
        E.burn_captions(out, out[:-4] + ".srt", out[:-4] + "_CC.mp4")
