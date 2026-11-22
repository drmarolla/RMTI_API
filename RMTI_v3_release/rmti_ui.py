"""Shared look and feel: clean white clinical SaaS cards, crimson used sparingly."""
import streamlit as st

CSS = """
<style>
.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:1180px}
[data-testid="stSidebar"]{border-right:1px solid #E2E8F0;background:#FFFFFF}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3{letter-spacing:-0.02em;color:#0F172A}
.st-key-hero,.st-key-devhero{background:#fff;border:1px solid #E2E8F0!important;border-radius:16px!important;
  padding:1.6rem 1.8rem;box-shadow:0 4px 20px rgba(15,23,42,.04)}
.pill{display:inline-block;background:#EFF6FF;color:#1D4ED8;font-size:.74rem;font-weight:600;
  padding:.3rem .8rem;border-radius:999px;margin-bottom:1rem}
.hero-title{font-size:2.55rem;font-weight:800;line-height:1.12;color:#0F172A;letter-spacing:-.03em;margin:0 0 1rem}
.hero-sub{font-size:1.02rem;line-height:1.6;color:#475569;margin-bottom:1.3rem;max-width:34rem}
.diagram{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:1.2rem;text-align:center}
.formula{display:inline-block;background:#fff;border:1px solid #CBD5E1;border-radius:999px;
  padding:.4rem 1.1rem;font-weight:700;font-size:.92rem;color:#0F172A;margin-top:.6rem}
.kpi{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:1.1rem 1.3rem;height:100%}
.kpi .n{font-size:2rem;font-weight:800;color:#0F172A;line-height:1.1}
.kpi .l{font-size:.9rem;color:#475569;line-height:1.4;margin-top:.3rem}
.kpi.red{border-top:4px solid #BE123C}.kpi.blue{border-top:4px solid #2563EB}
.kpi.navy{border-top:4px solid #0F172A}.kpi.sky{border-top:4px solid #93C5FD}
.tier{display:inline-block;padding:.25rem .8rem;border-radius:999px;font-weight:700;font-size:.85rem}
.tier-low{background:#DCFCE7;color:#166534}.tier-moderate{background:#FEF9C3;color:#854D0E}
.tier-high{background:#FFEDD5;color:#9A3412}.tier-critical{background:#FFE4E6;color:#9F1239}
.note{background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:.7rem 1rem;color:#78350F;font-size:.88rem}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(number: str, label: str, accent: str) -> str:
    return f'<div class="kpi {accent}"><div class="n">{number}</div><div class="l">{label}</div></div>'


def tier_badge(tier: str) -> str:
    return f'<span class="tier tier-{tier}">{tier.upper()}</span>'
