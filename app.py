
import json
from pathlib import Path
import pandas as pd
import pydeck as pdk
import streamlit as st

from src.config import CENTERS, RADII
from src.scoring import calculate, WEIGHTS, haversine_miles

st.set_page_config(page_title="SHPE Funding Discovery", page_icon="◆", layout="wide")

st.markdown("""
<style>
:root { --navy:#0b1f3a; --blue:#0067b9; --ink:#15263b; --muted:#6b7b8f; --line:#e3e9f0; --bg:#f6f8fb; --green:#177d62; --amber:#a46600; }
.stApp { background:var(--bg); }
.block-container { max-width:1500px; padding-top:1.2rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:var(--navy); }
[data-testid="stSidebar"] * { color:#eef5fb!important; }
.hero {background:linear-gradient(120deg,#0b1f3a,#123b65);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}
.hero h1{color:white!important;margin:0;font-size:2rem!important}.hero p{color:#cbd9e8;margin:.4rem 0 0}
.eyebrow{color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:10px}
.name{font-size:1.22rem;font-weight:750;color:var(--navy)}.muted{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;background:#eaf4fb;color:#0b5e93;border-radius:999px;padding:4px 9px;margin:5px 5px 0 0;font-size:.75rem;font-weight:700}
.badge.green{background:#eaf6f1;color:#177d62}.badge.amber{background:#fff4dc;color:#8b5a00}
.score{font-size:2.2rem;font-weight:800;color:var(--navy)}.small{font-size:.78rem;color:var(--muted)}
.metric-row{margin:12px 0}.metric-top{display:flex;justify-content:space-between;font-size:.9rem;margin-bottom:5px}
.track{height:9px;background:#edf1f5;border-radius:999px;overflow:hidden}.fill{height:9px;background:var(--blue);border-radius:999px}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:16px;border-radius:14px}
.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}
</style>
""", unsafe_allow_html=True)

ROOT=Path(__file__).parent
enriched=json.loads((ROOT/"data"/"companies.json").read_text())
cache_path=ROOT/"data"/"chamber_cache.json"
chamber_cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}

with st.sidebar:
    st.markdown("### ◆ SHPE")
    st.caption("FUNDING DISCOVERY")
    st.write("")
    page=st.radio("Navigation",["Discovery","Scoring model","Evidence sources","About"],label_visibility="collapsed")
    st.markdown("---")
    st.caption("Real organizations • transparent scoring")
    st.caption("Chamber discovery + company evidence")

st.markdown("""
<div class="hero"><div class="eyebrow">Fundraising Intelligence</div>
<h1>SHPE Funding Discovery</h1>
<p>Discover nearby organizations, open a company profile, and inspect the evidence behind sponsorship potential.</p></div>
""",unsafe_allow_html=True)

def enriched_for_center(center_name, radius):
    center=CENTERS[center_name]
    out=[]
    for c in enriched:
        score,parts,dist=calculate(c,center)
        if dist<=radius:
            out.append({"company":c["company"],"industry":c["industry"],"city":c["city"],"lat":c["lat"],"lon":c["lon"],"distance":dist,"status":"Scored","score":score,"parts":parts,"record":c,"source_type":"Enriched"})
    return out

def chamber_for_center(center_name, radius):
    center=CENTERS[center_name]; out=[]
    for c in chamber_cache.get(center_name,[]):
        lat,lon=c.get("lat"),c.get("lon")
        if lat is None or lon is None: continue
        dist=round(haversine_miles(center["lat"],center["lon"],lat,lon),1)
        if dist<=radius:
            out.append({"company":c["company"],"industry":"Chamber-listed business","city":c.get("address",""),"lat":lat,"lon":lon,"distance":dist,"status":"Needs enrichment","score":None,"parts":None,"record":c,"source_type":"Chamber lead"})
    return out

