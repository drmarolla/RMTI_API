# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Shared look for the Oncoclastics / RMTI site. Strictly RED, LIGHT BLUE and WHITE (navy only for text). No green, no gray, no washed-out tints.

    import oncoclastic_style as ui
    ui.apply()                    # after st.set_page_config; adds signature + RMTI logo at the bottom
    ui.apply(first_page=True)     # home page: signature only
    ui.governance_bar()           # one-line safety notice
Landing-page blocks: topbar(), hero_lp(), stats(), benefits(), industries(), path_cards(), equation_banner(), section().
"""
import base64
import html as _html
from pathlib import Path

import streamlit as st

# ---- palette -------------------------------------------------------------------------------------------------------
RED, RED_D, RED_L = "#d9262c", "#b81e24", "#ff6b73"        # primary action / energy
BLUE_A, BLUE_D, BLUE_L = "#1d6fd0", "#0f4fa8", "#6cb4f5"   # strong blue, deep blue, bright light blue
SKY, SKY2, LINE = "#eaf4ff", "#d3e8fb", "#b9d9f7"          # light-blue surfaces and borders
INK, BODY, MUTED = "#0b2545", "#1e3a5f", "#3f5f86"         # navy text only
BLUE, BLUE_M = SKY, SKY2                                   # legacy names (light surfaces)
TEAL = BLUE_A                                              # legacy names kept so old imports still work, now on-palette
AMBER, CORAL = RED_L, RED
ENGINE_VERSION = "v2.4.0"
YEAR, OWNER, ORCID = 2026, "Dr. Cesar Marolla", "0000-0001-8498-7380"
HOME_TITLE = "Overview & Oncoclastics"

_ROOT = Path(__file__).resolve().parent
_DEFAULT_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 64">'
    f'<rect x="6" y="38" width="9" height="18" rx="1.5" fill="{BLUE_L}"/>'
    f'<rect x="19" y="26" width="9" height="30" rx="1.5" fill="{RED}"/>'
    f'<rect x="32" y="34" width="9" height="22" rx="1.5" fill="{BLUE_A}"/>'
    f'<circle cx="23.5" cy="15" r="4.5" fill="{RED}"/>'
    f'<text x="54" y="37" font-family="Arial,Helvetica,sans-serif" font-size="27" fill="{INK}">RMTI</text>'
    f'<text x="55" y="54" font-family="Arial,Helvetica,sans-serif" font-size="10" letter-spacing="3" fill="{MUTED}">ONCOCLASTICS</text>'
    '</svg>')

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
.stApp,[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,%SKY% 0,#fff 420px) no-repeat,#fff;color:%BODY%;font-family:'Inter',system-ui,sans-serif}
html,body,.stApp{font-size:17px;line-height:1.65}
[data-testid="stAppViewContainer"]::before{content:"";position:fixed;top:0;left:0;right:0;height:6px;z-index:9999;background:linear-gradient(90deg,%RED% 0,%RED_L% 30%,%BLUE_A% 65%,%BLUE_L% 100%)}
header[data-testid="stHeader"]{background:rgba(255,255,255,.88);backdrop-filter:blur(8px)}
h1,h2,h3,h4{font-family:'Outfit','Inter',sans-serif;color:%INK%;letter-spacing:-.015em}
h1{font-weight:700;font-size:clamp(2.1rem,4.4vw,3.3rem);line-height:1.08}
h2{font-weight:600;font-size:clamp(1.55rem,2.6vw,2.15rem);margin-top:1.8rem}
h3{font-weight:600;font-size:1.3rem}
[data-testid="stMainBlockContainer"] h1:after{content:"";display:block;width:84px;height:6px;border-radius:4px;margin-top:.7rem;background:linear-gradient(90deg,%RED%,%BLUE_A%)}
p,li{color:%BODY%}
a{color:%BLUE_A%;font-weight:500}a:hover{color:%RED%}
[data-testid="stCaptionContainer"],.stCaption{color:%MUTED%}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1180px;padding-top:4.2rem;padding-bottom:3rem}
label,[data-testid="stWidgetLabel"] p{color:%INK%;font-weight:600}

/* ---------- sidebar menu ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff 0,%SKY% 100%);border-right:1px solid %LINE%}
[data-testid="stSidebarNav"]{padding-top:.2rem}
[data-testid="stSidebarNav"]::before{content:"RMTI  ONCOCLASTICS";display:block;padding:.4rem .9rem .9rem;font:700 .82rem 'Outfit',sans-serif;letter-spacing:.26em;color:%RED%;border-bottom:3px solid %RED%;margin:0 .6rem .7rem}
[data-testid="stSidebarNav"] ul{padding:0 .5rem;margin:0}
[data-testid="stSidebarNav"] li{margin:3px 0}
[data-testid="stSidebarNavLink"]{display:flex;text-decoration:none;padding:.62rem .95rem;min-height:0;border-radius:14px;font-size:1rem;font-weight:500;color:%INK%;border:1px solid transparent;transition:all .16s ease}
[data-testid="stSidebarNavLink"] span{line-height:1.25;color:inherit}
[data-testid="stSidebarNavLink"]:hover{background:%SKY2%;border-color:%LINE%;transform:translateX(3px)}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:linear-gradient(90deg,%RED%,%RED_L%);color:#fff;font-weight:700;box-shadow:0 8px 18px rgba(217,38,44,.30)}
[data-testid="stSidebarNavLink"][aria-current="page"] span{color:#fff}
/* first menu entry is the landing file (app.py.py): show a friendly label instead of "app.py" */
[data-testid="stSidebarNav"] li:first-child [data-testid="stSidebarNavLink"] span:last-child{font-size:0}
[data-testid="stSidebarNav"] li:first-child [data-testid="stSidebarNavLink"] span:last-child::after{content:"Start here";font-size:1rem}
[data-testid="stSidebarNavSeparator"],[data-testid="stNavSectionHeader"]{color:%BLUE_A%;font-weight:700;font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;margin-top:.8rem}

/* ---------- widgets ---------- */
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{border-radius:999px;font-weight:600;padding:.5rem 1.3rem;transition:transform .15s,box-shadow .15s,background .15s;background:#fff;color:%BLUE_A%;border:2px solid %BLUE_A%}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{background:%BLUE_A%;color:#fff;transform:translateY(-2px);box-shadow:0 10px 22px rgba(29,111,208,.30)}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:%RED%;color:#fff;border:2px solid %RED%}
.stButton>button[kind="primary"]:hover{background:%RED_D%;border-color:%RED_D%;box-shadow:0 10px 22px rgba(217,38,44,.35)}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:12px !important;border-color:%LINE% !important;background:#fff}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:%RED% !important;box-shadow:0 0 0 3px rgba(217,38,44,.18)}
[data-testid="stFileUploaderDropzone"]{background:%SKY%;border:2px dashed %BLUE_A%;border-radius:18px}
[data-testid="stExpander"]{border:1.5px solid %LINE%;border-radius:16px;background:#fff;overflow:hidden}
[data-testid="stExpander"] summary{font-weight:700;color:%INK%}
[data-testid="stExpander"]:hover{border-color:%RED%}
[data-testid="stMetric"]{background:#fff;border:1.5px solid %LINE%;border-top:5px solid %RED%;border-radius:16px;padding:.8rem 1.1rem;transition:transform .2s,box-shadow .2s}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 14px 28px rgba(11,37,69,.10)}
[data-testid="stMetricValue"]{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:600;color:%INK%}
[data-testid="stMetricLabel"] p{color:%MUTED%;font-weight:600}
[data-baseweb="tab-list"]{gap:.4rem}
[data-baseweb="tab"]{border-radius:999px;padding:.4rem 1.1rem;background:%SKY%;color:%INK%;font-weight:600}
[data-baseweb="tab"][aria-selected="true"]{background:%RED%;color:#fff}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
[data-testid="stDataFrame"],[data-testid="stTable"],[data-testid="stPlotlyChart"]{border:1.5px solid %LINE%;border-radius:16px;overflow:hidden;background:#fff}
code{background:%SKY%;color:%INK%;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th{background:%SKY2%;color:%INK%;text-align:left}
th,td{border:1px solid %LINE%;padding:.6rem .75rem;vertical-align:top}
[data-testid="stAlert"]{border-radius:16px;border:1.5px solid %LINE%;background:%SKY% !important;color:%INK%}
[data-testid="stAlert"] *{color:%INK% !important}
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),[data-testid="stAlert"]:has([data-testid="stAlertContentError"]){background:#ffe9ea !important;border-color:%RED%}
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]),[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]){background:%SKY% !important;border-color:%BLUE_A%}
[data-testid="stAlertContainer"]{background:transparent !important}

/* ---------- shared blocks ---------- */
.rm-card{background:#fff;border:1.5px solid %LINE%;border-left:6px solid %RED%;border-radius:16px;padding:1.1rem 1.4rem;margin:.6rem 0 1rem;box-shadow:0 6px 18px rgba(11,37,69,.06);transition:transform .2s,box-shadow .2s}
.rm-card:hover{box-shadow:0 14px 30px rgba(11,37,69,.12)}
.rm-card.soft{background:%SKY%;border-left-color:%BLUE_A%}
.rm-note{background:#ffe9ea;border-left:5px solid %RED%;border-radius:10px;padding:.7rem 1rem;color:%INK%;font-size:.95rem}
.rm-gov,.rm-strip{background:#ffe9ea;border:1.5px solid %RED_L%;border-left:6px solid %RED%;border-radius:12px;padding:.55rem 1rem;color:%INK%;font-size:.9rem;margin:.4rem 0 1rem}
.rm-kicker{color:%RED%;font-weight:700;letter-spacing:.2em;font-size:.78rem;text-transform:uppercase}
.rm-sym{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:%SKY%;border:1px solid %LINE%;border-radius:6px;padding:.05rem .45rem;color:%INK%;font-weight:600}
.rm-tools{display:flex;flex-wrap:wrap;gap:.5rem;margin:.3rem 0 1rem}
.rm-tools a{padding:.35rem .95rem;border:1.5px solid %BLUE_A%;border-radius:999px;text-decoration:none;color:%BLUE_A%;font-size:.92rem;background:#fff;font-weight:600;transition:all .15s}
.rm-tools a:hover{background:%BLUE_A%;color:#fff;transform:translateY(-1px)}
/* tool-page title band (style.hero) */
.rm-hero{background:linear-gradient(120deg,#fff 0,%SKY% 100%);border:1.5px solid %LINE%;border-left:10px solid %RED%;border-radius:20px;padding:1.2rem 1.6rem 1rem;margin-bottom:1rem;box-shadow:0 10px 26px rgba(29,111,208,.12)}
.rm-hero h1{margin:0;font-size:clamp(1.8rem,3.4vw,2.6rem);padding:0}.rm-hero h1:after{display:none}
.rm-sub{color:%MUTED%;font-size:1rem;margin:.3rem 0 .6rem}
.rm-chip{display:inline-block;border:1.5px solid %BLUE_A%;border-radius:999px;padding:2px 12px;margin:0 6px 4px 0;font-size:.8rem;color:%BLUE_A%;background:#fff;font-weight:600}
.rm-chip:first-of-type{background:%RED%;border-color:%RED%;color:#fff}

/* ---------- top bar ---------- */
.rm-top{display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap;padding:.5rem 0 .9rem}
.rm-top .links{display:flex;gap:1.05rem;flex:1;flex-wrap:wrap;justify-content:center}
.rm-top .links a{color:%INK%;font-weight:600;font-size:.9rem;white-space:nowrap;text-decoration:none;padding:.25rem 0;border-bottom:3px solid transparent;transition:border-color .15s,color .15s}
.rm-top .links a:hover{color:%RED%;border-color:%RED%}
.rm-btn{display:inline-block;padding:.65rem 1.4rem;border-radius:999px;font-weight:700;text-decoration:none !important;transition:transform .15s,box-shadow .15s;font-size:.95rem}
.rm-btn.r{background:%RED%;color:#fff !important;border:2px solid %RED%}.rm-btn.r:hover{background:%RED_D%;transform:translateY(-2px);box-shadow:0 12px 26px rgba(217,38,44,.38)}
.rm-btn.o{background:#fff;color:%BLUE_A% !important;border:2px solid %BLUE_A%}.rm-btn.o:hover{background:%BLUE_A%;color:#fff !important;transform:translateY(-2px);box-shadow:0 12px 26px rgba(29,111,208,.32)}
.rm-brand{display:flex;align-items:center;gap:.7rem}
.rm-brand .mk{display:flex;gap:3px;align-items:flex-end;height:34px}
.rm-brand .mk i{width:9px;border-radius:3px;display:block;transform-origin:bottom;animation:rmbar 2.4s ease-in-out infinite}
.rm-brand .mk i:nth-child(1){height:14px;background:%BLUE_L%}.rm-brand .mk i:nth-child(2){height:26px;background:%RED%;animation-delay:.25s}.rm-brand .mk i:nth-child(3){height:20px;background:%BLUE_A%;animation-delay:.5s}
.rm-brand b{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:700;font-size:1.5rem;line-height:1;color:%INK%}
.rm-brand small{display:block;letter-spacing:.32em;font-size:.62rem;color:%MUTED%;margin-top:3px}
@keyframes rmbar{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.68)}}

/* ---------- landing hero (copy LEFT, visual RIGHT, never overlapping) ---------- */
.rm-lp{position:relative;overflow:hidden;border-radius:30px;border:1.5px solid %LINE%;padding:2.8rem 2.8rem;background:linear-gradient(135deg,#fff 0,%SKY% 55%,%SKY2% 100%);animation:rmrise .7s ease both}
.rm-lp:before{content:"";position:absolute;inset:0;background:linear-gradient(115deg,transparent 52%,rgba(255,255,255,.85) 52%,rgba(255,255,255,.85) 70%,transparent 70%);pointer-events:none}
.rm-lp:after{content:"";position:absolute;right:-90px;bottom:-110px;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle,rgba(217,38,44,.20),transparent 70%);pointer-events:none}
.rm-lp .grid{position:relative;z-index:2;display:grid;grid-template-columns:1.1fr 1fr;gap:2.4rem;align-items:center}
.rm-lp h1{font-size:clamp(2rem,3.5vw,3rem);margin:.7rem 0 1rem;font-weight:700;line-height:1.08}
.rm-lp h1:after{display:none}
.rm-lp h1 em{font-style:normal;color:%RED%}
.rm-lp .lead{font-size:1.1rem;line-height:1.65;color:%BODY%;max-width:52ch}
.rm-lp .row{display:flex;gap:.8rem;margin-top:1.5rem;flex-wrap:wrap}
@media(max-width:900px){.rm-lp .grid{grid-template-columns:1fr}.rm-lp{padding:1.8rem 1.3rem}}
/* orbit visual */
.rm-orb{position:relative;width:min(100%,430px);aspect-ratio:1;margin:0 auto 3.2rem}
.rm-orb .ring{position:absolute;inset:7%;border:2.5px dashed %BLUE_L%;border-radius:50%;animation:rmspin 46s linear infinite}
.rm-orb .ring.b{inset:27%;border-color:%RED_L%;animation-direction:reverse;animation-duration:30s}
.rm-orb .sat{position:absolute;inset:7%;animation:rmspin 46s linear infinite}
.rm-orb .sat b{position:absolute;width:25%;aspect-ratio:1;margin:-12.5% 0 0 -12.5%;border-radius:50%;display:grid;place-items:center;color:#fff;font:600 clamp(1.2rem,2.6vw,1.8rem) 'Outfit',sans-serif;box-shadow:0 12px 24px rgba(11,37,69,.22);animation:rmspin 46s linear infinite reverse}
.rm-orb .sat b small{display:block;font:700 .46rem Inter,system-ui,sans-serif;letter-spacing:.03em;margin-top:-.15rem}
.rm-orb .sat b:nth-child(1){left:50%;top:0;background:%BLUE_A%}
.rm-orb .sat b:nth-child(2){left:100%;top:50%;background:%RED_L%}
.rm-orb .sat b:nth-child(3){left:50%;top:100%;background:%BLUE_D%}
.rm-orb .sat b:nth-child(4){left:0;top:50%;background:%BLUE_L%}
.rm-orb .core{position:absolute;inset:36%;border-radius:50%;display:grid;place-items:center;color:#fff;font:700 clamp(2.2rem,6vw,3.8rem) 'Outfit',sans-serif;background:radial-gradient(circle at 30% 28%,%RED_L%,%RED% 55%,%RED_D%);box-shadow:0 0 0 12px rgba(217,38,44,.14),0 0 0 28px rgba(217,38,44,.08),0 18px 40px rgba(217,38,44,.35);animation:rmpls 3.6s ease-in-out infinite}
.rm-orb .eq{position:absolute;left:50%;bottom:-16%;transform:translateX(-50%);background:#fff;border:2px solid %RED%;color:%INK%;border-radius:999px;padding:.35rem 1.1rem;font:600 clamp(.85rem,1.6vw,1.05rem) 'Outfit',Inter,system-ui,sans-serif;white-space:nowrap;box-shadow:0 10px 24px rgba(11,37,69,.16)}
.rm-orb .eq em{font-style:normal;color:%RED%}
@keyframes rmspin{to{transform:rotate(360deg)}}
@keyframes rmpls{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}
@keyframes rmrise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}

/* ---------- count-up stats ---------- */
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
.rm-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1.4rem 0 .4rem}
.rm-stat{background:#fff;border:1.5px solid %LINE%;border-radius:20px;padding:1.2rem 1.4rem;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;animation:rmrise .7s ease both}
.rm-stat:hover{transform:translateY(-5px);box-shadow:0 16px 32px rgba(11,37,69,.12)}
.rm-stat:before{content:"";position:absolute;left:0;top:0;width:100%;height:6px;background:var(--c,%RED%)}
.rm-stat .num{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:600;font-size:3rem;line-height:1.1;color:var(--c,%RED%);counter-reset:n var(--n);animation:rmcount 1.8s cubic-bezier(.2,.7,.2,1) forwards}
.rm-stat .num:after{content:counter(n) var(--suffix,"")}
.rm-stat .lbl{font-size:.9rem;color:%MUTED%;margin-top:.2rem;font-weight:500}
@keyframes rmcount{from{--n:0}to{--n:var(--to)}}

/* ---------- key-benefits panel (Infor-style) ---------- */
.rm-panel{position:relative;overflow:hidden;border-radius:30px;padding:2.4rem 2.2rem 2.6rem;margin:2.2rem 0;border:1.5px solid %LINE%;background:linear-gradient(135deg,%SKY% 0,#fff 45%,%SKY2% 100%)}
.rm-panel:before{content:"";position:absolute;inset:0;background:linear-gradient(118deg,transparent 58%,rgba(255,255,255,.8) 58%,rgba(255,255,255,.8) 78%,transparent 78%);pointer-events:none}
.rm-panel>*{position:relative}
.rm-eyebrow{font-size:.78rem;letter-spacing:.24em;text-transform:uppercase;color:%RED%;font-weight:700}
.rm-panel h2{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:300;font-size:clamp(1.8rem,3.2vw,2.7rem);margin:.3rem 0 1.6rem;line-height:1.15;color:%INK%}
.rm-panel h2 b{font-weight:600;color:%RED%}
.rm-bgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:1.1rem}
.rm-bc{background:#fff;border:1.5px solid %LINE%;border-radius:20px;padding:1.5rem 1.4rem;min-height:235px;position:relative;overflow:hidden;transition:transform .22s,box-shadow .22s,border-color .22s;animation:rmrise .7s ease both}
.rm-bc:before{content:"";position:absolute;left:0;top:0;height:100%;width:6px;background:var(--c,%RED%);transform:scaleY(.25);transform-origin:top;transition:transform .3s}
.rm-bc:hover{transform:translateY(-6px);border-color:var(--c,%RED%);box-shadow:0 20px 40px rgba(11,37,69,.14)}
.rm-bc:hover:before{transform:scaleY(1)}
.rm-bc .ico{width:48px;height:48px;border-radius:14px;display:grid;place-items:center;background:var(--c,%RED%);margin-bottom:.9rem}
.rm-bc .ico svg{width:26px;height:26px;stroke:#fff;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.rm-bc:hover .ico svg{animation:rmwig .7s ease}
.rm-bc h4{font:300 1.6rem/1.18 'Outfit',sans-serif;margin:0 0 .8rem;color:%INK%}
.rm-bc p{margin:0;font-size:.95rem;line-height:1.62;color:%BODY%}
.rm-bgrid .rm-bc:nth-child(2){animation-delay:.06s}.rm-bgrid .rm-bc:nth-child(3){animation-delay:.12s}.rm-bgrid .rm-bc:nth-child(4){animation-delay:.18s}
.rm-bgrid .rm-bc:nth-child(5){animation-delay:.24s}.rm-bgrid .rm-bc:nth-child(6){animation-delay:.30s}.rm-bgrid .rm-bc:nth-child(7){animation-delay:.36s}.rm-bgrid .rm-bc:nth-child(8){animation-delay:.42s}
@keyframes rmwig{0%,100%{transform:rotate(0)}30%{transform:rotate(-12deg) scale(1.1)}60%{transform:rotate(9deg)}}
.rm-ind{margin:2.6rem 0 1rem}.rm-ind h2{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:300;font-size:clamp(1.8rem,3.2vw,2.7rem);margin:.3rem 0 .8rem;color:%INK%;line-height:1.15}.rm-ind h2 b{font-weight:600;color:%BLUE_A%}
.rm-ind p{max-width:78ch;font-size:1.05rem}
/* tool cards */
.rm-sec{margin:2.4rem 0 .6rem}.rm-sec h2{margin:.2rem 0 0;font-weight:300;font-size:clamp(1.7rem,3vw,2.5rem)}.rm-sec p{color:%MUTED%;max-width:680px;margin:.3rem 0 0}
.rm-sec .k{font-size:.78rem;letter-spacing:.24em;text-transform:uppercase;color:%RED%;font-weight:700}
.rm-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.1rem;margin:1rem 0 1.6rem}
.rm-pc{display:block;border:1.5px solid %LINE%;border-radius:20px;padding:1.4rem;background:#fff;text-decoration:none !important;color:%INK% !important;position:relative;overflow:hidden;transition:transform .22s,box-shadow .22s,border-color .22s;animation:rmrise .7s ease both}
.rm-pc:hover{transform:translateY(-6px);box-shadow:0 20px 40px rgba(11,37,69,.14);border-color:var(--c,%RED%)}
.rm-pc .ico{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;background:var(--c,%RED%);margin-bottom:.9rem}
.rm-pc .ico svg{width:28px;height:28px;stroke:#fff;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.rm-pc:hover .ico svg{animation:rmwig .7s ease}
.rm-pc h4{margin:0 0 .3rem;font:400 1.3rem 'Outfit',sans-serif;color:%INK%}.rm-pc p{margin:0;color:%BODY%;font-size:.93rem;line-height:1.55}
.rm-pc .tg{display:inline-block;margin-top:.8rem;font-size:.74rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--c,%RED%)}
/* equation banner */
.rm-eq{background:linear-gradient(135deg,%RED% 0,%RED_D% 55%,%BLUE_D% 100%);color:#fff;border-radius:26px;padding:2rem 2.3rem;margin:1.2rem 0;position:relative;overflow:hidden;box-shadow:0 18px 40px rgba(217,38,44,.28)}
.rm-eq:after{content:"";position:absolute;right:-60px;top:-60px;width:240px;height:240px;border-radius:50%;background:radial-gradient(circle,rgba(108,180,245,.7),transparent 70%);animation:rmpls 5s ease-in-out infinite}
.rm-eq .fm{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:300;font-size:clamp(1.9rem,4.2vw,3rem);letter-spacing:.02em;color:#fff}.rm-eq .fm em{font-style:normal;font-weight:700;color:#fff;text-shadow:0 0 18px rgba(255,255,255,.55)}
.rm-eq .lg{display:flex;gap:1.3rem;flex-wrap:wrap;margin-top:.7rem;font-size:.92rem;color:#fff}
.rm-foot{margin-top:2.5rem;background:linear-gradient(90deg,%RED%,%BLUE_A%);color:#fff;padding:1.3rem 2rem;border-radius:20px;font-size:.9rem;text-align:center}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}.rm-stat .num{--n:var(--to)}}
@media (max-width:768px){.block-container,[data-testid="stMainBlockContainer"]{padding-left:.9rem;padding-right:.9rem}}
footer{visibility:hidden}
"""

