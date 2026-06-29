# Redrob Ranker Sandbox

This folder contains the small hosted sandbox required by the Redrob submission spec.

It runs the same dependency-free `rank.py` logic from the repository root, but exposes it through a Streamlit UI for small candidate samples.

## Local run

From the repository root:

```bash
pip install -r sandbox/requirements.txt
streamlit run sandbox/streamlit_app.py
```

Open the shown localhost URL, upload a candidate sample and job description, then download the ranked CSV.

## Streamlit Community Cloud deployment

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io or https://streamlit.io/cloud.
3. Create a new app from your GitHub repo.
4. Set the main file path to:

```text
sandbox/streamlit_app.py
```

5. Deploy.

Use the resulting URL as your `sandbox_link` in the Redrob portal and in `submission_metadata.yaml`.

## Official ranking command

Use the CLI for the real 100K file:

```bash
python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./team_yourid.csv --top-k 100
python validate_submission.py ./team_yourid.csv
```
