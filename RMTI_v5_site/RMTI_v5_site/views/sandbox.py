"""Oncology Cohort Sandbox: Hepatocellular Carcinoma (HCC) & Custom Cohort Triage."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from engine import core, short
from rmti_ui import disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])
HCC_PRESETS = [
    {"Name": "Fibrosis F1–F3 Baseline (BCLC 0)", "N": 1, "L": 0.150, "E_sel": 0.600, "V": 0.350, "rho_now": 0.200, "C": 3},
    {"Name": "Untreated HBV Cirrhosis F4 (Fan aMAP)", "N": 1, "L": 0.900, "E_sel": 0.720, "V": 0.600, "rho_now": 0.200, "C": 4},
    {"Name": "Early HCC BCLC 0/A (US + AFP)", "N": 1, "L": 0.650, "E_sel": 0.680, "V": 0.480, "rho_now": 0.250, "C": 4},
    {"Name": "Portal Invasion BCLC B/C (Faria ALBI n=54)", "N": 1, "L": 0.820, "E_sel": 0.780, "V": 0.522, "rho_now": 0.180, "C": 5},
    {"Name": "Metastatic HCC BCLC D Subgroup", "N": 1, "L": 0.880, "E_sel": 0.850, "V": 0.740, "rho_now": 0.150, "C": 5},
    {"Name": "Custom Oncology Cohort / Your Data", "N": 1, "L": 0.550, "E_sel": 0.600, "V": 0.500, "rho_now": 0.250, "C": 4},
]


def _synth(n, seed):
    rng = np.random.default_rng(int(seed))
    return {
        f"HCC-{i+1:03d}": dict(
            N=1,
            L=round(float(np.clip(rng.beta(2.2, 4.5), 0.05, 0.95)), 3),
            E_sel=round(float(np.clip(rng.beta(2.5, 3.0), 0.10, 0.95)), 3),
            V=round(float(np.clip(rng.beta(2.4, 3.2), 0.10, 0.95)), 3),
            rho_now=round(float(np.clip(rng.beta(2.0, 4.0), 0.05, 0.80)), 3),
            C=int(rng.choice((2, 3, 4, 5), p=(0.20, 0.35, 0.30, 0.15))),
        )
        for i in range(int(n))
    }


def _dual_card(df, raw, r0, r1, eal, rho):
    tiers = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
    c0s = [int((df["Tier now"] == t).sum()) for t in tiers]
    c1s = [int((df["Tier after"] == t).sum()) for t in tiers]
    mx = max(1, max(c0s + c1s))
    vals = list(raw.values())
    mL, mE, mV = np.mean([v["L"] for v in vals]), np.mean([v["E_sel"] for v in vals]), np.mean([v["V"] for v in vals])
    mR = np.mean([1.0 - v.get("rho_after", v["rho_now"]) for v in vals])
    bars = "".join(
        f'<div class="tg"><div class="pr"><div class="bw"><span class="cn">{c0}</span><div class="br b0" style="height:{max(4,int(c0/mx*108))}px"></div></div>'
        f'<div class="bw"><span class="cn cy">{c1}</span><div class="br b1" style="height:{max(4,int(c1/mx*108))}px"></div></div></div><div class="xl">{t.split()[1]}</div></div>'
        for t, c0, c1 in zip(tiers, c0s, c1s)
    )
    components.html(f"""
    <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}.cd{{position:relative;height:360px;border-radius:16px;overflow:hidden;border:1px solid #D6B899;background:linear-gradient(125deg,#F3DFC8,#C88A55 52%,#8F562E)}}video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}.sc{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(28,16,9,.08),rgba(42,24,14,.38) 38%,rgba(34,19,11,.76))}}.pl{{position:absolute;top:14px;left:14px;z-index:4;display:flex;gap:6px}}.pb{{background:rgba(36,21,13,.75);color:#FFF;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:4px}}.ov{{position:absolute;top:14px;right:16px;bottom:14px;width:62%;z-index:3;display:flex;flex-direction:column;justify-content:space-between;color:#FFF}}.mb{{background:rgba(28,16,9,.55);border:1px solid rgba(255,255,255,.22);border-radius:10px;padding:8px 12px}}.eq{{display:flex;justify-content:space-between;font-size:12px;font-weight:800}}.lv{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,.16);font-size:10.5px;text-align:center}}.lv b{{display:block;font-size:12px;color:#FDE68A}}.pt{{position:relative;flex:1;margin:12px 4px 18px 26px;border-left:1.5px solid rgba(255,255,255,.72);border-bottom:1.5px solid rgba(255,255,255,.72);display:grid;grid-template-columns:repeat(5,1fr);align-items:end}}.ya{{position:absolute;left:-26px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:space-between;font-size:10px;font-weight:700}}.tg{{display:flex;flex-direction:column;align-items:center}}.pr{{display:flex;align-items:flex-end;gap:5px;height:138px}}.bw{{position:relative;width:18px;height:100%;display:flex;align-items:flex-end;justify-content:center}}.br{{width:100%;border-radius:2px 2px 0 0;transition:height .4s}}.b0{{background:rgba(68,48,36,.75);border:1px solid rgba(255,255,255,.3)}}.b1{{background:rgba(56,189,248,.88);border:1px solid rgba(255,255,255,.55)}}.cn{{position:absolute;top:0;font-size:9.5px;font-weight:800}}.cy{{color:#7DD3FC}}.xl{{position:absolute;bottom:-18px;font-size:10px;font-weight:700}}.ft{{display:flex;justify-content:space-between;font-size:11px;font-weight:700;background:rgba(28,16,9,.48);padding:5px 10px;border-radius:8px}}</style>
    <div class="cd"><video autoplay loop muted playsinline><source src="{RAW_VIDEOS}/sandbox_dual3d.mp4" type="video/mp4"><source src="{RAW_VIDEOS}/video1_4stages_3d.mp4" type="video/mp4"></video><div class="sc"></div>
    <div class="pl"><span class="pb">Clinical Oncology</span><span class="pb">HCC · BCLC &amp; ALBI</span><span class="pb">Dual-Layer 3D + 2D</span></div>
    <div class="ov"><div class="mb"><div class="eq"><span>R = L · E · V · (1 − ρ)</span><span style="color:#7DD3FC">EAL = {eal:.3f}</span></div><div class="lv"><div>Mean L<b>{mL:.2f}</b></div><div>Mean E<b>{mE:.2f}</b></div><div>Mean V<b>{mV:.2f}</b></div><div>Mean (1−ρ)<b>{mR:.2f}</b></div></div></div>
    <div class="pt"><div class="ya"><span>{mx}</span><span>{mx//2}</span><span>0</span></div>{bars}</div>
    <div class="ft"><span>n = {len(df):,} · Target ρ = {rho:.2f}</span><span>Mean R: {r0:.3f} → <b style="color:#7DD3FC">{r1:.3f}</b></span></div></div></div>
    """, height=368)


def render():
    page_header("Oncology Cohort Sandbox — Hepatocellular Carcinoma (HCC) & Custom Triage", "Case Study: HCC BCLC & ALBI Surveillance Cohort (Marolla, 2026, SSRN: 7427450; Faria et al. ALBI Cohort, n = 54; Singal et al., 2022; Lau-Min et al., JAMA Netw Open, 2025).", "Research tools")
    with st.expander("How to Use the Oncology Cohort Sandbox (3-Step Guide)", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.markdown("**1. Customize Cohort**\nGenerate synthetic HCC rows, switch to **Custom Editable Table** to edit or add rows (`+`), or upload a CSV.")
        c2.markdown("**2. Simulate Surveillance (ρ)**\nAdjust **ρ after** to model ultrasound + AFP adherence or systemic therapy delivery.")
        c3.markdown("**3. Export Results**\nWatch the **Main 3D + 2D** bars shift across Tiers 1–5 and download your CSV.")
    st.warning("Do not upload patient-identifiable data. Use synthetic or aggregate values.")
    left, right = st.columns((1.05, 1.85), gap="large")
    with left:
        with st.container(border=True):
            src = st.radio("Data source", ["Synthetic HCC cohort", "Custom Editable Table", "Upload CSV"], horizontal=True)
            if src == "Synthetic HCC cohort":
                raw = _synth(st.slider("Synthetic patients", 50, 2000, 850, 50), st.number_input("Random seed", 1, 99999, 2026, 1))
            elif src == "Custom Editable Table":
                ed = st.data_editor(pd.DataFrame(HCC_PRESETS), num_rows="dynamic", width="stretch", key="onc_ed")
                raw = {str(r["Name"]): dict(N=float(r["N"]), L=float(r["L"]), E_sel=float(r["E_sel"]), V=float(r["V"]), rho_now=float(r["rho_now"]), C=int(r["C"])) for _, r in ed.dropna(subset=["Name", "L", "E_sel", "V", "rho_now", "C"]).iterrows()}
            else:
                up = st.file_uploader("Upload CSV (Name, N, L, E_sel, V, rho_now, C)", type=["csv"], key="onc_up")
                raw = {str(r["Name"]): dict(N=float(r.get("N", 1)), L=float(r["L"]), E_sel=float(r["E_sel"]), V=float(r["V"]), rho_now=float(r["rho_now"]), C=int(r.get("C", 3))) for _, r in pd.read_csv(up).dropna(subset=["Name", "L", "E_sel", "V", "rho_now"]).iterrows()} if up else _synth(250, 2026)
            ov = st.toggle("Override ρ after for every row", True, key="onc_ov")
            rho_s = st.slider("ρ after (surveillance scenario)", 0.05, 0.95, 0.65, 0.01, key="onc_rho") if ov else None
    if ov and rho_s is not None:
        for v in raw.values():
            v["rho_after"] = float(rho_s)
    df = pd.DataFrame([{"Name": r["name"], "Priority": r["priority_in_tier"], "R now": r["R_now"], "Tier now": short(r["tier_now"]), "R after": r.get("R_after"), "Tier after": short(r["tier_after"]) if "tier_after" in r else "", "Reduction %": r.get("risk_reduction_pct"), "EAL now": r["EAL_now"]} for r in core.rank_cohort(raw)])
    m0, m1, meal = float(df["R now"].mean()), float(df["R after"].mean()) if df["R after"].notna().any() else float(df["R now"].mean()), float(df["EAL now"].mean())
    with right:
        _dual_card(df, raw, m0, m1, meal, rho_s or 0.65)
        a, b, c = st.columns(3)
        a.metric("Rows scored", f"{len(df):,}"); b.metric("Mean R now", f"{m0:.3f}"); c.metric("Mean R after", f"{m1:.3f}", f"{((m1/m0)-1)*100:+.1f}%", delta_color="inverse")
        tiers = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]
        fig = go.Figure([go.Bar(x=tiers, y=[int((df["Tier now"] == t).sum()) for t in tiers], name="now", marker_color="#1E293B"), go.Bar(x=tiers, y=[int((df["Tier after"] == t).sum()) for t in tiers], name="after", marker_color="#93C5FD")])
        fig.update_layout(barmode="group", yaxis_title="Patients or cohorts")
        st.plotly_chart(style_fig(fig, 290), width="stretch")
        st.dataframe(df, hide_index=True, width="stretch", height=270)
        st.download_button("Download Oncology cohort (CSV)", df.to_csv(index=False).encode(), "rmti_oncology_sandbox.csv", "text/csv")
    disclaimer()
