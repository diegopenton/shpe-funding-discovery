from __future__ import annotations
import json, requests

SYSTEM_GUIDANCE = """You are a sponsorship-research analyst for a university SHPE chapter. Use only supplied evidence. Never invent philanthropy programs, contacts, sponsorship history, university relationships, employee counts, or financial facts. Missing evidence means unknown. Return strict JSON."""

def build_prompt(company, deterministic_score, components):
    payload={"organization":company.get("company"),"industry":company.get("industry"),"city":company.get("city"),"deterministic_score":deterministic_score,"metric_scores":components,"known_summary":company.get("summary",""),"evidence_sources":company.get("sources",[])}
    return SYSTEM_GUIDANCE + '\nReturn JSON with: ai_score, confidence, sponsor_tier, recommended_ask, outreach_angle, summary, strengths, risks, next_steps.\nOrganization evidence:\n' + json.dumps(payload,indent=2)

def generate_ollama_analysis(company, deterministic_score, components, model="qwen2.5:3b", endpoint="http://localhost:11434"):
    response=requests.post(endpoint.rstrip('/')+'/api/generate',json={"model":model,"prompt":build_prompt(company,deterministic_score,components),"stream":False,"format":"json","options":{"temperature":0.15}},timeout=120)
    response.raise_for_status()
    return json.loads(response.json().get("response","{}"))
