"""Render the three RMTI case-study videos (1280x720, 20 fps) + WebVTT captions + timing JSON.
usage:  python -m tools.make_videos liver|lung|breast   [--preview]
Silent by design: record your voice, then mux it with:  ffmpeg -i video.mp4 -i voice.mp3 -c:v copy -c:a aac out.mp4"""
import json, math, re, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tools.scenes3d import build, ORG
from tools.render3d import render
from tools.video_scripts import V

W, H, FPS = 1280, 720, 20
FD = "/usr/share/fonts/opentype/inter/"
_f = {}
def F(size, w="Bold"):
    k = (size, w)
    if k not in _f:
        _f[k] = ImageFont.truetype(f"{FD}Inter-{w}.otf", size)
    return _f[k]

NAVY, CRIM, SKY, BLUE, INK = (11, 18, 32), (225, 29, 72), (147, 197, 253), (37, 99, 235), (226, 232, 240)
TIERC = [(22, 163, 74), (202, 138, 4), (234, 88, 12), (220, 38, 38), (127, 29, 29)]
TIERN = ["Tier 1 · Low", "Tier 2 · Moderate", "Tier 3 · High", "Tier 4 · Severe", "Tier 5 · Critical"]
def tier_idx(r): return int(np.digitize(r, [0.05, 0.15, 0.35, 0.60]))
def ease(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t

def dur(s): return max(2.4, len(s.split()) / 2.5 + 0.8)
def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])

def bg_image():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([10, 17, 30]), np.array([22, 34, 56])
    a = (top * (1 - y) + bot * y) * np.ones((1, W, 1))
    xx, yy = np.meshgrid(np.arange(W), np.arange(H))
    g = np.exp(-(((xx - 900) / 430) ** 2 + ((yy - 340) / 330) ** 2))[..., None]
    a = a + g * np.array([14, 52, 66]) * 0.9
    v = 1 - 0.38 * (((xx - W / 2) / (W / 1.5)) ** 2 + ((yy - H / 2) / (H / 1.2)) ** 2)[..., None]
    return Image.fromarray(np.clip(a * v, 0, 255).astype(np.uint8))
BG = bg_image()

def timeline(v):
    secs = [("open", v["open"]), ("study", v["study"]), ("stages", [v["stage_intro"]] + v["stages"]), ("assess", v["assess"]),
            ("formula", v["formula"]), ("traj", v["traj"]), ("what", v["what"]), ("close", v["close"])]
    t, out, cues = 0.0, [], []
    for name, sents in secs:
        s0, wins = t, []
        for s in sents:
            d = dur(s); wins.append((t, t + d)); cues.append((t + 0.05, t + d - 0.15, s)); t += d
        hold = 4.5 if name == "close" else 0.5
        out.append(dict(name=name, start=s0, end=t + hold, sents=sents, wins=wins)); t += hold
    return out, cues, t

CACHE = {}
def model(organ, stage, yaw_i, pitch):
    k = (organ, stage, yaw_i)
    if k not in CACHE:
        ext = ORG[organ]["extent"][1 if stage >= 4 else 0]
        CACHE[k] = render(build(organ, stage), yaw=yaw_i, pitch=pitch, size=640, extent=ext)
    return CACHE[k].astype(np.float32)

def model_img(organ, stage_f, t, pitch, opacity=1.0):
    yaw = 14 * math.sin(2 * math.pi * t / 16.0)
    i0 = int(math.floor(yaw)); fr = yaw - i0
    def at(stage):
        a = model(organ, stage, i0, pitch); b = model(organ, stage, i0 + 1, pitch)
        return a * (1 - fr) + b * fr
    s0 = int(math.floor(stage_f)); fs = stage_f - s0
    arr = at(s0) if fs < 0.01 or s0 >= 4 else at(s0) * (1 - fs) + at(s0 + 1) * fs
    arr[..., 3] *= opacity
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

def rrect(d, box, r, fill, outline=None, w=1): d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)
def text(d, xy, s, size, fill=INK, w="Bold", anchor="la"): d.text(xy, s, font=F(size, w), fill=fill, anchor=anchor)

