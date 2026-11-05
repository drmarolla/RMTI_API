"""
tools/make_reading_scripts.py  --  one printable PDF per video: scene-by-scene reading script for recording your own voice-over.
    pip install reportlab
    python tools/make_reading_scripts.py reading_scripts
Text and delivery notes come from storyboards.py, so they always match the videos. No patient data.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from storyboards import BOARDS, direction_for

EMAIL = "cesar.marolla@alumni.harvard.edu"
FD = "/usr/share/fonts/truetype/dejavu/"
for n, f in (("DV", "DejaVuSans.ttf"), ("DVB", "DejaVuSans-Bold.ttf"), ("DVI", "DejaVuSans-Oblique.ttf")):
    pdfmetrics.registerFont(TTFont(n, FD + f if os.path.exists(FD + f) else f))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")
TEAL, AMBER, GREY = colors.HexColor("#0b3b40"), colors.HexColor("#b45309"), colors.HexColor("#5b7075")
S = dict(
    h1=ParagraphStyle("h1", fontName="DVB", fontSize=20, leading=25, textColor=TEAL, spaceAfter=4),
    sub=ParagraphStyle("sub", fontName="DV", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=10),
    h2=ParagraphStyle("h2", fontName="DVB", fontSize=13.5, leading=18, textColor=TEAL, spaceBefore=8, spaceAfter=4),
    body=ParagraphStyle("body", fontName="DV", fontSize=10.5, leading=15, textColor=colors.HexColor("#1b2f33")),
    small=ParagraphStyle("small", fontName="DV", fontSize=9, leading=12, textColor=GREY),
    read=ParagraphStyle("read", fontName="DV", fontSize=14, leading=22, textColor=colors.black),
    dir=ParagraphStyle("dir", fontName="DVI", fontSize=10, leading=14, textColor=AMBER),
    meta=ParagraphStyle("meta", fontName="DVB", fontSize=9.5, leading=13, textColor=TEAL),
)
FOLDER = dict(explained="explained", liver="liver", flood_heat="flood_heat")
TITLE = dict(explained="Video 1 · RMTI explained", liver="Video 2 · Liver cancer (HCC) case studies", flood_heat="Video 3 · Flood and heat case studies")


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hints(text):
    h = []
    pairs = [("RMTI", "RMTI: say the letters R, M, T, I"), (r"\brho\b", "rho: say \"roh\""), (r"\bALBI\b", "ALBI: \"AL-bee\""), (r"\baMAP\b", "aMAP: \"a-map\""),
             (r"\bAFP\b", "AFP: A, F, P"), (r"\bHCC\b", "HCC: H, C, C"), (r"\bHBV\b", "HBV: H, B, V"), (r"\bHCV\b", "HCV: H, C, V"), (r"\bEAL\b", "EAL: E, A, L"),
             (r"\bLilongwe\b", "Lilongwe: \"lih-LONG-way\""), (r"\bMalawi\b", "Malawi: \"mah-LAH-wee\""), (r"\bBamako\b", "Bamako: \"bah-mah-KOH\""), (r"\bLagos\b", "Lagos: \"LAY-goss\""),
             (r"\bApache 2\.0\b", "Apache 2.0: \"Apache two point oh\""), (r"\d\.\d", "numbers: 0.57 is \"zero point five seven\"")]
    for pat, msg in pairs:
        if re.search(pat, text):
            h.append(msg)
    return "  ·  ".join(h)


def build(key, out_dir):
    stem, fn = BOARDS[key]
    segs = fn()
    path = os.path.join(out_dir, f"{stem}_READING_SCRIPT.pdf")

    def page(c, d):
        c.saveState(); c.setFont("DV", 8); c.setFillColor(GREY)
        c.drawString(0.8 * inch, 0.5 * inch, "Research prototype · not validated · not a medical device · no patient data")
        c.drawRightString(letter[0] - 0.8 * inch, 0.5 * inch, f"{TITLE[key]} · page {d.page}")
        c.restoreState()

    doc = BaseDocTemplate(path, pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.75 * inch, bottomMargin=0.85 * inch,
                          title=f"Reading script: {TITLE[key]}", author="Dr. Cesar Marolla")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=page)])
    st = [Paragraph(f"Reading script: {esc(TITLE[key])}", S["h1"]),
          Paragraph("Risk Mechanism Theory Index (RMTI) API · Core logic created and formulated by Dr. Cesar Marolla · Quantifying systemic risk in disaster science and oncology", S["sub"])]
    words = sum(len(s["text"].split()) for s in segs)
    st.append(Paragraph(f"{len(segs)} scenes · {words} words · about {words / 2.3 / 60:.1f} minutes of speaking at a calm pace", S["meta"]))
    st.append(Paragraph("How to record (one page, everything you need)", S["h2"]))
    steps = [
        "<b>Room.</b> Quiet room with soft things around you (curtains, sofa, a duvet over a chair). Switch off fans, notifications and phone vibration.",
        "<b>Microphone.</b> A phone voice recorder is fine. Hold it or prop it about a hand-width (10–15 cm) from your mouth, slightly to the side. Keep the same distance and the same room for every scene.",
        "<b>One file per scene.</b> Start recording, stay silent for one second, read the scene, stay silent for one second, stop. If you slip, pause, repeat the sentence and keep going; the best take is the one you save.",
        "<b>Voice.</b> Speak to one interested person, not to an audience. Calm pace, small breaths at commas and full stops, a gentle smile on the warm scenes, and slow down on the words <i>not</i>, <i>only</i> and <i>except</i>. Follow the delivery note above each scene.",
        f"<b>Name the files</b> exactly like the \"Save as\" line of each scene (for example <b>title.mp3</b>). Accepted: mp3, wav, m4a, ogg, flac, aac. Put them in a folder called <b>voice/{FOLDER[key]}/</b>.",
        f"<b>Build the video.</b> Either send me the files in the chat, or run <b>python tools/make_videos.py {key} --audio-dir voice</b>. The scene lengths follow your voice automatically, and captions, chapters and the closing contact line are rebuilt.",
        "<b>Free tools.</b> Audacity (computer), Voice Memos (iPhone), Recorder (Android). Trim nothing: one second of silence at each end is wanted.",
    ]
    t = Table([[Paragraph(f"{i + 1}.", S["meta"]), Paragraph(x, S["body"])] for i, x in enumerate(steps)], colWidths=[0.3 * inch, doc.width - 0.3 * inch])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#dfe7ea")),
                           ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f8f9"))]))
    st += [t, Spacer(1, 8), Paragraph("Before you start, read the limits scene aloud once: it is the most important one to say clearly. Nothing in these videos is medical or engineering advice, and no patient data appears.", S["small"]),
           PageBreak()]
    for i, sg in enumerate(segs, 1):
        est = len(sg["text"].split()) / 2.3
        head = Table([[Paragraph(f"Scene {i} of {len(segs)}", S["meta"]), Paragraph(f"Save as: <b>{sg['id']}.mp3</b>", S["meta"]), Paragraph(f"about {est:.0f} s", S["meta"]), Paragraph("☐ recorded", S["meta"])]],
                     colWidths=[1.4 * inch, 2.6 * inch, 1.0 * inch, doc.width - 5.0 * inch])
        head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e6f0f1")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        blk = [head, Spacer(1, 4), Paragraph("Delivery: " + esc(direction_for(sg["id"])), S["dir"]), Spacer(1, 5), Paragraph(esc(sg["text"]), S["read"])]
        h = hints(sg["text"])
        if h:
            blk += [Spacer(1, 5), Paragraph("Pronunciation: " + esc(h), S["small"])]
        st += [KeepTogether(blk), Spacer(1, 14)]
    st += [Spacer(1, 10), Paragraph("When you have recorded every scene, send the files or run the build command from page 1. Everything can be re-recorded and rebuilt at any time.", S["body"]),
           Spacer(1, 14), Paragraph(f"Contact: <b>{EMAIL}</b>", ParagraphStyle("c", fontName="DV", fontSize=11, textColor=TEAL))]
    doc.build(st)
    return path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "reading_scripts"
    os.makedirs(out, exist_ok=True)
    for k in BOARDS:
        print("wrote", build(k, out))
