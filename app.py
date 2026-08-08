import json
from pathlib import Path
import pandas as pd
import pydeck as pdk
import streamlit as st
from src.config import CENTERS, RADII
from src.scoring import calculate, WEIGHTS, haversine_miles

st.set_page_config(page_title="SHPE Funding Discovery",page_icon="◆",layout="wide")
st.markdown('''<style>
:root{--navy:#0b1f3a;--blue:#0067b9;--muted:#6b7b8f;--line:#e3e9f0;--bg:#f6f8fb}.stApp{background:var(--bg)}.block-container{max-width:1500px;padding-top:1.2rem}[data-testid="stSidebar"]{background:var(--navy)}[data-testid="stSidebar"] *{color:#eef5fb!important}.hero{background:linear-gradient(120deg,#0b1f3a,#123b65);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}.hero h1{color:white!important;margin:0}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:10px}.name{font-size:1.22rem;font-weight:750;color:var(--navy)}.muted,.small{color:var(--muted);font-size:.84rem}.badge{display:inline-block;background:#eaf4fb;color:#0b5e93;border-radius:999px;padding:4px 9px;margin:5px 5px 0 0;font-size:.75rem;font-weight:700}.badge.green{background:#eaf6f1;color:#177d62}.score{font-size:2.2rem;font-weight:800;color:var(--navy)}.metric-row{margin:12px 0}.metric-top{display:flex;justify-content:space-between;font-size:.9rem;margin-bottom:5px}.track{height:9px;background:#edf1f5;border-radius:999px;overflow:hidden}.fill{height:9px;background:var(--blue);border-radius:999px}div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:16px;border-radius:14px}.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}</style>''',unsafe_allow_html=True)

ROOT=Path(__file__).parent
enriched=json.loads((ROOT/'data/companies.json').read_text())
chamber=json.loads((ROOT/'data/chamber_cache.json').read_text()) if (ROOT/'data/chamber_cache.json').exists() else {}
national=json.loads((ROOT/'data/shpe_national_relationships.json').read_text()) if (ROOT/'data/shpe_national_relationships.json').exists() else {}
AI={
'Publix Super Markets':(84,88,'High potential','$2,500–$7,500','Community impact + student development'),
'Lakeland Electric':(93,94,'Very high potential','$1,000–$5,000','STEAM education + local engineering workforce'),
'GEICO':(74,75,'Moderate potential','$1,000–$3,000','Career readiness + local student engagement'),
'Hypertherm Associates':(96,96,'Very high potential','$3,000–$10,000','STEM education + engineering recruiting + community grants'),
'Dartmouth Health':(88,91,'High potential','$2,500–$7,500','Student development + technology/healthcare careers'),
'King Arthur Baking Company':(69,82,'Moderate potential','$500–$2,500','Community partnership + event support')}
for c in enriched:
    if c['company'] in AI and not c.get('ai_analysis'):
        a=AI[c['company']]; c['ai_analysis']={'ai_score':a[0],'confidence':a[1],'sponsor_tier':a[2],'recommended_ask':a[3],'outreach_angle':a[4],'summary':c.get('summary',''),'strengths':[],'risks':[],'next_steps':[]}

def nat(name): return national.get(name)
def scored(center_name,radius):
    center=CENTERS[center_name]; out=[]
    for c in enriched:
        score,parts,dist=calculate(c,center)
        if dist<=radius: out.append({'company':c['company'],'lat':c['lat'],'lon':c['lon'],'distance':dist,'score':score,'parts':parts,'record':c,'status':'Scored'})
    return out
def leads(center_name,radius):
    center=CENTERS[center_name]; out=[]
    for c in chamber.get(center_name,[]):
        if c.get('lat') is None or c.get('lon') is None: continue
        d=round(haversine_miles(center['lat'],center['lon'],c['lat'],c['lon']),1)
        if d<=radius: out.append({'company':c['company'],'lat':c['lat'],'lon':c['lon'],'distance':d,'score':None,'parts':None,'record':c,'status':'Needs enrichment'})
    return out

with st.sidebar:
    st.markdown('### ◆ SHPE'); st.caption('FUNDING DISCOVERY'); st.write('')
    page=st.radio('Navigation',['Discovery','Scoring model','Evidence sources','About'],label_visibility='collapsed')
    st.markdown('---'); st.caption('Real organizations • transparent scoring')
