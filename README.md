# CurST-Net++ Project Dashboard

A Streamlit dashboard for the CurST-Net++ research project: overview, per-stage
results, cross-dataset analysis, bug log, and team/file reference — all built
from the project's actual results (Stage 0–3, PEMS03/04/08).

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Host it for free (so anyone with the link can view it)

**Streamlit Community Cloud** (easiest, free, official):
1. Push this folder (`app.py` + `requirements.txt`) to a GitHub repo.
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Click "New app", pick the repo/branch, set the file path to `app.py`.
4. Deploy — you get a public `*.streamlit.app` URL to share with your team.

Any time you update the results (new stage, new dataset, new bug fixed), just
edit `app.py` and push — the hosted app redeploys automatically.

## Updating the data

All project data lives in the `results` and `bugs` dictionaries near the top
of `app.py` — no need to touch the layout code to update numbers.
