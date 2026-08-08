import json
from pathlib import Path
import pandas as pd
import pydeck as pdk
import streamlit as st
from src.config import CENTERS, RADII
from src.scoring import calculate, WEIGHTS, haversine_miles

st.set_page_config(page_title="SHPE Funding Discovery", page_icon="◆", layout="wide")
st.markdown("""<style>:root{--navy:#0b1f3a;--blue:#0067b9;--muted:#6b7b8f;--line:#e3e9f0;--bg:#f6f8fb}.stApp{background:var(--bg)}.block-container{max-width:1500px;padding-top:1.2rem}[data-testid="stSidebar"]{background:var(--navy)}[data-testid="stSidebar"] *{color:#eef5fb!important}.hero{background:linear-gradient(120deg,#0b1f3a,#123b65);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}.hero h1{color:white!important;margin:0}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:10px}.name{font-size:1.22rem;font-weight:750;color:var(--navy)}.muted,.small{color:var(--muted);font-size:.84rem}.score{font-size:2.2rem;font-weight:800;color:var(--navy)}.metric-row{margin:12px 0}.metric-top{display:flex;justify-content:space-between;font-size:.9rem;margin-bottom:5px}.track{height:9px;background:#edf1f5;border-radius:999px;overflow:hidden}.fill{height:9px;background:var(--blue);border-radius:999px}div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:16px;border-radius:14px}.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}</style>""",unsafe_allow_html=True)

ROOT=Path(__file__).parent
enriched=json.loads((ROOT/"data"/"companies.json").read_text())
chamber_cache=json.loads((ROOT/"data"/"chamber_cache.json").read_text()) if (ROOT/"data"/"chamber_cache.json").exists() else {}
AI={
"Publix Super Markets":{"ai_score":84,"confidence":88,"sponsor_tier":"High potential","recommended_ask":"$2,500–$7,500","outreach_angle":"Community impact + student development","summary":"Publix combines substantial community giving with a headquarters presence in Lakeland and formal donation/sponsorship request channels.","strengths":["Formal community-giving and sponsorship process","Large local headquarters presence","Documented education and youth giving"],"risks":["Current evidence is less engineering-specific","Large-company requests may be competitive"],"next_steps":["Confirm the local community-relations contact","Frame the ask around STEM student development","Reference a specific SHPE event package"]},
"Lakeland Electric":{"ai_score":93,"confidence":94,"sponsor_tier":"Very high potential","recommended_ask":"$1,000–$5,000","outreach_angle":"STEAM education + local engineering workforce","summary":"Lakeland Electric is one of the strongest local prospects, with community giving, recurring sponsorships, STEAM scholarships, and direct relevance to engineering careers.","strengths":["Recurring community sponsorship program","STEAM scholarship activity","Strong technical workforce relevance","Very strong local alignment"],"risks":["Public-sector rules may limit flexibility","Sponsorship windows may follow annual cycles"],"next_steps":["Locate community-giving or communications contact","Lead with STEAM workforce development","Ask about annual sponsorship timing"]},
"GEICO":{"ai_score":74,"confidence":75,"sponsor_tier":"Moderate potential","recommended_ask":"$1,000–$3,000","outreach_angle":"Career readiness + local student engagement","summary":"GEICO is a credible local prospect because of its Lakeland employment presence and documented community-giving programs, with a weaker direct engineering sponsorship signal.","strengths":["Large local employment presence","Documented community giving","Technology and analytics career relevance"],"risks":["Weak direct STEM sponsorship evidence","May prioritize broader community causes"],"next_steps":["Verify local recruiting/community-relations contact","Emphasize technology and analytics careers","Start with an event-specific ask"]},
"Hypertherm Associates":{"ai_score":96,"confidence":96,"sponsor_tier":"Very high potential","recommended_ask":"$3,000–$10,000","outreach_angle":"STEM education + engineering recruiting + community grants","summary":"Hypertherm Associates is an exceptionally strong Dartmouth-area fit through Upper Valley grantmaking, STEM and robotics support, internships, and an engineering-heavy business profile.","strengths":["Dedicated Upper Valley grantmaking","Explicit STEM and robotics support","Advanced-manufacturing alignment","Student and internship engagement"],"risks":["Grant eligibility may apply","Large asks may require a formal cycle"],"next_steps":["Review foundation eligibility and timing","Lead with engineering talent and STEM access","Offer a multi-event partnership"]},
"Dartmouth Health":{"ai_score":88,"confidence":91,"sponsor_tier":"High potential","recommended_ask":"$2,500–$7,500","outreach_angle":"Student development + technology/healthcare careers","summary":"Dartmouth Health is a strong regional candidate with major community-benefit activity, internships, training pathways, and university relationships.","strengths":["Major community-benefit investment","Paid internship programs","University/workforce relationships","Large technical employer"],"risks":["Healthcare is broader than core engineering","Formal approval processes may apply"],"next_steps":["Target workforce development or recruiting","Highlight computing/data/biomedical interests","Propose a career-development sponsorship"]},
"King Arthur Baking Company":{"ai_score":69,"confidence":82,"sponsor_tier":"Moderate potential","recommended_ask":"$500–$2,500","outreach_angle":"Community partnership + event support","summary":"King Arthur Baking has a strong Upper Valley presence and formal community giving, but weaker direct engineering and technical recruiting alignment.","strengths":["Formal community-giving program","Strong local presence","Recognizable regional brand"],"risks":["Limited engineering alignment","Better suited to smaller or in-kind support"],"next_steps":["Explore event-level support first","Connect the ask to local student impact","Keep the first ask specific"]}}
for c in enriched:
    if c.get("company") in AI: c["ai_analysis"]=AI[c["company"]]