st.markdown('''<div class="hero"><div style="color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em">FUNDRAISING INTELLIGENCE</div><h1>SHPE Funding Discovery</h1><p>Discover nearby organizations and inspect AI-assisted sponsorship potential.</p></div>''',unsafe_allow_html=True)

if page=='Discovery':
    c1,c2,c3,c4=st.columns([1.35,.8,1,1])
    with c1: center_name=st.selectbox('University area',list(CENTERS))
    with c2: radius=st.radio('Radius',RADII,horizontal=True,format_func=lambda x:f'{x} mi')
    with c3: view=st.selectbox('Records',['All organizations','Scored only','Needs enrichment'])
    with c4: minimum=st.selectbox('Minimum scored fit',[0,50,60,70,80,90],format_func=lambda x:'Any score' if x==0 else f'{x}+')
    center=CENTERS[center_name]; s=[r for r in scored(center_name,radius) if r['score']>=minimum]; l=leads(center_name,radius)
    rows=s if view=='Scored only' else l if view=='Needs enrichment' else s+l
    rows=sorted(rows,key=lambda r:(r['score'] is None,-(r['score'] or 0),r['distance']))
    a,b,c,d=st.columns(4); a.metric('Organizations',len(rows)); b.metric('Scored prospects',len(s)); c.metric('Local businesses',len(l)); d.metric('AI analyses',sum(bool(r['record'].get('ai_analysis')) for r in rows))
    left,right=st.columns([1.45,1],gap='large')
    with left:
        st.subheader('Local sponsor map')
        if rows:
            df=pd.DataFrame([{'lat':r['lat'],'lon':r['lon'],'company':r['company'],'score':r['record'].get('ai_analysis',{}).get('ai_score',r['score'] if r['score'] is not None else 'Open'),'color':[0,103,185,185],'radius':620} for r in rows])
            st.pydeck_chart(pdk.Deck(layers=[pdk.Layer('ScatterplotLayer',df,get_position='[lon,lat]',get_radius='radius',get_fill_color='color',pickable=True)],initial_view_state=pdk.ViewState(latitude=center['lat'],longitude=center['lon'],zoom=9 if radius==25 else 10.4),tooltip={'text':'{company}\nScore: {score}'}),use_container_width=True)
    with right:
        st.subheader('Organizations'); st.caption('Click a company score to open its analysis.')
        if rows and st.session_state.get('selected_company') not in [r['company'] for r in rows]: st.session_state.selected_company=rows[0]['company']
        for r in rows[:40]:
            x,y=st.columns([4,1]); n=nat(r['company'])
            with x:
                st.markdown(f"**{r['company']}**")
                st.caption(f"{r['distance']} mi"+(' · SHPE National Contact' if n else ''))
            with y:
                disp=r['record'].get('ai_analysis',{}).get('ai_score',r['score'] if r['score'] is not None else 'Open')
                if st.button(str(disp),key='open_'+r['company'],use_container_width=True): st.session_state.selected_company=r['company']; st.rerun()
    if rows:
        sel=next((r for r in rows if r['company']==st.session_state.get('selected_company')),rows[0]); rec=sel['record']; ai=rec.get('ai_analysis'); nc=nat(sel['company'])
        st.markdown('---'); st.subheader(sel['company'])
        p1,p2=st.columns([3,1],gap='large')
        with p1:
            badges='<span class="badge green">Evidence scored</span>' if sel['score'] is not None else '<span class="badge">Needs enrichment</span>'
            if nc: badges+='<span class="badge green">SHPE National Contact</span>'
            relationship=f'<div class="small" style="margin-top:8px"><b>SHPE National relationship:</b> {nc["relationship"]} · <a href="{nc["source_url"]}" target="_blank">verify source</a></div>' if nc else ''
            st.markdown(f'''<div class="card"><div class="name">{sel['company']}</div><div class="muted">{rec.get('address') or rec.get('city','')} · {sel['distance']} miles from {center_name}</div>{badges}<p>{rec.get('summary','Local organization discovered for sponsorship research.')}</p>{relationship}</div>''',unsafe_allow_html=True)
        with p2:
            if ai: st.markdown(f'''<div class="card" style="text-align:center"><div class="small">AI SPONSOR SCORE</div><div class="score">{ai['ai_score']}<span style="font-size:1rem">/100</span></div><b>{ai['sponsor_tier']}</b><div class="small">Confidence {ai['confidence']}/100</div></div>''',unsafe_allow_html=True)
            elif sel['score'] is not None: st.markdown(f'''<div class="card" style="text-align:center"><div class="small">BASELINE SCORE</div><div class="score">{sel['score']}<span style="font-size:1rem">/100</span></div><b>AI analysis pending</b></div>''',unsafe_allow_html=True)
            else: st.markdown('''<div class="card" style="text-align:center"><div class="small">SPONSOR SCORE</div><div class="score">—</div><b>Enrichment pending</b></div>''',unsafe_allow_html=True)
        website=rec.get('website',''); contact=rec.get('contact_page',''); email=rec.get('contact_email',''); profile=rec.get('profile_url','')
        x,y,z=st.columns(3)
        with x:
            if website: st.link_button('Visit company website',website,use_container_width=True)
            elif profile: st.link_button('Open directory listing',profile,use_container_width=True)
        with y:
            if email: st.link_button('Email company',f'mailto:{email}',use_container_width=True)
            elif contact: st.link_button('Open contact page',contact,use_container_width=True)
        with z:
            if profile: st.link_button('View discovery source',profile,use_container_width=True)
        if ai:
            st.markdown('### AI sponsorship analysis'); x,y,z=st.columns(3); x.metric('AI score',f"{ai['ai_score']}/100"); y.metric('Confidence',f"{ai['confidence']}/100"); z.metric('Suggested ask',ai['recommended_ask'])
            st.markdown(f"**Recommended outreach angle:** {ai['outreach_angle']}"); st.write(ai.get('summary',''))
            q1,q2=st.columns(2,gap='large')
            with q1:
                st.markdown('#### Strongest signals')
                for item in ai.get('strengths',[]): st.markdown(f'✓ {item}')
                st.markdown('#### Recommended next steps')
                for i,item in enumerate(ai.get('next_steps',[]),1): st.markdown(f'**{i}.** {item}')
            with q2:
                st.markdown('#### Things to verify')
                for item in ai.get('risks',[]): st.markdown(f'• {item}')
                if sel['score'] is not None: st.markdown('#### AI vs. baseline'); st.write(f"**AI:** {ai['ai_score']}/100"); st.write(f"**Weighted baseline:** {sel['score']}/100")
        if sel['score'] is not None:
            st.markdown('### Transparent metric breakdown')
            labels={'philanthropy':'Philanthropy & community giving','stem_education':'STEM / education alignment','recruiting_talent':'Recruiting / student talent','past_sponsorships':'Previous sponsorship behavior','industry_fit':'Industry relevance to SHPE','local_presence':'Local presence','financial_capacity':'Financial capacity','proximity':'Geographic proximity','university_engagement':'University engagement','dei_shpe_alignment':'DEI / SHPE alignment','evidence_quality':'Evidence quality'}
            lcol,rcol=st.columns([1.15,1],gap='large')
            with lcol:
                for k,w in WEIGHTS.items():
                    v=sel['parts'][k]; st.markdown(f'''<div class="metric-row"><div class="metric-top"><b>{labels[k]}</b><span>{v}/100 · {round(w*100)}%</span></div><div class="track"><div class="fill" style="width:{v}%"></div></div></div>''',unsafe_allow_html=True)
            with rcol:
                st.markdown('#### Verified evidence')
                for e in rec.get('sources',[]): st.markdown(f"**[{e['title']}]({e['url']})**")
elif page=='Scoring model':
    st.subheader('Transparent scoring model'); st.write('The AI assessment is shown alongside a deterministic weighted baseline so the recommendation remains explainable.')
    st.dataframe(pd.DataFrame([{'Metric':k.replace('_',' ').title(),'Weight':f'{int(v*100)}%'} for k,v in WEIGHTS.items()]),use_container_width=True,hide_index=True)
elif page=='Evidence sources':
    st.subheader('Evidence & discovery ledger'); records=[]
    for c in enriched:
        for e in c.get('sources',[]): records.append({'Organization':c['company'],'Type':'Scoring evidence','Source':e['title'],'URL':e['url']})
    for name,nc in national.items(): records.append({'Organization':name,'Type':'SHPE National relationship','Source':nc['relationship'],'URL':nc['source_url']})
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True,column_config={'URL':st.column_config.LinkColumn('URL')})
else:
    st.subheader('About'); st.write('SHPE Funding Discovery combines local business discovery, transparent weighted scoring, evidence-grounded AI sponsorship analysis, and verified SHPE National relationship tags. Unverified information is treated as unknown rather than invented.')