if page=="Discovery":
    c1,c2,c3,c4=st.columns([1.35,.8,1,1])
    with c1: center_name=st.selectbox("University area",list(CENTERS))
    with c2: radius=st.radio("Radius",RADII,horizontal=True,format_func=lambda x:f"{x} mi")
    with c3: view_mode=st.selectbox("Records",["All organizations","Scored only","Needs enrichment"])
    with c4: min_score=st.selectbox("Minimum scored fit",[0,50,60,70,80,90],format_func=lambda x:"Any score" if x==0 else f"{x}+")
    center=CENTERS[center_name]
    scored=enriched_for_center(center_name,radius); leads=chamber_for_center(center_name,radius)
    scored=[r for r in scored if r["score"]>=min_score]
    rows=scored if view_mode=="Scored only" else leads if view_mode=="Needs enrichment" else scored+leads
    rows=sorted(rows,key=lambda r:(r["score"] is None,-(r["score"] or 0),r["distance"]))

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Organizations in radius",len(rows)); m2.metric("Scored prospects",sum(r["status"]=="Scored" for r in rows)); m3.metric("Local businesses",sum(r["status"]=="Needs enrichment" for r in rows)); m4.metric("Public contact routes",sum(bool(r["record"].get("website") or r["record"].get("contact_page") or r["record"].get("contact_email")) for r in rows))

    left,right=st.columns([1.45,1],gap="large")
    with left:
        st.subheader("Local sponsor map"); st.caption("Organizations within the selected university radius.")
        if rows:
            map_df=pd.DataFrame([{"lat":r["lat"],"lon":r["lon"],"company":r["company"],"score_label":f"{r['score']}/100" if r["score"] is not None else "Unscored","status":r["status"],"color":[0,103,185,185],"radius":620} for r in rows])
            layer=pdk.Layer("ScatterplotLayer",map_df,get_position="[lon, lat]",get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True)
            view=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.4)
            st.pydeck_chart(pdk.Deck(layers=[layer],initial_view_state=view,tooltip={"text":"{company}\\n{score_label}"}),use_container_width=True)
        else: st.info("No records match the current filters.")

    with right:
        st.subheader("Organizations"); st.caption("Click a score or Open button to view the organization.")
        if "selected_company" not in st.session_state and rows: st.session_state.selected_company=rows[0]["company"]
        for r in rows[:40]:
            a,b=st.columns([4.2,1.1])
            with a: st.markdown(f"**{r['company']}**"); st.caption(f"{r['status']} · {r['distance']} mi")
            with b:
                label=str(r["score"]) if r["score"] is not None else "Open"
                if st.button(label,key="open_"+r["company"],use_container_width=True): st.session_state.selected_company=r["company"]; st.rerun()

    if rows:
        selected=next((r for r in rows if r["company"]==st.session_state.get("selected_company")),rows[0]); rec=selected["record"]
        st.markdown("---"); st.subheader("Organization profile")
        top1,top2=st.columns([3,1],gap="large")
        with top1:
            if selected["status"]=="Scored":
                badges=f'<span class="badge green">Evidence scored</span><span class="badge">{rec.get("capacity_tier","").title()} capacity</span>'; summary=rec.get("summary",""); source=rec.get("discovery_source","Direct company research")
            else:
                badges=f'<span class="badge amber">Needs enrichment</span><span class="badge">{rec.get("discovery_source","Chamber directory")}</span>'; summary="This organization was discovered from a nearby Chamber / business-alliance directory. Philanthropy, STEM, recruiting, and sponsorship evidence has not yet been fully verified."; source=rec.get("discovery_source","Chamber directory")
            st.markdown(f"""<div class="card"><div class="name">{selected['company']}</div><div class="muted">{rec.get('address') or selected.get('city','')} · {selected['distance']} miles from {center_name}</div>{badges}<p style="margin-top:14px">{summary}</p><div class="small"><b>Discovered via:</b> {source}</div></div>""",unsafe_allow_html=True)
        with top2:
            if selected["score"] is not None:
                label="High priority" if selected["score"]>=80 else "Promising" if selected["score"]>=65 else "Needs review"
                st.markdown(f"""<div class="card" style="text-align:center"><div class="small">{"AI SPONSOR SCORE" if rec.get("ai_analysis") else "SPONSOR SCORE"}</div><div class="score">{rec.get("ai_analysis",{}).get("ai_score",selected["score"])}<span style="font-size:1rem">/100</span></div><b>{rec.get("ai_analysis",{}).get("sponsor_tier",label)}</b><div class="small" style="margin-top:7px">{"AI confidence: " + str(rec["ai_analysis"]["confidence"]) + "/100" if rec.get("ai_analysis") else "Evidence-backed weighted score"}</div><div class="small" style="margin-top:4px">Baseline: {selected["score"]}/100</div></div>""",unsafe_allow_html=True)
            else: st.markdown("""<div class="card" style="text-align:center"><div class="small">SPONSOR SCORE</div><div class="score">—</div><b>Enrichment pending</b><div class="small" style="margin-top:7px">No score until enough evidence is verified</div></div>""",unsafe_allow_html=True)

        website=rec.get("website",""); contact=rec.get("contact_page",""); email=rec.get("contact_email",""); profile=rec.get("profile_url","")
        a,b,c=st.columns(3)
        with a:
            if website: st.link_button("Visit company website",website,use_container_width=True)
            elif profile: st.link_button("Open directory listing",profile,use_container_width=True)
            else: st.button("Website not verified",disabled=True,use_container_width=True)
        with b:
            if email: st.link_button("Email company",f"mailto:{email}",use_container_width=True); st.caption(email)
            elif contact: st.link_button("Open contact page",contact,use_container_width=True); st.caption("No public email verified")
            else: st.button("Email not verified",disabled=True,use_container_width=True)
        with c:
            if profile: st.link_button("View discovery source",profile,use_container_width=True)
            else: st.button("Source in evidence ledger",disabled=True,use_container_width=True)

        if selected["score"] is not None:
            ai=rec.get("ai_analysis")
            if ai:
                st.markdown("### AI sponsorship analysis")
                ai1,ai2,ai3=st.columns(3); ai1.metric("AI score",f"{ai['ai_score']}/100"); ai2.metric("Confidence",f"{ai['confidence']}/100"); ai3.metric("Suggested ask",ai["recommended_ask"])
                st.markdown(f"**Recommended outreach angle:** {ai['outreach_angle']}"); st.write(ai["summary"])
                q1,q2=st.columns(2,gap="large")
                with q1:
                    st.markdown("#### Strongest signals")
                    for item in ai.get("strengths",[]): st.markdown(f"✓ {item}")
                    st.markdown("#### Recommended next steps")
                    for i,item in enumerate(ai.get("next_steps",[]),1): st.markdown(f"**{i}.** {item}")
                with q2:
                    st.markdown("#### Things to verify")
                    for item in ai.get("risks",[]): st.markdown(f"• {item}")
                    st.markdown("#### AI vs. baseline"); st.write(f"**AI assessment:** {ai['ai_score']}/100"); st.write(f"**Deterministic baseline:** {selected['score']}/100"); st.caption(f"AI adjustment: {ai['ai_score']-selected['score']:+d} points.")
                st.markdown("---")
            else: st.info("AI sponsorship analysis has not been generated for this scored company yet.")
            a,b=st.columns([1.15,1],gap="large")
            labels={"philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment","recruiting_talent":"Recruiting / student talent","past_sponsorships":"Previous sponsorship behavior","industry_fit":"Industry relevance to SHPE","local_presence":"Local presence","financial_capacity":"Financial capacity","proximity":"Geographic proximity","university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment","evidence_quality":"Evidence quality"}
            with a:
                st.markdown("#### Score breakdown")
                for k,w in WEIGHTS.items():
                    value=selected["parts"][k]; st.markdown(f"""<div class="metric-row"><div class="metric-top"><b>{labels[k]}</b><span>{value}/100 · {round(w*100)}%</span></div><div class="track"><div class="fill" style="width:{value}%"></div></div></div>""",unsafe_allow_html=True)
            with b:
                st.markdown("#### Verified evidence")
                for s in rec.get("sources",[]):
                    date=f" · {s['date']}" if s.get("date") else ""; st.markdown(f"**[{s['title']}]({s['url']})**  \n<span class='small'>{'Official company source' if s.get('official') else 'Directory / discovery source'}{date}</span>",unsafe_allow_html=True)
                st.info("A missing signal means not verified yet — not necessarily no.")
        else: st.info("This lead will receive a sponsor score only after company-site evidence is collected and reviewed.")

