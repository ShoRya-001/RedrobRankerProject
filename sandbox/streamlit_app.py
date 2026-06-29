from __future__ import annotations

import html
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
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
  color-scheme: light;
  --spotify-green: #1DB954;
  --spotify-green-soft: rgba(29, 185, 84, 0.13);
  --spotify-green-border: rgba(29, 185, 84, 0.30);
  --warning: #F59E0B;
  --error: #EF4444;

  --bg: #F8F9FA;
  --bg-2: #F2F3F5;
  --surface: #FFFFFF;
  --surface-2: #F7F8FA;
  --surface-hover: #EEF1F4;
  --glass: rgba(255, 255, 255, 0.78);
  --border: #E5E7EB;
  --border-soft: rgba(17, 24, 39, 0.08);
  --text: #111827;
  --text-2: #4B5563;
  --muted: #6B7280;
  --shadow: 0 18px 60px rgba(17, 24, 39, 0.10);
  --shadow-2: 0 10px 30px rgba(17, 24, 39, 0.08);
  --code-bg: #111827;
  --code-text: #ECFDF5;
  --sidebar-bg: #FFFFFF;
  --sidebar-text: #111827;
  --sidebar-muted: #4B5563;
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --bg: #121212;
    --bg-2: #181818;
    --surface: #202020;
    --surface-2: #181818;
    --surface-hover: #282828;
    --glass: rgba(32, 32, 32, 0.78);
    --border: rgba(255,255,255,0.08);
    --border-soft: rgba(255,255,255,0.08);
    --text: #FFFFFF;
    --text-2: #B3B3B3;
    --muted: #8A8A8A;
    --shadow: 0 22px 72px rgba(0,0,0,0.46);
    --shadow-2: 0 12px 34px rgba(0,0,0,0.35);
    --code-bg: #050505;
    --code-text: #E5E7EB;
    --sidebar-bg: #000000;
    --sidebar-text: #FFFFFF;
    --sidebar-muted: #B3B3B3;
  }
}

* {
  transition: background-color 220ms ease, border-color 220ms ease, box-shadow 220ms ease, transform 180ms ease, color 160ms ease;
}

.stApp {
  background:
    radial-gradient(circle at 15% 10%, rgba(29, 185, 84, 0.13), transparent 28rem),
    radial-gradient(circle at 90% 0%, rgba(29, 185, 84, 0.10), transparent 24rem),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
  color: var(--text);
  font-family: Inter, Manrope, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
}

.block-container {
  padding-top: 1.25rem;
  padding-bottom: 3rem;
  max-width: 1280px;
}

#MainMenu, footer, header[data-testid="stHeader"] {
  visibility: hidden;
}

[data-testid="stSidebar"] {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  box-shadow: 10px 0 32px rgba(0,0,0,0.06);
}

[data-testid="stSidebar"] * {
  color: var(--sidebar-text) !important;
}

[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaptionContainer,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: var(--sidebar-muted) !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
  min-height: 44px;
  padding: 0.65rem 0.75rem;
  border-radius: 14px;
  margin-bottom: 0.30rem;
  background: transparent;
  border: 1px solid transparent;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--surface-hover);
  border-color: var(--border);
  transform: translateX(2px);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--spotify-green-soft);
  border-color: var(--spotify-green-border);
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
  color: var(--text);
}

h1, h2, h3 {
  letter-spacing: -0.045em;
}

p, li {
  color: var(--text-2);
  line-height: 1.68;
}

a {
  color: var(--spotify-green) !important;
}

.spotify-shell {
  position: sticky;
  top: 0;
  z-index: 20;
  margin-bottom: 16px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: color-mix(in srgb, var(--glass) 86%, transparent);
  backdrop-filter: blur(18px);
  box-shadow: var(--shadow-2);
  padding: 14px 18px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  color: #000;
  background: var(--spotify-green);
  box-shadow: 0 12px 32px rgba(29,185,84,0.28);
  font-weight: 950;
}

.brand-title {
  font-weight: 950;
  letter-spacing: -0.05em;
  font-size: 1.12rem;
  color: var(--text);
}

.brand-subtitle {
  font-size: 0.82rem;
  color: var(--muted);
  font-weight: 700;
}

.topbar-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border-radius: 999px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  color: var(--text-2);
  background: var(--surface-2);
  font-size: 0.78rem;
  font-weight: 850;
  white-space: nowrap;
}

.badge-green {
  background: var(--spotify-green-soft);
  border-color: var(--spotify-green-border);
  color: var(--text);
}

