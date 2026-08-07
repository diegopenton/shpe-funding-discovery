# SHPE Funding Discovery

A local-first sponsorship intelligence dashboard for discovering organizations around a university,
ranking fundraising prospects, and showing **why** each organization received its score.

## MVP demo regions

- **Florida Polytechnic University** — 10 mi / 25 mi
- **Dartmouth College** — 10 mi / 25 mi

The included dataset uses real organizations. It now combines first-party company evidence with Chamber-verified local discovery records from the Lakeland Chamber of Commerce and Greater Winter Haven Chamber of Commerce. Chamber-only records are clearly marked as awaiting company-site enrichment. The current MVP includes
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


## Chamber lead collector

The repository now includes a respectful public-directory collector configured for nearby business organizations.

Florida Poly sources:
- Lakeland Chamber of Commerce
- Greater Winter Haven Chamber of Commerce
- Greater Bartow Chamber of Commerce
- Greater Auburndale Chamber of Commerce

Dartmouth sources:
- Upper Valley Business Alliance
- Hartford Area Chamber of Commerce (VT)
- Woodstock Area Chamber of Commerce

Target up to 100 records per university area:

```bash
python refresh_chamber_data.py --target-per-region 100
```

The collector attempts to retain:
- company name
- address
- phone
- Chamber / Alliance source
- company website
- public business email, when actually published
- public contact page, when no email is available

It never guesses email addresses. `info@domain` is not created unless that exact address is found publicly.


## Put the dashboard on a public link

The easiest deployment path is **Streamlit Community Cloud** after this repository is public on GitHub.

1. Push this repository to GitHub.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Choose **Create app** / **Deploy an app**.
4. Select this repository.
5. Branch: `main`
6. Main file path: `app.py`
7. Deploy.

The hosted URL will look similar to:

```text
https://your-app-name.streamlit.app
```

The dashboard uses the committed cache, so visitors do **not** need to run the Chamber scraper.
Run `refresh_chamber_data.py` locally when you want to update the source data, review the changes, then commit the refreshed cache.

### Important deployment design

Do not scrape Chamber sites on every web-page visit. The public app reads the cached dataset from GitHub.
This keeps the demonstration fast, avoids repeatedly hitting source sites, and makes the hosted version stable.
