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
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
:root {
  color-scheme: light;
  --bg: #F6EFE3;
  --bg-2: #EFE3D0;
  --paper: #FFF9EE;
  --paper-2: #FBF1E3;
  --ink: #1E1A14;
  --text-2: #51483C;
  --muted: #776B5E;
  --green: #2F5D3A;
  --green-2: #3E7A4C;
  --green-soft: rgba(47, 93, 58, 0.12);
  --orange: #E89B35;
  --orange-soft: rgba(232, 155, 53, 0.15);
  --blue: #2563EB;
  --blue-soft: rgba(37, 99, 235, 0.12);
  --red: #DC2626;
  --red-soft: rgba(220, 38, 38, 0.12);
  --border: rgba(57, 45, 31, 0.13);
  --shadow: 0 18px 55px rgba(55, 43, 25, 0.12);
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --bg: #161511;
    --bg-2: #201C16;
    --paper: #242019;
    --paper-2: #2C261D;
    --ink: #FFF7EA;
    --text-2: #D8CBB8;
    --muted: #B5A894;
    --green: #78C985;
    --green-2: #9BE3A7;
    --green-soft: rgba(120, 201, 133, 0.14);
    --orange: #F2AE4D;
    --orange-soft: rgba(242, 174, 77, 0.16);
    --blue: #70A5FF;
    --blue-soft: rgba(112, 165, 255, 0.15);
    --red: #F87171;
    --red-soft: rgba(248, 113, 113, 0.15);
    --border: rgba(255, 247, 234, 0.10);
    --shadow: 0 22px 70px rgba(0, 0, 0, 0.36);
  }
}

.stApp {
  background:
    radial-gradient(circle at 12% 8%, rgba(232,155,53,0.12), transparent 22rem),
    radial-gradient(circle at 90% 0%, rgba(47,93,58,0.12), transparent 26rem),
    linear-gradient(180deg, var(--bg), var(--bg-2));
  color: var(--ink);
  font-family: Inter, Manrope, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.block-container {
  width: 92%;
  max-width: 1380px;
  padding-top: 1.1rem;
  padding-bottom: 2.2rem;
}

#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
  display: none !important;
  visibility: hidden !important;
}

h1, h2, h3, h4, h5, h6, p, li, label, span, div {
  color: var(--ink);
}

p, li { color: var(--text-2); line-height: 1.65; }
a { color: var(--green) !important; }

.top-card, .hero-card, .bento-card, .panel-card, .success-box, .checklist-box, .footer-box {
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--paper) 86%, transparent);
  border-radius: 20px;
  box-shadow: var(--shadow);
}

.top-card {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 0.85rem 1rem;
  backdrop-filter: blur(18px);
  margin-bottom: 0.9rem;
}

.hero-card {
  padding: clamp(1.1rem, 2.5vw, 1.55rem);
  margin: 0.75rem 0 1rem;
  background:
    radial-gradient(circle at 88% 0%, var(--orange-soft), transparent 18rem),
    color-mix(in srgb, var(--paper) 90%, transparent);
}

.hero-title {
  font-size: clamp(2rem, 4vw, 4.4rem);
  line-height: 0.98;
  letter-spacing: -0.07em;
  font-weight: 950;
  margin: 0;
}

.hero-title span { color: var(--green); }
.hero-copy { max-width: 760px; margin: 0.7rem 0 0; font-size: 1rem; color: var(--text-2); }

.nav-wrap div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 0.55rem; }
.nav-wrap div[role="radiogroup"] label {
  border: 1px solid var(--border) !important;
  background: var(--paper) !important;
  border-radius: 999px !important;
  min-height: 42px;
  padding: 0.55rem 0.85rem !important;
  box-shadow: 0 8px 24px rgba(55,43,25,0.06);
}
.nav-wrap div[role="radiogroup"] label:hover { transform: translateY(-1px); background: var(--paper-2) !important; }
.nav-wrap div[role="radiogroup"] label:has(input:checked) { border-color: var(--green) !important; background: var(--green-soft) !important; }

