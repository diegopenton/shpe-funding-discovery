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
:root{--navy:#0b1f3a;--blue:#0067b9;--muted:#6b7b8f;--line:#e3e9f0;--bg:#f6f8fb}
.stApp{background:var(--bg)}
.block-container{max-width:1550px;padding-top:1.0rem;padding-bottom:2rem}
[data-testid="stSidebar"]{background:var(--navy)}
[data-testid="stSidebar"] *{color:#eef5fb!important}
.hero{background:linear-gradient(120deg,#0b1f3a,#123b65);padding:22px 26px;border-radius:18px;color:white;margin-bottom:16px}
.hero h1{color:white!important;margin:0}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:10px}
.name{font-size:1.24rem;font-weight:750;color:var(--navy)}
.muted,.small{color:var(--muted);font-size:.84rem}
.badge{display:inline-block;background:#eaf4fb;color:#0b5e93;border-radius:999px;padding:4px 9px;margin:5px 5px 0 0;font-size:.75rem;font-weight:700}
.badge.green{background:#eaf6f1;color:#177d62}
.score{font-size:2.1rem;font-weight:800;color:var(--navy)}
.metric-row{margin:10px 0}
.metric-top{display:flex;justify-content:space-between;font-size:.88rem;margin-bottom:4px}
.track{height:8px;background:#edf1f5;border-radius:999px;overflow:hidden}
.fill{height:8px;background:var(--blue);border-radius:999px}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:14px;border-radius:14px}
.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent
enriched = json.loads((ROOT / "data" / "companies.json").read_text())
chamber = json.loads((ROOT / "data" / "chamber_cache.json").read_text()) if (ROOT / "data" / "chamber_cache.json").exists() else {}
extra_path = ROOT / "data" / "chamber_extra.json"
if extra_path.exists():
    extra = json.loads(extra_path.read_text())
    for area, entries in extra.items():
        chamber.setdefault(area, []).extend(entries)

national = json.loads((ROOT / "data" / "shpe_national_relationships.json").read_text()) if (ROOT / "data" / "shpe_national_relationships.json").exists() else {}

AI = {
    "Publix Super Markets": (84, 88, "High potential", "$2,500–$7,500", "Community impact + student development"),
    "Lakeland Electric": (93, 94, "Very high potential", "$1,000–$5,000", "STEAM education + local engineering workforce"),
    "GEICO": (74, 75, "Moderate potential", "$1,000–$3,000", "Career readiness + local student engagement"),
    "Hypertherm Associates": (96, 96, "Very high potential", "$3,000–$10,000", "STEM education + engineering recruiting + community grants"),
    "Dartmouth Health": (88, 91, "High potential", "$2,500–$7,500", "Student development + technology/healthcare careers"),
    "King Arthur Baking Company": (69, 82, "Moderate potential", "$500–$2,500", "Community partnership + event support"),
}
for company in enriched:
    if company["company"] in AI and not company.get("ai_analysis"):
        a = AI[company["company"]]
        company["ai_analysis"] = {
            "ai_score": a[0], "confidence": a[1], "sponsor_tier": a[2],
            "recommended_ask": a[3], "outreach_angle": a[4],
            "summary": company.get("summary", ""), "strengths": [], "risks": [], "next_steps": [],
        }

def national_relationship(name):
    return national.get(name)

def scored_rows(center_name, radius):
    center = CENTERS[center_name]
    rows = []
    for company in enriched:
        score, parts, distance = calculate(company, center)
        if distance <= radius:
            rows.append({
                "company": company["company"], "lat": company["lat"], "lon": company["lon"],
                "distance": distance, "score": score, "parts": parts, "record": company, "status": "Scored"
            })
    return rows

def chamber_rows(center_name, radius):
    center = CENTERS[center_name]
    rows = []
    seen = set()
    for company in chamber.get(center_name, []):
        key = company.get("company", "").casefold()
        if key in seen or company.get("lat") is None or company.get("lon") is None:
            continue
        seen.add(key)
        distance = round(haversine_miles(center["lat"], center["lon"], company["lat"], company["lon"]), 1)
        if distance <= radius:
            rows.append({
                "company": company["company"], "lat": company["lat"], "lon": company["lon"],
                "distance": distance, "score": None, "parts": None, "record": company, "status": "Needs enrichment"
            })
    return rows

def select_company(name):
    st.session_state.selected_company = name

def description_for(row):
    record = row["record"]
    if record.get("summary"):
        return record["summary"]
    source = record.get("discovery_source", "a nearby Chamber directory")
    phone = record.get("phone")
    base = f"{row['company']} is a local organization discovered through {source}."
    if phone:
        base += f" Public directory phone: {phone}."
    return base + " Sponsorship and philanthropy enrichment is still pending."

def score_display(row):
    ai = row["record"].get("ai_analysis")
    if ai:
        return f"{ai['ai_score']}/100"
    if row["score"] is not None:
        return f"{row['score']}/100"
    return "Pending"

def render_mini_map(row):
    df = pd.DataFrame([{"lat": row["lat"], "lon": row["lon"], "radius": 120}])
    layer = pdk.Layer(
        "ScatterplotLayer", df,
        get_position="[lon,lat]",
        get_radius="radius",
        get_fill_color="[0,103,185,210]",
        pickable=False
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=row["lat"], longitude=row["lon"], zoom=13.2),
        map_style=None,
    )
    st.pydeck_chart(deck, use_container_width=True, height=170)

def render_company_panel(row, center_name):
    record = row["record"]
    ai = record.get("ai_analysis")
    nc = national_relationship(row["company"])

    badges = ""
    if row["score"] is not None:
        badges += '<span class="badge green">Evidence scored</span>'
    else:
        badges += '<span class="badge">Enrichment pending</span>'
    if nc:
        badges += '<span class="badge green">SHPE National Contact</span>'

    st.markdown(f"""
    <div class="card">
      <div class="name">{row['company']}</div>
      <div class="muted">{record.get('address') or record.get('city','')} · {row['distance']} miles from {center_name}</div>
      <div>{badges}</div>
    </div>
    """, unsafe_allow_html=True)

    if ai:
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.metric("AI Sponsor Score", f"{ai['ai_score']}/100")
        with c2:
            st.metric("Confidence", f"{ai['confidence']}/100")
    elif row["score"] is not None:
        st.metric("Sponsor Score", f"{row['score']}/100")
    else:
        st.metric("Sponsor Score", "Pending")

    render_mini_map(row)

    tab_overview, tab_ai, tab_metrics = st.tabs(["Overview", "AI Analysis", "Metrics & Evidence"])

    with tab_overview:
        st.write(description_for(row))
        if nc:
            st.success(f"SHPE National relationship: {nc['relationship']}")
            st.link_button("Verify SHPE National source", nc["source_url"], use_container_width=True)

        website = record.get("website", "")
        contact = record.get("contact_page", "")
        email = record.get("contact_email", "")
        profile = record.get("profile_url", "")

        a, b = st.columns(2)
        with a:
            if website:
                st.link_button("Visit company website", website, use_container_width=True)
            elif profile:
                st.link_button("Open directory listing", profile, use_container_width=True)
            else:
                st.button("Website not verified", disabled=True, use_container_width=True)
        with b:
            if email:
                st.link_button("Email company", f"mailto:{email}", use_container_width=True)
            elif contact:
                st.link_button("Open contact page", contact, use_container_width=True)
            else:
                st.button("Email not verified", disabled=True, use_container_width=True)

        if profile:
            st.link_button("View discovery source", profile, use_container_width=True)

    with tab_ai:
        if ai:
            st.metric("Suggested ask", ai["recommended_ask"])
            st.markdown(f"**Recommended outreach angle:** {ai['outreach_angle']}")
            if ai.get("summary"):
                st.write(ai["summary"])

            if ai.get("strengths"):
                st.markdown("#### Strongest signals")
                for item in ai["strengths"]:
                    st.markdown(f"✓ {item}")
            if ai.get("risks"):
                st.markdown("#### Things to verify")
                for item in ai["risks"]:
                    st.markdown(f"• {item}")
            if ai.get("next_steps"):
                st.markdown("#### Recommended next steps")
                for i, item in enumerate(ai["next_steps"], 1):
                    st.markdown(f"**{i}.** {item}")

            if row["score"] is not None:
                st.caption(f"Transparent weighted baseline: {row['score']}/100")
        else:
            st.info("AI sponsorship analysis is not available for this company yet.")

    with tab_metrics:
        if row["score"] is not None:
            labels = {
                "philanthropy": "Philanthropy & community giving",
                "stem_education": "STEM / education alignment",
                "recruiting_talent": "Recruiting / student talent",
                "past_sponsorships": "Previous sponsorship behavior",
                "industry_fit": "Industry relevance to SHPE",
                "local_presence": "Local presence",
                "financial_capacity": "Financial capacity",
                "proximity": "Geographic proximity",
                "university_engagement": "University engagement",
                "dei_shpe_alignment": "DEI / SHPE alignment",
                "evidence_quality": "Evidence quality",
            }
            for k, w in WEIGHTS.items():
                v = row["parts"][k]
                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-top"><b>{labels[k]}</b><span>{v}/100 · {round(w*100)}%</span></div>
                    <div class="track"><div class="fill" style="width:{v}%"></div></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### Verified evidence")
            for e in record.get("sources", []):
                st.markdown(f"**[{e['title']}]({e['url']})**")
        else:
            st.info("Metric scoring will appear after this Chamber lead is enriched with verified company evidence.")

with st.sidebar:
    st.markdown("### ◆ SHPE")
    st.caption("FUNDING DISCOVERY")
    st.write("")
    page = st.radio("Navigation", ["Discovery", "Scoring model", "Evidence sources", "About"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Real organizations • transparent scoring")

st.markdown("""
<div class="hero">
<div style="color:#71d2ee;font-size:.72rem;font-weight:800;letter-spacing:.12em">FUNDRAISING INTELLIGENCE</div>
<h1>SHPE Funding Discovery</h1>
<p>Discover nearby organizations and inspect AI-assisted sponsorship potential.</p>
</div>
""", unsafe_allow_html=True)

if page == "Discovery":
    c1, c2, c3, c4 = st.columns([1.35, .8, 1, 1])
    with c1:
        center_name = st.selectbox("University area", list(CENTERS))
    with c2:
        radius = st.radio("Radius", RADII, horizontal=True, format_func=lambda x: f"{x} mi")
    with c3:
        view = st.selectbox("Records", ["All organizations", "Scored only", "Needs enrichment"])
    with c4:
        minimum = st.selectbox("Minimum scored fit", [0, 50, 60, 70, 80, 90], format_func=lambda x: "Any score" if x == 0 else f"{x}+")

    center = CENTERS[center_name]
    scored = [row for row in scored_rows(center_name, radius) if row["score"] >= minimum]
    leads = chamber_rows(center_name, radius)

    if view == "Scored only":
        rows = scored
    elif view == "Needs enrichment":
        rows = leads
    else:
        scored_names = {r["company"].casefold() for r in scored}
        rows = scored + [r for r in leads if r["company"].casefold() not in scored_names]

    rows = sorted(rows, key=lambda r: (r["score"] is None, -(r["score"] or 0), r["distance"]))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Organizations", len(rows))
    m2.metric("Scored prospects", len(scored))
    m3.metric("Local businesses", len(leads))
    m4.metric("AI analyses", sum(bool(r["record"].get("ai_analysis")) for r in rows))

    names = [r["company"] for r in rows]
    if rows and st.session_state.get("selected_company") not in names:
        st.session_state.selected_company = rows[0]["company"]

    map_col, panel_col = st.columns([1.55, 1], gap="large")

    with map_col:
        st.subheader("Local sponsor map")
        st.caption("Choose a company below the map; its profile opens immediately on the right.")

        if rows:
            df = pd.DataFrame([
                {
                    "lat": r["lat"], "lon": r["lon"], "company": r["company"],
                    "score": score_display(r), "radius": 95
                }
                for r in rows
            ])
            layer = pdk.Layer(
                "ScatterplotLayer", df,
                get_position="[lon,lat]",
                get_radius="radius",
                get_fill_color="[0,103,185,175]",
                pickable=True,
                auto_highlight=True,
            )
            state = pdk.ViewState(
                latitude=center["lat"], longitude=center["lon"],
                zoom=9 if radius == 25 else 10.4
            )
            st.pydeck_chart(
                pdk.Deck(layers=[layer], initial_view_state=state, tooltip={"text": "{company}\nScore: {score}"}),
                use_container_width=True,
                height=470,
            )

            st.markdown("#### Companies")
            for r in rows[:60]:
                left_name, right_score = st.columns([4.4, 1])
                with left_name:
                    st.button(
                        r["company"],
                        key=f"company_{r['company']}",
                        on_click=select_company,
                        args=(r["company"],),
                        use_container_width=True,
                    )
                with right_score:
                    st.markdown(f"**{score_display(r)}**")
                st.caption(
                    f"{r['distance']} mi"
                    + (" · SHPE National Contact" if national_relationship(r["company"]) else "")
                )
        else:
            st.info("No organizations match the selected filters.")

    with panel_col:
        st.subheader("Company profile")
        if rows:
            selected = next(
                (r for r in rows if r["company"] == st.session_state.get("selected_company")),
                rows[0],
            )
            render_company_panel(selected, center_name)
        else:
            st.info("Select a broader radius or lower the score filter.")

elif page == "Scoring model":
    st.subheader("Transparent scoring model")
    st.write("The AI assessment is shown alongside a deterministic weighted baseline so the recommendation remains explainable.")
    st.dataframe(
        pd.DataFrame([{"Metric": k.replace("_", " ").title(), "Weight": f"{int(v*100)}%"} for k, v in WEIGHTS.items()]),
        use_container_width=True,
        hide_index=True,
    )

elif page == "Evidence sources":
    st.subheader("Evidence & discovery ledger")
    records = []
    for c in enriched:
        for e in c.get("sources", []):
            records.append({"Organization": c["company"], "Type": "Scoring evidence", "Source": e["title"], "URL": e["url"]})
    for name, nc in national.items():
        records.append({"Organization": name, "Type": "SHPE National relationship", "Source": nc["relationship"], "URL": nc["source_url"]})
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True, column_config={"URL": st.column_config.LinkColumn("URL")})

else:
    st.subheader("About")
    st.write("SHPE Funding Discovery combines local business discovery, transparent weighted scoring, evidence-grounded AI sponsorship analysis, and verified SHPE National relationship tags. Unverified information is treated as unknown rather than invented.")
