from pathlib import Path

p = Path("app.py")
text = p.read_text()
old = '''if page=="Discovery":
    c1,c2,c3,c4=st.columns([1.35,.8,1,1])
    with c1: center_name=st.selectbox("University area",list(CENTERS))
    with c2: radius=st.radio("Radius",RADII,horizontal=True,format_func=lambda x:f"{x} mi")
    with c3: view=st.selectbox("Companies",["All companies","Analyzed companies","Local directory companies"])
    with c4: minimum=st.selectbox("Minimum sponsor score",[0,50,60,70,80,90],format_func=lambda x:"Any score" if x==0 else f"{x}+")

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

    selected=next((r for r in rows if r["company"]==st.session_state.get("selected_company")),rows[0] if rows else None)
'''
new = '''if page=="Discovery":
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
'''
if old not in text:
    raise SystemExit("Target Discovery block not found; refusing to patch an unexpected app.py")
text = text.replace(old, new, 1)
text = text.replace('initial_sidebar_state="auto"', 'initial_sidebar_state="collapsed"', 1)
marker = '.stButton>button,.stLinkButton>a{border-radius:10px!important;font-weight:650!important}\n'
extra = marker + 'div[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:14px!important;background:white!important}\ndiv[data-testid="stExpander"] summary{font-weight:700!important;color:var(--navy)!important}\n'
if 'div[data-testid="stExpander"] summary' not in text:
    text = text.replace(marker, extra, 1)
p.write_text(text)
