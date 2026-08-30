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

## Updating the data

All project data lives in the `results` and `bugs` dictionaries near the top
of `app.py` — no need to touch the layout code to update numbers.