with st.sidebar:
    st.markdown("### ◆ SHPE"); st.caption("FUNDING DISCOVERY"); st.write("")
    page=st.radio("Navigation",["Discovery","Scoring model","Evidence sources","About"],label_visibility="collapsed")
    st.markdown("---"); st.caption("Real organizations • transparent scoring")

st.markdown("""<div class="hero"><div style="color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em">FUNDRAISING INTELLIGENCE</div><h1>SHPE Funding Discovery</h1><p>Discover nearby organizations and inspect AI-assisted sponsorship potential.</p></div>""",unsafe_allow_html=True)

def scored_rows(center_name,radius):
    center=CENTERS[center_name]; out=[]
    for c in enriched:
        score,parts,dist=calculate(c,center)
        if dist<=radius: out.append({"company":c["company"],"lat":c["lat"],"lon":c["lon"],"distance":dist,"score":score,"parts":parts,"record":c,"status":"Scored"})
    return out

def lead_rows(center_name,radius):
    center=CENTERS[center_name]; out=[]
    for c in chamber_cache.get(center_name,[]):
        if c.get("lat") is None or c.get("lon") is None: continue
        dist=round(haversine_miles(center["lat"],center["lon"],c["lat"],c["lon"]),1)
        if dist<=radius: out.append({"company":c["company"],"lat":c["lat"],"lon":c["lon"],"distance":dist,"score":None,"parts":None,"record":c,"status":"Needs enrichment"})
    return out