.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  border: 1px solid var(--border);
  background:
    radial-gradient(circle at 88% 4%, rgba(29,185,84,0.26), transparent 22rem),
    linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
  box-shadow: var(--shadow);
  padding: clamp(1.4rem, 4vw, 2.4rem);
  margin-bottom: 18px;
}

.hero-card:before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(29,185,84,0.10), transparent 44%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--spotify-green-soft);
  border: 1px solid var(--spotify-green-border);
  color: var(--text);
  font-weight: 950;
  font-size: 0.78rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.hero-title {
  max-width: 900px;
  margin: 0;
  color: var(--text);
  font-size: clamp(2.15rem, 5vw, 5.8rem);
  line-height: 0.95;
  letter-spacing: -0.075em;
  font-weight: 980;
}

.gradient-text {
  background: linear-gradient(90deg, var(--spotify-green), #7DE39B 62%, var(--text));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  max-width: 820px;
  margin-top: 18px;
  margin-bottom: 0;
  color: var(--text-2);
  font-size: 1.05rem;
  line-height: 1.72;
}

.quick-card, .glass-card, .method-card {
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-2);
  padding: 18px;
  height: 100%;
}

.quick-card:hover, .glass-card:hover, .method-card:hover {
  background: var(--surface-hover);
  transform: translateY(-2px) scale(1.005);
  box-shadow: var(--shadow);
}

.step-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px;
  border-radius: 999px;
  color: var(--text);
  background: var(--spotify-green-soft);
  border: 1px solid var(--spotify-green-border);
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
}

.card-title {
  margin: 0 0 8px 0;
  color: var(--text);
  font-size: 1.08rem;
  font-weight: 950;
  letter-spacing: -0.035em;
}

.card-copy {
  margin: 0;
  color: var(--text-2);
  font-size: 0.92rem;
}

.status-card {
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-2);
  padding: 16px;
}

.status-label {
  color: var(--muted);
  font-size: 0.69rem;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.status-value {
  color: var(--text);
  margin-top: 3px;
  font-size: 1.35rem;
  font-weight: 950;
  letter-spacing: -0.04em;
}

.stButton > button {
  min-height: 46px !important;
  border: 0 !important;
  border-radius: 999px !important;
  padding: 0.72rem 1.25rem !important;
  font-weight: 950 !important;
  color: #000000 !important;
  background: var(--spotify-green) !important;
  box-shadow: 0 14px 34px rgba(29,185,84,0.24) !important;
}

.stButton > button:hover {
  background: #22d660 !important;
  color: #000000 !important;
  transform: translateY(-2px);
  box-shadow: 0 18px 44px rgba(29,185,84,0.32) !important;
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 3px solid rgba(29,185,84,0.42) !important;
  outline-offset: 2px !important;
}

.stDownloadButton > button {
  min-height: 46px !important;
  border-radius: 999px !important;
  font-weight: 950 !important;
  border: 1px solid var(--spotify-green-border) !important;
  color: var(--text) !important;
  background: var(--spotify-green-soft) !important;
}

[data-testid="stFileUploader"] section {
  border: 1.5px dashed var(--spotify-green-border) !important;
  border-radius: 20px !important;
  background: color-mix(in srgb, var(--surface-2) 88%, var(--spotify-green) 12%) !important;
  padding: 18px !important;
}

[data-testid="stFileUploader"] section:hover {
  border-color: var(--spotify-green) !important;
  background: var(--surface-hover) !important;
}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
  color: var(--text-2) !important;
}

textarea, input {
  border-radius: 14px !important;
  color: var(--text) !important;
  background: var(--surface) !important;
  border-color: var(--border) !important;
}

textarea::placeholder, input::placeholder {
  color: var(--muted) !important;
  opacity: 1 !important;
}

textarea:focus, input:focus {
  border-color: var(--spotify-green) !important;
  box-shadow: 0 0 0 3px rgba(29,185,84,0.16) !important;
}

[data-testid="stMetric"] {
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-2);
  padding: 16px;
}

[data-testid="stMetricLabel"] p {
  color: var(--text-2) !important;
  font-weight: 800;
}

[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-weight: 950 !important;
  letter-spacing: -0.05em;
}

div[data-testid="stTabs"] button {
  border-radius: 999px;
  padding-left: 1rem;
  padding-right: 1rem;
  font-weight: 900;
  color: var(--text-2) !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--text) !important;
}

.stAlert {
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
}

pre, code {
  background: var(--code-bg) !important;
  color: var(--code-text) !important;
  border-radius: 14px !important;
}

.results-table-wrap {
  margin-top: 18px;
  overflow-x: auto;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-2);
}

.results-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 860px;
}

.results-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 0.72rem;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}

.results-table tbody tr:nth-child(even) {
  background: color-mix(in srgb, var(--surface-2) 52%, transparent);
}