_TOK = (("%RED_D%", RED_D), ("%RED_L%", RED_L), ("%RED%", RED), ("%BLUE_A%", BLUE_A), ("%BLUE_D%", BLUE_D), ("%BLUE_L%", BLUE_L),
        ("%SKY2%", SKY2), ("%SKY%", SKY), ("%LINE%", LINE), ("%INK%", INK), ("%BODY%", BODY), ("%MUTED%", MUTED))


def _css() -> str:
    css = _CSS
    for k, v in _TOK:
        css = css.replace(k, v)
    return css


def logo_svg() -> str:
    custom = _ROOT / "assets" / "rmti_logo.svg"
    return custom.read_text(encoding="utf-8") if custom.exists() else _DEFAULT_LOGO


LINE1 = f"Oncoclastics Platform · Risk Mechanism Theory Index (RMTI) engine {ENGINE_VERSION} · Apache-2.0"
LINE2 = f"For research use only. Not for clinical or diagnostic use. © {YEAR} {OWNER} · ORCID {ORCID}"


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
    css = _css()
    css += ('.block-container::after,[data-testid="stMainBlockContainer"]::after{content:"";display:block;'
            f'height:{110 if with_logo else 46}px;margin:3rem auto 0;'
            f'background:url(data:image/svg+xml;base64,{b64}) center/contain no-repeat}}')
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