.bento-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.9rem; margin: 0.9rem 0 1.1rem; }
.bento-card { padding: 1rem; min-height: 126px; }
.bento-card:hover, .panel-card:hover { transform: translateY(-2px); }
.bento-icon { font-size: 1.65rem; margin-bottom: 0.55rem; }
.bento-label { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.13em; font-weight: 900; }
.bento-value { color: var(--ink); font-size: 1.25rem; font-weight: 900; margin-top: 0.25rem; }

.step-grid { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 0.75rem; margin: 0 0 1rem; }
.step-card { padding: 0.9rem; min-height: 94px; border-radius: 18px; border: 1px solid var(--border); background: var(--paper); box-shadow: 0 8px 24px rgba(55,43,25,0.07); }
.step-card.done { border-color: var(--green); background: var(--green-soft); }
.step-card.active { border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft), 0 8px 24px rgba(55,43,25,0.07); }
.step-kicker { color: var(--muted); font-size: 0.7rem; letter-spacing: 0.12em; font-weight: 900; }
.step-title { margin-top: 0.45rem; font-weight: 900; color: var(--ink); }
.step-tick { float: right; height: 24px; width: 24px; border-radius: 50%; display: grid; place-items: center; color: #fff; background: var(--green); animation: pop 240ms ease both; }

.panel-card, .checklist-box { padding: 1rem; }
.card-title { font-size: 1.1rem; font-weight: 900; margin-bottom: 0.35rem; }
.card-copy { color: var(--text-2); margin: 0; }
.step-pill { display: inline-block; border-radius: 999px; padding: 0.38rem 0.7rem; background: var(--green-soft); color: var(--green); border: 1px solid color-mix(in srgb, var(--green) 30%, transparent); font-size: 0.75rem; font-weight: 900; margin-bottom: 0.75rem; }

.check-progress-label { display: flex; justify-content: space-between; color: var(--text-2); font-size: 0.86rem; font-weight: 800; margin: 0.7rem 0 0.5rem; }
.check-track { height: 9px; border-radius: 999px; background: var(--paper-2); border: 1px solid var(--border); overflow: hidden; margin-bottom: 0.9rem; }
.check-fill { height: 100%; background: linear-gradient(90deg, var(--green), #8FD99A); border-radius: 999px; animation: grow 420ms ease both; }
.check-list { display: grid; gap: 0.65rem; }
.check-item { display: grid; grid-template-columns: 30px 1fr; align-items: center; gap: 0.65rem; color: var(--text-2); }
.check-dot { height: 25px; width: 25px; border-radius: 50%; border: 2px solid var(--muted); display: grid; place-items: center; color: transparent; }
.check-dot.done { background: var(--green); border-color: var(--green); color: white; animation: pop 240ms ease both; }
.check-label.done { color: var(--ink); font-weight: 850; }

.success-box { display: grid; grid-template-columns: 38px 1fr; gap: 0.8rem; padding: 0.9rem; background: var(--green-soft); border-color: color-mix(in srgb, var(--green) 35%, transparent); margin-top: 0.75rem; animation: fadeIn 260ms ease both; }
.success-icon { height: 34px; width: 34px; border-radius: 50%; background: var(--green); color: white; display: grid; place-items: center; font-weight: 900; }
.success-title { font-weight: 900; color: var(--ink); }
.success-meta { color: var(--text-2); font-size: 0.9rem; }

.stButton > button { border-radius: 999px !important; min-height: 46px !important; border: 0 !important; background: var(--green) !important; color: #fff !important; font-weight: 900 !important; box-shadow: 0 12px 30px rgba(47,93,58,0.20) !important; }
.stButton > button:hover { transform: translateY(-2px); filter: brightness(1.05); }
.stButton > button:disabled { background: var(--paper-2) !important; color: var(--muted) !important; box-shadow: none !important; }
.stDownloadButton > button { border-radius: 999px !important; min-height: 46px !important; font-weight: 900 !important; background: var(--green-soft) !important; color: var(--ink) !important; border: 1px solid color-mix(in srgb, var(--green) 35%, transparent) !important; }

[data-testid="stFileUploader"] section { border: 1.5px dashed color-mix(in srgb, var(--green) 40%, transparent) !important; border-radius: 18px !important; background: color-mix(in srgb, var(--paper-2) 85%, var(--green) 15%) !important; padding: 1rem !important; }
[data-testid="stFileUploader"] section:hover { background: var(--paper-2) !important; }
[data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p { color: var(--text-2) !important; }
textarea, input { border-radius: 14px !important; color: var(--ink) !important; background: var(--paper) !important; border-color: var(--border) !important; }
textarea::placeholder, input::placeholder { color: var(--muted) !important; opacity: 1 !important; }

.sticky-run-panel { position: sticky; bottom: 16px; z-index: 12; padding: 0.9rem; border: 1px solid var(--border); border-radius: 20px; background: color-mix(in srgb, var(--paper) 92%, transparent); box-shadow: var(--shadow); backdrop-filter: blur(16px); }

.preview-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.9rem; margin: 1rem 0; }
.preview-card { padding: 1rem; border: 1px solid var(--border); border-radius: 20px; background: var(--paper); box-shadow: var(--shadow); }
.preview-card.rank-one { border-color: var(--gold); }
.preview-rank { color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.72rem; font-weight: 900; }
.preview-name { font-size: 1.1rem; font-weight: 900; margin-top: 0.45rem; }
.preview-score { font-size: 1.8rem; font-weight: 950; color: var(--green); margin: 0.65rem 0; }
.skill-chip { display: inline-block; padding: 0.28rem 0.55rem; border-radius: 999px; background: var(--blue-soft); color: var(--ink); font-size: 0.78rem; font-weight: 800; margin: 0 0.25rem 0.35rem 0; }

.empty-state { min-height: 300px; display: grid; place-items: center; text-align: center; }
.empty-icon { height: 86px; width: 86px; border-radius: 24px; display: grid; place-items: center; margin: 0 auto 1rem; background: var(--blue-soft); color: var(--blue); font-size: 2rem; }

.footer-box { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; padding: 1rem; margin-top: 1.6rem; }
.footer-links { display: flex; gap: 1rem; flex-wrap: wrap; font-weight: 850; }

@keyframes pop { 0% { transform: scale(.7); opacity: .5 } 70% { transform: scale(1.12); opacity: 1 } 100% { transform: scale(1); opacity: 1 } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
@keyframes grow { from { width: 0 } }

@media (max-width: 980px) { .bento-grid, .step-grid, .preview-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 720px) { .bento-grid, .step-grid, .preview-grid { grid-template-columns: 1fr; } .topbar { flex-direction: column; align-items: flex-start; } .hero-title { font-size: 2.2rem; } }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

sample_candidates_path = REPO_ROOT / "uploads" / "sample_candidates.json"
sample_job_path = REPO_ROOT / "uploads" / "A1.txt"

DEFAULT_STATE = {
    "rank_rows": [],
    "rank_csv": "",
    "rank_errors": [],
    "last_run_summary": None,
    "candidate_details": {},
    "candidate_ready": False,
    "job_ready": False,
    "ranking_done": False,
    "validation_done": False,
    "download_done": False,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def format_bytes(size: int | float | None) -> str:
    if size is None:
        return "Unknown size"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} GB"


def uploaded_job_to_text(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    data = uploaded_file.getvalue()
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support requires python-docx. Add python-docx to requirements.txt.") from exc
        document = Document(BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
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


def count_candidates(path: Path) -> int | None:
    try:
        return sum(1 for _ in iter_candidates(path))
    except Exception:
        return None


def candidate_success_card(file_name: str, file_size: int | None, candidate_count: int | None) -> None:
    count_text = f" · {candidate_count} candidates" if candidate_count is not None else ""
    st.markdown(
        f"""
        <div class="success-box">
          <div class="success-icon">✓</div>
          <div>
            <div class="success-title">Candidate sample ready</div>
            <div class="success-meta">{html.escape(file_name)} · {format_bytes(file_size)}{count_text}<br>Upload completed successfully.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def job_success_card(file_name: str, file_size: int | None, note: str = "Upload completed successfully.") -> None:
    st.markdown(
        f"""
        <div class="success-box">
          <div class="success-icon">✓</div>
          <div>
            <div class="success-title">Job description ready</div>
            <div class="success-meta">{html.escape(file_name)} · {format_bytes(file_size)}<br>{html.escape(note)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_candidate_details_for_ids(path: Path, candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    if not candidate_ids:
        return details
    try:
        for candidate in iter_candidates(path):
            candidate_id = str(candidate.get("candidate_id") or "")
            if candidate_id not in candidate_ids:
                continue
            profile = candidate.get("profile") or {}
            skills = [str(item.get("name") or "") for item in candidate.get("skills") or [] if item.get("name")]
            details[candidate_id] = {
                "name": profile.get("anonymized_name") or candidate_id,
                "title": profile.get("current_title") or profile.get("headline") or "Candidate",
                "years": profile.get("years_of_experience"),
                "skills": skills[:8],
            }
            if len(details) == len(candidate_ids):
                break
    except Exception:
        return details
    return details


def extract_reason_skills(reasoning: str) -> list[str]:
    marker = "evidence includes "
    if marker not in reasoning:
        return []
    segment = reasoning.split(marker, 1)[1].split(";", 1)[0]
    if "few exact" in segment.lower():
        return []
    return [part.strip() for part in segment.split(",") if part.strip()][:5]


def candidate_display(row: Any) -> dict[str, Any]:
    details = st.session_state.candidate_details.get(row.candidate_id, {})
    skills = details.get("skills") or extract_reason_skills(row.reasoning)
    name = details.get("name") or row.candidate_id
    title = details.get("title") or "Candidate"
    years = details.get("years")
    years_text = f"{float(years):.1f} yrs" if isinstance(years, int | float) else "experience signal"
    summary = f"{title} with {years_text}. {row.reasoning}"
    return {"name": name, "skills": skills[:6], "summary": summary}


def mark_downloaded() -> None:
    st.session_state.download_done = True


def checklist_state() -> list[tuple[int, str, bool]]:
    return [
        (1, "Candidate Sample", bool(st.session_state.candidate_ready)),
        (2, "Job Description", bool(st.session_state.job_ready)),
        (3, "Run Ranking", bool(st.session_state.ranking_done)),
        (4, "Validate Final Top-100 Locally", bool(st.session_state.validation_done)),
        (5, "Download CSV", bool(st.session_state.download_done)),
    ]


def render_checklist_card() -> None:
    items = checklist_state()
    completed = sum(1 for _, _, done in items if done)
    percent = int(completed / len(items) * 100)
    rows = []
    for index, label, done in items:
        rows.append(
            f'<div class="check-item"><div class="check-dot {"done" if done else ""}">{"✓" if done else ""}</div><div class="check-label {"done" if done else ""}">{index}. {html.escape(label)}</div></div>'
        )
    st.markdown(
        f"""
        <div class="checklist-box">
          <div class="card-title">Live checklist</div>
          <p class="card-copy">Complete each step to generate a submission-ready ranking.</p>
          <div class="check-progress-label"><span>{completed} / {len(items)} Completed</span><span>{percent}%</span></div>
          <div class="check-track"><div class="check-fill" style="width:{percent}%"></div></div>
          <div class="check-list">{''.join(rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def bento_card(label: str, value: str, icon: str) -> None:
    st.markdown(
        f"""
        <div class="bento-card">
          <div class="bento-icon">{icon}</div>
          <div class="bento-label">{html.escape(label)}</div>
          <div class="bento-value">{html.escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        """
        <div class="top-card">
          <div class="topbar">
            <div>
              <div style="font-weight:950; font-size:1.08rem; letter-spacing:-0.04em;">Redrob Candidate Ranker</div>
              <div style="color:var(--muted); font-size:0.84rem;">Offline submission sandbox</div>
            </div>
            <div style="display:flex; gap:.5rem; flex-wrap:wrap; justify-content:flex-end;">
              <span style="border:1px solid var(--border); border-radius:999px; padding:.42rem .7rem; background:var(--green-soft); font-weight:850;">CPU-only</span>
              <span style="border:1px solid var(--border); border-radius:999px; padding:.42rem .7rem; background:var(--paper-2); font-weight:850;">DOCX ready</span>
              <span style="border:1px solid var(--border); border-radius:999px; padding:.42rem .7rem; background:var(--paper-2); font-weight:850;">CSV export</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
          <h1 class="hero-title">Rank candidates with <span>offline AI logic</span>.</h1>
          <p class="hero-copy">Upload candidates and a job description, run the deterministic ranker, validate top-100 output, and export CSV.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def active_step() -> int:
    if not st.session_state.candidate_ready:
        return 1
    if not st.session_state.job_ready:
        return 2
    if not st.session_state.ranking_done:
        return 3
    if not st.session_state.validation_done:
        return 4
    if not st.session_state.download_done:
        return 5
    return 5


def render_steps() -> None:
    active = active_step()
    step_defs = [
        (1, "Upload Candidates", st.session_state.candidate_ready),
        (2, "Upload Job Description", st.session_state.job_ready),
        (3, "Run Ranking", st.session_state.ranking_done),
        (4, "Validate Top-100", st.session_state.validation_done),
        (5, "Download CSV", st.session_state.download_done),
    ]
    cards = []
    for index, title, done in step_defs:
        cls = "step-card done" if done else "step-card active" if active == index else "step-card"
        tick = '<span class="step-tick">✓</span>' if done else ""
        cards.append(f'<div class="{cls}">{tick}<div class="step-kicker">STEP {index}</div><div class="step-title">{html.escape(title)}</div></div>')
    st.markdown(f'<div class="step-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


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
            progress.progress(22, text="Reading candidate sample...")
            with st.spinner("Ranking candidates with deterministic offline scoring..."):
                progress.progress(58, text="Scoring candidate-job fit...")
                rows = rank_candidates(iter_candidates(candidates_path), top_k=top_k)
                progress.progress(84, text="Loading candidate preview data...")
                details = load_candidate_details_for_ids(candidates_path, {row.candidate_id for row in rows})
                progress.progress(92, text="Writing CSV...")
        except SystemExit as exc:
            progress.empty()
            st.error(str(exc))
            st.stop()
        except Exception as exc:
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
        st.session_state.candidate_details = details
        st.session_state.last_run_summary = {"candidate_source": candidate_source, "job_source": job_source}
        st.session_state.candidate_ready = True
        st.session_state.job_ready = True
        st.session_state.ranking_done = True
        st.session_state.validation_done = len(rows) == 100 and not official_errors
        st.session_state.download_done = False


def score_class(score: float) -> str:
    if score >= 0.70:
        return "score-high"
    if score >= 0.40:
        return "score-mid"
    return "score-low"


def extract_reason_skills(reasoning: str) -> list[str]:
    marker = "evidence includes "
    if marker not in reasoning:
        return []
    segment = reasoning.split(marker, 1)[1].split(";", 1)[0]
    if "few exact" in segment.lower():
        return []
    return [part.strip() for part in segment.split(",") if part.strip()][:5]


def candidate_display(row: Any) -> dict[str, Any]:
    details = st.session_state.candidate_details.get(row.candidate_id, {})
    skills = details.get("skills") or extract_reason_skills(row.reasoning)
    name = details.get("name") or row.candidate_id
    title = details.get("title") or "Candidate"
    years = details.get("years")
    years_text = f"{float(years):.1f} yrs" if isinstance(years, int | float) else "experience signal"
    summary = f"{title} with {years_text}. {row.reasoning}"
    return {"name": name, "skills": skills[:6], "summary": summary}


def skill_text(skills: list[str]) -> str:
    return ", ".join(skills[:5]) if skills else "Evidence in reason"


def render_preview_cards(rows: list[Any]) -> None:
    cols = st.columns(3)
    for index, row in enumerate(rows[:3], start=1):
        data = candidate_display(row)
        with cols[index - 1]:
            with st.container(border=True):
                st.caption(f"Rank #{index}")
                st.subheader(str(data["name"]))
                st.metric("Match", f"{row.score * 100:.1f}%")
                st.write(f"**Skills:** {skill_text(data['skills'])}")
                st.write(str(data["summary"])[:240])


def render_results() -> None:
    rows = st.session_state.rank_rows
    if not rows:
        st.markdown(
            """
            <div class="empty-state">
              <div>
                <div class="empty-icon">▦</div>
                <h3>No ranking generated yet.</h3>
                <p>Upload candidates and a job description to begin.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.success(f"Generated {len(rows)} ranked rows.")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Ranked rows", len(rows))
    metric_cols[1].metric("Top score", f"{rows[0].score:.4f}")
    metric_cols[2].metric("Best candidate", rows[0].candidate_id)
    metric_cols[3].metric("CSV columns", "4")

    summary = st.session_state.last_run_summary or {}
    if summary:
        st.caption(f"Candidate source: {summary.get('candidate_source')} · Job source: {summary.get('job_source')}")

    if len(rows) == 100:
        if st.session_state.rank_errors:
            st.warning("CSV generated, but official validator found issues:")
            for error in st.session_state.rank_errors:
                st.write(f"- {error}")
        else:
            st.success("Official validator passed.")
    else:
        st.info("Official validator requires exactly 100 rows. Validation completes only for a valid top-100 run.")

    st.download_button(
        "Download ranked CSV",
        data=st.session_state.rank_csv,
        file_name="sandbox_submission.csv",
        mime="text/csv",
        use_container_width=True,
        on_click=mark_downloaded,
    )

    st.subheader("Top 3 candidates")
    render_preview_cards(rows)

    st.subheader("Ranked candidates")
    table_rows = []
    for index, row in enumerate(rows, start=1):
        data = candidate_display(row)
        table_rows.append(
            {
                "Rank": index,
                "Candidate": f"{data['name']} ({row.candidate_id})",
                "Match Score": round(row.score * 100, 2),
                "Match %": f"{row.score * 100:.1f}%",
                "Skills": skill_text(data["skills"]),
                "Reason": row.reasoning,
            }
        )
    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Match Score": st.column_config.ProgressColumn("Match Score", min_value=0, max_value=100, format="%.1f%%"),
        },
    )



render_topbar()

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
page = st.radio(
    "Navigation",
    ["Overview", "Upload & Rank", "Results"],
    horizontal=True,
    label_visibility="collapsed",
    key="nav_choice",
)
st.markdown('</div>', unsafe_allow_html=True)

render_hero()

stat_cols = st.columns(4)
with stat_cols[0]:
    bento_card("Candidates", "Max 100", "◎")
with stat_cols[1]:
    bento_card("Job Description", "TXT / MD / DOCX", "□")
with stat_cols[2]:
    bento_card("Ranking", "Offline Engine", "▶")
with stat_cols[3]:
    bento_card("Output", "CSV Export", "⇩")

st.write("")

if page == "Overview":
    st.subheader("Overview")
    with st.container(border=True):
        st.subheader("A lightweight ranking workspace for Redrob submissions.")
        st.write("Use the Upload & Rank page to run the sandbox workflow. The official 100K run should still be executed locally with `rank.py`.")

elif page == "Upload & Rank":
    render_steps()
    upload_cols = st.columns([1.05, 1.05, 0.9])

    with upload_cols[0]:
        with st.container(border=True):
            st.markdown("### STEP 1 · Upload Candidates")
            use_repo_sample = sample_candidates_path.exists() and st.checkbox("Use bundled sample_candidates.json", value=True)
            candidate_upload = None
            if not use_repo_sample:
                candidate_upload = st.file_uploader(
                    "Upload candidate sample",
                    type=["json", "jsonl", "ndjson", "txt", "gz"],
                    help="Accepts JSON array, JSONL/NDJSON/TXT with one JSON object per line, or gzipped JSONL.",
                )
            st.session_state.candidate_ready = bool(use_repo_sample or candidate_upload is not None)
            if use_repo_sample:
                candidate_success_card("sample_candidates.json", sample_candidates_path.stat().st_size, count_candidates(sample_candidates_path))
            elif candidate_upload is not None:
                candidate_count = None
                if candidate_upload.size <= 25 * 1024 * 1024:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(candidate_upload.name).suffix or ".jsonl") as handle:
                        handle.write(candidate_upload.getvalue())
                        temp_candidate_path = Path(handle.name)
                    candidate_count = count_candidates(temp_candidate_path)
                    temp_candidate_path.unlink(missing_ok=True)
                candidate_success_card(candidate_upload.name, candidate_upload.size, candidate_count)
            st.caption("Sandbox samples can be ≤100 candidates. Use the CLI for the official 100K run.")

    with upload_cols[1]:
        with st.container(border=True):
            st.markdown("### STEP 2 · Upload Job Description")
            use_repo_job = sample_job_path.exists() and st.checkbox("Use bundled A1.txt job description", value=True)
            job_upload = None
            job_text = ""
            if not use_repo_job:
                job_upload = st.file_uploader(
                    "Upload job description",
                    type=["txt", "md", "docx"],
                    help="DOCX files are parsed with python-docx; text and markdown are read directly.",
                )
                job_text = st.text_area("Or paste job description", height=165, placeholder="Paste the job description here...")
            st.session_state.job_ready = bool(use_repo_job or job_upload is not None or job_text.strip())
            if use_repo_job:
                job_success_card("A1.txt", sample_job_path.stat().st_size)
            elif job_upload is not None:
                job_success_card(job_upload.name, job_upload.size)
            elif job_text.strip():
                job_success_card("Pasted job description", len(job_text.encode("utf-8")), "Text entered successfully.")
            st.caption("DOCX, TXT, MD, or pasted text are supported.")

    with upload_cols[2]:
        render_checklist_card()

    st.write("")
    top_k = st.slider(
        "Top K rows to generate",
        min_value=1,
        max_value=100,
        value=50 if use_repo_sample else 100,
        help="Official submission requires 100 rows. Small sandbox samples may contain fewer candidates.",
    )
    required_ready = bool(st.session_state.candidate_ready and st.session_state.job_ready)
    st.markdown('<div class="sticky-run-panel">', unsafe_allow_html=True)
    run_cols = st.columns([2, 1])
    with run_cols[0]:
        st.markdown("### STEP 3 · Run Ranking")
        st.write("Ready to rank candidates." if required_ready else "Upload/select candidates and a job description to enable ranking.")
    with run_cols[1]:
        run = st.button("Run Ranking", type="primary", use_container_width=True, disabled=not required_ready)
    st.markdown('</div>', unsafe_allow_html=True)

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

elif page == "Results":
    render_results()


st.markdown(
    """
    <div class="footer-box">
      <div>
        <strong>Built for the Redrob AI Challenge</strong><br>
        Offline Candidate Ranking Engine · Version 1.0
      </div>
      <div class="footer-links">
        <a href="https://github.com/ShoRya-001/RedrobRankerProject" target="_blank">GitHub</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
