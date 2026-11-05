"""
voice_backends.py  --  voice options for the RMTI videos, from basic to natural and expressive.

  flite       offline basic synthetic voice. Works with no internet. Robotic; for drafts and timing only.
  openai      OpenAI text-to-speech 'gpt-4o-mini-tts': natural, and you can TELL it how to feel (instructions). Needs OPENAI_API_KEY.
  elevenlabs  ElevenLabs voices: very natural, expressive; stability/style tuned per scene. Needs ELEVENLABS_API_KEY (+ ELEVENLABS_VOICE_ID).
  edge        Microsoft neural voices through the free `edge-tts` package (pip install edge-tts, internet). Natural, no API key.
  piper       local neural voice (pip install piper-tts, a downloaded .onnx voice, PIPER_MODEL=path). Offline, natural.
  files       your own recording or audio from ANY tool: put <segment id>.mp3|wav|m4a in a folder and pass --audio-dir.

openai / elevenlabs / edge / piper could not be run in the environment that wrote this file (no internet): the request code is
unit-tested with mocked responses only. Test one short scene first (see UPLOAD_GUIDE.md).
All backends end as a mono 44.1 kHz WAV, loudness-normalised. Spoken text is normalised by speak_text() (RMTI -> "R M T I", rho, tiers...).
"""
import ctypes, glob, json, os, re, shutil, subprocess, urllib.request, wave

# ----------------------------------------------------------------------- text normalisation for speech
_SPEAK = [
    (r"RMTI", "R M T I"), (r"\bHCC\b", "H C C"), (r"\bHBV\b", "H B V"), (r"\bHCV\b", "H C V"), (r"\bEAL\b", "E A L"),
    (r"\bALBI\b", "albi"), (r"\bBCLC\b", "B C L C"), (r"\bAFP\b", "A F P"), (r"\bMASLD\b", "masld"), (r"\bSVR\b", "S V R"),
    (r"\bFIB-4\b", "fib four"), (r"\baMAP\b", "a map"), (r"R₀", "R zero"), (r"ρ", "rho"),
    (r"×", " times "), (r"·", " "), (r"→", " to "), (r"−", " minus "), (r"≥", " at least "),
    (r"\bn = (\d+)", r"n equals \1"), (r"Apache-2\.0|Apache 2\.0", "Apache two point oh"), (r"\bdoi\b", "D O I"),
]


def speak_text(t):
    for a, b in _SPEAK:
        t = re.sub(a, b, t)
    return re.sub(r"\s+", " ", t).strip()


def _ffmpeg():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# ----------------------------------------------------------------------- flite via ctypes (offline, basic)
_LIBDIRS = ["/usr/lib/x86_64-linux-gnu/", "/usr/lib/", "/usr/local/lib/", "/usr/lib/aarch64-linux-gnu/"]
_flite = None


def _flite_load(voice="slt"):
    global _flite
    if _flite:
        return _flite
    def find(n):
        for d in _LIBDIRS:
            for f in glob.glob(d + n + ".so*"):
                return f
        raise FileNotFoundError(n)
    lib = ctypes.CDLL(find("libflite"), mode=ctypes.RTLD_GLOBAL)
    for n in ("libflite_usenglish", "libflite_cmulex"):
        ctypes.CDLL(find(n), mode=ctypes.RTLD_GLOBAL)
    v = ctypes.CDLL(find("libflite_cmu_us_" + voice), mode=ctypes.RTLD_GLOBAL)
    lib.flite_init()
    reg = getattr(v, "register_cmu_us_" + voice); reg.restype = ctypes.c_void_p
    lib.flite_text_to_speech.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p]
    _flite = (lib, reg(None))
    return _flite


def tts_flite(text, out_wav, direction=None, voice="slt"):
    lib, vp = _flite_load(voice)
    lib.flite_text_to_speech(speak_text(text).encode("utf-8"), vp, out_wav.encode("utf-8"))
    return out_wav


# ----------------------------------------------------------------------- natural / expressive backends
BASE_STYLE = ("Speak as a warm, clear and credible science communicator talking to an intelligent non-specialist. "
              "Natural conversational pace with small pauses between ideas, gentle emphasis on key numbers and on the words 'not', 'only' and 'except'. "
              "Say RMTI as the letters R, M, T, I. Never sound like a robot or an advertisement.")


