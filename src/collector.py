
from __future__ import annotations
import json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

UA = "SHPE-Funding-Discovery/0.3 (student research prototype; respectful public-directory collector)"
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
LETTERS = "abcdefghijklmnopqrstuvwxyz"

def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language":"en-US,en;q=0.8"})
    return s

def _robots_allows(session, url):
    p=urlparse(url)
    robots=f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        r=session.get(robots,timeout=15)
        if not r.ok:
            return True
        rp=RobotFileParser()
        rp.parse(r.text.splitlines())
        return rp.can_fetch(UA,url)
    except Exception:
        return False

def _clean(text):
    return " ".join((text or "").split())

def _external_website(profile_host, soup, page_url):
    preferred=[]
    for a in soup.select("a[href]"):
        href=urljoin(page_url,a.get("href",""))
        host=urlparse(href).netloc.lower()
        txt=_clean(a.get_text(" ",strip=True)).lower()
        if not host or host==profile_host or any(x in host for x in ("google.com","facebook.com","instagram.com","linkedin.com","twitter.com","x.com")):
            continue
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue
        weight=0
        if "visit website" in txt or "website" == txt: weight += 5
        if "visit site" in txt: weight += 5
        if href.startswith("https://"): weight += 1
        preferred.append((weight,href))
    return sorted(preferred,reverse=True)[0][1] if preferred else ""

def _emails(soup):
    found=set()
    for a in soup.select('a[href^="mailto:"]'):
        val=a.get("href","")[7:].split("?")[0].strip()
        if EMAIL_RE.fullmatch(val): found.add(val.lower())
    for m in EMAIL_RE.findall(soup.get_text(" ",strip=True)):
        # Avoid common asset/technical strings.
        if not any(x in m.lower() for x in ("example.com","sentry.io","wixpress.com")):
            found.add(m.lower())
    return sorted(found)

def _contact_page(session, website):
    if not website: return ""
    try:
        r=session.get(website,timeout=15,allow_redirects=True)
        if not r.ok: return ""
        soup=BeautifulSoup(r.text,"html.parser")
        host=urlparse(r.url).netloc
        for a in soup.select("a[href]"):
            txt=_clean(a.get_text(" ",strip=True)).lower()
            if any(k in txt for k in ("contact","get in touch","contact us")):
                href=urljoin(r.url,a.get("href"))
                if urlparse(href).netloc==host:
                    return href
    except Exception:
        pass
    return ""

def _enrich_public_contact(session, website, delay=.35):
    if not website:
        return "", "", []
    urls=[website]
    contact=_contact_page(session,website)
    if contact and contact not in urls: urls.append(contact)
    emails=[]
    final_site=website
    for url in urls[:2]:
        try:
            time.sleep(delay)
            r=session.get(url,timeout=15,allow_redirects=True)
            if not r.ok: continue
            final_site=r.url if url==website else final_site
            soup=BeautifulSoup(r.text,"html.parser")
            emails.extend(_emails(soup))
        except Exception:
            continue
    emails=sorted(set(emails))
    return final_site, contact, emails

