# SHPE Funding Discovery

A local-first sponsorship intelligence dashboard for discovering organizations around a university,
ranking fundraising prospects, and showing **why** each organization received its score.

## MVP demo regions

- **Florida Polytechnic University** — 10 mi / 25 mi
- **Dartmouth College** — 10 mi / 25 mi

The included seed dataset uses real organizations and first-party public evidence. The current MVP includes
Publix, Lakeland Electric, GEICO, Hypertherm Associates, Dartmouth Health, and King Arthur Baking Company.

## What makes the score different?

The app does not ask an LLM to invent a score. It extracts/records structured evidence and applies an
explainable 100-point model.

| Metric | Weight |
|---|---:|
| Philanthropy & community giving | 25% |
| STEM / education alignment | 15% |
| Recruiting / student talent | 15% |
| Previous sponsorship behavior | 10% |
| Industry relevance to SHPE | 8% |
| Local presence | 7% |
| Financial capacity | 6% |
| Geographic proximity | 5% |
| University engagement | 4% |
| DEI / SHPE alignment | 3% |
| Evidence quality / recency | 2% |

## Run locally

### Windows

Double-click:

```text
RUN_WINDOWS.bat
```

Or run manually:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --default-timeout=180 --retries 10 -r requirements.txt
python -m streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Repository structure

```text
app.py                  Streamlit dashboard
data/companies.json     Verified seed organizations + source ledger
src/config.py           Campus centers and allowed radii
src/scoring.py          Deterministic scoring engine
docs/SCORING.md         Full scoring model
docs/DATA_NOTES.md      Data quality notes
```

## Data integrity

The MVP deliberately distinguishes **not verified** from **no**. Real-world company research is incomplete,
and absence of a public page is not proof that a program does not exist.

Coordinates in the seed file are approximate facility/HQ points for the radius demonstration.
Before production use, replace them with geocoded address records and retain the geocoding source.

## Planned next steps

- Chamber / business-directory ingestion where automated access is permitted
- Company-site enrichment with source caching
- Deduplication across discovery sources
- Structured counts for jobs, internships, sponsorships, and university relationships
- Optional small local LLM for page classification only
- Human verification queue
- Contact / outreach pipeline

## Disclaimer

This is a student-built fundraising research prototype. Scores are prioritization aids, not statements of
corporate intent or guarantees of sponsorship.
