# Deploy SHPE Funding Discovery to Streamlit Community Cloud

The public app stays Python/Streamlit. GitHub stores the repository; Streamlit Community Cloud runs it.

## 1. Push the repository to GitHub

Create an empty public repository named:

`SHPE-Funding-Discovery`

Do not initialize it with a README, license, or .gitignore.

From this project folder:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/SHPE-Funding-Discovery.git
git push -u origin main
```

## 2. Deploy on Streamlit Community Cloud

1. Go to Streamlit Community Cloud.
2. Sign in with GitHub.
3. Click **Create app**.
4. Select `YOUR_USERNAME/SHPE-Funding-Discovery`.
5. Branch: `main`
6. Main file path: `app.py`
7. Deploy.

The resulting public URL will look like:

`https://<app-name>.streamlit.app`

It can be opened directly in Safari on iPhone/iPad.

## 3. Data refresh model

The public site reads committed JSON files. Do **not** scrape Chambers on every page load.

To refresh locally:

```powershell
.venv\Scripts\activate
python refresh_chamber_data.py --target-per-region 100
python validate_data.py
git add data/chamber_cache.json
git commit -m "data: refresh local chamber lead cache"
git push
```

Streamlit Community Cloud will redeploy automatically after the GitHub push.

## 4. Why this setup

This preserves:
- Python scoring logic
- Chamber collection scripts
- future local-LLM enrichment support
- interactive Streamlit UI
- public Safari-compatible URL

while keeping the public site fast and avoiding unnecessary repeated requests to source directories.
