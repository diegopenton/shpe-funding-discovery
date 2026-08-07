
import json
from pathlib import Path
import pandas as pd
import pydeck as pdk
import streamlit as st

from src.config import CENTERS, RADII
from src.scoring import calculate, WEIGHTS

st.set_page_config(page_title="SHPE Funding Discovery", page_icon="◆", layout="wide")

st.markdown("""
<style>
:root { --navy:#0b1f3a; --blue:#0067b9; --ink:#15263b; --muted:#6b7b8f; --line:#e3e9f0; --bg:#f6f8fb; }
.stApp { background:var(--bg); }
.block-container { max-width:1500px; padding-top:1.2rem; }
[data-testid="stSidebar"] { background:var(--navy); }
[data-testid="stSidebar"] * { color:#eef5fb!important; }
.hero {background:linear-gradient(120deg,#0b1f3a,#123b65);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}
.hero h1{color:white!important;margin:0;font-size:2rem!important}.hero p{color:#cbd9e8;margin:.4rem 0 0}
.eyebrow{color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:10px}
.name{font-size:1.22rem;font-weight:750;color:var(--navy)}.muted{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;background:#eaf4fb;color:#0b5e93;border-radius:999px;padding:4px 9px;margin:5px 5px 0 0;font-size:.75rem;font-weight:700}
.score{font-size:2.2rem;font-weight:800;color:var(--navy)}.small{font-size:.78rem;color:var(--muted)}
.metric-row{margin:12px 0}.metric-top{display:flex;justify-content:space-between;font-size:.9rem;margin-bottom:5px}
.track{height:9px;background:#edf1f5;border-radius:999px;overflow:hidden}.fill{height:9px;background:var(--blue);border-radius:999px}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:16px;border-radius:14px}
.stButton>button{border-radius:10px;font-weight:650}
</style>
""", unsafe_allow_html=True)

companies = json.loads((Path(__file__).parent/"data"/"companies.json").read_text())