elif page=="Scoring model":
    st.subheader("Transparent 100-point scoring model")
    names={"philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment","recruiting_talent":"Recruiting / talent alignment","past_sponsorships":"Previous sponsorship behavior","industry_fit":"Industry relevance to SHPE","local_presence":"Local presence","financial_capacity":"Financial capacity","proximity":"Geographic proximity","university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment","evidence_quality":"Evidence quality / recency"}
    st.dataframe(pd.DataFrame([{"Metric":names[k],"Weight":f"{int(v*100)}%"} for k,v in WEIGHTS.items()]),use_container_width=True,hide_index=True)
    st.markdown("The dashboard keeps a transparent deterministic baseline and can also display a cached **AI Sponsor Score** generated from the verified evidence. This lets viewers compare the AI recommendation with an explainable scoring model.")

elif page=="Evidence sources":
    st.subheader("Evidence & discovery ledger"); records=[]
    for c in enriched:
        for s in c["sources"]: records.append({"Organization":c["company"],"Type":"Scoring evidence","Source":s["title"],"Official":s["official"],"Date":s.get("date") or "Undated","URL":s["url"]})
    for area,items in chamber_cache.items():
        for c in items: records.append({"Organization":c["company"],"Type":"Chamber discovery","Source":c.get("discovery_source",""),"Official":False,"Date":"Current directory","URL":c.get("profile_url","")})
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True,column_config={"URL":st.column_config.LinkColumn("URL")})

elif page=="About":
    st.subheader("About the prototype")
    st.markdown("""
    **SHPE Funding Discovery** is a local-first fundraising research prototype.

    The app uses nearby Chamber and business-alliance directories for organization discovery, filters companies around a university area,
    and only assigns a sponsor score after enough public evidence has been verified.

    **Demo areas:** Florida Polytechnic University and Dartmouth College, each with 10-mile and 25-mile views.

    **Data principle:** unverified is not the same thing as no. The app avoids inventing emails, philanthropy programs, sponsorship history, or relationships.
    """)