if page=="Discovery":
    c1,c2,c3,c4=st.columns([1.35,.8,1,1])
    with c1: center_name=st.selectbox("University area",list(CENTERS))
    with c2: radius=st.radio("Radius",RADII,horizontal=True,format_func=lambda x:f"{x} mi")
    with c3: view=st.selectbox("Records",["All organizations","Scored only","Needs enrichment"])
    with c4: minimum=st.selectbox("Minimum scored fit",[0,50,60,70,80,90],format_func=lambda x:"Any score" if x==0 else f"{x}+")
    center=CENTERS[center_name]; scored=[r for r in scored_rows(center_name,radius) if r["score"]>=minimum]; leads=lead_rows(center_name,radius)
    rows=scored if view=="Scored only" else leads if view=="Needs enrichment" else scored+leads
    rows=sorted(rows,key=lambda r:(r["score"] is None,-(r["score"] or 0),r["distance"]))
    m1,m2,m3,m4=st.columns(4); m1.metric("Organizations",len(rows)); m2.metric("Scored prospects",len(scored)); m3.metric("Local businesses",len(leads)); m4.metric("AI analyses",sum(bool(r["record"].get("ai_analysis")) for r in rows))
    left,right=st.columns([1.45,1],gap="large")
    with left:
        st.subheader("Local sponsor map")
        if rows:
            df=pd.DataFrame([{"lat":r["lat"],"lon":r["lon"],"company":r["company"],"score":r["record"].get("ai_analysis",{}).get("ai_score",r["score"] if r["score"] is not None else "Open"),"color":[0,103,185,185],"radius":620} for r in rows])
            st.pydeck_chart(pdk.Deck(layers=[pdk.Layer("ScatterplotLayer",df,get_position="[lon,lat]",get_radius="radius",get_fill_color="color",pickable=True)],initial_view_state=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.4),tooltip={"text":"{company}\nScore: {score}"}),use_container_width=True)
    with right:
        st.subheader("Organizations"); st.caption("Click a company score to open its analysis.")
        if rows and st.session_state.get("selected_company") not in [r["company"] for r in rows]: st.session_state.selected_company=rows[0]["company"]
        for r in rows[:40]:
            a,b=st.columns([4,1])
            with a: st.markdown(f"**{r['company']}**"); st.caption(f"{r['distance']} mi")
            with b:
                display=r["record"].get("ai_analysis",{}).get("ai_score",r["score"] if r["score"] is not None else "Open")
                if st.button(str(display),key="open_"+r["company"],use_container_width=True): st.session_state.selected_company=r["company"]; st.rerun()
    if rows:
        selected=next((r for r in rows if r["company"]==st.session_state.get("selected_company")),rows[0]); rec=selected["record"]; ai=rec.get("ai_analysis")
        st.markdown("---"); st.subheader(selected["company"])
        p1,p2=st.columns([3,1],gap="large")
        with p1:
            st.markdown(f"""<div class="card"><div class="name">{selected['company']}</div><div class="muted">{rec.get('address') or rec.get('city','')} · {selected['distance']} miles from {center_name}</div><p>{rec.get('summary','Local organization discovered for sponsorship research.')}</p></div>""",unsafe_allow_html=True)
        with p2:
            if ai: st.markdown(f"""<div class="card" style="text-align:center"><div class="small">AI SPONSOR SCORE</div><div class="score">{ai['ai_score']}<span style="font-size:1rem">/100</span></div><b>{ai['sponsor_tier']}</b><div class="small">Confidence {ai['confidence']}/100</div></div>""",unsafe_allow_html=True)
            elif selected["score"] is not None: st.markdown(f"""<div class="card" style="text-align:center"><div class="small">BASELINE SCORE</div><div class="score">{selected['score']}<span style="font-size:1rem">/100</span></div><b>AI analysis pending</b></div>""",unsafe_allow_html=True)
            else: st.markdown("""<div class="card" style="text-align:center"><div class="small">SPONSOR SCORE</div><div class="score">—</div><b>Enrichment pending</b></div>""",unsafe_allow_html=True)
        website=rec.get("website",""); contact=rec.get("contact_page",""); email=rec.get("contact_email",""); profile=rec.get("profile_url","")
        x,y,z=st.columns(3)
        with x:
            if website: st.link_button("Visit company website",website,use_container_width=True)
            elif profile: st.link_button("Open directory listing",profile,use_container_width=True)
        with y:
            if email: st.link_button("Email company",f"mailto:{email}",use_container_width=True)
            elif contact: st.link_button("Open contact page",contact,use_container_width=True)
        with z:
            if profile: st.link_button("View discovery source",profile,use_container_width=True)
        if ai:
            st.markdown("### AI sponsorship analysis"); a1,a2,a3=st.columns(3); a1.metric("AI score",f"{ai['ai_score']}/100"); a2.metric("Confidence",f"{ai['confidence']}/100"); a3.metric("Suggested ask",ai["recommended_ask"])
            st.markdown(f"**Recommended outreach angle:** {ai['outreach_angle']}"); st.write(ai["summary"])
            q1,q2=st.columns(2,gap="large")
            with q1:
                st.markdown("#### Strongest signals")
                for item in ai["strengths"]: st.markdown(f"✓ {item}")
                st.markdown("#### Recommended next steps")
                for i,item in enumerate(ai["next_steps"],1): st.markdown(f"**{i}.** {item}")
            with q2:
                st.markdown("#### Things to verify")
                for item in ai["risks"]: st.markdown(f"• {item}")
                if selected["score"] is not None: st.markdown("#### AI vs. baseline"); st.write(f"**AI:** {ai['ai_score']}/100"); st.write(f"**Weighted baseline:** {selected['score']}/100")
        if selected["score"] is not None:
            st.markdown("### Transparent metric breakdown")
            labels={"philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment","recruiting_talent":"Recruiting / student talent","past_sponsorships":"Previous sponsorship behavior","industry_fit":"Industry relevance to SHPE","local_presence":"Local presence","financial_capacity":"Financial capacity","proximity":"Geographic proximity","university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment","evidence_quality":"Evidence quality"}
            l,r=st.columns([1.15,1],gap="large")
            with l:
                for k,w in WEIGHTS.items():
                    v=selected["parts"][k]; st.markdown(f"""<div class="metric-row"><div class="metric-top"><b>{labels[k]}</b><span>{v}/100 · {round(w*100)}%</span></div><div class="track"><div class="fill" style="width:{v}%"></div></div></div>""",unsafe_allow_html=True)
            with r:
                st.markdown("#### Verified evidence")
                for s in rec.get("sources",[]): st.markdown(f"**[{s['title']}]({s['url']})**")

elif page=="Scoring model":
    st.subheader("Transparent scoring model"); st.write("The AI assessment is shown alongside a deterministic weighted baseline so the recommendation remains explainable.")
    st.dataframe(pd.DataFrame([{"Metric":k.replace('_',' ').title(),"Weight":f"{int(v*100)}%"} for k,v in WEIGHTS.items()]),use_container_width=True,hide_index=True)
elif page=="Evidence sources":
    st.subheader("Evidence & discovery ledger"); records=[]
    for c in enriched:
        for s in c.get("sources",[]): records.append({"Organization":c["company"],"Source":s["title"],"Official":s.get("official",False),"URL":s["url"]})
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True,column_config={"URL":st.column_config.LinkColumn("URL")})
else:
    st.subheader("About"); st.write("SHPE Funding Discovery combines local business discovery, transparent weighted scoring, and evidence-grounded AI sponsorship analysis. Unverified information is treated as unknown rather than invented.")
