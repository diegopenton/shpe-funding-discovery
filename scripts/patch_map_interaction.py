from pathlib import Path
import re

p = Path("app.py")
text = p.read_text()

# 1) Add a robust helper for reading the selected PyDeck object.
needle = '''def sync_company_picker():\n    picked=st.session_state.get("company_picker")\n    if picked:\n        st.session_state.selected_company=picked\n'''
replacement = '''def sync_company_picker():\n    picked=st.session_state.get("company_picker")\n    if picked:\n        st.session_state.selected_company=picked\n\ndef selected_map_company(event, layer_id="company-markers"):\n    try:\n        selection = event.selection\n        objects = selection.objects\n    except (AttributeError, TypeError):\n        try:\n            objects = event.get("selection", {}).get("objects", {})\n        except (AttributeError, TypeError):\n            return None\n    picks = objects.get(layer_id, []) if objects else []\n    if not picks:\n        return None\n    return picks[0].get("company")\n'''
if needle not in text:
    raise SystemExit("sync helper block not found")
text = text.replace(needle, replacement, 1)

# 2) Remove the company picker from inside Filters. It will live directly above Company Profile.
old_picker = '''        if rows:\n            st.selectbox("Open company",names,key="company_picker",on_change=sync_company_picker)\n'''
if old_picker not in text:
    raise SystemExit("filter company picker block not found")
text = text.replace(old_picker, "", 1)

# 3) Make the map layer selectable, with visible-but-compact fixed pixel markers.
old_map = '''            layer=pdk.Layer("ScatterplotLayer",map_df,get_position="[lon,lat]",get_radius=3,radius_units="pixels",radius_scale=1,radius_min_pixels=2,radius_max_pixels=3,get_fill_color=[0,103,185,190],pickable=True,auto_highlight=True,stroked=True,get_line_color=[255,255,255,160],line_width_min_pixels=.5)\n            state=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.4)\n            st.pydeck_chart(pdk.Deck(layers=[layer],initial_view_state=state,tooltip={"text":"{company}\\nScore: {score}"}),use_container_width=True,height=390)\n'''
new_map = '''            layer=pdk.Layer(\n                "ScatterplotLayer",\n                map_df,\n                id="company-markers",\n                get_position="[lon,lat]",\n                get_radius=5,\n                radius_units="pixels",\n                radius_scale=1,\n                radius_min_pixels=4,\n                radius_max_pixels=6,\n                get_fill_color=[0,103,185,205],\n                pickable=True,\n                auto_highlight=True,\n                stroked=True,\n                get_line_color=[255,255,255,190],\n                line_width_min_pixels=1,\n            )\n            state=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],zoom=9 if radius==25 else 10.4)\n            map_event=st.pydeck_chart(\n                pdk.Deck(layers=[layer],initial_view_state=state,tooltip={"text":"{company}\\nScore: {score}"}),\n                use_container_width=True,\n                height=390,\n                on_select="rerun",\n                selection_mode="single-object",\n                key="company_map",\n            )\n            clicked_company=selected_map_company(map_event)\n            if clicked_company in names:\n                st.session_state.selected_company=clicked_company\n                st.session_state.company_picker=clicked_company\n                selected=next((r for r in rows if r["company"]==clicked_company),selected)\n            st.caption("Tap or click a company dot to open its profile.")\n'''
if old_map not in text:
    raise SystemExit("map block not found")
text = text.replace(old_map, new_map, 1)

# 4) Put a company dropdown immediately before the profile, on desktop and phone.
old_profile = '''    with right:\n        st.subheader("Company profile")\n'''
new_profile = '''    with right:\n        if rows:\n            if st.session_state.get("company_picker") not in names:\n                st.session_state.company_picker=st.session_state.get("selected_company",names[0])\n            st.selectbox("Select company",names,key="company_picker",on_change=sync_company_picker)\n            selected=next((r for r in rows if r["company"]==st.session_state.get("selected_company")),selected)\n        st.subheader("Company profile")\n'''
if old_profile not in text:
    raise SystemExit("profile header block not found")
text = text.replace(old_profile, new_profile, 1)

p.write_text(text)
print("Patched clickable map, marker sizing, and profile company picker.")
