
from __future__ import annotations
from math import radians, sin, cos, asin, sqrt

WEIGHTS = {
    "philanthropy": 0.25,
    "stem_education": 0.15,
    "recruiting_talent": 0.15,
    "past_sponsorships": 0.10,
    "industry_fit": 0.08,
    "local_presence": 0.07,
    "financial_capacity": 0.06,
    "proximity": 0.05,
    "university_engagement": 0.04,
    "dei_shpe_alignment": 0.03,
    "evidence_quality": 0.02,
}

INDUSTRY_FIT = {
    "Engineering": 100,
    "Technology": 100,
    "Advanced Manufacturing": 100,
    "Aerospace & Defense": 100,
    "Energy & Utilities": 95,
    "Construction": 90,
    "Logistics": 85,
    "Healthcare": 72,
    "Finance & Insurance": 70,
    "Retail": 55,
    "Food & Consumer": 48,
}

CAPACITY = {"enterprise": 100, "large": 90, "medium": 70, "small": 45, "unknown": 50}
LOCAL_PRESENCE = {"headquarters": 100, "major_facility": 90, "regional_office": 80, "local_branch": 65, "unknown": 45}

def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2-lat1)
    dl = radians(lon2-lon1)
    a = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*r*asin(sqrt(a))

def proximity_score(distance):
    if distance <= 5: return 100
    if distance <= 10: return 90
    if distance <= 15: return 75
    if distance <= 25: return 60
    return max(0, round(60 - (distance-25)*2))

def philanthropy_score(signals):
    score = 0
    score += 35 if signals.get("foundation_or_grants") else 0
    score += 25 if signals.get("explicit_sponsorship") else 0
    score += 20 if signals.get("community_giving") else 0
    score += 20 if signals.get("quantified_giving") else 0
    return min(score, 100)

def stem_score(signals):
    score = 0
    score += 45 if signals.get("explicit_stem") else 0
    score += 30 if signals.get("education_programs") else 0
    score += 25 if signals.get("scholarships") else 0
    return min(score, 100)

def recruiting_score(signals):
    score = 0
    score += 40 if signals.get("internships") else 0
    score += 30 if signals.get("student_programs") else 0
    score += 30 if signals.get("technical_careers") else 0
    return min(score, 100)

def sponsorship_score(signals):
    score = 0
    score += 65 if signals.get("explicit_sponsorship") else 0
    score += 35 if signals.get("documented_sponsorship_examples") else 0
    return min(score, 100)

def university_score(signals):
    score = 0
    score += 45 if signals.get("university_partnerships") else 0
    score += 35 if signals.get("college_internships") else 0
    score += 20 if signals.get("education_partnerships") else 0
    return min(score, 100)

def dei_score(signals):
    score = 0
    score += 50 if signals.get("dei_commitment") else 0
    score += 50 if signals.get("inclusive_grantmaking_or_erg") else 0
    return min(score, 100)

def evidence_quality_score(sources):
    if not sources: return 0
    official = sum(1 for s in sources if s.get("official"))
    dated = sum(1 for s in sources if s.get("date"))
    return min(100, round((official/len(sources))*75 + (dated/len(sources))*25))

def calculate(company, center):
    distance = haversine_miles(center["lat"], center["lon"], company["lat"], company["lon"])
    signals = company.get("signals", {})
    components = {
        "philanthropy": philanthropy_score(signals),
        "stem_education": stem_score(signals),
        "recruiting_talent": recruiting_score(signals),
        "past_sponsorships": sponsorship_score(signals),
        "industry_fit": INDUSTRY_FIT.get(company.get("industry"), 55),
        "local_presence": LOCAL_PRESENCE.get(company.get("local_presence"), 45),
        "financial_capacity": CAPACITY.get(company.get("capacity_tier"), 50),
        "proximity": proximity_score(distance),
        "university_engagement": university_score(signals),
        "dei_shpe_alignment": dei_score(signals),
        "evidence_quality": evidence_quality_score(company.get("sources", [])),
    }
    total = round(sum(components[k] * WEIGHTS[k] for k in WEIGHTS))
    return total, components, round(distance, 1)
