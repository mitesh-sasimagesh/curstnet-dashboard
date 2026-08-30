# Can AI Predict Tomorrow's Traffic? — Public Demo

A non-technical, interactive demo of the CurST-Net++ project, built for a general
audience — no ML jargon, no tables of metrics. Pick a road, pick a day type and
departure time, and see how a "Smart AI" (the project's improved model) predicts
traffic more tightly than a "Basic AI" (the unimproved starting point).

**This is a simulation, not the research paper.** The traffic curves shown are
illustrative, generated live in the browser — but the accuracy and improvement
numbers driving the simulation (how much tighter the Smart AI's guesses are) are
the project's real results.

## Run it locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Opens at `http://localhost:8501`.

## Deploy it publicly (same flow as the other dashboard)

1. Push `app.py` + `requirements.txt` to a new GitHub repo (e.g. `curstnet-demo`).
2. Go to https://share.streamlit.io → "New app" → point it at the repo, entry file `app.py`.
3. Deploy — you get a public link anyone can open, no install needed.

## Updating

All the numbers that drive the simulation (per-road accuracy, error size) live in
the `ROADS` dictionary near the top of `app.py`.