def _post(url, headers, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def tts_openai(text, out_wav, direction=None):
    """gpt-4o-mini-tts takes free-text 'instructions': that is where the emotion and delivery come from."""
    key = os.environ["OPENAI_API_KEY"]
    payload = {"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"), "voice": os.environ.get("OPENAI_TTS_VOICE", "coral"),
               "input": speak_text(text), "instructions": BASE_STYLE + (" Delivery for this passage: " + direction if direction else ""),
               "response_format": "wav"}
    audio = _post("https://api.openai.com/v1/audio/speech", {"Authorization": "Bearer " + key, "Content-Type": "application/json"}, payload)
    open(out_wav, "wb").write(audio)
    return out_wav


def _eleven_settings(direction):
    d = (direction or "").lower()
    st = dict(stability=0.45, similarity_boost=0.80, style=0.35, use_speaker_boost=True)
    if any(w in d for w in ("serious", "careful", "calm", "measured")):
        st.update(stability=0.65, style=0.15)
    if any(w in d for w in ("warm", "welcom", "enthusias", "curious", "inspir")):
        st.update(stability=0.35, style=0.50)
    return st


def tts_elevenlabs(text, out_wav, direction=None):
    key = os.environ["ELEVENLABS_API_KEY"]; vid = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    payload = {"text": speak_text(text), "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"), "voice_settings": _eleven_settings(direction)}
    audio = _post(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                  {"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"}, payload)
    mp3 = out_wav + ".mp3"; open(mp3, "wb").write(audio)
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", out_wav], check=True); os.remove(mp3)
    return out_wav


def tts_edge(text, out_wav, direction=None):
    import asyncio, edge_tts            # pip install edge-tts
    mp3 = out_wav + ".mp3"
    comm = edge_tts.Communicate(speak_text(text), os.environ.get("EDGE_VOICE", "en-US-AriaNeural"), rate=os.environ.get("EDGE_RATE", "-4%"),
                                pitch=os.environ.get("EDGE_PITCH", "+0Hz"))
    asyncio.run(comm.save(mp3))
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", out_wav], check=True); os.remove(mp3)
    return out_wav


def tts_piper(text, out_wav, direction=None):
    subprocess.run(["piper", "--model", os.environ.get("PIPER_MODEL", "en_US-lessac-medium.onnx"), "--output_file", out_wav],
                   input=speak_text(text).encode(), check=True)
    return out_wav


BACKENDS = {"flite": tts_flite, "openai": tts_openai, "elevenlabs": tts_elevenlabs, "edge": tts_edge, "piper": tts_piper}


def wav_seconds(path):
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def _normalise(src, out_wav, slow=1.0):
    flt = (f"atempo={slow}," if slow != 1.0 else "") + "highpass=f=70,loudnorm=I=-18:TP=-2:LRA=9"
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", src, "-af", flt, "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", out_wav], check=True)
    return wav_seconds(out_wav)


def synth(text, out_wav, backend="flite", direction=None):
    """Synthesise, normalise loudness, return duration in seconds. Only the basic voice is slowed and band-limited."""
    raw = out_wav + ".raw.wav"
    BACKENDS[backend](text, raw, direction=direction)
    if backend == "flite":
        flt = "atempo=0.92,highpass=f=90,lowpass=f=7600,loudnorm=I=-18:TP=-2:LRA=9"
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", raw, "-af", flt, "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", out_wav], check=True)
        d = wav_seconds(out_wav)
    else:
        d = _normalise(raw, out_wav)
    os.remove(raw)
    return d


def find_audio(audio_dir, seg_id, video_key=None):
    """Your own audio: <dir>/<video key>/<id>.ext or <dir>/<id>.ext (mp3, wav, m4a, ogg, flac, aac)."""
    for base in ([os.path.join(audio_dir, video_key)] if video_key else []) + [audio_dir]:
        for ext in ("wav", "mp3", "m4a", "ogg", "flac", "aac", "WAV", "MP3", "M4A"):
            p = os.path.join(base, f"{seg_id}.{ext}")
            if os.path.exists(p):
                return p
    return None


def import_audio(src, out_wav):
    return _normalise(src, out_wav)
