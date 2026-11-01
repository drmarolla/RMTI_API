"""Shared look for the extra pages. Calm clinical palette, no green (green reads as 'safe' in a risk tool, as in app.py.py), WCAG AA contrast,
and the tier is never conveyed by colour alone: every tier shows its number and name."""
import html
import streamlit as st

INK, MUTED, LINE, PANEL, PRIMARY = "#17283B", "#4A5A6B", "#D5DEE7", "#F2F6F9", "#0B5E7E"
# tier -> (accent for borders and bars, >= 3:1 on white; tint; text on the tint, >= 4.5:1). Same hue family as app.py.py, darkened where it failed.
TIER = {1: ("#5F7189", "#E9EDF2", "#1E2B3A"), 2: ("#3F6597", "#E6EDF6", "#14284A"), 3: ("#A67C00", "#FBF1D6", "#4A3600"),
        4: ("#C2571A", "#FBE8DC", "#5A2605"), 5: ("#9B2C2C", "#F8E1E1", "#4F1010")}
TIER_NAMES = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
TIER_ACCENTS = [TIER[i][0] for i in range(1, 6)]
STRIP = ("Research prototype. Not a medical device and not for patient-care decisions. "
         "A score is a relative rank on a fixed scale, not the probability that a person will develop cancer.")

CSS = f"""<style>
.block-container {{ padding-top: 3.6rem; max-width: 1180px; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
.rm-hero {{ border-bottom: 3px solid {PRIMARY}; padding-bottom: .55rem; margin-bottom: .7rem; }}
.rm-hero h1 {{ margin: 0; font-size: 1.85rem; padding: 0; }}
.rm-sub {{ color: {MUTED}; font-size: .95rem; margin: .25rem 0 .55rem; }}
.rm-chip {{ display: inline-block; border: 1px solid {LINE}; border-radius: 999px; padding: 2px 11px; margin: 0 6px 4px 0;
           font-size: .78rem; color: {MUTED}; background: #fff; }}
.rm-strip {{ background: {PANEL}; border-left: 4px solid {PRIMARY}; padding: .55rem .85rem; border-radius: 4px; font-size: .88rem; margin: .3rem 0 1rem; }}
.rm-tier {{ display: inline-block; border-left: 6px solid var(--a); background: var(--t); color: var(--x); padding: .35rem .85rem;
           border-radius: 4px; font-weight: 600; font-size: 1.02rem; }}
.rm-card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 8px; padding: .75rem 1rem; min-height: 9.2rem; }}
.rm-cl {{ color: {MUTED}; font-size: .85rem; }}
.rm-cv {{ font-size: 2.1rem; line-height: 1.25; color: {INK}; }}
.rm-cd {{ color: {MUTED}; font-size: .85rem; margin-bottom: .35rem; }}
.rm-note {{ color: {MUTED}; font-size: .86rem; }}
[data-testid="stMetric"] {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 8px; padding: .65rem .85rem; }}
:focus-visible {{ outline: 3px solid {PRIMARY}; outline-offset: 2px; }}
</style>"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, subtitle, chips=()):
    st.markdown(f"<div class='rm-hero'><h1>{html.escape(title)}</h1><div class='rm-sub'>{html.escape(subtitle)}</div>"
                + "".join(f"<span class='rm-chip'>{html.escape(c)}</span>" for c in chips) + "</div>", unsafe_allow_html=True)


def strip(text=STRIP):
    st.markdown(f"<div class='rm-strip' role='note'>{html.escape(text)}</div>", unsafe_allow_html=True)


def tier_chip(tier):
    """tier like '2 Moderate'. Always shows number and name."""
    i = int(str(tier).strip()[0])
    a, t, x = TIER[i]
    return f"<span class='rm-tier' style='--a:{a};--t:{t};--x:{x}'>{html.escape(str(tier))}</span>"


def note(text):
    st.markdown(f"<div class='rm-note'>{html.escape(text)}</div>", unsafe_allow_html=True)


def result_card(label, value, tier=None, detail=None):
    """One result: label, big number, optional detail line and the tier chip, all inside the same card so cards line up."""
    d = f"<div class='rm-cd'>{html.escape(detail)}</div>" if detail else ""
    c = tier_chip(tier) if tier else ""
    st.markdown(f"<div class='rm-card'><div class='rm-cl'>{html.escape(label)}</div><div class='rm-cv'>{html.escape(str(value))}</div>{d}{c}</div>", unsafe_allow_html=True)
