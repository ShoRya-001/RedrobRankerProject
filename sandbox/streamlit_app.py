from __future__ import annotations

import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

import streamlit as st

# Import the dependency-free ranker from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rank import iter_candidates, rank_candidates, write_submission  # noqa: E402
from validate_submission import validate_submission  # noqa: E402


st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
  --forest-dark: #253D2C;
  --forest-primary: #2E6F40;
  --forest-mint: #68BA7F;
  --forest-pale: #CFFFDC;
  --forest-ink: #102016;
  --forest-soft: rgba(207, 255, 220, 0.72);
  --forest-card: rgba(255, 255, 255, 0.78);
  --forest-border: rgba(46, 111, 64, 0.18);
  --forest-shadow: 0 24px 70px rgba(37, 61, 44, 0.20);
}

.stApp {
  background:
    radial-gradient(circle at 10% 10%, rgba(104, 186, 127, 0.32), transparent 28rem),
    radial-gradient(circle at 88% 5%, rgba(207, 255, 220, 0.52), transparent 26rem),
    radial-gradient(circle at 50% 95%, rgba(46, 111, 64, 0.22), transparent 30rem),
    linear-gradient(135deg, #f6fff8 0%, #e9faee 42%, #d7f5df 100%);
  color: var(--forest-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.block-container {
  padding-top: 1.6rem;
  padding-bottom: 3rem;
  max-width: 1240px;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #253D2C 0%, #1b2b20 100%);
  border-right: 1px solid rgba(207, 255, 220, 0.16);
}

[data-testid="stSidebar"] * {
  color: #f5fff7 !important;
}

[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stCheckbox label {
  color: #f5fff7 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 0.58rem 0.65rem;
  border-radius: 14px;
  margin-bottom: 0.25rem;
  background: rgba(207, 255, 220, 0.06);
  border: 1px solid rgba(207, 255, 220, 0.08);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: rgba(207, 255, 220, 0.14);
}

h1, h2, h3 {
  color: var(--forest-dark);
  letter-spacing: -0.035em;
}

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 2.05rem;
  border-radius: 32px;
  border: 1px solid rgba(46, 111, 64, 0.18);
  background:
    linear-gradient(135deg, rgba(207, 255, 220, 0.92), rgba(255, 255, 255, 0.76)),
    radial-gradient(circle at 85% 0%, rgba(104, 186, 127, 0.40), transparent 22rem);
  box-shadow: var(--forest-shadow);
  backdrop-filter: blur(18px);
  margin-bottom: 1.2rem;
}

.hero-card:after {
  content: "";
  position: absolute;
  right: -4rem;
  top: -4rem;
  width: 14rem;
  height: 14rem;
  border-radius: 999px;
  background: rgba(104, 186, 127, 0.24);
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.42rem 0.8rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--forest-dark);
  background: rgba(104, 186, 127, 0.22);
  border: 1px solid rgba(46, 111, 64, 0.16);
  margin-bottom: 1rem;
}

.hero-title {
  position: relative;
  z-index: 1;
  font-size: clamp(2rem, 4vw, 4.6rem);
  line-height: 0.98;
  font-weight: 950;
  letter-spacing: -0.075em;
  margin: 0;
  color: var(--forest-dark);
}

.gradient-text {
  background: linear-gradient(90deg, #253D2C, #2E6F40, #68BA7F);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  position: relative;
  z-index: 1;
  color: rgba(16, 32, 22, 0.76);
  max-width: 860px;
  font-size: 1.08rem;
  line-height: 1.75;
  margin-top: 1rem;
}

.quick-card, .glass-card {
  padding: 1.2rem;
  border-radius: 24px;
  border: 1px solid var(--forest-border);
  background: var(--forest-card);
  box-shadow: 0 18px 50px rgba(37, 61, 44, 0.12);
  backdrop-filter: blur(16px);
  height: 100%;
}

.quick-card:hover, .glass-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 24px 70px rgba(37, 61, 44, 0.16);
  transition: all 180ms ease;
}

.step-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.38rem 0.75rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  color: var(--forest-dark);
  background: rgba(104, 186, 127, 0.18);
  border: 1px solid rgba(46, 111, 64, 0.16);
  margin-bottom: 0.7rem;
}

.status-card {
  padding: 1rem;
  border-radius: 20px;
  border: 1px solid rgba(46, 111, 64, 0.16);
  background: rgba(255, 255, 255, 0.66);
}

.status-label {
  color: rgba(37, 61, 44, 0.62);
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.68rem;
  font-weight: 900;
}

.status-value {
  color: var(--forest-dark);
  font-size: 1.38rem;
  font-weight: 950;
  margin-top: 0.15rem;
}

.stButton > button {
  border: 0 !important;
  border-radius: 16px !important;
  padding: 0.75rem 1.25rem !important;
  font-weight: 900 !important;
  color: white !important;
  background: linear-gradient(90deg, #253D2C, #2E6F40) !important;
  box-shadow: 0 14px 34px rgba(46, 111, 64, 0.26) !important;
}

.stButton > button:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

.stDownloadButton > button {
  border-radius: 16px !important;
  font-weight: 900 !important;
  border: 1px solid rgba(46, 111, 64, 0.18) !important;
}

[data-testid="stMetric"] {
  background: rgba(255,255,255,0.68);
  border: 1px solid rgba(46, 111, 64, 0.14);
  padding: 1rem;
  border-radius: 20px;
}

[data-testid="stMetricValue"] {
  color: var(--forest-dark);
  font-weight: 950;
}

[data-testid="stMetricLabel"] {
  color: rgba(37, 61, 44, 0.72);
}

div[data-testid="stTabs"] button {
  border-radius: 999px;
  padding-left: 1rem;
  padding-right: 1rem;
  font-weight: 800;
}

hr {
  border-color: rgba(46, 111, 64, 0.16) !important;
}

.command-box {
  background: #253D2C;
  color: #CFFFDC;
  border-radius: 18px;
  padding: 1rem;
  border: 1px solid rgba(207, 255, 220, 0.16);
}

.small-muted {
  color: rgba(16, 32, 22, 0.68);
  font-size: 0.94rem;
  line-height: 1.65;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


sample_candidates_path = REPO_ROOT / "uploads" / "sample_candidates.json"
sample_job_path = REPO_ROOT / "uploads" / "A1.txt"


if "rank_rows" not in st.session_state:
    st.session_state.rank_rows = []
if "rank_csv" not in st.session_state:
    st.session_state.rank_csv = ""
if "rank_errors" not in st.session_state:
    st.session_state.rank_errors = []
if "last_run_summary" not in st.session_state:
    st.session_state.last_run_summary = None


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


def status_html(label: str, value: str) -> None:
    st.markdown(
        f'<div class="status-card"><div class="status-label">{label}</div><div class="status-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
          <p class="hero-eyebrow">🌿 Lush Forest · Offline Ranking Sandbox</p>
          <h1 class="hero-title">Redrob <span class="gradient-text">Candidate Ranker</span></h1>
          <p class="hero-subtitle">
            A clean, reproducible sandbox for candidate discovery. Upload a small candidate sample and a
            TXT, MD, DOCX, or pasted job description, run the deterministic ranker, inspect results,
            and download a submission-style CSV.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_ranking(
    *,
    use_repo_sample: bool,
    candidate_upload: Any,
    use_repo_job: bool,
    job_upload: Any,
    job_text: str,
    top_k: int,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        if use_repo_sample:
            candidates_path = sample_candidates_path
            candidate_source = "bundled sample_candidates.json"
        elif candidate_upload is not None:
            suffix = Path(candidate_upload.name).suffix or ".jsonl"
            candidates_path = tmp / f"candidates{suffix}"
            candidates_path.write_bytes(candidate_upload.getvalue())
            candidate_source = candidate_upload.name
        else:
            st.error("Please provide a candidate sample.")
            st.stop()

        if use_repo_job:
            job_path = sample_job_path
            job_source = "bundled A1.txt"
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
            job_source = job_upload.name
        elif job_text.strip():
            job_path = tmp / "job_description.txt"
            job_path.write_text(job_text, encoding="utf-8")
            job_source = "pasted text"
        else:
            st.error("Please provide a job description.")
            st.stop()

        try:
            with st.spinner("Ranking candidates with deterministic offline scoring..."):
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
        official_errors = validate_submission(str(output_path)) if len(rows) == 100 else []

        st.session_state.rank_rows = rows
        st.session_state.rank_csv = csv_text
        st.session_state.rank_errors = official_errors
        st.session_state.last_run_summary = {
            "candidate_source": candidate_source,
            "job_source": job_source,
            "ranked_rows": len(rows),
            "top_score": rows[0].score,
            "top_candidate": rows[0].candidate_id,
        }


def render_results() -> None:
    rows = st.session_state.rank_rows
    if not rows:
        st.info("No ranking has been generated yet. Go to **Run Ranker** and click **Run ranking**.")
        return

    summary = st.session_state.last_run_summary or {}
    st.success(f"Generated {len(rows)} ranked rows.")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Ranked rows", len(rows))
    metric_cols[1].metric("Top score", f"{rows[0].score:.4f}")
    metric_cols[2].metric("Best candidate", rows[0].candidate_id)
    metric_cols[3].metric("CSV columns", "4")

    if summary:
        st.caption(
            f"Candidate source: {summary.get('candidate_source')} · Job source: {summary.get('job_source')}"
        )

    if len(rows) == 100:
        if st.session_state.rank_errors:
            st.warning("CSV generated, but official validator found issues:")
            for error in st.session_state.rank_errors:
                st.write(f"- {error}")
        else:
            st.success("Official validator passed.")
    else:
        st.info("Official validator requires exactly 100 rows. This sandbox run is valid for small-sample demo purposes.")

    st.download_button(
        "⬇️ Download ranked CSV",
        data=st.session_state.rank_csv,
        file_name="sandbox_submission.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Ranked candidates")
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


with st.sidebar:
    st.markdown("## 🌿 Redrob Ranker")
    st.caption("Small-sample sandbox for the official offline ranking system.")
    st.divider()

    page = st.radio(
        "Quick access",
        ["🏠 Overview", "🚀 Run Ranker", "📊 Results", "🧠 Methodology", "📦 Submit"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### Checklist")
    st.write("1. Candidate sample")
    st.write("2. Job description")
    st.write("3. Run ranking")
    st.write("4. Download CSV")
    st.write("5. Validate final top-100 locally")

    if st.session_state.rank_rows:
        st.divider()
        st.markdown("### Last run")
        st.metric("Rows", len(st.session_state.rank_rows))
        st.metric("Top score", f"{st.session_state.rank_rows[0].score:.4f}")

    st.divider()
    st.caption("Official ranking: CPU-only · no network · no hosted LLM calls")

render_hero()

status_cols = st.columns(4)
with status_cols[0]:
    status_html("Candidate input", "JSONL/JSON")
with status_cols[1]:
    status_html("JD input", "TXT/MD/DOCX")
with status_cols[2]:
    status_html("Output", "CSV")
with status_cols[3]:
    status_html("Palette", "Lush Forest")

st.write("")

if page == "🏠 Overview":
    st.subheader("Workflow")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="quick-card"><span class="step-pill">Step 1</span><h3>Upload candidates</h3><p class="small-muted">Use JSON array, JSONL, NDJSON, TXT, or GZ sample files.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="quick-card"><span class="step-pill">Step 2</span><h3>Add job description</h3><p class="small-muted">Use bundled A1.txt, upload TXT/MD/DOCX, or paste text.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="quick-card"><span class="step-pill">Step 3</span><h3>Run ranker</h3><p class="small-muted">Deterministic offline scoring. No network or hosted AI calls.</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="quick-card"><span class="step-pill">Step 4</span><h3>Download CSV</h3><p class="small-muted">Export candidate_id, rank, score, and reasoning.</p></div>', unsafe_allow_html=True)

    st.write("")
    st.info("Use the sidebar to jump directly to Run Ranker, Results, Methodology, or Submit commands.")

elif page == "🚀 Run Ranker":
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-pill">1 · Candidate sample</span>', unsafe_allow_html=True)
        use_repo_sample = sample_candidates_path.exists() and st.checkbox(
            "Use bundled sample_candidates.json",
            value=True,
            key="use_repo_sample",
        )
        candidate_upload = None
        if not use_repo_sample:
            candidate_upload = st.file_uploader(
                "Upload candidate sample",
                type=["json", "jsonl", "ndjson", "txt", "gz"],
                help="Accepts JSON array, JSONL/NDJSON/TXT with one JSON object per line, or gzipped JSONL.",
                key="candidate_upload",
            )
        st.caption("Sandbox samples can be ≤100 candidates. Use the CLI for the official 100K run.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-pill">2 · Job description</span>', unsafe_allow_html=True)
        use_repo_job = sample_job_path.exists() and st.checkbox(
            "Use bundled A1.txt job description",
            value=True,
            key="use_repo_job",
        )
        job_upload = None
        job_text = ""
        if not use_repo_job:
            job_upload = st.file_uploader(
                "Upload job description",
                type=["txt", "md", "docx"],
                help="DOCX files are parsed with python-docx; text and markdown are read directly.",
                key="job_upload",
            )
            job_text = st.text_area("Or paste job description", height=165, key="job_text")
        st.caption("DOCX, TXT, MD, or pasted text are supported.")
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
            key="top_k",
        )
    with run_cols[1]:
        st.write("")
        st.write("")
        run = st.button("🚀 Run ranking", type="primary", use_container_width=True)
    with run_cols[2]:
        st.write("")
        st.write("")
        st.caption("Tip: after running, jump to Results from the sidebar.")

    if run:
        run_ranking(
            use_repo_sample=use_repo_sample,
            candidate_upload=candidate_upload,
            use_repo_job=use_repo_job,
            job_upload=job_upload,
            job_text=job_text,
            top_k=top_k,
        )
        render_results()

elif page == "📊 Results":
    render_results()

elif page == "🧠 Methodology":
    st.subheader("Ranking strategy")
    st.markdown(
        """
        The ranker is tuned to the released Senior AI Engineer founding-team JD. It rewards candidates who show
        real production evidence of owning retrieval, ranking, matching, embeddings, vector search, applied ML/NLP,
        evaluation infrastructure, and product engineering.

        **Positive signals**
        - Production search, recommendation, retrieval, ranking, or matching systems
        - Embeddings/vector databases/hybrid search
        - Python and production engineering depth
        - Evaluation frameworks: relevance, NDCG, MRR, MAP, offline/online correlation, A/B tests
        - Product-company experience and 5-9 year seniority fit
        - Strong Redrob availability signals: response rate, recency, open-to-work, notice period

        **Down-weighted signals**
        - Keyword-stuffed profiles without matching career evidence
        - Consulting-only histories without product-company depth
        - Inactive candidates and very low recruiter response rates
        - Long notice periods
        - CV/speech-heavy AI profiles without retrieval/NLP/IR evidence
        - Framework-only GenAI profiles without production search/ranking depth
        - Honeypot-style impossible skill claims
        """
    )

elif page == "📦 Submit":
    st.subheader("Official reproduction command")
    st.code(
        "python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./team_yourid.csv --top-k 100\n"
        "python validate_submission.py ./team_yourid.csv",
        language="bash",
    )

    st.subheader("PowerShell example")
    st.code(
        "python rank.py `\n"
        "  --candidates C:\\redrob-data\\candidates.jsonl `\n"
        "  --job uploads\\A1.txt `\n"
        "  --out team_yourid.csv `\n"
        "  --top-k 100\n\n"
        "python validate_submission.py team_yourid.csv",
        language="powershell",
    )

    st.subheader("Portal checklist")
    st.write("✅ Final top-100 CSV")
    st.write("✅ GitHub repository URL")
    st.write("✅ Sandbox/demo link")
    st.write("✅ AI tools declaration")
    st.write("✅ Compute environment summary")
    st.write("✅ Team member list")
    st.write("✅ Methodology summary")

st.divider()
st.caption("Redrob Candidate Ranker Sandbox · Lush Forest UI · deterministic offline ranking · no hosted LLM calls during ranking")