def chrome(img, d, label, sub, t, total, secs):
    # brand
    for i, (h, c) in enumerate([(26, SKY), (44, CRIM), (34, BLUE)]): d.rectangle([58 + i * 15, 70 - h, 69 + i * 15, 70], fill=c)
    text(d, (112, 28), "RMTI", 34, (255, 255, 255), "ExtraBold")
    text(d, (113, 66), "RISK MECHANISM THEORY INDEX", 12, (150, 170, 195), "SemiBold")
    # lower third
    rrect(d, [0, 626, 700, 690], 0, (12, 36, 56, 235)); d.rectangle([0, 626, 10, 690], fill=CRIM)
    text(d, (34, 634), label, 30, (255, 255, 255), "Bold"); text(d, (34, 668), sub, 15, (150, 190, 215), "Medium")
    # progress
    d.rectangle([0, 706, W, 720], fill=(15, 25, 42, 255))
    for s in secs: d.rectangle([int(s["start"] / total * W), 706, int(s["start"] / total * W) + 2, 720], fill=(60, 80, 110))
    d.rectangle([0, 706, int(t / total * W), 720], fill=CRIM)
    text(d, (W - 30, 686), "Research prototype · synthetic illustration · not a medical device", 14, (120, 140, 165), "Medium", "ra")

def card(d, box, title, body, accent, alpha=255, big=None):
    x0, y0, x1, y1 = box
    rrect(d, box, 18, (255, 255, 255, int(alpha * 0.07)), (255, 255, 255, int(alpha * 0.22)), 2)
    d.rounded_rectangle([x0, y0, x0 + 8, y1], 4, fill=accent + (alpha,))
    if big:
        text(d, (x0 + 28, y0 + 16), big, 50, (255, 255, 255, alpha), "ExtraBold")
        text(d, (x0 + 28, y0 + 78), title, 20, (170, 195, 220, alpha), "Medium")
    else:
        text(d, (x0 + 28, y0 + 18), title, 26, (255, 255, 255, alpha), "Bold")
        for i, ln in enumerate(wrap(d, body, F(20, "Regular"), x1 - x0 - 60)):
            text(d, (x0 + 28, y0 + 56 + i * 28), ln, 20, (185, 205, 225, alpha), "Regular")

def count(s, u):
    m = re.match(r"^([\d,\.]+)(.*)$", s)
    if not m or "–" in s: return s
    raw = m.group(1); dec = len(raw.split(".")[1]) if "." in raw else 0
    val = float(raw.replace(",", "")) * ease(u)
    num = f"{val:,.{dec}f}"
    return num + m.group(2)

