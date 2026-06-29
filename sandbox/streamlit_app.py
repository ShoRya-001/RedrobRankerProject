from __future__ import annotations

import tempfile
from pathlib import Path
import sys

import streamlit as st

# Import the dependency-free ranker from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rank import iter_candidates, rank_candidates, write_submission  # noqa: E402
from validate_submission import validate_submission  # noqa: E402

st.set_page_config(page_title="Redrob Candidate Ranker Sandbox", page_icon="🎯", layout="wide")

st.title("🎯 Redrob Candidate Ranker Sandbox")
st.caption(
    "Small-sample hosted sandbox for the Redrob Intelligent Candidate Discovery & Ranking Challenge. "
    "This UI runs the same offline rank.py logic used for submission reproduction."
)

with st.expander("What this sandbox does", expanded=False):
    st.markdown(
        """
        - Accepts a small candidate sample as JSON, JSONL, TXT, or JSONL.GZ.
        - Accepts the job description as upload or pasted text.
        - Runs the deterministic offline ranker end-to-end.
        - Produces a CSV with `candidate_id,rank,score,reasoning`.
        - Uses no hosted LLM/API calls during ranking.

        For the official 100K run, use the CLI command from the repository README.
        """
    )

sample_candidates_path = REPO_ROOT / "uploads" / "sample_candidates.json"
sample_job_path = REPO_ROOT / "uploads" / "A1.txt"

left, right = st.columns(2)

with left:
    st.subheader("1. Candidate sample")
    use_repo_sample = sample_candidates_path.exists() and st.checkbox(
        "Use repo sample_candidates.json", value=True
    )
    candidate_upload = None
    if not use_repo_sample:
        candidate_upload = st.file_uploader(
            "Upload candidate sample", type=["json", "jsonl", "ndjson", "txt", "gz"]
        )

with right:
    st.subheader("2. Job description")
    use_repo_job = sample_job_path.exists() and st.checkbox("Use repo A1.txt job description", value=True)
    job_upload = None
    job_text = ""
    if not use_repo_job:
        job_upload = st.file_uploader("Upload job description text", type=["txt", "md"])
        job_text = st.text_area("Or paste job description", height=180)

st.subheader("3. Ranking settings")
top_k = st.slider(
    "Top K rows to generate",
    min_value=1,
    max_value=100,
    value=50 if use_repo_sample else 100,
    help="Official submission requires 100 rows. Small sandbox samples may contain fewer candidates.",
)

run = st.button("Run ranking", type="primary")

if run:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        if use_repo_sample:
            candidates_path = sample_candidates_path
        elif candidate_upload is not None:
            suffix = Path(candidate_upload.name).suffix or ".jsonl"
            candidates_path = tmp / f"candidates{suffix}"
            candidates_path.write_bytes(candidate_upload.getvalue())
        else:
            st.error("Please provide a candidate sample.")
            st.stop()

        if use_repo_job:
            job_path = sample_job_path
        elif job_upload is not None:
            job_path = tmp / "job_description.txt"
            job_path.write_bytes(job_upload.getvalue())
        elif job_text.strip():
            job_path = tmp / "job_description.txt"
            job_path.write_text(job_text, encoding="utf-8")
        else:
            st.error("Please provide a job description.")
            st.stop()

        try:
            rows = rank_candidates(iter_candidates(candidates_path), top_k=top_k)
        except SystemExit as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:  # pragma: no cover - defensive UI guard
            st.exception(exc)
            st.stop()

        if not rows:
            st.error("No valid candidates found in the uploaded file.")
            st.stop()

        output_path = tmp / "sandbox_submission.csv"
        write_submission(rows, output_path)
        csv_text = output_path.read_text(encoding="utf-8")

        st.success(f"Generated {len(rows)} ranked rows.")

        official_errors = validate_submission(str(output_path)) if len(rows) == 100 else []
        if len(rows) == 100:
            if official_errors:
                st.warning("CSV generated, but official validator found issues:")
                for error in official_errors:
                    st.write(f"- {error}")
            else:
                st.success("Official validator passed.")
        else:
            st.info("Official validator requires exactly 100 rows. This sandbox run is still valid for small-sample demo purposes.")

        st.download_button(
            "Download ranked CSV",
            data=csv_text,
            file_name="sandbox_submission.csv",
            mime="text/csv",
        )

        st.subheader("Top candidates")
        st.dataframe(
            [
                {
                    "rank": index,
                    "candidate_id": row.candidate_id,
                    "score": f"{row.score:.4f}",
                    "reasoning": row.reasoning,
                }
                for index, row in enumerate(rows, start=1)
            ],
            use_container_width=True,
            hide_index=True,
        )

st.divider()
st.markdown(
    """
    **Official reproduction command**

    ```bash
    python rank.py --candidates ./candidates.jsonl --job ./uploads/job_description.docx --out ./team_Core4.csv --top-k 100
    python validate_submission.py ./team_yourid.csv
    ```
    """
)
