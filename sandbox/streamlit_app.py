from __future__ import annotations

import sys
import tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st

# Import the dependency-free ranker from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rank import iter_candidates, rank_candidates, write_submission  # noqa: E402
from validate_submission import validate_submission  # noqa: E402


st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
  --redrob-bg: #07111f;
  --redrob-card: rgba(15, 23, 42, 0.78);
  --redrob-border: rgba(148, 163, 184, 0.22);
  --redrob-text: #f8fafc;
  --redrob-muted: #cbd5e1;
  --redrob-primary: #7c3aed;
  --redrob-cyan: #06b6d4;
  --redrob-green: #22c55e;
}

.stApp {
  background:
    radial-gradient(circle at 12% 10%, rgba(124, 58, 237, 0.30), transparent 30rem),
    radial-gradient(circle at 90% 18%, rgba(6, 182, 212, 0.24), transparent 28rem),
    radial-gradient(circle at 50% 95%, rgba(34, 197, 94, 0.10), transparent 28rem),
    linear-gradient(135deg, #020617 0%, #07111f 55%, #111827 100%);
  color: var(--redrob-text);
}

.block-container {
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1220px;
}

[data-testid="stSidebar"] {
  background: rgba(2, 6, 23, 0.88);
  border-right: 1px solid rgba(148, 163, 184, 0.16);
}

.hero-card {
  padding: 2rem;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.30), rgba(6, 182, 212, 0.16));
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(18px);
  margin-bottom: 1.25rem;
}

.hero-title {
  font-size: clamp(2rem, 4vw, 4.2rem);
  line-height: 1.02;
  font-weight: 900;
  letter-spacing: -0.06em;
  margin: 0;
}

.gradient-text {
  background: linear-gradient(90deg, #a78bfa, #22d3ee, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  color: var(--redrob-muted);
  max-width: 850px;
  font-size: 1.05rem;
  line-height: 1.75;
  margin-top: 1rem;
}

.glass-card {
  padding: 1.25rem;
  border-radius: 22px;
  border: 1px solid var(--redrob-border);
  background: var(--redrob-card);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(14px);
  height: 100%;
}

.step-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.38rem 0.75rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #e0f2fe;
  background: rgba(14, 165, 233, 0.15);
  border: 1px solid rgba(14, 165, 233, 0.22);
  margin-bottom: 0.8rem;
}

.status-card {
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(2, 6, 23, 0.40);
}

.status-label {
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.70rem;
  font-weight: 800;
}

.status-value {
  color: #f8fafc;
  font-size: 1.45rem;
  font-weight: 900;
  margin-top: 0.15rem;
}

