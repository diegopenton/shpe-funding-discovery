
import json
from pathlib import Path
from src.config import CENTERS
from src.scoring import calculate

companies=json.loads((Path(__file__).parent/"data"/"companies.json").read_text())
assert len(companies)>=6
for company in companies:
    assert company["sources"], company["company"]
    for center in CENTERS.values():
        score, parts, distance=calculate(company, center)
        assert 0 <= score <= 100
        assert len(parts)==11
print(f"Validated {len(companies)} organizations across {len(CENTERS)} campus centers.")