def governance_bar() -> None:
    st.markdown('<div class="rm-gov"><b>Research prototype.</b> Synthetic or published aggregate values only. '
                'Do not enter patient data. Not a medical device; not for clinical decisions.</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------- landing components
_ICONS = {
    "calculator": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
    "liver": '<path d="M2.5 10c4-4.5 12-5.5 18.5-2 1 .6 1.2 1.9.5 2.9C19.5 14 15 19 9.5 18.5 6 18.2 3.5 16 2.5 13z"/><path d="M13 7.5c-.2 2.2 1 4 3.2 4.8"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M17 14c2.5 0 4 1.8 4 4"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    "book": '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 21V5M9 8h6"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "code": '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
    "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 15h18M8 4v16M16 4v16"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "gauge": '<path d="M4 16a8 8 0 1116 0"/><path d="M12 16l4-5"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-9"/><path d="M15 6h6v6"/>',
    "wave": '<path d="M2 12c3-6 5-6 8 0s5 6 8 0 3-3 4-2"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
}


def _e(s) -> str:
    return _html.escape(str(s))


def brand() -> str:
    return ('<div class="rm-brand"><div class="mk"><i></i><i></i><i></i></div>'
            '<div><b>RMTI</b><small>ONCOCLASTICS</small></div></div>')


def topbar(links, cta_label="Request API access", cta_href="https://orcid.org/0000-0001-8498-7380") -> None:
    """links = [(label, '/Url_Path'), ...]"""
    nav = "".join(f'<a href="{_e(h)}" target="_self">{_e(t)}</a>' for t, h in links)
    st.markdown(f'<div class="rm-top"><a href="/" target="_self" style="text-decoration:none">{brand()}</a><div class="links">{nav}</div>'
                f'<a class="rm-btn r" href="{_e(cta_href)}" target="_blank">{_e(cta_label)}</a></div>', unsafe_allow_html=True)


def hero_lp(eyebrow, title_html, lead, primary, secondary=None) -> None:
    """primary / secondary = (label, href). Copy on the left, animated orbit of L, E, V, rho on the right: nothing overlaps."""
    b2 = f'<a class="rm-btn o" href="{_e(secondary[1])}" target="_self">{_e(secondary[0])}</a>' if secondary else ""
    orb = ('<div class="rm-orb"><div class="ring"></div><div class="ring b"></div>'
           '<div class="sat"><b>L<small>LIKELIHOOD</small></b><b>E<small>EXPOSURE</small></b><b>V<small>VULNERABLE</small></b><b>ρ<small>RESILIENCE</small></b></div>'
           '<div class="core">R</div><div class="eq">R = L · E · V · (1 − <em>ρ</em>)</div></div>')
    st.markdown(f'<div class="rm-lp"><div class="grid"><div><div class="rm-kicker">{_e(eyebrow)}</div><h1>{title_html}</h1>'
                f'<p class="lead">{_e(lead)}</p><div class="row"><a class="rm-btn r" href="{_e(primary[1])}" target="_self">{_e(primary[0])}</a>{b2}</div></div>'
                f'<div>{orb}</div></div></div>', unsafe_allow_html=True)


def stats(items) -> None:
    """items = [(int_value, label, suffix, css_color)]; numbers count up on load."""
    cells = "".join(f'<div class="rm-stat" style="--to:{int(v)};--suffix:\'{_e(sfx)}\';--c:{c}"><div class="num"></div>'
                    f'<div class="lbl">{_e(lbl)}</div></div>' for v, lbl, sfx, c in items)
    st.markdown(f'<div class="rm-stats">{cells}</div>', unsafe_allow_html=True)


def benefits(eyebrow, title_html, items) -> None:
    """Key-benefits panel: red eyebrow, big light title, grid of white cards. items = [dict(icon, title, text, color)]."""
    cards = "".join(f'<div class="rm-bc" style="--c:{i.get("color", RED)}"><div class="ico"><svg viewBox="0 0 24 24" aria-hidden="true">{_ICONS[i["icon"]]}</svg></div>'
                    f'<h4>{_e(i["title"])}</h4><p>{_e(i["text"])}</p></div>' for i in items)
    st.markdown(f'<div class="rm-panel"><div class="rm-eyebrow">{_e(eyebrow)}</div><h2>{title_html}</h2><div class="rm-bgrid">{cards}</div></div>',
                unsafe_allow_html=True)


def industries(eyebrow, title_html, text) -> None:
    st.markdown(f'<div class="rm-ind"><div class="rm-eyebrow">{_e(eyebrow)}</div><h2>{title_html}</h2><p>{_e(text)}</p></div>', unsafe_allow_html=True)


def section(kicker: str, title: str, text: str = "", anchor: str = "") -> None:
    a = f'<a id="{anchor}"></a>' if anchor else ""
    p = f"<p>{_e(text)}</p>" if text else ""
    st.markdown(f'{a}<div class="rm-sec"><div class="k">{_e(kicker)}</div><h2>{_e(title)}</h2>{p}</div>', unsafe_allow_html=True)


def path_cards(items) -> None:
    """items = [dict(icon, title, text, tag, color, href)]. href is a page url_path such as '/Risk_Calculator'."""
    out = "".join(f'<a class="rm-pc" href="{_e(i["href"])}" target="_self" style="--c:{i.get("color", RED)}">'
                  f'<div class="ico"><svg viewBox="0 0 24 24" aria-hidden="true">{_ICONS[i["icon"]]}</svg></div>'
                  f'<h4>{_e(i["title"])}</h4><p>{_e(i["text"])}</p><span class="tg">{_e(i.get("tag", ""))}</span></a>' for i in items)
    st.markdown(f'<div class="rm-grid">{out}</div>', unsafe_allow_html=True)


def equation_banner() -> None:
    st.markdown('<div class="rm-eq"><div class="fm">R = <em>L</em> · <em>E</em> · <em>V</em> · (1 − <em>ρ</em>)</div>'
                '<div class="lg"><span><b>L</b> likelihood</span><span><b>E</b> exposure</span><span><b>V</b> vulnerability</span>'
                '<span><b>ρ</b> resilience</span></div></div>', unsafe_allow_html=True)


def foot(text: str) -> None:
    st.markdown(f'<div class="rm-foot">{_e(text)}</div>', unsafe_allow_html=True)
