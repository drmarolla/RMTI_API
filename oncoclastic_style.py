# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Shared look for the Oncoclastics / RMTI site: soft red, light blue and white, readable type.

    import oncoclastic_style as ui
    ui.apply()                    # after st.set_page_config; adds signature + RMTI logo at the bottom
    ui.apply(first_page=True)     # home page: signature only
    ui.governance_bar()           # one-line safety notice
To use your own logo, put an SVG (with xmlns) at assets/rmti_logo.svg. All colors are the tokens below.
"""
import base64
from pathlib import Path

import streamlit as st

RED, RED_D = "#c9505a", "#a93f48"                   # primary action color
BLUE, BLUE_M, LINE = "#eef5fb", "#d6e6f4", "#d9e4ef"  # soft light-blue surfaces and borders
INK, BODY, MUTED = "#1f2d3d", "#334155", "#5d6d80"     # headings, body text, secondary text
ENGINE_VERSION = "v2.4.0"
YEAR, OWNER, ORCID = 2026, "Dr. Cesar Marolla", "0000-0001-8498-7380"
HOME_TITLE = "Overview & Oncoclastics"

_ROOT = Path(__file__).resolve().parent
_DEFAULT_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 64">'
    f'<rect x="6" y="38" width="9" height="18" rx="1.5" fill="#5b9bd5"/>'
    f'<rect x="19" y="26" width="9" height="30" rx="1.5" fill="{RED}"/>'
    f'<rect x="32" y="34" width="9" height="22" rx="1.5" fill="#5b9bd5"/>'
    f'<circle cx="23.5" cy="15" r="4.5" fill="{RED}"/>'
    f'<text x="54" y="37" font-family="Arial,Helvetica,sans-serif" font-size="27" fill="{INK}">RMTI</text>'
    f'<text x="55" y="54" font-family="Arial,Helvetica,sans-serif" font-size="10" letter-spacing="3" fill="{MUTED}">ONCOCLASTICS</text>'
    '</svg>')

_CSS = """
.stApp,[data-testid="stAppViewContainer"]{background:#fff;color:%BODY%}
html,body,.stApp{font-size:17px;line-height:1.65}
h1,h2,h3,h4{color:%INK%;font-weight:600;letter-spacing:-.01em}
h1{font-size:2.05rem}h2{font-size:1.5rem;margin-top:1.8rem}h3{font-size:1.2rem}
p,li{color:%BODY%}
a{color:#3b78b4}
[data-testid="stCaptionContainer"],.stCaption{color:%MUTED%}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1100px;padding-top:4.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:%BLUE%;border-right:1px solid %LINE%}
[data-testid="stSidebarNav"]{padding-top:.4rem}
[data-testid="stSidebarNav"] ul{padding:0;margin:0;gap:0}
[data-testid="stSidebarNav"] li{margin:0}
[data-testid="stSidebarNavLink"]{padding:.28rem .7rem;margin:1px 0;min-height:0;border-radius:6px;font-size:.95rem}
[data-testid="stSidebarNavLink"] span{line-height:1.25}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:%BLUE_M%;font-weight:600}
[data-testid="stSidebarNavSeparator"],[data-testid="stNavSectionHeader"]{color:%MUTED%;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{background:%RED%;color:#fff;border:0;border-radius:8px;padding:.45rem 1.1rem}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{background:%RED_D%;color:#fff}
[data-testid="stExpander"]{border:1px solid %LINE%;border-radius:10px;background:#fff}
[data-testid="stExpander"] summary{font-weight:600;color:%INK%}
[data-testid="stMetric"]{background:%BLUE%;border:1px solid %LINE%;border-radius:10px;padding:.7rem 1rem}
[data-testid="stMetricValue"]{color:%INK%}
[data-baseweb="tab-list"]{gap:.25rem}
[data-baseweb="tab"]{border-radius:8px 8px 0 0}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid %LINE%;border-radius:8px}
code{background:#f1f5f9;color:%INK%;border-radius:5px}
table{border-collapse:collapse;width:100%;font-size:.93rem}
th{background:#eaf3fb;color:%INK%;text-align:left}
th,td{border:1px solid %LINE%;padding:.6rem .75rem;vertical-align:top}
.rm-card{background:#fff;border:1px solid %LINE%;border-left:5px solid %RED%;border-radius:10px;padding:1.1rem 1.4rem;margin:.6rem 0 1rem;box-shadow:0 2px 6px rgba(31,45,61,.04)}
.rm-card.soft{background:%BLUE%;border-left-color:#5b9bd5}
.rm-note{background:#fdf1f2;border-left:4px solid %RED%;border-radius:6px;padding:.7rem 1rem;color:#4a3338;font-size:.95rem}
.rm-gov{background:#fdf1f2;border:1px solid #f1ccd0;border-radius:8px;padding:.45rem .9rem;color:#5a3a40;font-size:.86rem;margin:0 0 1rem}
.rm-kicker{color:%RED%;font-weight:700;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
.rm-sym{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:%BLUE%;border:1px solid %BLUE_M%;border-radius:6px;padding:.05rem .45rem;color:%INK%;font-weight:600}
.rm-tools{display:flex;flex-wrap:wrap;gap:.45rem;margin:.3rem 0 1rem}
.rm-tools a{padding:.3rem .85rem;border:1px solid #c5d6e6;border-radius:999px;text-decoration:none;color:%INK%;font-size:.92rem;background:#fff}
.rm-tools a:hover{background:%BLUE_M%;border-color:#9fbbd6}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]){background:%BLUE% !important;border:1px solid %LINE%;color:%INK% !important}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) *{color:%INK% !important}
@media (max-width:768px){.block-container,[data-testid="stMainBlockContainer"]{padding-left:.9rem;padding-right:.9rem}}
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600&family=Inter:wght@400;500;600&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"]{font-family:'Inter',system-ui,sans-serif}
h1,h2,h3,h4{font-family:'Outfit','Inter',sans-serif;font-weight:300;letter-spacing:-.015em}
h1{font-size:clamp(2.1rem,4.4vw,3.4rem);line-height:1.1}
h2{font-size:clamp(1.55rem,2.6vw,2.1rem)}
header[data-testid="stHeader"]{background:rgba(255,255,255,.85);backdrop-filter:blur(8px)}
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{border-radius:999px;font-weight:500;transition:transform .15s,box-shadow .15s}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(201,80,90,.28)}
[data-testid="stMetric"]{background:#fff;border-radius:18px;transition:transform .2s,box-shadow .2s}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(31,45,61,.08)}
[data-testid="stMetricValue"]{font-family:'Outfit';font-weight:300}
[data-testid="stExpander"],[data-testid="stDataFrame"],[data-testid="stTable"],[data-testid="stPlotlyChart"]{border-radius:18px;overflow:hidden}
[data-baseweb="tab"]{border-radius:999px;padding:.35rem 1rem;background:%BLUE%}
[data-baseweb="tab"][aria-selected="true"]{background:%RED%;color:#fff}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
[data-testid="stSidebarNavLink"]{border-radius:12px;transition:background .15s,transform .15s}
[data-testid="stSidebarNavLink"]:hover{transform:translateX(2px)}
.rm-card{border-radius:18px;transition:transform .2s,box-shadow .2s}
.rm-card:hover{box-shadow:0 12px 28px rgba(31,45,61,.08)}
.rm-tools a{transition:transform .15s,border-color .15s,background .15s}
.rm-tools a:hover{transform:translateY(-1px);border-color:%RED%}
/* brand mark */
.rm-brand{display:flex;align-items:center;gap:.7rem;padding:.1rem 0 .7rem}
.rm-brand .mk{display:flex;gap:3px;align-items:flex-end;height:34px}
.rm-brand .mk i{width:9px;border-radius:3px;display:block;transform-origin:bottom;animation:rmbar 2.4s ease-in-out infinite}
.rm-brand .mk i:nth-child(1){height:14px;background:#5b9bd5}.rm-brand .mk i:nth-child(2){height:26px;background:%RED%;animation-delay:.25s}.rm-brand .mk i:nth-child(3){height:20px;background:#5b9bd5;animation-delay:.5s}
.rm-brand b{font-family:'Outfit';font-weight:500;font-size:1.5rem;line-height:1;color:%INK%}
.rm-brand small{display:block;letter-spacing:.32em;font-size:.62rem;color:%MUTED%;margin-top:3px}
@keyframes rmbar{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.68)}}
/* hero */
.rm-hero{position:relative;overflow:hidden;border-radius:28px;padding:3rem 3rem 2.8rem;min-height:400px;border:1px solid %LINE%;
 background:linear-gradient(120deg,#fff 0%,#f6f8fb 55%,#eaf3fb 100%);animation:rmrise .7s ease both}
.rm-hero .copy{position:relative;z-index:2}
.rm-hero h1{margin:.6rem 0 1rem;max-width:640px}
.rm-hero .lead{max-width:540px;font-size:1.08rem;line-height:1.65;color:%BODY%}
.rm-hero .cta{display:inline-block;margin-top:1.3rem;background:%RED%;color:#fff !important;text-decoration:none !important;padding:.8rem 1.7rem;border-radius:999px;font-weight:500;transition:transform .15s,box-shadow .15s}
.rm-hero .cta:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(201,80,90,.32)}
.rm-hero svg.art{position:absolute;right:-40px;top:0;height:100%;width:55%;min-width:360px;pointer-events:none}
@media(max-width:900px){.rm-hero{padding:2rem 1.3rem}.rm-hero svg.art{opacity:.22;width:90%}}
.art .f1{animation:rmfa 7s ease-in-out infinite}.art .f2{animation:rmfb 9s ease-in-out infinite}.art .f3{animation:rmfa 11s ease-in-out infinite reverse}
.art .spin{transform-origin:300px 220px;animation:rmspin 26s linear infinite}
.art .pls{transform-box:fill-box;transform-origin:center;animation:rmpls 3.6s ease-in-out infinite}
.art .dsh{stroke-dasharray:6 10;animation:rmdsh 3s linear infinite}
@keyframes rmfa{0%,100%{transform:translate(0,0)}50%{transform:translate(-18px,14px)}}
@keyframes rmfb{0%,100%{transform:translate(0,0)}50%{transform:translate(16px,-16px)}}
@keyframes rmspin{to{transform:rotate(360deg)}}
@keyframes rmpls{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}
@keyframes rmdsh{to{stroke-dashoffset:-64}}
@keyframes rmrise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
/* count-up stats */
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
.rm-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem;margin:1.3rem 0 .4rem}
.rm-stat{background:#fff;border:1px solid %LINE%;border-radius:18px;padding:1.1rem 1.3rem;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;animation:rmrise .7s ease both}
.rm-stat:hover{transform:translateY(-4px);box-shadow:0 14px 30px rgba(31,45,61,.09)}
.rm-stat:before{content:"";position:absolute;left:0;top:0;width:100%;height:4px;background:var(--c,%RED%)}
.rm-stat .num{font-family:'Outfit';font-weight:300;font-size:2.6rem;line-height:1.1;counter-reset:n var(--n);animation:rmcount 1.8s cubic-bezier(.2,.7,.2,1) forwards}
.rm-stat .num:after{content:counter(n) var(--suffix,"")}
.rm-stat .lbl{font-size:.86rem;color:%MUTED%;margin-top:.2rem}
@keyframes rmcount{from{--n:0}to{--n:var(--to)}}
/* pathway cards */
.rm-sec{margin:2.2rem 0 .6rem}.rm-sec .k{font-size:.75rem;letter-spacing:.2em;text-transform:uppercase;color:%RED%;font-weight:600}
.rm-sec h2{margin:.2rem 0 0}.rm-sec p{color:%MUTED%;max-width:680px;margin:.3rem 0 0}
.rm-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.1rem;margin:1rem 0 1.6rem}
.rm-pc{display:block;border:1px solid %LINE%;border-radius:20px;padding:1.4rem;background:#fff;text-decoration:none !important;color:%INK% !important;position:relative;overflow:hidden;
 transition:transform .22s,box-shadow .22s,border-color .22s;animation:rmrise .7s ease both}
.rm-pc:hover{transform:translateY(-6px);box-shadow:0 18px 38px rgba(31,45,61,.11);border-color:var(--c,%RED%)}
.rm-pc .ico{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;background:color-mix(in srgb,var(--c,%RED%) 12%,white);margin-bottom:.9rem}
.rm-pc .ico svg{width:28px;height:28px;stroke:var(--c,%RED%);fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.rm-pc:hover .ico svg{animation:rmwig .7s ease}
@keyframes rmwig{0%,100%{transform:rotate(0)}30%{transform:rotate(-10deg) scale(1.08)}60%{transform:rotate(8deg)}}
.rm-pc h4{margin:0 0 .3rem;font-size:1.2rem;font-weight:400;color:%INK%}.rm-pc p{margin:0;color:%MUTED%;font-size:.92rem;line-height:1.55}
.rm-pc .tg{display:inline-block;margin-top:.8rem;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--c,%RED%)}
.rm-grid .rm-pc:nth-child(2){animation-delay:.07s}.rm-grid .rm-pc:nth-child(3){animation-delay:.14s}.rm-grid .rm-pc:nth-child(4){animation-delay:.21s}.rm-grid .rm-pc:nth-child(5){animation-delay:.28s}.rm-grid .rm-pc:nth-child(6){animation-delay:.35s}
/* equation banner */
.rm-eq{background:linear-gradient(135deg,#0f2a4a,#17406e);color:#fff;border-radius:24px;padding:1.9rem 2.2rem;margin:1.2rem 0;position:relative;overflow:hidden}
.rm-eq:after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle,rgba(79,160,149,.55),transparent 70%);animation:rmpls 5s ease-in-out infinite}
.rm-eq .fm{font-family:'Outfit';font-weight:300;font-size:clamp(1.8rem,4vw,2.8rem);letter-spacing:.02em}.rm-eq .fm em{font-style:normal;color:#f2b84b}
.rm-eq .lg{display:flex;gap:1.3rem;flex-wrap:wrap;margin-top:.7rem;font-size:.88rem;color:#cfe0f3}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}.rm-stat .num{--n:var(--to)}}
footer{visibility:hidden}
"""


def logo_svg() -> str:
    custom = _ROOT / "assets" / "rmti_logo.svg"
    return custom.read_text(encoding="utf-8") if custom.exists() else _DEFAULT_LOGO


LINE1 = f"Oncoclastics Platform \u00b7 Risk Mechanism Theory Index (RMTI) engine {ENGINE_VERSION} \u00b7 Apache-2.0"
LINE2 = f"For research use only. Not for clinical or diagnostic use. \u00a9 {YEAR} {OWNER} \u00b7 ORCID {ORCID}"


def _footer_svg(with_logo: bool) -> str:
    top, logo = 0, ""
    if with_logo:
        b64 = base64.b64encode(logo_svg().encode("utf-8")).decode("ascii")
        logo = (f'<image x="250" y="8" width="200" height="52" preserveAspectRatio="xMidYMid meet" '
                f'href="data:image/svg+xml;base64,{b64}"/>')
        top = 64
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 {top + 46}">{logo}'
            f'<line x1="0" x2="700" y1="1" y2="1" stroke="{LINE}"/>'
            f'<text x="350" y="{top + 20}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="{INK}">{LINE1}</text>'
            f'<text x="350" y="{top + 38}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="11" fill="{MUTED}">{LINE2}</text>'
            f'</svg>')


def apply(first_page: bool = False) -> None:
    """Inject the shared look and the bottom signature (every page after the first also gets the RMTI logo)."""
    with_logo = not first_page
    b64 = base64.b64encode(_footer_svg(with_logo).encode("utf-8")).decode("ascii")
    css = _CSS
    for k, v in (("%RED_D%", RED_D), ("%RED%", RED), ("%BLUE_M%", BLUE_M), ("%BLUE%", BLUE), ("%LINE%", LINE),
                 ("%INK%", INK), ("%BODY%", BODY), ("%MUTED%", MUTED)):
        css = css.replace(k, v)
    css += ('.block-container::after,[data-testid="stMainBlockContainer"]::after{content:"";display:block;'
            f'height:{110 if with_logo else 46}px;margin:3rem auto 0;'
            f'background:url(data:image/svg+xml;base64,{b64}) center/contain no-repeat}}')
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


def governance_bar() -> None:
    st.markdown('<div class="rm-gov"><b>Research prototype.</b> Synthetic or published aggregate values only. '
                'Do not enter patient data. Not a medical device; not for clinical decisions.</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------- v3 components
import html as _html

_ICONS = {
    "calculator": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
    "liver": '<path d="M3 11c0-4 4-6 9-6s9 2 9 6c0 5-5 8-10 8-3 0-4-2-6-3-1-1-2-2-2-5z"/><path d="M12 9v4"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M17 14c2.5 0 4 1.8 4 4"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    "book": '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 21V5M9 8h6"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "code": '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
    "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 15h18M8 4v16M16 4v16"/>',
}
TEAL, AMBER, CORAL, NAVY, DEEP = "#4fa095", "#f2a100", "#e8553d", "#2b3a9e", "#00443f"


def brand() -> None:
    st.markdown('<div class="rm-brand"><div class="mk"><i></i><i></i><i></i></div><div><b>RMTI</b><small>ONCOCLASTICS</small></div></div>',
                unsafe_allow_html=True)


def _hero_art() -> str:
    return (f'<svg class="art" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<g class="f1"><rect x="330" y="40" width="300" height="110" rx="55" fill="{TEAL}" opacity=".9"/></g>'
            f'<g class="f2" style="mix-blend-mode:multiply"><circle cx="300" cy="230" r="150" fill="{AMBER}" opacity=".92"/>'
            f'<circle cx="420" cy="230" r="150" fill="#5b9bd5" opacity=".88"/><circle cx="540" cy="230" r="120" fill="{TEAL}" opacity=".8"/></g>'
            f'<circle cx="360" cy="230" r="56" fill="#fff"/>'
            f'<g class="spin"><path d="M300 90 A140 140 0 0 1 440 220" fill="none" stroke="{DEEP}" stroke-width="26" stroke-linecap="round"/></g>'
            f'<circle class="pls" cx="420" cy="110" r="24" fill="{NAVY}"/><circle class="pls" cx="420" cy="350" r="24" fill="{NAVY}" style="animation-delay:1.2s"/>'
            f'<g class="f3"><path d="M180 330 q60 -70 120 0 t120 0" fill="none" stroke="{CORAL}" stroke-width="5" stroke-linecap="round" class="dsh"/></g>'
            f'<circle class="pls" cx="150" cy="120" r="12" fill="{RED}" style="animation-delay:.6s"/></svg>')


def hero(eyebrow: str, title_html: str, lead: str, cta_label: str = "", cta_href: str = "#pathways") -> None:
    cta = f'<a class="cta" href="{_html.escape(cta_href)}">{_html.escape(cta_label)}</a>' if cta_label else ""
    st.markdown(f'<div class="rm-hero">{_hero_art()}<div class="copy"><div class="rm-kicker">{_html.escape(eyebrow)}</div>'
                f'<h1>{title_html}</h1><p class="lead">{_html.escape(lead)}</p>{cta}</div></div>', unsafe_allow_html=True)


def stats(items) -> None:
    """items = [(int_value, label, suffix, css_color)]; numbers count up on load."""
    cells = "".join(f'<div class="rm-stat" style="--to:{int(v)};--suffix:\'{_html.escape(sfx)}\';--c:{c}"><div class="num"></div>'
                    f'<div class="lbl">{_html.escape(lbl)}</div></div>' for v, lbl, sfx, c in items)
    st.markdown(f'<div class="rm-stats">{cells}</div>', unsafe_allow_html=True)


def section(kicker: str, title: str, text: str = "", anchor: str = "") -> None:
    a = f'<a id="{anchor}"></a>' if anchor else ""
    p = f"<p>{_html.escape(text)}</p>" if text else ""
    st.markdown(f'{a}<div class="rm-sec"><div class="k">{_html.escape(kicker)}</div><h2>{_html.escape(title)}</h2>{p}</div>',
                unsafe_allow_html=True)


def path_cards(items) -> None:
    """items = [dict(icon, title, text, tag, color, href)]. href is a page url_path such as '/Risk_Calculator'."""
    out = "".join(f'<a class="rm-pc" href="{_html.escape(i["href"])}" target="_self" style="--c:{i.get("color", RED)}">'
                  f'<div class="ico"><svg viewBox="0 0 24 24" aria-hidden="true">{_ICONS[i["icon"]]}</svg></div>'
                  f'<h4>{_html.escape(i["title"])}</h4><p>{_html.escape(i["text"])}</p><span class="tg">{_html.escape(i.get("tag", ""))}</span></a>'
                  for i in items)
    st.markdown(f'<div class="rm-grid">{out}</div>', unsafe_allow_html=True)


def equation_banner() -> None:
    st.markdown('<div class="rm-eq"><div class="fm">R = <em>L</em> · <em>E</em> · <em>V</em> · (1 − <em>ρ</em>)</div>'
                '<div class="lg"><span><b>L</b> likelihood</span><span><b>E</b> exposure</span><span><b>V</b> vulnerability</span>'
                '<span><b>ρ</b> resilience</span></div></div>', unsafe_allow_html=True)
