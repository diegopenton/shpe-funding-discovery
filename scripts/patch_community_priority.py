from pathlib import Path

p = Path("app.py")
text = p.read_text()

old = 'for supplemental in ("chamber_extra.json", "chamber_more.json", "chamber_dense.json"):'
new = 'for supplemental in ("chamber_extra.json", "chamber_more.json", "chamber_dense.json", "community_priority.json"):'
if old not in text:
    raise SystemExit("supplemental tuple not found")
text = text.replace(old, new, 1)

old_fields = 'for field in ("website","contact_email","contact_page","phone","address","profile_url","lat","lon"):'
new_fields = 'for field in ("website","contact_email","contact_page","phone","address","profile_url","lat","lon","community_tags","ownership_basis","impact_summary","impact_source_url","coordinate_note"):'
if old_fields not in text:
    raise SystemExit("merge fields not found")
text = text.replace(old_fields, new_fields, 1)

old_desc = '''def description_for(row):\n    record=row["record"]\n    if record.get("summary"):\n        return record["summary"]\n'''
new_desc = '''def description_for(row):\n    record=row["record"]\n    if record.get("impact_summary"):\n        return record["impact_summary"]\n    if record.get("summary"):\n        return record["summary"]\n'''
if old_desc not in text:
    raise SystemExit("description block not found")
text = text.replace(old_desc, new_desc, 1)

old_badges = '''            badge_html=('<span class="badge green">SHPE National Contact</span>' if nc else '')+('<span class="badge green">AI analyzed</span>' if ai else '')+('<span class="badge green">Verified SHPE Sponsor</span>' if sp else '')\n'''
new_badges = '''            community_badges="".join(f'<span class="badge">{tag}</span>' for tag in record.get("community_tags",[]))\n            badge_html=('<span class="badge green">SHPE National Contact</span>' if nc else '')+('<span class="badge green">AI analyzed</span>' if ai else '')+('<span class="badge green">Verified SHPE Sponsor</span>' if sp else '')+community_badges\n'''
if old_badges not in text:
    raise SystemExit("badge line not found")
text = text.replace(old_badges, new_badges, 1)

needle = '''                if nc:\n                    st.markdown("**SHPE National connection**")\n                    st.success(nc.get("relationship","Verified relationship"))\n                    source_url=nc.get("source_url","")\n                    if is_public_url(source_url): st.link_button("View SHPE relationship source",source_url,use_container_width=True)\n\n                st.markdown("**Contact**")\n'''
replacement = '''                if nc:\n                    st.markdown("**SHPE National connection**")\n                    st.success(nc.get("relationship","Verified relationship"))\n                    source_url=nc.get("source_url","")\n                    if is_public_url(source_url): st.link_button("View SHPE relationship source",source_url,use_container_width=True)\n\n                if record.get("community_tags"):\n                    st.markdown("**Community / STEM relevance**")\n                    st.write(" · ".join(record.get("community_tags",[])))\n                    if record.get("ownership_basis"):\n                        st.caption(record["ownership_basis"])\n                    impact_url=record.get("impact_source_url","")\n                    if is_public_url(impact_url):\n                        st.link_button("View community / STEM source",impact_url,use_container_width=True)\n\n                st.markdown("**Contact**")\n'''
if needle not in text:
    raise SystemExit("overview insertion point not found")
text = text.replace(needle, replacement, 1)

p.write_text(text)
print("Community priority data wired into app.")