def _parse_directory_page(session, page_url, source_name):
    if not _robots_allows(session,page_url):
        return []
    r=session.get(page_url,timeout=20)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    host=urlparse(page_url).netloc
    out=[]
    seen=set()

    # GrowthZone/ChamberMaster directory pages typically expose member profile
    # links around H4/H5 headings. Generic fallback handles both systems.
    candidates=[]
    for heading in soup.select("h2,h3,h4,h5,h6"):
        a=heading.find("a",href=True)
        if a:
            candidates.append((heading,a))
    if not candidates:
        for a in soup.select("a[href]"):
            href=urljoin(page_url,a["href"])
            if any(k in href.lower() for k in ("/member/","/directory/","/manufacturers/","/business/")):
                candidates.append((a.parent or a,a))

    for container,a in candidates:
        name=_clean(a.get_text(" ",strip=True))
        href=urljoin(page_url,a.get("href"))
        if len(name)<2 or name.lower() in {"learn more","visit website","visit site","show on map","view on google maps"}:
            continue
        key=(name.lower(),href)
        if key in seen: continue
        seen.add(key)

        block=container
        for _ in range(3):
            if block.parent: block=block.parent
        text=_clean(block.get_text(" ",strip=True))
        # Basic address recognition; keep original text for later geocoding.
        addr=""
        addr_match=re.search(r"\b\d{1,6}\s+[^|]{3,90}\b(?:FL|NH|VT)\s+\d{5}(?:-\d{4})?",text,re.I)
        if addr_match: addr=_clean(addr_match.group(0))
        phone=""
        phone_match=re.search(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}",text)
        if phone_match: phone=phone_match.group(0)

        # Prefer an external URL already present in the listing block.
        website=_external_website(host,block,page_url)
        out.append({
            "company":name,"profile_url":href,"website":website,"address":addr,"phone":phone,
            "discovery_source":source_name
        })
    return out

def collect_source(source, limit=100, request_delay=.35):
    session=_session()
    typ=source["type"]
    urls=[]
    if typ in ("growthzone_alpha","chambermaster_alpha"):
        base=source["directory_url"].rstrip("/")
        # GrowthZone normally uses /list/searchalpha/a; ChamberMaster deployments
        # often accept /searchalpha/a from the directory host.
        for letter in LETTERS:
            if "/list" in base:
                urls.append(f"{base}/searchalpha/{letter}")
            else:
                urls.append(f"{source['base_url'].rstrip('/')}/searchalpha/{letter}")
    else:
        urls=[source["directory_url"]]

    records=[]
    seen=set()
    for url in urls:
        if len(records)>=limit: break
        try:
            batch=_parse_directory_page(session,url,source["name"])
        except Exception:
            continue
        for rec in batch:
            key=rec["company"].strip().lower()
            if key in seen: continue
            seen.add(key)
            # If the directory listing doesn't expose the external website, inspect profile.
            if rec["profile_url"] and not rec["website"] and urlparse(rec["profile_url"]).netloc:
                try:
                    time.sleep(request_delay)
                    pr=session.get(rec["profile_url"],timeout=15)
                    if pr.ok:
                        ps=BeautifulSoup(pr.text,"html.parser")
                        rec["website"]=_external_website(urlparse(pr.url).netloc,ps,pr.url)
                        prof_emails=_emails(ps)
                    else:
                        prof_emails=[]
                except Exception:
                    prof_emails=[]
            else:
                prof_emails=[]

            site,contact,site_emails=_enrich_public_contact(session,rec["website"],request_delay)
            rec["website"]=site or rec["website"]
            rec["contact_page"]=contact
            rec["contact_email"]=(prof_emails+site_emails)[0] if (prof_emails+site_emails) else ""
            records.append(rec)
            if len(records)>=limit: break
        time.sleep(request_delay)
    return records

def collect_all(config_path, target_per_region=100):
    config=json.loads(Path(config_path).read_text())
    result={}
    for region,sources in config.items():
        merged={}
        # Collect across sources fairly instead of letting one chamber dominate.
        per=max(20, (target_per_region//max(1,len(sources)))+15)
        for src in sources:
            batch=collect_source(src,limit=per)
            for r in batch:
                k=r["company"].strip().lower()
                if k not in merged:
                    merged[k]=r
                else:
                    old=merged[k]
                    names=set(filter(None,(old.get("discovery_source","")+" | "+r.get("discovery_source","")).split(" | ")))
                    old["discovery_source"]=" | ".join(sorted(names))
                    if not old.get("website"): old["website"]=r.get("website","")
                    if not old.get("contact_email"): old["contact_email"]=r.get("contact_email","")
                    if not old.get("contact_page"): old["contact_page"]=r.get("contact_page","")
                    if not old.get("address"): old["address"]=r.get("address","")
        result[region]=list(merged.values())[:target_per_region]
    return result