.results-table tbody tr:hover {
  background: var(--surface-hover);
}

.results-table td {
  color: var(--text-2);
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-soft);
  vertical-align: top;
}

.results-table .candidate-id {
  color: var(--text);
  font-weight: 900;
}

.rank-chip {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-weight: 950;
  color: #000;
  background: var(--spotify-green);
}

.score-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  border-radius: 999px;
  padding: 6px 10px;
  font-weight: 950;
}

.score-high { background: rgba(29,185,84,0.18); color: var(--spotify-green); }
.score-mid { background: rgba(245,158,11,0.17); color: var(--warning); }
.score-low { background: rgba(107,114,128,0.14); color: var(--text-2); }

.score-bars {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.score-bar-row {
  display: grid;
  grid-template-columns: 130px 1fr 70px;
  gap: 12px;
  align-items: center;
}

.score-bar-track {
  height: 10px;
  border-radius: 999px;
  background: var(--surface-hover);
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--spotify-green), #7DE39B);
}

hr {
  border-color: var(--border) !important;
}

@media (max-width: 760px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  .topbar-badges { justify-content: flex-start; }
  .hero-title { font-size: 2.35rem; }
  .score-bar-row { grid-template-columns: 1fr; gap: 6px; }
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


def icon_svg(name: str) -> str:
    icons = {
        "target": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "upload": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        "play": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>',
        "download": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        "check": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    }
    return icons.get(name, icons["target"])


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


def status_html(label: str, value: str, icon_name: str) -> None:
    st.markdown(
        f"""
        <div class="status-card">
          <div class="status-label">{icon_svg(icon_name)} {html.escape(label)}</div>
          <div class="status-value">{html.escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        f"""
        <div class="spotify-shell">
          <div class="topbar">
            <div class="brand-lockup">
              <div class="brand-icon">{icon_svg("target")}</div>
              <div>
                <div class="brand-title">Redrob Candidate Ranker</div>
                <div class="brand-subtitle">Offline submission sandbox</div>
              </div>
            </div>
            <div class="topbar-badges">
              <span class="badge badge-green">{icon_svg("check")} CPU-only</span>
              <span class="badge">No network</span>
              <span class="badge">TXT · MD · DOCX</span>
              <span class="badge">CSV export</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="hero-content">
            <p class="hero-eyebrow">{icon_svg("target")} Spotify-inspired · Offline Ranking</p>
            <h1 class="hero-title">Discover the <span class="gradient-text">right candidates</span>.</h1>
            <p class="hero-subtitle">
              A premium, reproducible sandbox for the Redrob candidate ranking challenge. Upload a small candidate
              sample and a TXT, MD, DOCX, or pasted job description, run the deterministic ranker, inspect results,
              and download a submission-style CSV.
            </p>
          </div>
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

        progress = st.progress(0, text="Preparing files...")
        try:
            progress.progress(20, text="Reading candidate profiles...")
            with st.spinner("Ranking candidates with deterministic offline scoring..."):
                progress.progress(55, text="Scoring candidate-job fit...")
                rows = rank_candidates(iter_candidates(candidates_path), top_k=top_k)
                progress.progress(88, text="Writing CSV...")
        except SystemExit as exc:
            progress.empty()
            st.error(str(exc))
            st.stop()
        except Exception as exc:  # pragma: no cover - defensive UI guard
            progress.empty()
            st.exception(exc)
            st.stop()

        if not rows:
            progress.empty()
            st.error("No valid candidates found in the uploaded file.")
            st.stop()

        output_path = tmp / "sandbox_submission.csv"
        write_submission(rows, output_path)
        csv_text = output_path.read_text(encoding="utf-8")
        official_errors = validate_submission(str(output_path)) if len(rows) == 100 else []
        progress.progress(100, text="Ranking complete.")

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


def score_class(score: float) -> str:
    if score >= 0.70:
        return "score-high"
    if score >= 0.40:
        return "score-mid"
    return "score-low"


def render_score_bars(rows: list[Any]) -> None:
    top_rows = rows[:5]
    if not top_rows:
        return
    bars = []
    for row in top_rows:
        pct = max(2, min(100, row.score * 100))
        bars.append(
            f"""
            <div class="score-bar-row">
              <div class="candidate-id">{html.escape(row.candidate_id)}</div>
              <div class="score-bar-track"><div class="score-bar-fill" style="width:{pct:.1f}%"></div></div>
              <div>{row.score:.4f}</div>
            </div>
            """
        )
    st.markdown('<div class="score-bars">' + "".join(bars) + "</div>", unsafe_allow_html=True)


def render_results_table(rows: list[Any]) -> None:
    body = []
    for index, row in enumerate(rows, start=1):
        body.append(
            f"""
            <tr>
              <td><span class="rank-chip">{index}</span></td>
              <td class="candidate-id">{html.escape(row.candidate_id)}</td>
              <td><span class="score-pill {score_class(row.score)}">{row.score:.4f}</span></td>
              <td>{html.escape(row.reasoning)}</td>
            </tr>
            """
        )
    st.markdown(
        f"""
        <div class="results-table-wrap">
          <table class="results-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Candidate ID</th>
                <th>Score</th>
                <th>Reasoning</th>
              </tr>
            </thead>
            <tbody>{''.join(body)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        f"{icon_svg('download')} Download ranked CSV",
        data=st.session_state.rank_csv,
        file_name="sandbox_submission.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Score spread")
    render_score_bars(rows)

    st.subheader("Ranked candidates")
    render_results_table(rows)


with st.sidebar:
    st.markdown("## 🎧 Redrob Ranker")
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
    st.caption("CPU-only · no network · no hosted LLM calls")

render_topbar()
render_hero()

status_cols = st.columns(4)
with status_cols[0]:
    status_html("Candidate input", "JSONL/JSON", "upload")
with status_cols[1]:
    status_html("JD input", "TXT/MD/DOCX", "upload")
with status_cols[2]:
    status_html("Output", "CSV", "download")
with status_cols[3]:
    status_html("Mode", "Offline", "check")

st.write("")

if page == "🏠 Overview":
    st.subheader("Workflow")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="quick-card"><span class="step-pill">{icon_svg("upload")} Step 1</span><h3 class="card-title">Upload candidates</h3><p class="card-copy">Use JSON array, JSONL, NDJSON, TXT, or GZ sample files.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="quick-card"><span class="step-pill">{icon_svg("upload")} Step 2</span><h3 class="card-title">Add job description</h3><p class="card-copy">Use bundled A1.txt, upload TXT/MD/DOCX, or paste text.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="quick-card"><span class="step-pill">{icon_svg("play")} Step 3</span><h3 class="card-title">Run ranker</h3><p class="card-copy">Deterministic offline scoring. No network or hosted AI calls.</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="quick-card"><span class="step-pill">{icon_svg("download")} Step 4</span><h3 class="card-title">Download CSV</h3><p class="card-copy">Export candidate_id, rank, score, and reasoning.</p></div>', unsafe_allow_html=True)

    st.write("")
    st.info("Use the sidebar to jump directly to Run Ranker, Results, Methodology, or Submit commands.")

elif page == "🚀 Run Ranker":
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<span class="step-pill">{icon_svg("upload")} 1 · Candidate sample</span>', unsafe_allow_html=True)
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
        st.markdown(f'<span class="step-pill">{icon_svg("upload")} 2 · Job description</span>', unsafe_allow_html=True)
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
        run = st.button("Run ranking", type="primary", use_container_width=True)
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
    method_cols = st.columns(2)
    with method_cols[0]:
        st.markdown(
            """
            <div class="method-card">
              <span class="step-pill">Positive signals</span>
              <ul>
                <li>Production search, recommendation, retrieval, ranking, or matching systems</li>
                <li>Embeddings, vector databases, and hybrid search</li>
                <li>Python and production engineering depth</li>
                <li>Relevance metrics, NDCG, MRR, MAP, offline/online evaluation, and A/B tests</li>
                <li>Product-company experience and 5-9 year seniority fit</li>
                <li>Strong Redrob availability signals</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with method_cols[1]:
        st.markdown(
            """
            <div class="method-card">
              <span class="step-pill">Down-weighted signals</span>
              <ul>
                <li>Keyword-stuffed profiles without matching career evidence</li>
                <li>Consulting-only histories without product-company depth</li>
                <li>Inactive candidates and very low recruiter response rates</li>
                <li>Long notice periods</li>
                <li>CV/speech-heavy AI profiles without retrieval/NLP/IR evidence</li>
                <li>Honeypot-style impossible skill claims</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
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
    checklist_cols = st.columns(2)
    with checklist_cols[0]:
        st.write("✅ Final top-100 CSV")
        st.write("✅ GitHub repository URL")
        st.write("✅ Sandbox/demo link")
        st.write("✅ AI tools declaration")
    with checklist_cols[1]:
        st.write("✅ Compute environment summary")
        st.write("✅ Team member list")
        st.write("✅ Methodology summary")
        st.write("✅ CSV validation passed")

st.divider()
st.caption("Redrob Candidate Ranker Sandbox · Spotify-inspired SaaS UI · deterministic offline ranking · no hosted LLM calls during ranking")
