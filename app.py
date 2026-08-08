import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.config import CENTERS, RADII
from src.scoring import calculate, WEIGHTS, haversine_miles

st.set_page_config(
    page_title="SHPE Funding Discovery",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root{--navy:#0b1f3a;--blue:#0067b9;--muted:#6b7b8f;--line:#e3e9f0;--bg:#f6f8fb}
*{box-sizing:border-box}
html,body,[data-testid="stAppViewContainer"]{overflow-x:hidden}
.stApp{background:var(--bg)}
.block-container{max-width:1500px;padding-top:1.1rem;padding-bottom:2rem}

/* Collapsible SHPE navigation drawer */
[data-testid="stSidebar"]{
    background:var(--navy);
    transition:transform .22s ease,width .22s ease;
}
[data-testid="stSidebar"] *{color:#eef5fb!important}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button{
    background:var(--navy)!important;
    color:white!important;
    border:1px solid rgba(255,255,255,.28)!important;
    border-radius:999px!important;
    width:38px!important;
    height:38px!important;
    min-width:38px!important;
    padding:0!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    box-shadow:0 3px 12px rgba(11,31,58,.18)!important;
}
[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="stSidebarCollapsedControl"] button svg{display:none!important}
[data-testid="stSidebarCollapseButton"] button::after{
    content:"‹";
    color:white;
    font-size:30px;
    line-height:1;
    transform:translateY(-1px);
}
[data-testid="stSidebarCollapsedControl"] button::after{
    content:"›";
    color:white;
    font-size:30px;
    line-height:1;
    transform:translateY(-1px);
}
[data-testid="stSidebarCollapsedControl"]{z-index:999999!important}

.hero{background:linear-gradient(120deg,#0b1f3a,#123b65);padding:22px 26px;border-radius:18px;color:white;margin-bottom:16px}
.hero h1{color:white!important;margin:0}
.hero p{margin:.35rem 0 0}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:10px}
.name{font-size:1.2rem;font-weight:750;color:var(--navy)}
.muted,.small{color:var(--muted);font-size:.84rem}
.badge{display:inline-block;background:#eaf4fb;color:#0b5e93;border-radius:999px;padding:4px 9px;margin:5px 5px 0 0;font-size:.75rem;font-weight:700}
.badge.green{background:#eaf6f1;color:#177d62}
.badge.gray{background:#eef1f4;color:#5d6874}
.metric-row{margin:11px 0}
.metric-top{display:flex;justify-content:space-between;gap:10px;font-size:.88rem;margin-bottom:5px}
.track{height:8px;background:#edf1f5;border-radius:999px;overflow:hidden}
.fill{height:8px;background:var(--blue);border-radius:999px}
.status-grid{display:grid;grid-template-columns:1fr 1.2fr;gap:12px;margin:8px 0 12px}
.status-card{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;min-height:92px}
.status-label{font-size:.82rem;color:var(--muted);margin-bottom:8px}
.status-value{font-size:1.55rem;line-height:1.15;font-weight:650;color:var(--navy);overflow-wrap:anywhere}
.status-value.assessment{font-size:1.05rem;line-height:1.25}
.status-sub{font-size:.76rem;color:var(--muted);margin-top:5px}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:14px;border-radius:14px}
.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}
div[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:14px!important;background:white!important}
div[data-testid="stExpander"] summary{font-weight:700!important;color:var(--navy)!important}

/* Phone layout */
@media(max-width:768px){
    .block-container{max-width:100%;padding:.65rem .72rem 1.5rem!important}
    .hero{padding:16px 17px;border-radius:14px;margin-bottom:12px}
    .hero h1{font-size:1.55rem!important;line-height:1.15!important}
    .hero p{font-size:.88rem!important;line-height:1.35!important}
    .hero>div{font-size:.62rem!important}

    /* Stack Streamlit columns rather than squeezing desktop panels */
    div[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.65rem!important}
    div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{
        flex:1 1 100%!important;
        width:100%!important;
        min-width:0!important;
    }

    .status-grid{grid-template-columns:1fr 1fr;gap:8px}
    .status-card{min-height:80px;padding:12px}
    .status-value{font-size:1.28rem}
    .status-value.assessment{font-size:.92rem}
    .card{padding:14px}
    .name{font-size:1.08rem}
    .muted,.small{font-size:.78rem}
    div[data-testid="stMetric"]{padding:11px!important}
    div[data-testid="stMetricValue"]{font-size:1.35rem!important}
    div[data-testid="stMetricLabel"]{font-size:.76rem!important}

    /* Make tabs usable with a thumb on narrow screens */
    div[data-baseweb="tab-list"]{overflow-x:auto!important;flex-wrap:nowrap!important;scrollbar-width:none}
    div[data-baseweb="tab-list"]::-webkit-scrollbar{display:none}
    button[data-baseweb="tab"]{white-space:nowrap!important;font-size:.82rem!important;padding-left:.65rem!important;padding-right:.65rem!important}

    /* Keep tables and maps inside the phone viewport */
    [data-testid="stDataFrame"], [data-testid="stDeckGlJsonChart"]{max-width:100%!important;overflow:hidden!important}
    .stButton>button,.stLinkButton>a{min-height:42px!important}

    /* Mobile drawer arrow stays easy to reach */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapsedControl"] button{
        width:42px!important;height:42px!important;min-width:42px!important
    }
    [data-testid="stSidebarCollapsedControl"]{top:.45rem!important;left:.35rem!important}
}

@media(max-width:430px){
    .status-grid{grid-template-columns:1fr}
    .hero h1{font-size:1.4rem!important}
}
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent

def load_json(name, default):
    path = ROOT / "data" / name
    return json.loads(path.read_text()) if path.exists() else default

enriched = load_json("companies.json", [])
national = load_json("shpe_national_relationships.json", {})
sponsors = load_json("shpe_sponsors.json", {})
public_websites = load_json("public_websites.json", {})
public_evidence = load_json("public_evidence.json", {})

chamber = load_json("chamber_cache.json", {})
for supplemental in ("chamber_extra.json", "chamber_more.json", "chamber_dense.json"):
    extra = load_json(supplemental, {})
    for area, entries in extra.items():
        chamber.setdefault(area, []).extend(entries)

for area, entries in list(chamber.items()):
    merged = {}
    for item in entries:
        key = item.get("company", "").strip().casefold()
        if not key:
            continue
        if key not in merged:
            merged[key] = item
        else:
            existing = merged[key]
            for field in ("website","contact_email","contact_page","phone","address","profile_url","lat","lon"):
                if not existing.get(field) and item.get(field):
                    existing[field] = item[field]
    chamber[area] = list(merged.values())

AI = {
    "Publix Super Markets": (84,88,"High potential","$2,500–$7,500","Community impact + student development"),
    "Lakeland Electric": (93,94,"Very high potential","$1,000–$5,000","STEAM education + local engineering workforce"),
    "GEICO": (74,75,"Moderate potential","$1,000–$3,000","Career readiness + local student engagement"),
    "Hypertherm Associates": (96,96,"Very high potential","$3,000–$10,000","STEM education + engineering recruiting + community grants"),
    "Dartmouth Health": (88,91,"High potential","$2,500–$7,500","Student development + technology/healthcare careers"),
    "King Arthur Baking Company": (69,82,"Moderate potential","$500–$2,500","Community partnership + event support"),
}
for company in enriched:
    if company["company"] in AI and not company.get("ai_analysis"):
        a = AI[company["company"]]
        company["ai_analysis"] = {
            "ai_score":a[0],"confidence":a[1],"sponsor_tier":a[2],
            "recommended_ask":a[3],"outreach_angle":a[4],
            "summary":company.get("summary",""),"strengths":[],"risks":[],"next_steps":[]
        }

BLOCKED_HOST_PARTS=("epiint.","integration.","staging.","localhost","127.0.0.1")
BLOCKED_PATH_PARTS=("/login","/signin","/sign-in","/sso","/auth","/account/login")

def is_public_url(url):
    if not url or not url.startswith(("http://","https://")):
        return False
    parsed=urlparse(url)
    return not any(x in parsed.netloc.lower() for x in BLOCKED_HOST_PARTS) and not any(x in parsed.path.lower() for x in BLOCKED_PATH_PARTS)

def company_website(record):
    mapped=public_websites.get(record.get("company",""))
    if mapped and is_public_url(mapped):
        return mapped
    candidate=record.get("website","")
    return candidate if is_public_url(candidate) else ""

def safe_profile_url(record):
    url=record.get("profile_url","")
    return url if is_public_url(url) else ""

def national_relationship(name):
    return national.get(name)

def sponsor_relationship(name):
    return sponsors.get(name)

def scored_rows(center_name,radius):
    center=CENTERS[center_name]
    out=[]
    for company in enriched:
        score,parts,distance=calculate(company,center)
        if distance<=radius:
            out.append({"company":company["company"],"lat":company["lat"],"lon":company["lon"],"distance":distance,"score":score,"parts":parts,"record":company,"status":"analyzed"})
    return out

def chamber_rows(center_name,radius):
    center=CENTERS[center_name]
    out=[]
    for company in chamber.get(center_name,[]):
        if company.get("lat") is None or company.get("lon") is None:
            continue
        distance=round(haversine_miles(center["lat"],center["lon"],company["lat"],company["lon"]),1)
        if distance<=radius:
            out.append({"company":company["company"],"lat":company["lat"],"lon":company["lon"],"distance":distance,"score":None,"parts":None,"record":company,"status":"local"})
    return out

def description_for(row):
    record=row["record"]
    if record.get("summary"):
        return record["summary"]
    source=record.get("discovery_source","a local business directory")
    text=f"{row['company']} is a local organization listed by {source}."
    if record.get("phone"):
        text+=f" Public business phone: {record['phone']}."
    return text

def display_evidence(record):
    return [item for item in public_evidence.get(record.get("company",""),[]) if is_public_url(item.get("url",""))]

def sync_company_picker():
    picked=st.session_state.get("company_picker")
    if picked:
        st.session_state.selected_company=picked

with st.sidebar:
    st.markdown("### ◆ SHPE")
    st.caption("FUNDING DISCOVERY")
    st.write("")
    page=st.radio("Navigation",["Discovery","Scoring model","Evidence sources","About"],label_visibility="collapsed")

st.markdown("""<div class="hero"><div style="color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em">FUNDRAISING INTELLIGENCE</div><h1>SHPE Funding Discovery</h1><p>Discover nearby organizations and evaluate sponsorship potential.</p></div>""",unsafe_allow_html=True)

if page=="Discovery":
    # Keep the entire search/filter area hidden until the user opens it.
    with st.expander("Filters", expanded=False):
        c1,c2=st.columns(2)
        with c1:
            center_name=st.selectbox("University area",list(CENTERS))
            view=st.selectbox("Companies",["All companies","Analyzed companies","Local directory companies"])
        with c2:
            radius=st.selectbox("Radius",RADII,format_func=lambda x:f"{x} mi")
            minimum=st.selectbox("Minimum sponsor score",[0,50,60,70,80,90],format_func=lambda x:"Any score" if x==0 else f"{x}+")

        center=CENTERS[center_name]
        analyzed=[r for r in scored_rows(center_name,radius) if r["score"]>=minimum]
        local=chamber_rows(center_name,radius)
        if view=="Analyzed companies": rows=analyzed
        elif view=="Local directory companies": rows=local
        else:
            analyzed_names={r["company"].casefold() for r in analyzed}
            rows=analyzed+[r for r in local if r["company"].casefold() not in analyzed_names]
        rows=sorted(rows,key=lambda r:(r["score"] is None,-(r["score"] or 0),r["distance"]))

        m1,m2,m3,m4=st.columns(4)
        m1.metric("Companies",len(rows)); m2.metric("Analyzed",len(analyzed)); m3.metric("Local directory",len(local)); m4.metric("AI assessments",sum(bool(r["record"].get("ai_analysis")) for r in rows))

        names=[r["company"] for r in rows]
        if rows and st.session_state.get("selected_company") not in names:
            st.session_state.selected_company=rows[0]["company"]
        if rows and st.session_state.get("company_picker") not in names:
            st.session_state.company_picker=st.session_state.selected_company
        if rows:
            st.selectbox("Open company",names,key="company_picker",on_change=sync_company_picker)

    # Recompute current results after the collapsed panel so the rest of the page works normally.
    center=CENTERS[center_name]
    analyzed=[r for r in scored_rows(center_name,radius) if r["score"]>=minimum]
    local=chamber_rows(center_name,radius)
    if view=="Analyzed companies": rows=analyzed
    elif view=="Local directory companies": rows=local
    else:
        analyzed_names={r["company"].casefold() for r in analyzed}
        rows=analyzed+[r for r in local if r["company"].casefold() not in analyzed_names]
    rows=sorted(rows,key=lambda r:(r["score"] is None,-(r["score"] or 0),r["distance"]))

    names=[r["company"] for r in rows]
    if rows and st.session_state.get("selected_company") not in names:
        st.session_state.selected_company=rows[0]["company"]
    selected=next((r for r in rows if r["company"]==st.session_state.get("selected_company")),rows[0] if rows else None)

    left,right=st.columns([1.45,1],gap="large")
    with left:
        st.subheader("Local sponsor map")
        if rows:
            map_df=pd.DataFrame([{"lat":r["lat"],"lon":r["lon"],"company":r["company"],"score":r["record"].get("ai_analysis",{}).get("ai_score",r["score"] if r["score"] is not None else "—")} for r in rows])
            layer=pdk.Layer("ScatterplotLayer",map_df,get_position="[lon,lat]",get_radius=3,radius_units="pixels",radius_scale=1,radius_min_pixels=2,radius_max_pixels=3,get_fill_color=[0,103,185,190],pickable=True,auto_highlight=True,stroked=True,get_line_color=[255,255,255,160],line_width_min_pixels=.5)
            state=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.4)
            st.pydeck_chart(pdk.Deck(layers=[layer],initial_view_state=state,tooltip={"text":"{company}\nScore: {score}"}),use_container_width=True,height=390)

    with right:
        st.subheader("Company profile")
        if not selected:
            st.info("Select a company from the list.")
        else:
            record=selected["record"]; ai=record.get("ai_analysis"); nc=national_relationship(selected["company"]); sp=sponsor_relationship(selected["company"])
            website=company_website(record); profile=safe_profile_url(record); contact=record.get("contact_page",""); email=record.get("contact_email","")
            score_value=ai["ai_score"] if ai else selected["score"]
            score_label=ai.get("sponsor_tier","Research in progress") if ai else ("Analyzed" if selected["score"] is not None else "Research in progress")
            badge_html=('<span class="badge green">SHPE National Contact</span>' if nc else '')+('<span class="badge green">AI analyzed</span>' if ai else '')+('<span class="badge green">Verified SHPE Sponsor</span>' if sp else '')
            st.markdown(f"""<div class="card"><div class="name">{selected['company']}</div><div class="muted">{record.get('address') or record.get('city','')} · {selected['distance']} miles from {center_name}</div>{badge_html}<p style="margin-top:12px">{description_for(selected)}</p></div>""",unsafe_allow_html=True)

            if score_value is not None:
                st.markdown(f"""<div class="status-grid">
                <div class="status-card"><div class="status-label">Sponsor score</div><div class="status-value">{score_value}/100</div></div>
                <div class="status-card"><div class="status-label">Assessment</div><div class="status-value assessment">{score_label}</div><div class="status-sub">{'AI-assisted assessment' if ai else 'Weighted assessment'}</div></div>
                </div>""",unsafe_allow_html=True)
            else:
                st.markdown("""<div class="status-grid"><div class="status-card"><div class="status-label">Sponsor score</div><div class="status-value assessment">Research in progress</div></div></div>""",unsafe_allow_html=True)

            mini_df=pd.DataFrame([{"lat":selected["lat"],"lon":selected["lon"],"company":selected["company"]}])
            mini_layer=pdk.Layer("ScatterplotLayer",mini_df,get_position="[lon,lat]",get_radius=4,radius_units="pixels",radius_min_pixels=3,radius_max_pixels=4,get_fill_color=[0,103,185,210],pickable=True)
            st.pydeck_chart(pdk.Deck(layers=[mini_layer],initial_view_state=pdk.ViewState(latitude=selected["lat"],longitude=selected["lon"],zoom=13),tooltip={"text":"{company}"}),use_container_width=True,height=170)

            tab1,tab2,tab3=st.tabs(["Overview","AI Analysis","Metrics & Evidence"])
            with tab1:
                st.markdown("#### Company links & SHPE status")
                sweb,ssponsor=st.columns(2)
                with sweb:
                    st.markdown("**Website**")
                    if website: st.link_button("Open company website",website,use_container_width=True)
                    elif profile: st.link_button("Open public Chamber listing",profile,use_container_width=True)
                    else: st.button("Website unavailable",disabled=True,use_container_width=True)
                with ssponsor:
                    st.markdown("**SHPE Sponsor**")
                    if sp:
                        st.success(sp.get("label","Verified SHPE Sponsor"))
                        source=sp.get("source_url","")
                        if is_public_url(source): st.link_button("View SHPE sponsor source",source,use_container_width=True)
                    else:
                        st.info("Not verified as a SHPE sponsor")

                if nc:
                    st.markdown("**SHPE National connection**")
                    st.success(nc.get("relationship","Verified relationship"))
                    source_url=nc.get("source_url","")
                    if is_public_url(source_url): st.link_button("View SHPE relationship source",source_url,use_container_width=True)

                st.markdown("**Contact**")
                if email: st.link_button("Email company",f"mailto:{email}",use_container_width=True)
                elif is_public_url(contact): st.link_button("Open contact page",contact,use_container_width=True)
                else: st.caption("No public email/contact page verified.")
                if record.get("phone"): st.write(f"**Phone:** {record['phone']}")
                if record.get("discovery_source"): st.write(f"**Listed by:** {record['discovery_source']}")

            with tab2:
                if ai:
                    a1,a2=st.columns(2); a1.metric("AI score",f"{ai['ai_score']}/100"); a2.metric("Confidence",f"{ai['confidence']}/100")
                    st.write(f"**Suggested ask:** {ai['recommended_ask']}")
                    st.write(f"**Outreach angle:** {ai['outreach_angle']}")
                    st.write(ai.get("summary",""))
                    if ai.get("strengths"):
                        st.markdown("**Strongest signals**")
                        for item in ai["strengths"]: st.write(f"✓ {item}")
                    if ai.get("risks"):
                        st.markdown("**Things to verify**")
                        for item in ai["risks"]: st.write(f"• {item}")
                    if ai.get("next_steps"):
                        st.markdown("**Recommended next steps**")
                        for i,item in enumerate(ai["next_steps"],1): st.write(f"{i}. {item}")
                else:
                    st.info("Sponsorship analysis is being expanded for this company.")

            with tab3:
                if selected["score"] is not None:
                    labels={"philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment","recruiting_talent":"Recruiting / student talent","past_sponsorships":"Previous sponsorship behavior","industry_fit":"Industry relevance to SHPE","local_presence":"Local presence","financial_capacity":"Financial capacity","proximity":"Geographic proximity","university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment","evidence_quality":"Evidence quality"}
                    for key,weight in WEIGHTS.items():
                        value=selected["parts"][key]
                        st.markdown(f"""<div class="metric-row"><div class="metric-top"><b>{labels[key]}</b><span>{value}/100 · {round(weight*100)}%</span></div><div class="track"><div class="fill" style="width:{value}%"></div></div></div>""",unsafe_allow_html=True)
                else:
                    st.info("Detailed sponsorship metrics are not yet available for this company.")
                evidence=display_evidence(record)
                if evidence:
                    st.markdown("**Public evidence**")
                    for item in evidence: st.link_button(item["title"],item["url"],use_container_width=True)
                elif profile:
                    st.link_button("View Chamber listing",profile,use_container_width=True)

    st.markdown("#### Companies")
    if rows:
        list_df=pd.DataFrame([{
            "Company":r["company"],"Miles":r["distance"],
            "Score":r["record"].get("ai_analysis",{}).get("ai_score",r["score"] if r["score"] is not None else None),
            "Website":company_website(r["record"]),
            "SHPE Sponsor":"Verified" if sponsor_relationship(r["company"]) else "Not verified"
        } for r in rows])
        event=st.dataframe(
            list_df,use_container_width=True,hide_index=True,height=330,selection_mode="single-row",on_select="rerun",
            column_config={"Miles":st.column_config.NumberColumn("Miles",format="%.1f"),"Score":st.column_config.NumberColumn("Score",format="%d"),"Website":st.column_config.LinkColumn("Website",display_text="Open")}
        )
        if event.selection.rows:
            picked=list_df.iloc[event.selection.rows[0]]["Company"]
            st.session_state.selected_company=picked
            st.session_state.company_picker=picked

elif page=="Scoring model":
    st.subheader("Scoring model")
    labels={"philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment","recruiting_talent":"Recruiting / talent alignment","past_sponsorships":"Previous sponsorship behavior","industry_fit":"Industry relevance to SHPE","local_presence":"Local presence","financial_capacity":"Financial capacity","proximity":"Geographic proximity","university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment","evidence_quality":"Evidence quality / recency"}
    st.dataframe(pd.DataFrame([{"Metric":labels[k],"Weight":f"{int(v*100)}%"} for k,v in WEIGHTS.items()]),use_container_width=True,hide_index=True)

elif page=="Evidence sources":
    st.subheader("Evidence sources")
    records=[]
    for company in enriched:
        for source in display_evidence(company):
            records.append({"Organization":company["company"],"Source":source["title"],"URL":source["url"]})
    for name,relation in national.items():
        url=relation.get("source_url","")
        if is_public_url(url): records.append({"Organization":name,"Source":relation.get("relationship","SHPE National relationship"),"URL":url})
    for name,relation in sponsors.items():
        url=relation.get("source_url","")
        if is_public_url(url): records.append({"Organization":name,"Source":relation.get("relationship","SHPE sponsor"),"URL":url})
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True,column_config={"URL":st.column_config.LinkColumn("URL")})

else:
    st.subheader("About")
    st.write("SHPE Funding Discovery helps chapters find nearby organizations, compare sponsorship potential, and reach public company contact channels.")