.stButton > button {
  border: 0 !important;
  border-radius: 14px !important;
  padding: 0.75rem 1.25rem !important;
  font-weight: 850 !important;
  color: white !important;
  background: linear-gradient(90deg, #7c3aed, #06b6d4) !important;
  box-shadow: 0 12px 30px rgba(6, 182, 212, 0.18) !important;
}

.stButton > button:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

.stDownloadButton > button {
  border-radius: 14px !important;
  font-weight: 850 !important;
}

[data-testid="stMetricValue"] {
  color: #f8fafc;
  font-weight: 900;
}

[data-testid="stMetricLabel"] {
  color: #cbd5e1;
}

hr {
  border-color: rgba(148, 163, 184, 0.18) !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def uploaded_job_to_text(uploaded_file) -> str:
    """Read uploaded TXT/MD/DOCX job descriptions as plain text for the sandbox."""

    suffix = Path(uploaded_file.name).suffix.lower()
    data = uploaded_file.getvalue()
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover - deployment dependency guard
            raise RuntimeError("DOCX support requires python-docx. Add python-docx to requirements.txt.") from exc

        document = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        table_rows: list[str] = []
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    table_rows.append(" | ".join(cells))
        return "\n".join(paragraphs + table_rows).strip()

    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore").strip()


sample_candidates_path = REPO_ROOT / "uploads" / "sample_candidates.json"
sample_job_path = REPO_ROOT / "uploads" / "A1.txt"

with st.sidebar:
    st.markdown("## 🎯 Redrob Ranker")
    st.caption("Hosted small-sample sandbox for reproducible candidate ranking.")
    st.divider()

    st.markdown("### Submission checklist")
    st.write("✅ Upload/select candidate sample")
    st.write("✅ Upload/select job description")
    st.write("✅ Run ranking")
    st.write("✅ Download CSV")
    st.write("✅ Validate final top-100 locally")
    st.divider()

    st.markdown("### Official CLI")
    st.code(
        "python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./submission.csv --top-k 100",
        language="bash",
    )
    st.caption("Ranking step is deterministic, CPU-only, offline, and uses no hosted LLM/API calls.")

st.markdown(
    """
    <div class="hero-card">
      <p class="step-pill">⚡ CPU-only · Offline · Reproducible</p>
      <h1 class="hero-title">Redrob <span class="gradient-text">Candidate Ranker</span></h1>
      <p class="hero-subtitle">
        Upload a candidate sample and a job description, run the same deterministic ranking logic used by
        <code>rank.py</code>, inspect the top candidates, and download a validator-compatible CSV.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_cols = st.columns(4)
with status_cols[0]:
    st.markdown('<div class="status-card"><div class="status-label">Candidate input</div><div class="status-value">JSONL/JSON</div></div>', unsafe_allow_html=True)
with status_cols[1]:
    st.markdown('<div class="status-card"><div class="status-label">JD input</div><div class="status-value">TXT/MD/DOCX</div></div>', unsafe_allow_html=True)
with status_cols[2]:
    st.markdown('<div class="status-card"><div class="status-label">Output</div><div class="status-value">CSV</div></div>', unsafe_allow_html=True)
with status_cols[3]:
    st.markdown('<div class="status-card"><div class="status-label">Network</div><div class="status-value">None</div></div>', unsafe_allow_html=True)

st.write("")

tab_inputs, tab_method, tab_output = st.tabs(["📁 Inputs & Ranking", "🧠 Methodology", "📦 Submission Commands"])

with tab_inputs:
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-pill">1 · Candidate sample</span>', unsafe_allow_html=True)
        use_repo_sample = sample_candidates_path.exists() and st.checkbox(
            "Use bundled sample_candidates.json", value=True
        )
        candidate_upload = None
        if not use_repo_sample:
            candidate_upload = st.file_uploader(
                "Upload candidate sample",
                type=["json", "jsonl", "ndjson", "txt", "gz"],
                help="Accepts JSON array, JSONL/NDJSON/TXT with one JSON object per line, or gzipped JSONL.",
            )
        st.caption("Sandbox samples can be ≤100 candidates. The official 100K run should be done with the CLI.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-pill">2 · Job description</span>', unsafe_allow_html=True)
        use_repo_job = sample_job_path.exists() and st.checkbox("Use bundled A1.txt job description", value=True)
        job_upload = None
        job_text = ""
        if not use_repo_job:
            job_upload = st.file_uploader(
                "Upload job description",
                type=["txt", "md", "docx"],
                help="DOCX files are parsed with python-docx; text and markdown are read directly.",
            )
            job_text = st.text_area("Or paste job description", height=165)
        st.caption("DOCX, TXT, MD, or pasted text are supported in the hosted sandbox.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    run_cols = st.columns([1.2, 1, 1])
    with run_cols[0]:
        top_k = st.slider(
            "Top K rows to generate",
            min_value=1,
            max_value=100,
            value=50 if use_repo_sample else 100,
            help="Official submission requires 100 rows. Small sandbox samples may contain fewer candidates.",
        )
    with run_cols[1]:
        st.write("")
        st.write("")
        run = st.button("🚀 Run ranking", type="primary", use_container_width=True)
    with run_cols[2]:
        st.write("")
        st.write("")
        st.caption("Ranking uses local deterministic scoring; no external model/API calls are made.")

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
                try:
                    extracted_job_text = uploaded_job_to_text(job_upload)
                except Exception as exc:
                    st.error(f"Could not read job description file: {exc}")
                    st.stop()
                if not extracted_job_text:
                    st.error("The uploaded job description did not contain readable text.")
                    st.stop()
                job_path = tmp / "job_description.txt"
                job_path.write_text(extracted_job_text, encoding="utf-8")
            elif job_text.strip():
                job_path = tmp / "job_description.txt"
                job_path.write_text(job_text, encoding="utf-8")
            else:
                st.error("Please provide a job description.")
                st.stop()

            try:
                with st.spinner("Ranking candidates..."):
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

            metric_cols = st.columns(4)
            metric_cols[0].metric("Ranked rows", len(rows))
            metric_cols[1].metric("Top score", f"{rows[0].score:.4f}")
            metric_cols[2].metric("Best candidate", rows[0].candidate_id)
            metric_cols[3].metric("CSV columns", "4")

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
                "⬇️ Download ranked CSV",
                data=csv_text,
                file_name="sandbox_submission.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.subheader("Top candidates")
            st.dataframe(
                [
                    {
                        "Rank": index,
                        "Candidate ID": row.candidate_id,
                        "Score": f"{row.score:.4f}",
                        "Reasoning": row.reasoning,
                    }
                    for index, row in enumerate(rows, start=1)
                ],
                use_container_width=True,
                hide_index=True,
            )

with tab_method:
    st.markdown(
        """
        ### Ranking strategy

        The ranker is tuned to the released Senior AI Engineer founding-team JD. It rewards candidates who show
        real production evidence of owning retrieval, ranking, matching, embeddings, vector search, applied ML/NLP,
        evaluation infrastructure, and product engineering.

        It down-weights candidates who are likely traps for keyword-only systems:

        - keyword-stuffed profiles without matching career evidence
        - consulting-only histories without product-company depth
        - inactive candidates and very low recruiter response rates
        - long notice periods
        - CV/speech-heavy AI profiles without retrieval/NLP/IR evidence
        - framework-only GenAI profiles without production search/ranking depth
        - honeypot-style impossible skill claims

        The reasoning column references candidate facts such as title, years of experience, matching skills,
        response rate, recency, notice period, and concerns.
        """
    )

with tab_output:
    st.markdown("### Official reproduction command")
    st.code(
        "python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./team_yourid.csv --top-k 100\n"
        "python validate_submission.py ./team_yourid.csv",
        language="bash",
    )
    st.markdown("### PowerShell example")
    st.code(
        "python rank.py `\n"
        "  --candidates C:\\redrob-data\\candidates.jsonl `\n"
        "  --job uploads\\A1.txt `\n"
        "  --out team_yourid.csv `\n"
        "  --top-k 100\n\n"
        "python validate_submission.py team_yourid.csv",
        language="powershell",
    )

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        padding:12px;
        color:#9CA3AF;
        font-size:15px;
        letter-spacing:0.4px;
    ">
        Crafted with <span style="color:#ff4b4b;">❤️</span> by
        <strong style="color:#ffffff;">Core4</strong> ✨
    </div>
    """,
    unsafe_allow_html=True,
)
