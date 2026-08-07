
import argparse, json
from pathlib import Path
from src.collector import collect_all

p=argparse.ArgumentParser()
p.add_argument("--target-per-region",type=int,default=100)
args=p.parse_args()

root=Path(__file__).parent
out=collect_all(root/"data"/"chamber_sources.json",args.target_per_region)
path=root/"data"/"chamber_cache.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
for region,rows in out.items():
    with_email=sum(bool(x.get("contact_email")) for x in rows)
    with_site=sum(bool(x.get("website")) for x in rows)
    print(f"{region}: {len(rows)} organizations | {with_site} websites | {with_email} public emails")
print(f"Saved {path}")
