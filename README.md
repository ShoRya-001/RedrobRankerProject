# Redrob Candidate Discovery & Ranking Submission

This repository contains only the code needed for the **Redrob Intelligent Candidate Discovery & Ranking Challenge** submission.

The goal is to produce a `candidate_id,rank,score,reasoning` CSV containing the **top 100 candidates** for the released **Senior AI Engineer — Founding Team** job description.

The ranking step is:

- CPU-only
- deterministic
- offline
- standard-library only
- no hosted LLM/API calls
- no network required during ranking

---

## Repository Contents

```text
.
├── rank.py                         # Official offline ranking script
├── validate_submission.py          # CSV format validator
├── requirements.txt                # Streamlit sandbox dependency only
├── submission_metadata.yaml        # Portal metadata mirror; fill before submission
├── submission_metadata.yaml.example
├── Dockerfile                      # Optional Streamlit sandbox Dockerfile
├── sandbox/
│   ├── streamlit_app.py            # Hosted small-sample sandbox/demo
│   ├── requirements.txt
│   └── README.md
└── uploads/
    ├── job_description.docx        # Released job description
    ├── x.txt                       # One-line JSONL sample candidate
    ├── sample_candidates.json      # First 50 candidates, JSON array
    ├── sample_submission.csv       # Format reference
    └── candidate_schema.json       # Candidate schema reference
```

The real `candidates.jsonl` / `candidates.jsonl.gz` file is intentionally **not committed**.

---

## Official Reproduction Command

Place the released candidate file at repo root as:

```text
candidates.jsonl
```

Then run:

```bash
python rank.py --candidates ./candidates.jsonl --job ./uploads/job_description.docx --out ./submission.csv --top-k 100
```

If the candidate file is gzipped:

```bash
python rank.py --candidates ./candidates.jsonl.gz --job ./uploads/job_description.docx --out ./submission.csv --top-k 100
```

Validate the output:

```bash
python validate_submission.py ./submission.csv
```

Expected validator output:

```text
Submission is valid.
```

This is the single-command ranking path used for Stage 3 reproduction. No precomputation is required.

---

## Windows PowerShell Commands

Example with a real local candidate file:

```powershell
python rank.py `
  --candidates C:\redrob-data\candidates.jsonl `
  --job uploads\job_description.docx `
  --out team_Core4.csv `
  --top-k 100

python validate_submission.py team_yourid.csv
```

Example with gzipped candidate file:

```powershell
python rank.py `
  --candidates C:\redrob-data\candidates.jsonl.gz `
  --job uploads\job_description.docx `
  --out team_Core4.csv `
  --top-k 100

python validate_submission.py team_yourid.csv
```

---

## Local Smoke Tests

Test JSON array support with the 50-candidate sample:

```bash
python rank.py --candidates ./uploads/sample_candidates.json --job ./uploads/job_description.docx --out ./sample50_ranked.csv --top-k 50
```

Test JSONL support with the one-candidate sample:

```bash
python rank.py --candidates ./uploads/x.txt --job ./uploads/job_description.docx --out ./one_ranked.csv --top-k 1
```

Official validation requires exactly 100 rows, so validate only the real top-100 output.

---

## Ranking Methodology

The ranker is tuned to the released Senior AI Engineer JD. It prioritizes evidence that the candidate can own Redrob's intelligence layer: retrieval, ranking, candidate-job matching, embeddings, vector databases, production ML/NLP systems, evaluation frameworks, and product engineering.

Scoring combines:

- retrieval/search/recommendation/ranking evidence
- embeddings and vector database experience
- applied ML/NLP/LLM experience
- Python and production engineering depth
- ranking evaluation signals such as relevance, NDCG/MRR/MAP, offline/online evaluation, and A/B tests
- product-company career evidence
- 5-9 year seniority fit
- India/Pune/Noida or relocation/logistics fit
- Redrob behavioral signals such as response rate, recency, open-to-work, notice period, saved-by-recruiters, interview completion, verification, and GitHub activity

It down-weights:

- keyword-stuffed profiles without matching role/career evidence
- consulting-only histories without product-company experience
- inactive candidates and low response rates
- very long notice periods
- CV/speech/robotics-heavy AI profiles without meaningful NLP/IR/retrieval evidence
- framework-only GenAI profiles without production ranking/retrieval experience
- honeypot-style impossible claims, such as many advanced/expert skills with almost no duration

The reasoning column is generated from candidate facts only: title, years, matching skills, response rate, recency, notice period, and major concerns.

---

## Sandbox / Demo Link

The required hosted sandbox is implemented with Streamlit:

```text
sandbox/streamlit_app.py
```

It accepts a small candidate sample, runs the ranker end-to-end, and lets reviewers download a ranked CSV.

Run locally:

```bash
pip install -r requirements.txt
streamlit run sandbox/streamlit_app.py
```

Host on Streamlit Community Cloud:

1. Push this repo to GitHub.
2. Open `https://streamlit.io/cloud`.
3. Create a new app from this GitHub repo.
4. Set the main file path to:

```text
sandbox/streamlit_app.py
```

5. Deploy and use the generated Streamlit URL as the portal `sandbox_link`.

---

## Optional Docker Sandbox

Build:

```bash
docker build -t redrob-ranker .
```

Run:

```bash
docker run -p 8501:8501 redrob-ranker
```

Open: http://localhost:8501

---

## AI Tools Declaration

AI tools were used as development assistants for implementation, debugging, and documentation. The submitted ranking step itself is deterministic and does not call any hosted AI/LLM APIs during ranking.

Other: Arena.ai Agent Mode was used for architecture, implementation assistance, debugging, and documentation. The ranking step is deterministic, offline, CPU-only, and does not call hosted LLM APIs during ranking.

---

## Compute Environment 
Windows 11 laptop, 6 CPU cores, 16GB RAM, Python 3.14.2, CPU-only, no network during ranking.

---
## Files Not Included
The released full candidate pool is not included in this repository:

candidates.jsonl
candidates.jsonl.gz

Those files should be supplied at runtime using `--candidates`.
---