with st.sidebar:
    st.markdown("### ◆ SHPE")
    st.caption("FUNDING DISCOVERY")
    st.write("")
    page = st.radio("Navigation", ["Discovery", "Chamber leads", "Scoring model", "Evidence sources"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Real organizations • first-party evidence")
    st.caption("No LLM required")

st.markdown("""
<div class="hero"><div class="eyebrow">Fundraising Intelligence</div>
<h1>SHPE Funding Discovery</h1>
<p>Find local sponsor prospects, understand their score, and inspect the evidence behind it.</p></div>
""", unsafe_allow_html=True)

if page == "Discovery":
    c1,c2,c3 = st.columns([1.4,.8,1])
    with c1:
        center_name = st.selectbox("University area", list(CENTERS))
    with c2:
        radius = st.radio("Radius", RADII, horizontal=True, format_func=lambda x:f"{x} mi")
    center = CENTERS[center_name]

    rows=[]
    for c in companies:
        score, parts, dist = calculate(c, center)
        if dist <= radius:
            rows.append({**c, "score":score, "parts":parts, "distance":dist})
    rows = sorted(rows, key=lambda x:(-x["score"], x["distance"]))

    with c3:
        min_score = st.selectbox("Minimum sponsor score", [0,50,60,70,80,90], index=0,
                                 format_func=lambda x:"Show all" if x==0 else f"{x}+")
    rows=[r for r in rows if r["score"]>=min_score]

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Organizations", len(rows))
    m2.metric("80+ prospects", sum(r["score"]>=80 for r in rows))
    m3.metric("10-mile prospects", sum(r["distance"]<=10 for r in rows))
    m4.metric("Official evidence links", sum(len(r["sources"]) for r in rows))

    left,right=st.columns([1.45,1], gap="large")
    with left:
        st.subheader("Local prospect map")
        if rows:
            map_df=pd.DataFrame([{"lat":r["lat"],"lon":r["lon"],"company":r["company"],"score":r["score"]} for r in rows])
            layer=pdk.Layer("ScatterplotLayer",map_df,get_position="[lon, lat]",get_radius=650,
                            get_fill_color="[0,103,185,180]",pickable=True)
            view=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.2)
            st.pydeck_chart(pdk.Deck(layers=[layer],initial_view_state=view,
                                     tooltip={"text":"{company}\\nSponsor score: {score}/100"}),use_container_width=True)
        else:
            st.info("No verified seed organizations match this filter.")
    with right:
        st.subheader("Ranked prospects")
        if "selected" not in st.session_state and rows:
            st.session_state.selected=rows[0]["company"]
        for r in rows:
            a,b=st.columns([4.3,1])
            with a:
                st.markdown(f"**{r['company']}**")
                st.caption(f"{r['industry']} · {r['city']} · {r['distance']} mi")
            with b:
                if st.button(str(r["score"]), key="open_"+r["company"], use_container_width=True,
                             help="Open sponsor profile"):
                    st.session_state.selected=r["company"]
                    st.rerun()

    if rows:
        selected = next((r for r in rows if r["company"]==st.session_state.get("selected")), rows[0])
        st.markdown("---")
        st.subheader("Company sponsorship profile")
        top1,top2=st.columns([3,1])
        with top1:
            st.markdown(f"""<div class="card"><div class="name">{selected['company']}</div>
            <div class="muted">{selected['industry']} · {selected['city']} · {selected['distance']} miles from {center_name}</div>
            <span class="badge">{selected['local_presence'].replace('_',' ').title()}</span>
            <span class="badge">{selected['capacity_tier'].title()} capacity tier</span>\n            <span class="badge">{selected.get('discovery_source', 'Direct research')}</span>
            <p style="margin-top:14px">{selected['summary']}</p>\n            <div class="small"><b>Evidence status:</b> {selected.get('evidence_status', 'Company sources enriched')}</div></div>""",unsafe_allow_html=True)
        with top2:
            label="High priority" if selected["score"]>=80 else "Promising" if selected["score"]>=65 else "Needs review"
            st.markdown(f"""<div class="card" style="text-align:center">
            <div class="small">SPONSOR SCORE</div><div class="score">{selected['score']}<span style="font-size:1rem">/100</span></div>
            <b>{label}</b><div class="small" style="margin-top:7px">Deterministic weighted score</div></div>""",unsafe_allow_html=True)

        a,b=st.columns([1.15,1],gap="large")
        labels={
          "philanthropy":"Philanthropy & community giving",
          "stem_education":"STEM / education alignment",
          "recruiting_talent":"Recruiting / student talent",
          "past_sponsorships":"Previous sponsorship behavior",
          "industry_fit":"Industry relevance to SHPE",
          "local_presence":"Local presence",
          "financial_capacity":"Financial capacity",
          "proximity":"Geographic proximity",
          "university_engagement":"University engagement",
          "dei_shpe_alignment":"DEI / SHPE alignment",
          "evidence_quality":"Evidence quality",
        }
        with a:
            st.markdown("#### Score breakdown")
            for k,w in WEIGHTS.items():
                value=selected["parts"][k]
                st.markdown(f"""<div class="metric-row">
                <div class="metric-top"><b>{labels[k]}</b><span>{value}/100 · {round(w*100)}%</span></div>
                <div class="track"><div class="fill" style="width:{value}%"></div></div></div>""",unsafe_allow_html=True)
        with b:
            st.markdown("#### Verified evidence")
            for s in selected["sources"]:
                date=f" · {s['date']}" if s.get("date") else ""
                st.markdown(f"**[{s['title']}]({s['url']})**  \n<span class='small'>Official source{date}</span>",unsafe_allow_html=True)
            st.info("A missing signal means 'not verified in this prototype' — not necessarily 'no'.")


elif page=="Chamber leads":
    st.subheader("Local Chamber lead pool")
    st.caption("Real organizations discovered from nearby Chamber / business-alliance directories. Run the refresh script to target 100 per university area.")

    chamber_cache_path=Path(__file__).parent/"data"/"chamber_cache.json"
    chamber_cache=json.loads(chamber_cache_path.read_text()) if chamber_cache_path.exists() else {}
    area=st.selectbox("University area",list(CENTERS),key="chamber_area")
    leads=chamber_cache.get(area,[])

    a,b,c,d=st.columns(4)
    a.metric("Cached Chamber leads",len(leads))
    b.metric("Target",100)
    c.metric("Company websites",sum(bool(x.get("website")) for x in leads))
    d.metric("Verified public emails",sum(bool(x.get("contact_email")) for x in leads))

    st.info("To populate/refresh up to 100 real directory leads per university, run:  python refresh_chamber_data.py --target-per-region 100")

    if leads:
        options=[x["company"] for x in leads]
        selected_name=st.selectbox("Open Chamber-listed organization",options)
        lead=next(x for x in leads if x["company"]==selected_name)
        st.markdown(f"""<div class="card">
        <div class="name">{lead['company']}</div>
        <div class="muted">{lead.get('address','')}</div>
        <span class="badge">{lead.get('discovery_source','Chamber directory')}</span>
        <p style="margin-top:12px"><b>Phone:</b> {lead.get('phone') or 'Not listed'}</p>
        </div>""",unsafe_allow_html=True)

        x,y,z=st.columns(3)
        with x:
            if lead.get("website"):
                st.link_button("Visit company website",lead["website"],use_container_width=True)
            else:
                st.link_button("Open Chamber listing",lead.get("profile_url","#"),use_container_width=True)
        with y:
            if lead.get("contact_email"):
                st.link_button("Email company",f"mailto:{lead['contact_email']}",use_container_width=True)
                st.caption(lead["contact_email"])
            elif lead.get("contact_page"):
                st.link_button("Open company contact page",lead["contact_page"],use_container_width=True)
                st.caption("No public email verified")
            else:
                st.link_button("Open Chamber listing",lead.get("profile_url","#"),use_container_width=True)
                st.caption("Public email not yet verified")
        with z:
            st.caption("Contact data is only displayed when found publicly; the app does not guess email addresses.")

        table=pd.DataFrame(leads)
        cols=[c for c in ["company","address","phone","website","contact_email","discovery_source"] if c in table.columns]
        st.dataframe(table[cols],use_container_width=True,hide_index=True,
                     column_config={"website":st.column_config.LinkColumn("Website")})

elif page=="Scoring model":
    st.subheader("Transparent 100-point scoring model")
    names={
      "philanthropy":"Philanthropy & community giving","stem_education":"STEM / education alignment",
      "recruiting_talent":"Recruiting / talent alignment","past_sponsorships":"Previous sponsorship behavior",
      "industry_fit":"Industry relevance to SHPE","local_presence":"Local presence",
      "financial_capacity":"Financial capacity","proximity":"Geographic proximity",
      "university_engagement":"University engagement","dei_shpe_alignment":"DEI / SHPE alignment",
      "evidence_quality":"Evidence quality / recency"
    }
    st.dataframe(pd.DataFrame([{"Metric":names[k],"Weight":f"{int(v*100)}%"} for k,v in WEIGHTS.items()]),
                 use_container_width=True,hide_index=True)
    st.markdown("The score is computed from structured evidence flags and organization metadata. **No LLM generates the score.**")

elif page=="Evidence sources":
    st.subheader("Evidence ledger")
    records=[]
    for c in companies:
        for s in c["sources"]:
            records.append({"Organization":c["company"],"Region":c["city"],"Source":s["title"],
                            "Official":s["official"],"Date":s.get("date") or "Undated","URL":s["url"]})
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True,
                 column_config={"URL":st.column_config.LinkColumn("URL")})
    st.caption("Production ingestion should preserve this source-level traceability for every scored signal.")
