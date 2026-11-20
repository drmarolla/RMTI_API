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
SKY, SKY2, LINE = "#dff0ff", "#bfe0ff", "#0b2545"          # flat light-blue surfaces; LINE is now the solid navy outline
AZURE = "#9fd5ff"                                          # the vivid light blue used for solid bands, buttons and tiles
INK, BODY, MUTED = "#0b2545", "#0b2545", "#27476f"         # navy text only
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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&family=Inter:wght@500;600;700;800&display=swap');
:root{--hs:5px 5px 0 %INK%;--hs-lg:8px 8px 0 %INK%}
.stApp,[data-testid="stAppViewContainer"]{background:#fff;color:%INK%;font-family:'Inter',system-ui,sans-serif;font-weight:500}
html,body,.stApp{font-size:17px;line-height:1.6}
[data-testid="stAppViewContainer"]::before{content:"";position:fixed;top:0;left:0;right:0;height:8px;z-index:9999;background:linear-gradient(90deg,%RED% 0 50%,%AZURE% 50% 100%)}
header[data-testid="stHeader"]{background:#fff;border-bottom:3px solid %INK%}
h1,h2,h3,h4{font-family:'Outfit','Inter',sans-serif;color:%INK%;letter-spacing:-.02em;font-weight:800}
h1{font-weight:900;font-size:clamp(2.3rem,4.8vw,3.6rem);line-height:1.05}
h2{font-size:clamp(1.7rem,2.9vw,2.4rem);margin-top:2rem}
h3{font-size:1.4rem}
[data-testid="stMainBlockContainer"] h1:after{content:"";display:block;width:120px;height:12px;margin-top:.8rem;background:%RED%;border:3px solid %INK%;border-radius:6px}
p,li,[data-testid="stMarkdownContainer"] p{color:%INK%}
[data-testid="stMarkdownContainer"] p{font-size:1.04rem}
a{color:%BLUE_D%;font-weight:700;text-decoration-thickness:2px}a:hover{color:%RED%}
[data-testid="stCaptionContainer"],.stCaption{color:%MUTED%;font-weight:500}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1180px;padding-top:4.4rem;padding-bottom:3rem}
label,[data-testid="stWidgetLabel"] p{color:%INK%;font-weight:700}

/* ---------- sidebar: solid blue, white text ---------- */
[data-testid="stSidebar"]{background:%BLUE_A%;border-right:4px solid %INK%}
[data-testid="stSidebarNav"]{padding-top:.2rem}
[data-testid="stSidebarNav"]::before{content:"RMTI  ONCOCLASTICS";display:block;padding:.5rem .9rem .9rem;font:900 .95rem 'Outfit',sans-serif;letter-spacing:.2em;color:#fff;border-bottom:4px solid #fff;margin:0 .6rem .6rem}
[data-testid="stSidebarNav"] ul{padding:0 .5rem;margin:0}
[data-testid="stSidebarNav"] li{margin:4px 0}
[data-testid="stSidebarNavLink"]{display:flex;text-decoration:none;padding:.6rem .9rem;min-height:0;border-radius:10px;font-size:1.02rem;font-weight:700;color:#fff;border:3px solid transparent;transition:transform .12s}
[data-testid="stSidebarNavLink"] span{line-height:1.25;color:inherit}
[data-testid="stSidebarNavLink"]:hover{background:%BLUE_D%;border-color:#fff;transform:translateX(3px)}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#fff;color:%RED%;font-weight:900;border-color:%INK%;box-shadow:4px 4px 0 %INK%}
[data-testid="stSidebarNavLink"][aria-current="page"] span{color:%RED%}
[data-testid="stSidebarNavSeparator"],[data-testid="stNavSectionHeader"]{color:%AZURE%;font-weight:900;font-size:.8rem;letter-spacing:.16em;text-transform:uppercase;margin-top:1rem}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] .stCaption{color:#fff}

/* ---------- widgets ---------- */
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{border-radius:12px;font-weight:800;padding:.5rem 1.3rem;background:%AZURE%;color:%INK%;border:3px solid %INK%;box-shadow:4px 4px 0 %INK%;transition:transform .1s,box-shadow .1s}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{background:%AZURE%;color:%INK%;border-color:%INK%;transform:translate(-2px,-2px);box-shadow:7px 7px 0 %INK%}
.stButton>button:active,[data-testid="stLinkButton"] a:active{transform:translate(3px,3px);box-shadow:1px 1px 0 %INK%}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"],[data-testid="stLinkButton"] a[kind="primary"]{background:%RED%;color:#fff;border:3px solid %INK%}
.stButton>button[kind="primary"]:hover{background:%RED_D%;color:#fff}
.stButton>button p,.stDownloadButton>button p{font-weight:800}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:10px !important;border:2.5px solid %INK% !important;background:#fff}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:%RED% !important;box-shadow:3px 3px 0 %RED%}
[data-testid="stFileUploaderDropzone"]{background:%SKY%;border:3px dashed %INK%;border-radius:14px}
[data-testid="stExpander"]{border:3px solid %INK%;border-radius:14px;background:#fff;overflow:hidden;box-shadow:var(--hs)}
[data-testid="stExpander"] summary{font-weight:800;color:%INK%;background:%AZURE%;font-size:1.05rem}
[data-testid="stMetric"]{background:#fff;border:3px solid %INK%;border-top:12px solid %RED%;border-radius:14px;padding:.8rem 1.1rem;box-shadow:var(--hs)}
[data-testid="stMetricValue"]{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:900;color:%INK%}
[data-testid="stMetricLabel"] p{color:%INK%;font-weight:800}
[data-baseweb="tab-list"]{gap:.5rem}
[data-baseweb="tab"]{border-radius:10px;padding:.45rem 1.2rem;background:#fff;color:%INK%;font-weight:800;border:3px solid %INK%}
[data-baseweb="tab"][aria-selected="true"]{background:%RED%;color:#fff;box-shadow:3px 3px 0 %INK%}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
[data-testid="stDataFrame"],[data-testid="stTable"],[data-testid="stPlotlyChart"]{border:3px solid %INK%;border-radius:14px;overflow:hidden;background:#fff}
code{background:%SKY%;color:%INK%;border-radius:6px;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:.98rem}
th{background:%AZURE%;color:%INK%;text-align:left;font-weight:800}
th,td{border:2px solid %INK%;padding:.6rem .75rem;vertical-align:top;color:%INK%}
[data-testid="stAlert"]{border-radius:14px;border:3px solid %INK%;background:%AZURE% !important;color:%INK%;box-shadow:4px 4px 0 %INK%}
[data-testid="stAlert"] *{color:%INK% !important;font-weight:600}
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),[data-testid="stAlert"]:has([data-testid="stAlertContentError"]){background:#ffd3d5 !important}
[data-testid="stAlertContainer"]{background:transparent !important}

/* ---------- shared blocks ---------- */
.rm-card{background:#fff;border:3px solid %INK%;border-left:14px solid %RED%;border-radius:14px;padding:1.1rem 1.4rem;margin:.6rem 0 1.2rem;box-shadow:var(--hs)}
.rm-card.soft{background:%SKY%;border-left-color:%BLUE_A%}
.rm-note{background:#ffd3d5;border:3px solid %INK%;border-radius:12px;padding:.7rem 1rem;color:%INK%;font-size:.98rem;font-weight:600}
.rm-gov,.rm-strip{background:#ffd3d5;border:3px solid %INK%;border-radius:12px;padding:.55rem 1rem;color:%INK%;font-size:.92rem;font-weight:600;margin:.4rem 0 1rem}
.rm-kicker{display:inline-block;background:%RED%;color:#fff;font-weight:800;letter-spacing:.16em;font-size:.78rem;text-transform:uppercase;padding:.25rem .75rem;border-radius:6px;border:2px solid %INK%}
.rm-sym{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:%AZURE%;border:2px solid %INK%;border-radius:6px;padding:.05rem .45rem;color:%INK%;font-weight:800}
.rm-tools{display:flex;flex-wrap:wrap;gap:.6rem;margin:.3rem 0 1rem}
.rm-tools a{padding:.35rem 1rem;border:3px solid %INK%;border-radius:10px;text-decoration:none;color:%INK%;font-size:.95rem;background:%AZURE%;font-weight:800;box-shadow:3px 3px 0 %INK%}
.rm-tools a:hover{background:%RED%;color:#fff}
/* tool-page title band (style.hero) */
.rm-hero{background:%AZURE%;border:3px solid %INK%;border-left:16px solid %RED%;border-radius:16px;padding:1.3rem 1.7rem 1.1rem;margin-bottom:1.2rem;box-shadow:var(--hs-lg)}
.rm-hero h1{margin:0;font-size:clamp(1.9rem,3.6vw,2.8rem);padding:0}.rm-hero h1:after{display:none}
.rm-sub{color:%INK%;font-size:1.05rem;margin:.4rem 0 .7rem;font-weight:600}
.rm-chip{display:inline-block;border:2px solid %INK%;border-radius:8px;padding:2px 12px;margin:0 6px 4px 0;font-size:.85rem;color:%INK%;background:#fff;font-weight:800}
.rm-chip:first-of-type{background:%RED%;color:#fff}

/* ---------- top bar / buttons ---------- */
.rm-top{display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap;padding:.5rem 0 .9rem}
.rm-top .links{display:flex;gap:1.05rem;flex:1;flex-wrap:wrap;justify-content:center}
.rm-top .links a{color:%INK%;font-weight:800;font-size:.92rem;white-space:nowrap;text-decoration:none;padding:.25rem 0;border-bottom:4px solid transparent}
.rm-top .links a:hover{color:%RED%;border-color:%RED%}
.rm-btn{display:inline-block;padding:.7rem 1.5rem;border-radius:12px;font-weight:800;text-decoration:none !important;font-size:1rem;border:3px solid %INK%;box-shadow:4px 4px 0 %INK%;transition:transform .1s,box-shadow .1s}
.rm-btn:hover{transform:translate(-2px,-2px);box-shadow:7px 7px 0 %INK%}
.rm-btn.r{background:%RED%;color:#fff !important}
.rm-btn.o{background:%AZURE%;color:%INK% !important}
.rm-brand{display:flex;align-items:center;gap:.7rem}
.rm-brand .mk{display:flex;gap:3px;align-items:flex-end;height:34px}
.rm-brand .mk i{width:9px;border-radius:3px;display:block;transform-origin:bottom;animation:rmbar 2.4s ease-in-out infinite}
.rm-brand .mk i:nth-child(1){height:14px;background:%BLUE_L%}.rm-brand .mk i:nth-child(2){height:26px;background:%RED%;animation-delay:.25s}.rm-brand .mk i:nth-child(3){height:20px;background:%BLUE_A%;animation-delay:.5s}
.rm-brand b{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:900;font-size:1.5rem;line-height:1;color:%INK%}
.rm-brand small{display:block;letter-spacing:.32em;font-size:.62rem;color:%MUTED%;margin-top:3px;font-weight:700}
@keyframes rmbar{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.68)}}

/* ---------- landing hero: solid red, white type, orbit on a white card ---------- */
.rm-orb{width:min(100%,440px);margin:0 auto}
.rm-orb svg{display:block;width:100%;height:auto;overflow:visible;shape-rendering:geometricPrecision;text-rendering:geometricPrecision}
.rm-orb .spin{transform-origin:230px 230px;animation:rmspin 46s linear infinite}
.rm-orb .spin.rev{animation-direction:reverse;animation-duration:30s}
.rm-orb .cs{transform-box:fill-box;transform-origin:center;animation:rmspin 46s linear infinite reverse}
.rm-orb .core{transform-box:fill-box;transform-origin:center;animation:rmpls 3.6s ease-in-out infinite}
.rm-orb text{font-family:'Outfit',Inter,system-ui,sans-serif;paint-order:normal}
.rm-lp{position:relative;overflow:hidden;border-radius:28px;border:4px solid %INK%;padding:3rem 2.8rem;background:%RED%;box-shadow:var(--hs-lg);animation:rmrise .6s ease both}
.rm-lp .grid{position:relative;z-index:2;display:grid;grid-template-columns:1.1fr 1fr;gap:2.4rem;align-items:center}
.rm-lp .orbwrap{background:#fff;border:4px solid %INK%;border-radius:24px;box-shadow:8px 8px 0 %INK%;padding:1rem .6rem .4rem}
.rm-lp .rm-kicker{background:#fff;color:%RED%}
.rm-lp h1{font-size:clamp(2.3rem,4.2vw,3.7rem);margin:1rem 0 1.1rem;font-weight:900;line-height:1.1;color:#fff}
.rm-lp h1:after{display:none}
.rm-lp h1 em{font-style:normal;background:%AZURE%;color:%INK%;padding:.02em .2em;border-radius:10px;box-decoration-break:clone;-webkit-box-decoration-break:clone;line-height:1.25}
.rm-lp .lead{font-size:1.25rem;line-height:1.55;color:#fff;max-width:52ch;font-weight:600}
.rm-lp .row{display:flex;gap:1rem;margin-top:1.8rem;flex-wrap:wrap}
.rm-lp .rm-btn.r{background:#fff;color:%RED% !important}
.rm-lp .rm-btn.o{background:%AZURE%;color:%INK% !important}
@media(max-width:900px){.rm-lp .grid{grid-template-columns:1fr}.rm-lp{padding:1.8rem 1.2rem}}
@keyframes rmspin{to{transform:rotate(360deg)}}
@keyframes rmpls{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}
@keyframes rmrise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

/* ---------- count-up stats: four solid tiles ---------- */
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
.rm-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1.3rem;margin:2rem 0 .8rem}
.rm-stat{border:4px solid %INK%;border-radius:18px;padding:1.2rem 1.4rem;box-shadow:var(--hs);background:#fff;color:%INK%;transition:transform .12s,box-shadow .12s;animation:rmrise .6s ease both}
.rm-stat:nth-child(1){background:%RED%;color:#fff}.rm-stat:nth-child(2){background:%AZURE%}.rm-stat:nth-child(4){background:%BLUE_A%;color:#fff}
.rm-stat:hover{transform:translate(-3px,-3px);box-shadow:9px 9px 0 %INK%}
.rm-stat .num{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:900;font-size:4rem;line-height:1.05;color:inherit;counter-reset:n var(--n);animation:rmcount 1.6s cubic-bezier(.2,.7,.2,1) forwards}
.rm-stat .num:after{content:counter(n) var(--suffix,"")}
.rm-stat .lbl{font-size:1rem;margin-top:.2rem;font-weight:700;color:inherit}
@keyframes rmcount{from{--n:0}to{--n:var(--to)}}

/* ---------- key-benefits panel ---------- */
.rm-panel{position:relative;border-radius:28px;padding:2.6rem 2.2rem 2.8rem;margin:2.6rem 0;border:4px solid %INK%;background:%AZURE%;box-shadow:var(--hs-lg)}
.rm-eyebrow{display:inline-block;font-size:.8rem;letter-spacing:.2em;text-transform:uppercase;color:#fff;background:%RED%;font-weight:800;padding:.25rem .8rem;border-radius:6px;border:2px solid %INK%}
.rm-panel h2{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:900;font-size:clamp(2rem,3.6vw,3rem);margin:.8rem 0 1.8rem;line-height:1.12;color:%INK%}
.rm-panel h2 b,.rm-ind h2 b,.rm-sec h2 b{font-weight:900;color:#fff;background:%RED%;padding:0 .2em;border-radius:8px}
.rm-bgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:1.3rem}
.rm-bc{background:#fff;border:3px solid %INK%;border-radius:18px;padding:1.5rem 1.4rem;min-height:240px;box-shadow:var(--hs);transition:transform .12s,box-shadow .12s;animation:rmrise .6s ease both}
.rm-bc:hover{transform:translate(-3px,-3px);box-shadow:9px 9px 0 %INK%}
.rm-bc .ico{width:54px;height:54px;border-radius:14px;display:grid;place-items:center;background:var(--c,%RED%);border:3px solid %INK%;margin-bottom:1rem}
.rm-bc .ico svg{width:28px;height:28px;stroke:#fff;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.rm-bc:hover .ico svg{animation:rmwig .7s ease}
.rm-bc h4{font:800 1.4rem/1.18 'Outfit',sans-serif;margin:0 0 .7rem;color:%INK%}
.rm-bc p{margin:0;font-size:1.02rem;line-height:1.55;color:%INK%;font-weight:500}
.rm-bgrid .rm-bc:nth-child(2){animation-delay:.05s}.rm-bgrid .rm-bc:nth-child(3){animation-delay:.1s}.rm-bgrid .rm-bc:nth-child(4){animation-delay:.15s}
.rm-bgrid .rm-bc:nth-child(5){animation-delay:.2s}.rm-bgrid .rm-bc:nth-child(6){animation-delay:.25s}.rm-bgrid .rm-bc:nth-child(7){animation-delay:.3s}.rm-bgrid .rm-bc:nth-child(8){animation-delay:.35s}
@keyframes rmwig{0%,100%{transform:rotate(0)}30%{transform:rotate(-12deg) scale(1.1)}60%{transform:rotate(9deg)}}
.rm-ind{margin:2.8rem 0 1rem}.rm-ind h2{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:900;font-size:clamp(2rem,3.6vw,3rem);margin:.8rem 0 .8rem;color:%INK%;line-height:1.12}
.rm-ind h2 b{background:%BLUE_A%}
.rm-ind p{max-width:78ch;font-size:1.12rem;font-weight:500}
/* tool cards */
.rm-sec{margin:2.8rem 0 .6rem}.rm-sec h2{margin:.7rem 0 0;font-weight:900;font-size:clamp(1.9rem,3.4vw,2.8rem)}.rm-sec p{color:%INK%;max-width:680px;margin:.4rem 0 0;font-size:1.08rem;font-weight:500}
.rm-sec .k{display:inline-block;font-size:.8rem;letter-spacing:.2em;text-transform:uppercase;color:#fff;background:%RED%;font-weight:800;padding:.25rem .8rem;border-radius:6px;border:2px solid %INK%}
.rm-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.3rem;margin:1.2rem 0 1.8rem}
.rm-pc{display:block;border:3px solid %INK%;border-radius:18px;padding:1.4rem;background:#fff;text-decoration:none !important;color:%INK% !important;box-shadow:var(--hs);transition:transform .12s,box-shadow .12s,background .12s;animation:rmrise .6s ease both}
.rm-pc:hover{transform:translate(-3px,-3px);box-shadow:9px 9px 0 %INK%;background:%AZURE%}
.rm-pc .ico{width:56px;height:56px;border-radius:14px;display:grid;place-items:center;background:var(--c,%RED%);border:3px solid %INK%;margin-bottom:1rem}
.rm-pc .ico svg{width:30px;height:30px;stroke:#fff;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.rm-pc:hover .ico svg{animation:rmwig .7s ease}
.rm-pc h4{margin:0 0 .35rem;font:800 1.4rem 'Outfit',sans-serif;color:%INK%}.rm-pc p{margin:0;color:%INK%;font-size:1rem;line-height:1.5;font-weight:500}
.rm-pc .tg{display:inline-block;margin-top:.9rem;font-size:.76rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#fff;background:var(--c,%RED%);padding:.2rem .65rem;border-radius:6px;border:2px solid %INK%}
/* equation banner */
.rm-eq{background:%BLUE_A%;color:#fff;border:4px solid %INK%;border-radius:24px;padding:2.2rem 2.4rem;margin:1.6rem 0;box-shadow:var(--hs-lg)}
.rm-eq .fm{font-family:'Outfit',Inter,system-ui,sans-serif;font-weight:800;font-size:clamp(2rem,4.6vw,3.4rem);letter-spacing:.01em;color:#fff}
.rm-eq .fm em{font-style:normal;font-weight:900;color:#fff;background:%RED%;border:3px solid %INK%;border-radius:10px;padding:0 .22em;margin:0 .04em}
.rm-eq .lg{display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:1rem;font-size:1.02rem;color:#fff;font-weight:700}
.rm-foot{margin-top:2.5rem;background:%RED%;color:#fff;border:4px solid %INK%;padding:1.3rem 2rem;border-radius:18px;font-size:.98rem;font-weight:700;text-align:center;box-shadow:var(--hs)}
/* ---------- never truncate text in Streamlit metrics ---------- */
[data-testid="stMetric"] *{white-space:normal !important;overflow:visible !important;text-overflow:clip !important;overflow-wrap:anywhere}
[data-testid="stMetricValue"]{font-size:clamp(1.4rem,2.2vw,2.1rem);line-height:1.2}

/* ---------- clinical KPI cards ---------- */
.rm-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:1.1rem;margin:.8rem 0 1.4rem}
.rm-kpi{background:#fff;border:3px solid %INK%;border-top:12px solid var(--c,%RED%);border-radius:14px;padding:.9rem 1.1rem;display:flex;flex-direction:column;gap:.35rem;min-width:0;box-shadow:var(--hs)}
.rm-kpi .t{font:800 .8rem Inter,system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:%INK%}
.rm-kpi .v{font:900 clamp(1.7rem,2.6vw,2.4rem)/1.12 'Outfit',Inter,system-ui,sans-serif;color:%INK%;overflow-wrap:anywhere}
.rm-kpi .d{font-size:.95rem;font-weight:800;color:%BLUE_D%}
.rm-kpi .s{font-size:.9rem;color:%MUTED%;line-height:1.4;font-weight:600}
.rm-tc{display:inline-block;padding:.22rem .7rem;border-radius:8px;border:2px solid %INK%;font-weight:800;font-size:.95rem;line-height:1.25}
.rm-tier-pair{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem}
.rm-tier-pair .ar{font-weight:900;color:%INK%}

/* ---------- clinical interpretation box ---------- */
.rm-interp{background:#fff;border:3px solid %INK%;border-left:16px solid %BLUE_A%;border-radius:14px;padding:1.2rem 1.5rem;margin:.8rem 0 1.4rem;box-shadow:var(--hs)}
.rm-interp h4{margin:0 0 .5rem;font:900 1.3rem 'Outfit',Inter,system-ui,sans-serif;color:%INK%}
.rm-interp p{margin:.45rem 0;font-size:1.04rem;line-height:1.6;color:%INK%}
.rm-interp b.n{color:#fff;background:%RED%;padding:0 .3em;border-radius:5px}
.rm-interp .cav{font-size:.9rem;color:%MUTED%;border-top:3px solid %AZURE%;padding-top:.5rem;margin-top:.7rem;font-weight:600}

/* ---------- evidence list ---------- */
.rm-refs{margin:.3rem 0 .8rem;padding:0;list-style:none}
.rm-refs li{padding:.7rem .9rem;border:2.5px solid %INK%;border-radius:12px;margin:.55rem 0;font-size:.98rem;line-height:1.5;background:#fff}
.rm-refs .stt{display:inline-block;background:%AZURE%;border:2px solid %INK%;border-radius:6px;padding:0 .55rem;font-size:.72rem;font-weight:800;color:%INK%;margin-right:.4rem;letter-spacing:.04em;text-transform:uppercase}
.rm-refs a{font-weight:800}

/* ---------- one persistent disclaimer bar ---------- */
.rm-bar{position:fixed;left:0;right:0;bottom:0;z-index:100;background:%INK%;border-top:5px solid %RED%;color:#fff;font-size:.84rem;line-height:1.35;padding:.5rem 1rem;display:flex;flex-wrap:wrap;gap:.2rem .8rem;align-items:center;justify-content:center;text-align:center;font-weight:600}
.rm-bar b{color:#fff}
.rm-bar .tg{background:%RED%;color:#fff;padding:.14rem .65rem;border-radius:6px;letter-spacing:.08em;font-size:.72rem;font-weight:800;white-space:nowrap}
.stApp:has(.rm-bar) [data-testid="stMainBlockContainer"]{padding-bottom:6rem}
.stApp:has(.rm-bar) .rm-gov,.stApp:has(.rm-bar) .rm-strip{display:none !important}
.stApp:has([data-testid="stSidebar"][aria-expanded="true"]) .rm-bar{left:21rem}
@media (max-width:991px){.stApp:has([data-testid="stSidebar"][aria-expanded="true"]) .rm-bar{left:0}}
/* persistent top-right call to action (container key rm_cta) */
.st-key-rm_cta{position:fixed;top:.5rem;right:4.6rem;z-index:1000002;width:auto !important}
.st-key-rm_cta button{background:%RED% !important;color:#fff !important;border:3px solid %INK% !important;border-radius:10px !important;font-weight:800 !important;padding:.25rem 1.1rem !important;min-height:2.3rem;box-shadow:3px 3px 0 %INK% !important}
.st-key-rm_cta button:hover{background:%RED_D% !important}
.st-key-rm_cta button p{color:#fff !important;font-size:.9rem}
@media (max-width:640px){.st-key-rm_cta{right:3.2rem}.st-key-rm_cta button{padding:.2rem .7rem !important}}
@media (max-width:768px){.rm-bar{font-size:.74rem}}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}.rm-stat .num{--n:var(--to)}}
@media (max-width:768px){.block-container,[data-testid="stMainBlockContainer"]{padding-left:.9rem;padding-right:.9rem}}
footer{visibility:hidden}
"""

_TOK = (("%RED_D%", RED_D), ("%RED_L%", RED_L), ("%RED%", RED), ("%BLUE_A%", BLUE_A), ("%BLUE_D%", BLUE_D), ("%BLUE_L%", BLUE_L),
        ("%SKY2%", SKY2), ("%SKY%", SKY), ("%AZURE%", AZURE), ("%LINE%", LINE), ("%INK%", INK), ("%BODY%", BODY), ("%MUTED%", MUTED))


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


def _orb_svg() -> str:
    """Crisp vector orbit: L, E, V, rho circles around R. Real SVG text (sharp at any zoom); labels stay upright while the ring turns."""
    sats = [("L", "LIKELIHOOD", 230, 62, BLUE_A, "#fff"), ("E", "EXPOSURE", 398, 230, RED, "#fff"),
            ("V", "VULNERABILITY", 230, 398, INK, "#fff"), ("ρ", "RESILIENCE", 62, 230, AZURE, INK)]
    g = ""
    for sym, sub, x, y, col, tx in sats:
        g += (f'<g class="cs"><circle cx="{x}" cy="{y}" r="62" fill="{col}" stroke="{INK}" stroke-width="4"/>'
              f'<text x="{x}" y="{y+2}" text-anchor="middle" fill="{tx}" font-size="38" font-weight="900">{sym}</text>'
              f'<text x="{x}" y="{y+26}" text-anchor="middle" fill="{tx}" font-size="12" font-weight="800" letter-spacing=".2">{sub}</text></g>')
    return (f'<div class="rm-orb"><svg viewBox="0 0 460 530" role="img" aria-label="R equals L times E times V times one minus rho">'
            f'<circle class="spin" cx="230" cy="230" r="168" fill="none" stroke="{BLUE_A}" stroke-width="4" stroke-dasharray="10 10"/>'
            f'<circle class="spin rev" cx="230" cy="230" r="100" fill="none" stroke="{RED}" stroke-width="4" stroke-dasharray="7 9"/>'
            f'<g class="spin">{g}</g>'
            f'<g class="core"><circle cx="230" cy="230" r="62" fill="{RED}" stroke="{INK}" stroke-width="4"/>'
            f'<text x="230" y="250" text-anchor="middle" fill="#fff" font-size="62" font-weight="900">R</text></g>'
            f'<rect x="30" y="478" width="400" height="46" rx="12" fill="#fff" stroke="{INK}" stroke-width="4"/>'
            f'<text x="230" y="510" text-anchor="middle" fill="{INK}" font-size="23" font-weight="800">R = L · E · V · (1 − '
            f'<tspan fill="{RED}">ρ</tspan>)</text></svg></div>')


def disclaimer_bar() -> None:
    """The one persistent notice, fixed at the bottom of every page. Same wording in demo and private mode (the mode is named, not alarmed)."""
    private = False
    try:
        import demo_mode
        private = not demo_mode.DEMO
    except Exception:  # noqa: BLE001
        pass
    mode = "PRIVATE INSTANCE" if private else "PUBLIC DEMO"
    tail = "Approved, pseudonymous data only." if private else "Synthetic or published aggregate values only. Do not enter patient data."
    st.markdown(f'<div class="rm-bar" role="note"><span class="tg">{mode}</span>'
                f'<span><b>Research prototype.</b> {tail} Not validated, not a medical device, not for patient-care or emergency decisions.</span></div>',
                unsafe_allow_html=True)


def hero_lp(eyebrow, title_html, lead, primary, secondary=None) -> None:
    """primary / secondary = (label, href). Copy on the left, animated orbit of L, E, V, rho on the right: nothing overlaps."""
    b2 = f'<a class="rm-btn o" href="{_e(secondary[1])}" target="_self">{_e(secondary[0])}</a>' if secondary else ""
    orb = _orb_svg()
    st.markdown(f'<div class="rm-lp"><div class="grid"><div><div class="rm-kicker">{_e(eyebrow)}</div><h1>{title_html}</h1>'
                f'<p class="lead">{_e(lead)}</p><div class="row"><a class="rm-btn r" href="{_e(primary[1])}" target="_self">{_e(primary[0])}</a>{b2}</div></div>'
                f'<div class="orbwrap">{orb}</div></div></div>', unsafe_allow_html=True)


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
