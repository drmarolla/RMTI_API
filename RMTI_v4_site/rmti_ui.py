"""Shared look: clean white clinical SaaS, large type for 100% browser zoom, crimson used sparingly."""
import plotly.graph_objects as go
import streamlit as st

from engine import TIER_BANDS, TIER_COLORS, TIER_LABELS

CSS = """
<style>
html{font-size:19px}
.block-container{padding-top:1.6rem;padding-bottom:4rem;max-width:1500px}
[data-testid="stSidebar"]{border-right:1px solid #E2E8F0;background:#fff}
[data-testid="stSidebar"][aria-expanded="true"]{min-width:340px;max-width:400px}
[data-testid="stSidebarNav"] a{font-size:1.02rem;padding:.38rem .6rem;border-radius:8px}
[data-testid="stSidebarNav"] span{font-size:1.02rem}
header[data-testid="stHeader"]{background:transparent}
h1{font-size:2.5rem!important;font-weight:800!important;letter-spacing:-.025em;color:#0F172A}
h2{font-size:1.85rem!important;font-weight:750!important;letter-spacing:-.02em;color:#0F172A}
h3{font-size:1.4rem!important;font-weight:700!important;color:#0F172A}
p,li,label,[data-testid="stMarkdownContainer"]{font-size:1rem;line-height:1.6}
.stButton>button,.stDownloadButton>button{font-size:1rem;padding:.6rem 1.3rem;border-radius:10px;font-weight:600}
[data-testid="stMetricValue"]{font-size:2.3rem;font-weight:800}
[data-testid="stMetricLabel"] p{font-size:1rem}
[data-baseweb="tab"]{font-size:1.05rem;padding:.7rem 1.1rem}
.st-key-hero,.st-key-devhero,.st-key-panel{background:#fff;border:1px solid #E2E8F0!important;border-radius:18px!important;
  padding:1.8rem 2.2rem;box-shadow:0 4px 22px rgba(15,23,42,.05)}
.pill{display:inline-block;background:#EFF6FF;color:#1D4ED8;font-size:.9rem;font-weight:600;padding:.4rem 1rem;border-radius:999px;margin-bottom:1.1rem}
.hero-title{font-size:3.5rem;font-weight:800;line-height:1.08;color:#0F172A;letter-spacing:-.035em;margin:0 0 1.1rem}
.hero-sub{font-size:1.28rem;line-height:1.6;color:#475569;margin-bottom:1.6rem;max-width:40rem}
.diagram{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:14px;padding:1.2rem;text-align:center}
.formula{display:inline-block;background:#fff;border:1px solid #CBD5E1;border-radius:999px;padding:.55rem 1.4rem;font-weight:700;font-size:1.15rem;color:#0F172A;margin-top:.7rem}
.kpi{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:1.3rem 1.5rem;height:100%}
.kpi .n{font-size:2.6rem;font-weight:800;color:#0F172A;line-height:1.1}
.kpi .l{font-size:1.08rem;color:#475569;line-height:1.4;margin-top:.4rem}
.kpi.red{border-top:5px solid #BE123C}.kpi.blue{border-top:5px solid #2563EB}
.kpi.navy{border-top:5px solid #0F172A}.kpi.sky{border-top:5px solid #93C5FD}
.tier{display:inline-block;padding:.35rem 1rem;border-radius:999px;font-weight:700;font-size:1rem}
.t1{background:#DCFCE7;color:#166534}.t2{background:#FEF9C3;color:#854D0E}.t3{background:#FFEDD5;color:#9A3412}
.t4{background:#FFE4E6;color:#9F1239}.t5{background:#450A0A;color:#fff}
.note{background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:.85rem 1.2rem;color:#78350F;font-size:.98rem}
.card{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:1.2rem 1.4rem;height:100%}
.card h4{margin:0 0 .4rem;font-size:1.15rem;color:#0F172A}
.card p{margin:0;color:#475569;font-size:1rem}
.stageno{display:inline-block;background:#BE123C;color:#fff;border-radius:8px;padding:.1rem .6rem;font-weight:700;margin-right:.5rem}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(n, label, accent):
    return f'<div class="kpi {accent}"><div class="n">{n}</div><div class="l">{label}</div></div>'


def badge(label):
    n = label.split()[1]
    return f'<span class="tier t{n}">{label.replace("Tier ", "Tier ")}</span>'


def card(title, body):
    return f'<div class="card"><h4>{title}</h4><p>{body}</p></div>'


def page_header(title, sub=None, pill=None):
    if pill:
        st.markdown(f'<span class="pill">{pill}</span>', unsafe_allow_html=True)
    st.title(title)
    if sub:
        st.markdown(f'<p style="font-size:1.2rem;color:#475569;max-width:60rem">{sub}</p>', unsafe_allow_html=True)


def disclaimer():
    from engine import DISCLAIMER
    st.markdown(f'<div class="note">{DISCLAIMER}</div>', unsafe_allow_html=True)


def style_fig(fig, height=460):
    fig.update_layout(template="plotly_white", height=height, font=dict(size=15, color="#0F172A"),
                      margin=dict(l=10, r=10, t=50, b=10), legend=dict(font=dict(size=14)))
    return fig


def add_tier_bands(fig, axis="y", x0=None, x1=None):
    """Shade the five fixed tier bands (Table 3) behind a chart."""
    soft = ["#ECFDF3", "#FEF9E7", "#FFF1E6", "#FEE8E8", "#F5DADA"]
    for (lo, hi), col, lbl in zip(TIER_BANDS, soft, TIER_LABELS):
        if axis == "y":
            fig.add_hrect(y0=lo, y1=hi, fillcolor=col, line_width=0, layer="below")
        else:
            fig.add_vrect(x0=lo, x1=hi, fillcolor=col, line_width=0, layer="below")
    return fig
