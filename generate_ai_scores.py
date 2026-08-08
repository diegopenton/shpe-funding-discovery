import argparse, json
from pathlib import Path
from src.config import CENTERS
from src.scoring import calculate
from src.ai_enrichment import generate_ollama_analysis

p=argparse.ArgumentParser(); p.add_argument('--model',default='qwen2.5:3b'); p.add_argument('--endpoint',default='http://localhost:11434'); p.add_argument('--company',default=''); args=p.parse_args()
root=Path(__file__).parent; path=root/'data'/'companies.json'; companies=json.loads(path.read_text()); count=0
for company in companies:
    if args.company and args.company.lower() not in company['company'].lower(): continue
    choices=[]
    for center_name,center in CENTERS.items():
        score,parts,distance=calculate(company,center); choices.append((distance,score,parts,center_name))
    distance,score,parts,center_name=min(choices,key=lambda x:x[0])
    print(f"Generating: {company['company']} | {center_name} | baseline {score}/100")
    company['ai_analysis']=generate_ollama_analysis(company,score,parts,args.model,args.endpoint); count+=1
path.write_text(json.dumps(companies,indent=2)); print(f'Updated {count} organizations.')