def frame(v, t, secs, total):
    sec = next((s for s in secs if t < s["end"]), secs[-1])
    lt = t - sec["start"]
    si = max([i for i, w in enumerate(sec["wins"]) if t >= w[0]] or [0])
    sw = sec["wins"][si]; sf = (t - sw[0]) / max(sw[1] - sw[0], 1e-6)
    img = BG.copy(); d = ImageDraw.Draw(img, "RGBA")
    organ, pitch = v["organ"], v["pitch"]
    n = sec["name"]; label, sub, stage, op = "", "", 0, 1.0
    if n == "open":
        label, sub = "Introduction", "Dr. Cesar Marolla · Harvard University DCE"
        text(d, (58, 170), v["title"], 78, (255, 255, 255), "ExtraBold")
        text(d, (60, 262), "From tumor events to trajectory", 34, SKY, "SemiBold")
        for i, ln in enumerate(["Dr. Cesar Marolla", "Instructor, Harvard University", "Division of Continuing Education"]):
            text(d, (60, 360 + i * 34), ln, 24 if i else 28, (200, 215, 230) if i else (255, 255, 255), "Medium" if i else "Bold")
        rrect(d, [58, 500, 520, 566], 33, (255, 255, 255, 18), (255, 255, 255, 90), 2)
        text(d, (289, 533), "R = L · E · V · (1 − ρ)", 34, (255, 255, 255), "Bold", "mm")
    elif n == "study":
        label, sub, stage = "Published case study", v["cite"], 0
        text(d, (58, 120), "PUBLISHED CASE STUDY", 16, CRIM + (255,), "ExtraBold")
        for i, ln in enumerate(wrap(d, v["cite"].replace(" · ", ", "), F(34, "Bold"), 480)): text(d, (58, 148 + i * 44), ln, 34, (255, 255, 255), "Bold")
        for i, (big, lab) in enumerate(v["stats"]):
            u = (lt - 2.0 - i * 1.3) / 1.4
            if u > 0: card(d, [58, 268 + i * 106, 520, 360 + i * 106], lab, "", [CRIM, BLUE, SKY][i], int(255 * ease(u * 2)), count(big, u))
    elif n == "stages":
        k = si
        label, sub, stage = "Tumor stages" + (f" · Stage {k}" if k else ""), "Schematic model · rotate view", k
        if si and lt < 99: stage = (k - 1) + ease((t - sw[0]) / 0.9) if k > 1 else ease((t - sw[0]) / 0.9) * 1.0
        text(d, (58, 120), "TUMOR STAGES", 16, CRIM + (255,), "ExtraBold")
        for j in range(4):
            on = k >= j + 1
            rrect(d, [58 + j * 118, 150, 168 + j * 118, 190], 20, CRIM + (255,) if k == j + 1 else ((255, 255, 255, 40) if on else (255, 255, 255, 16)))
            text(d, (113 + j * 118, 170), f"{j + 1}", 20, (255, 255, 255) if on else (120, 140, 165), "Bold", "mm")
        if k == 0: text(d, (58, 250), "Four stages", 64, (255, 255, 255), "ExtraBold"); text(d, (60, 330), "from a small, contained tumor to distant spread", 26, SKY, "Medium")
        else:
            text(d, (58, 230), f"Stage {k}", 80, (255, 255, 255), "ExtraBold")
            desc = v["stages"][k - 1].split(": ", 1)[1]; desc = desc[0].upper() + desc[1:]
            a = int(255 * ease((t - sw[0]) / 0.8))
            for i, ln in enumerate(wrap(d, desc, F(32, "Medium"), 500)): text(d, (60, 336 + i * 46), ln, 32, (225, 235, 245, a), "Medium")
    elif n == "assess":
        label, sub, stage, op = "Data assessment", "Illustrative mapping of published data to RMTI levers", 2, 0.6
        text(d, (58, 120), "DATA ASSESSMENT", 16, CRIM + (255,), "ExtraBold"); text(d, (58, 150), "Published data → RMTI levers", 40, (255, 255, 255), "ExtraBold")
        for i, (sym, name, desc) in enumerate(v["levers"]):
            u = ease((lt - 3.0 - i * 2.2) / 0.9) if si >= 1 else 0
            col = {"L": BLUE, "E": CRIM, "V": (30, 41, 59), "ρ": SKY}[sym]
            if u > 0:
                y0 = 250 + i * 118; a = int(255 * u)
                rrect(d, [58 - int((1 - u) * 60), y0, 540, y0 + 100], 18, (255, 255, 255, int(a * 0.07)), (255, 255, 255, int(a * 0.2)), 2)
                d.ellipse([78 - int((1 - u) * 60), y0 + 20, 138 - int((1 - u) * 60), y0 + 80], fill=col + (a,)); text(d, (108 - int((1 - u) * 60), y0 + 50), sym, 34, (255, 255, 255, a), "Bold", "mm")
                text(d, (160 - int((1 - u) * 60), y0 + 16), name, 24, (255, 255, 255, a), "Bold")
                for j, ln in enumerate(wrap(d, desc, F(19, "Regular"), 360)[:2]): text(d, (160 - int((1 - u) * 60), y0 + 50 + j * 24), ln, 19, (185, 205, 225, a), "Regular")
    elif n == "formula":
        label, sub, stage, op = "The RMTI formula", "R = L · E · V · (1 − ρ), fixed five-band scale", 2, 0.22
        text(d, (W // 2, 150), "R = L · E · V · (1 − ρ)", 80, (255, 255, 255), "ExtraBold", "mm")
        toks = [("L", "Likelihood", BLUE), ("E", "Exposure", CRIM), ("V", "Vulnerability", (51, 65, 85)), ("ρ", "Resilience", SKY)]
        for i, (s, nme, c) in enumerate(toks):
            cx = 330 + i * 207; u = ease((lt - 1.2 - i * 0.7) / 0.6) if si >= 1 else 0
            if u > 0:
                d.ellipse([cx - 34, 220, cx + 34, 288], fill=c + (int(255 * u),)); text(d, (cx, 254), s, 36, (255, 255, 255, int(255 * u)), "Bold", "mm"); text(d, (cx, 310), nme, 18, (190, 205, 225, int(255 * u)), "Medium", "mm")
        text(d, (W // 2, 350), "illustrative inputs", 16, (120, 140, 165), "Medium", "mm")
        if si >= 2:
            u = ease((t - sw[0]) / 1.8); r = v["r0"] * u; ti = tier_idx(v["r0"])
            text(d, (W // 2, 440), f"R = {r:.3f}", 84, (255, 255, 255), "ExtraBold", "mm")
            x0, x1 = 160, 1120; seg = (x1 - x0) / 5
            for j in range(5):
                d.rectangle([x0 + j * seg, 530, x0 + (j + 1) * seg - 4, 556], fill=TIERC[j] + ((255 if j == ti else 90),))
                text(d, (x0 + j * seg + seg / 2, 580), TIERN[j], 15, (210, 220, 235, 255 if j == ti else 120), "SemiBold", "mm")
            edges = [0, 0.05, 0.15, 0.35, 0.60, 1.0]; px = x0 + ti * seg + (v["r0"] - edges[ti]) / (edges[ti + 1] - edges[ti]) * (seg - 4)
            d.polygon([(px, 520), (px - 11, 502), (px + 11, 502)], fill=(255, 255, 255)); text(d, (px, 488), f"{v['r0']:.3f}", 18, (255, 255, 255), "Bold", "mm")
    elif n == "traj":
        label, sub = "Trajectory over review cycles", "Synthetic example · intermediate cycles are interpolated", 
        x0, x1, y0, y1, ymax = 150, 1140, 170, 560, 0.12
        Y = lambda r: y1 - r / ymax * (y1 - y0)
        d.rectangle([x0, Y(0.05), x1, y1], fill=TIERC[0] + (50,)); d.rectangle([x0, y0, x1, Y(0.05)], fill=TIERC[1] + (46,))
        text(d, (x1 - 10, Y(0.025)), "Tier 1 · Low", 18, (134, 239, 172), "SemiBold", "rm"); text(d, (x1 - 10, Y(0.085)), "Tier 2 · Moderate", 18, (253, 224, 71), "SemiBold", "rm")
        d.line([x0, Y(0.05), x1, Y(0.05)], fill=(255, 255, 255, 150), width=2)
        text(d, (x0 - 14, Y(0.05)), "0.05", 16, (200, 215, 230), "Medium", "rm")
        for tick in (0, 0.03, 0.06, 0.09, 0.12): text(d, (x0 - 14, Y(tick)), f"{tick:.2f}", 15, (140, 160, 185), "Regular", "rm")
        d.line([x0, y1, x1, y1], fill=(160, 180, 205), width=2); d.line([x0, y0, x0, y1], fill=(160, 180, 205), width=2)
        text(d, (x0, 130), "Residual risk R", 22, (255, 255, 255), "Bold"); text(d, ((x0 + x1) // 2, y1 + 42), "Review cycle", 20, (200, 215, 230), "SemiBold", "mm")
        xs = [x0 + 90 + i * (x1 - x0 - 180) / 3 for i in range(4)]
        rs = [v["r0"] * (v["r1"] / v["r0"]) ** (i / 3) for i in range(4)]
        for i, x in enumerate(xs): text(d, (x, y1 + 18), f"{i + 1}", 18, (200, 215, 230), "SemiBold", "mm")
        p = 0 if si < 2 else (ease(sf * 1.4) if si == 2 else 1)
        shown = 1 if si >= 1 else 0
        pts = [(xs[0], Y(rs[0]))]
        for i in range(1, 4):
            lo = (i - 1) / 3
            if p > lo: f = min((p - lo) * 3, 1); pts.append((lerp(xs[i - 1], xs[i], f), lerp(Y(rs[i - 1]), Y(rs[i]), f)))
        if shown:
            if len(pts) > 1: d.line(pts, fill=(255, 255, 255), width=6, joint="curve")
            for i, (x, y) in enumerate(pts):
                end = i in (0, 3); rr = 13 if end else 8
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(CRIM if i == 0 else (22, 163, 74)) + (255,) if end else (255, 255, 255, 255), outline=(255, 255, 255), width=3)
            text(d, (xs[0] + 22, Y(rs[0]) - 40), f"R = {rs[0]:.3f}", 26, (255, 255, 255), "Bold")
            if p >= 0.999: text(d, (xs[3] + 4, Y(rs[3]) - 64), f"R = {rs[3]:.3f}", 26, (255, 255, 255), "Bold", "ma")
        if si >= 3: text(d, (W // 2, 112), f"Band two → band one, {v['traj_note']}", 26, SKY, "SemiBold", "mm")
    elif n == "what":
        label, sub = "What RMTI does", "One score · fixed bands · tracked across cycles", 
        text(d, (58, 120), "WHAT RMTI DOES", 16, CRIM + (255,), "ExtraBold")
        items = [("Quantify", "Risk as one score on a bounded 0–1 scale.", CRIM), ("Assess", "On five fixed, pre-registered bands.", BLUE), ("Track", "Vulnerability and resilience across review cycles.", SKY)]
        for i, (a, b, c) in enumerate(items):
            u = ease((lt - 1.5 - i * 2.4) / 0.8) if si == 0 else 1
            if u > 0: card(d, [58 + i * 395, 200, 420 + i * 395, 420], a, b, c, int(255 * u))
        if si >= 1: text(d, (W // 2, 520), "Treatment decisions stay with clinicians.", 40, (255, 255, 255, int(255 * ease((t - sw[0]) / 0.8))), "Bold", "mm")
    else:
        label, sub = "Closing", "Research prototype"
        text(d, (58, 130), "RESEARCH PROTOTYPE", 16, CRIM + (255,), "ExtraBold")
        text(d, (58, 160), "Uncalibrated.", 46, (255, 255, 255), "ExtraBold"); text(d, (58, 216), "Synthetic examples.", 46, (255, 255, 255), "ExtraBold"); text(d, (58, 272), "Not a medical device.", 46, (255, 255, 255), "ExtraBold")
        for i, ln in enumerate(wrap(d, "I am testing whether trajectory adds information beyond the current level.", F(28, "Medium"), 480)): text(d, (60, 360 + i * 40), ln, 28, SKY, "Medium")
        text(d, (60, 510), "Thank you for watching.", 30, (255, 255, 255), "Bold")
        rrect(d, [700, 140, 1230, 600], 20, (255, 255, 255, 16), (255, 255, 255, 60), 2)
        text(d, (728, 164), "PEER-REVIEWED AND CITED SOURCES", 15, CRIM + (255,), "ExtraBold")
        y = 200
        for r in v["refs"]:
            for ln in wrap(d, r, F(21, "Medium"), 470): text(d, (728, y), ln, 21, (215, 225, 238), "Medium"); y += 30
            y += 16
    show_model = n in ("open", "study", "stages", "assess")
    if show_model:
        m = model_img(organ, stage, t, pitch, op)
        img.paste(m.convert("RGB"), (590, 6), m.split()[3])
        d = ImageDraw.Draw(img, "RGBA")
    chrome(img, d, label, sub, t, total, secs)
    return img.convert("RGB")

def main(key, preview=False):
    v = V[key]; secs, cues, total = timeline(v)
    out = f"media/rmti_{key}_case_study"
    ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    with open(out + ".vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n" + "\n".join(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{s}\n" for i, (a, b, s) in enumerate(cues)))
    json.dump(dict(video=key, seconds=round(total, 2), sections=[dict(name=s["name"], start=round(s["start"], 2), sentences=[dict(text=t_, start=round(w[0], 2), end=round(w[1], 2)) for t_, w in zip(s["sents"], s["wins"])]) for s in secs]),
              open(out + "_timing.json", "w"), indent=1)
    if preview:
        for name, tt in (("open", 3), ("study", 9), ("stages", None), ("assess", None), ("formula", None), ("traj", None), ("what", None), ("close", None)):
            s = next(s for s in secs if s["name"] == name)
            t = tt if tt else (s["start"] + (s["end"] - s["start"]) * 0.8)
            frame(v, t, secs, total).save(f"/tmp/prev_{key}_{name}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out + ".mp4"], stdin=subprocess.PIPE)
    nf = int(total * FPS)
    for i in range(nf):
        p.stdin.write(frame(v, i / FPS, secs, total).tobytes())
        if i % 200 == 0: print(key, i, "/", nf, flush=True)
    p.stdin.close(); p.wait(); CACHE.clear()
    print("DONE", key, round(total, 1), "s", os.path.getsize(out + ".mp4") // 1024, "KB", flush=True)

if __name__ == "__main__":
    main(sys.argv[1], "--preview" in sys.argv)
