"""Home view — Full-page dark 3D video background, ambient audio toggle, and clickable RMTI cards."""
import streamlit as st
import streamlit.components.v1 as components
PAGES = {}
RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])
RAW_ROOT = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main"])
def render():
    onc_mp4 = f"{RAW_VIDEOS}/home_oncology.mp4"
    dis_mp4 = f"{RAW_VIDEOS}/home_disaster.mp4"
    fb_onc = f"{RAW_VIDEOS}/video1_4stages_3d.mp4"
    fb_dis = f"{RAW_ROOT}/rmti_3_flood_heat_case_studies.mp4"
    st.markdown("""
    <style>
    html, body, .stApp, [data-testid="stAppViewContainer"] { background: transparent !important; }
    [data-testid="stHeader"] { background: linear-gradient(180deg, rgba(11,17,32,0.88) 0%, transparent 100%) !important; }
    [data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stHeader"] svg { color: #F1F5F9 !important; fill: #F1F5F9 !important; opacity: 0.95 !important; }
    [data-testid="stHeader"] button:hover, [data-testid="stHeader"] a:hover { color: #38BDF8 !important; }
    [data-testid="stMain"], [data-testid="stAppViewContainer"] > .main { position: relative !important; z-index: 5 !important; background: transparent !important; }
    [data-testid="stSidebar"] { background: rgba(11,17,32,0.92) !important; backdrop-filter: blur(14px); z-index: 6 !important; }
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3, [data-testid="stMain"] p, [data-testid="stMain"] strong { color: #FFFFFF !important; }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p, [data-testid="stMain"] small { color: #CBD5E1 !important; opacity: 1 !important; }
    .hero-wrap { padding: 20px 4px 8px 4px; max-width: 680px; }
    .hero-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
    .hero-pill { background: #FFFFFF; color: #0F172A !important; font-size: 11.5px; font-weight: 800; padding: 4px 10px; border-radius: 4px; }
    .hero-pill.red { background: #DC2626; color: #FFFFFF !important; }
    .hero-pill.blue { background: #0284C7; color: #FFFFFF !important; }
    .hero-lead { color: #E2E8F0 !important; font-size: 16px; line-height: 1.6; margin-bottom: 14px; max-width: 560px; }
    .hero-title { color: #FFFFFF !important; font-size: 48px; font-weight: 800; line-height: 1.06; letter-spacing: -0.03em; margin-bottom: 14px; }
    .pillar-tag { display: inline-block; background: rgba(2,132,199,0.25); color: #38BDF8 !important; font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 999px; margin-bottom: 8px; }
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15,23,42,0.86) !important; backdrop-filter: blur(12px);
        border: 1px solid rgba(148,163,184,0.32) !important; border-radius: 12px !important; padding: 10px !important;
    }
    [data-testid="stMain"] .stButton > button[kind="secondary"] { background: #F8FAFC !important; color: #0F172A !important; border: 1px solid #FFF !important; font-weight: 700 !important; }
    [data-testid="stMain"] .stButton > button[kind="secondary"] * { color: #0F172A !important; }
    [data-testid="stMain"] .stButton > button[kind="secondary"]:hover { background: #0284C7 !important; border-color: #0284C7 !important; }
    [data-testid="stMain"] .stButton > button[kind="secondary"]:hover * { color: #FFFFFF !important; }
    [data-testid="stMain"] .stButton > button[kind="primary"] { background: #DC2626 !important; border-color: #DC2626 !important; font-weight: 700 !important; }
    [data-testid="stMain"] .stButton > button[kind="primary"] * { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)
    components.html(f"""
    <script>
    (function() {{
      const doc = window.parent.document;
      const old = doc.getElementById('rmti-fullpage-bg');
      if (old) old.remove();
      const bg = doc.createElement('div');
      bg.id = 'rmti-fullpage-bg';
      bg.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;background:#0B1120;overflow:hidden;pointer-events:none;';
      bg.innerHTML = `
        <video id="rmti-bg-onc" autoplay loop muted playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right center;opacity:1;transition:opacity 1.5s;">
          <source src="{onc_mp4}" type="video/mp4"><source src="{fb_onc}" type="video/mp4">
        </video>
        <video id="rmti-bg-dis" autoplay loop muted playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right center;opacity:0;transition:opacity 1.5s;">
          <source src="{dis_mp4}" type="video/mp4"><source src="{fb_dis}" type="video/mp4">
        </video>
        <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(11,17,32,0.94) 0%,rgba(11,17,32,0.80) 38%,rgba(11,17,32,0.28) 72%,rgba(11,17,32,0.10) 100%);"></div>`;
      doc.body.prepend(bg);
      let s = true;
      setInterval(() => {{
        const o = doc.getElementById('rmti-bg-onc'), d = doc.getElementById('rmti-bg-dis');
        if (o && d) {{ s = !s; o.style.opacity = s ? '1' : '0'; d.style.opacity = s ? '0' : '1'; }}
      }}, 9000);
    }})();
    </script>
    """, height=0)
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-pills">
        <span class="hero-pill">Risk Intelligence • RMTI</span>
        <span class="hero-pill blue">Disaster Science</span>
        <span class="hero-pill red">Clinical Oncology</span>
        <span class="hero-pill">Deterministic FHIR API</span>
      </div>
      <p class="hero-lead">Quantitative risk intelligence bridging disaster-risk reduction and clinical oncology—modeling hazard, exposure, vulnerability, and system resilience before risk fragments care.</p>
      <div class="hero-title">Quantify systemic risk.<br>Before it fragments care.</div>
    </div>
    """, unsafe_allow_html=True)
    components.html("""
    <style>
      body{margin:0;background:transparent;font-family:sans-serif}
      .bar{display:inline-flex;align-items:center;gap:14px;background:rgba(15,23,42,0.88);border:1px solid rgba(148,163,184,0.38);padding:10px 18px;border-radius:10px;color:#FFF;font-size:14px;font-weight:700}
      .btn{background:#1E293B;color:#F8FAFC;border:1px solid #64748B;border-radius:999px;padding:6px 14px;font-size:12.5px;font-weight:700;cursor:pointer;transition:all 0.2s ease}
      .btn:hover{border-color:#38BDF8;color:#FFFFFF;box-shadow:0 0 14px rgba(56,189,248,0.55)}
      .btn.on{background:#0284C7;border-color:#38BDF8;color:#FFFFFF}
    </style>
    <div class="bar">
      <span>R = <span style="color:#38BDF8">L</span> · <span style="color:#F87171">E</span> · <span style="color:#FBBF24">V</span> · (1 − <span style="color:#34D399">ρ</span>)</span>
      <button id="t" class="btn" onclick="tog()">🔇 Ambient Sound: Off</button>
    </div>
    <script>
      let ctx=null,g=null,tm=null,on=false;
      async function tog(){
        const b=document.getElementById('t');
        if(!on){
          on=true; const AC=window.AudioContext||window.webkitAudioContext; ctx=new AC();
          if(ctx.state==='suspended') await ctx.resume();
          g=ctx.createGain(); g.gain.setValueAtTime(0.001,ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.16,ctx.currentTime+1.5);
          const f=ctx.createBiquadFilter(); f.type='lowpass'; f.frequency.value=760; f.connect(g); g.connect(ctx.destination);
          [130.81,196.00,293.66,329.63,493.88].forEach((hz,i)=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=i<2?'sine':'triangle';o.frequency.value=hz;og.gain.value=i<2?0.32:0.14;o.connect(og);og.connect(f);o.start();});
          tm=setInterval(()=>{if(!ctx||!on)return;const n=ctx.currentTime,p=ctx.createOscillator(),pg=ctx.createGain();p.frequency.value=587.33;pg.gain.setValueAtTime(0.001,n);pg.gain.exponentialRampToValueAtTime(0.08,n+0.35);pg.gain.exponentialRampToValueAtTime(0.001,n+0.9);p.connect(pg);pg.connect(f);p.start(n);p.stop(n+0.92);},937);
          b.classList.add('on'); b.textContent='🔊 Ambient Sound: On';
        } else {
          on=false; clearInterval(tm); if(g&&ctx)g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.5); const c=ctx; setTimeout(()=>c&&c.close(),600); ctx=null;
          b.classList.remove('on'); b.textContent='🔇 Ambient Sound: Off';
        }
      }
    </script>
    """, height=58)
    c1, c2, c3, c4, _ = st.columns([1.5, 1.7, 1.8, 1.8, 2.2])
    if c1.button("Explore the tools", type="primary", use_container_width=True, key="hero_explore"):
        if "calc" in PAGES: st.switch_page(PAGES["calc"])
    if c2.button("Disaster case studies", use_container_width=True, key="hero_disaster"):
        if "urban" in PAGES: st.switch_page(PAGES["urban"])
    if c3.button("Oncology case studies", use_container_width=True, key="hero_oncology"):
        if "liver" in PAGES: st.switch_page(PAGES["liver"])
    if c4.button("Books & Publications", use_container_width=True, key="hero_pubs"):
        if "pubs" in PAGES: st.switch_page(PAGES["pubs"])
    st.write("")
    pillars = [
        ("Unified framework", "R = L·E·V·(1−ρ)", "Disaster & Oncology", "method"),
        ("Cancer cohorts", "Liver, Lung, Breast", "BCLC & ALBI calibrated", "liver"),
        ("Urban resilience", "Six African cities", "Flood & heat stress", "urban"),
        ("Clinical integration", "HL7 FHIR R4", "Deterministic tiers 1–4", "api"),
    ]
    p_cols = st.columns(4)
    for col, (lbl, val, tag, pk) in zip(p_cols, pillars):
        with col.container(border=True):
            st.caption(lbl)
            st.markdown(f"### {val}")
            st.markdown(f'<span class="pillar-tag">{tag}</span>', unsafe_allow_html=True)
            if st.button("Open", key=f"pil_{pk}", use_container_width=True):
                if pk in PAGES:
                    st.switch_page(PAGES[pk])
