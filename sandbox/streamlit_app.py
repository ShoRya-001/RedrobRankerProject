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
    initial_sidebar_state="expanded",
    initial_sidebar_state="collapsed",
)


CUSTOM_CSS = """
<style>
:root {
 color-scheme: light;
  --accent: #1DB954;
  --accent-hover: #22D660;
  --accent-soft: rgba(29, 185, 84, 0.12);
  --accent-border: rgba(29, 185, 84, 0.28);
  --info: #2563EB;
  --info-soft: rgba(37, 99, 235, 0.12);
  --warning: #F59E0B;
  --warning-soft: rgba(245, 158, 11, 0.14);
  --error: #EF4444;
  --error-soft: rgba(239, 68, 68, 0.12);

  --bg: #F8F9FA;
  --bg-2: #F2F3F5;
  --surface: #FFFFFF;
  --surface-2: #F7F8FA;
  --surface-hover: #EEF1F4;
  --glass: rgba(255, 255, 255, 0.82);
  --border: #E5E7EB;
  --border-soft: rgba(17, 24, 39, 0.08);
  --text: #111827;
  --text-2: #4B5563;
  --muted: #6B7280;
  --sidebar-bg: #FFFFFF;
  --sidebar-text: #111827;
  --sidebar-muted: #4B5563;
  --shadow: 0 18px 55px rgba(17, 24, 39, 0.10);
  --shadow-2: 0 10px 28px rgba(17, 24, 39, 0.08);
  --code-bg: #111827;
  --code-text: #ECFDF5;
  --bg: #FAF7EF;
  --bg-2: #F2EBDD;
  --surface: #FFFDF8;
  --surface-2: #F7F0E6;
  --surface-3: #EFE3D0;
  --hover: #F0E6D8;
  --glass: rgba(255, 253, 248, 0.78);
  --border: rgba(67, 55, 38, 0.12);
  --border-strong: rgba(67, 55, 38, 0.20);
  --text: #201A13;
  --text-2: #4F463A;
  --muted: #766B5C;
  --green: #1DB954;
  --green-dark: #157A38;
  --green-soft: rgba(29, 185, 84, 0.12);
  --green-border: rgba(29, 185, 84, 0.28);
  --blue: #2563EB;
  --blue-soft: rgba(37, 99, 235, 0.12);
  --orange: #D97706;
  --orange-soft: rgba(217, 119, 6, 0.14);
  --red: #DC2626;
  --red-soft: rgba(220, 38, 38, 0.12);
  --gold: #D4AF37;
  --shadow: 0 20px 60px rgba(58, 45, 27, 0.13);
  --shadow-soft: 0 10px 28px rgba(58, 45, 27, 0.09);
  --code-bg: #211A12;
  --code-text: #FFF7E8;
}

@media (prefers-color-scheme: dark) {
@@ -67,18 +65,26 @@
   --bg-2: #181818;
   --surface: #202020;
   --surface-2: #181818;
    --surface-hover: #282828;
    --glass: rgba(32, 32, 32, 0.82);
    --border: rgba(255,255,255,0.08);
    --border-soft: rgba(255,255,255,0.08);
    --surface-3: #282828;
    --hover: #282828;
    --glass: rgba(32, 32, 32, 0.80);
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.15);
   --text: #FFFFFF;
   --text-2: #B3B3B3;
   --muted: #8A8A8A;
    --sidebar-bg: #000000;
    --sidebar-text: #FFFFFF;
    --sidebar-muted: #B3B3B3;
    --shadow: 0 22px 70px rgba(0,0,0,0.45);
    --shadow-2: 0 12px 32px rgba(0,0,0,0.35);
    --green: #1DB954;
    --green-dark: #1DB954;
    --green-soft: rgba(29, 185, 84, 0.14);
    --green-border: rgba(29, 185, 84, 0.34);
    --blue: #60A5FA;
    --blue-soft: rgba(96, 165, 250, 0.14);
    --orange: #F59E0B;
    --orange-soft: rgba(245, 158, 11, 0.16);
    --red: #EF4444;
    --red-soft: rgba(239, 68, 68, 0.14);
    --shadow: 0 24px 70px rgba(0, 0, 0, 0.44);
    --shadow-soft: 0 12px 30px rgba(0, 0, 0, 0.32);
   --code-bg: #050505;
   --code-text: #E5E7EB;
 }
@@ -90,9 +96,9 @@

.stApp {
 background:
    radial-gradient(circle at 12% 8%, rgba(29, 185, 84, 0.13), transparent 28rem),
    radial-gradient(circle at 92% 0%, rgba(37, 99, 235, 0.08), transparent 24rem),
    radial-gradient(circle at 50% 100%, rgba(29, 185, 84, 0.07), transparent 30rem),
    radial-gradient(circle at 12% 8%, rgba(29, 185, 84, 0.11), transparent 28rem),
    radial-gradient(circle at 86% 0%, rgba(217, 119, 6, 0.08), transparent 22rem),
    radial-gradient(circle at 50% 100%, rgba(37, 99, 235, 0.06), transparent 30rem),
   linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
 color: var(--text);
 font-family: Inter, Manrope, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
@@ -101,48 +107,13 @@
.block-container {
 width: 92%;
 max-width: 1480px;
  padding-top: 1.15rem;
  padding-top: 1.05rem;
 padding-bottom: 2.5rem;
}

#MainMenu, footer, header[data-testid="stHeader"] {
  visibility: hidden;
}

[data-testid="stSidebar"] {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  box-shadow: 10px 0 34px rgba(0,0,0,0.08);
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
  min-height: 46px;
  padding: 0.65rem 0.75rem;
  border-radius: 16px;
  margin-bottom: 0.34rem;
  background: transparent;
  border: 1px solid transparent;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--surface-hover);
  border-color: var(--border);
  transform: translateX(2px);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--accent-soft);
  border-color: var(--accent-border);
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
  display: none !important;
  visibility: hidden !important;
}

h1, h2, h3, h4, h5, h6, p, li, label, span, div {
@@ -158,117 +129,19 @@
 letter-spacing: -0.045em;
}

a { color: var(--accent) !important; }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0 10px;
}

.sidebar-logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: #000000;
  box-shadow: 0 12px 32px rgba(29,185,84,0.28);
}

.sidebar-title {
  font-size: 1.15rem;
  line-height: 1.1;
  font-weight: 950;
  letter-spacing: -0.04em;
}

.sidebar-copy {
  margin: 0 0 16px;
  color: var(--sidebar-muted) !important;
  font-size: 0.91rem;
}

.check-progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin: 8px 0 8px;
  color: var(--sidebar-muted) !important;
  font-size: 0.86rem;
  font-weight: 800;
}

.check-progress-track {
  height: 8px;
  width: 100%;
  border-radius: 999px;
  overflow: hidden;
  background: var(--surface-hover);
  border: 1px solid var(--border);
  margin-bottom: 14px;
}

.check-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), #7DE39B);
  animation: progressIn 420ms ease both;
}

.checklist-wrap {
  display: grid;
  gap: 10px;
}
a { color: var(--green-dark) !important; }

.check-item {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 11px;
  align-items: center;
  min-height: 40px;
  color: var(--sidebar-muted);
  font-size: 0.92rem;
}

.check-dot {
  width: 27px;
  height: 27px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  border: 2px solid color-mix(in srgb, var(--sidebar-muted) 58%, transparent);
  color: transparent;
  font-weight: 950;
}

.check-dot.done {
  border-color: var(--accent);
  background: var(--accent);
  color: #000;
  box-shadow: 0 10px 24px rgba(29,185,84,0.28);
  animation: tickPop 260ms ease both;
}

.check-label.done {
  color: var(--sidebar-text) !important;
  font-weight: 850;
}

.spotify-shell {
.top-shell {
 position: sticky;
 top: 0;
  z-index: 20;
  z-index: 30;
 margin-bottom: 14px;
 border: 1px solid var(--border);
  border-radius: 20px;
  background: color-mix(in srgb, var(--glass) 88%, transparent);
  border-radius: 22px;
  background: color-mix(in srgb, var(--glass) 90%, transparent);
 backdrop-filter: blur(18px);
  box-shadow: var(--shadow-2);
  padding: 12px 16px;
  box-shadow: var(--shadow-soft);
  padding: 14px 16px;
}

.topbar {
@@ -281,24 +154,24 @@
.brand-lockup {
 display: flex;
 align-items: center;
  gap: 11px;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  width: 42px;
  height: 42px;
  border-radius: 14px;
 display: grid;
 place-items: center;
  background: var(--accent);
  color: #000;
  box-shadow: 0 12px 32px rgba(29,185,84,0.28);
  color: #000000;
  background: var(--green);
  box-shadow: 0 12px 30px rgba(29,185,84,0.26);
}

.brand-title {
 font-weight: 950;
 letter-spacing: -0.05em;
  font-size: 1.05rem;
  font-size: 1.08rem;
 color: var(--text);
}

@@ -330,81 +203,145 @@
}

.badge-green {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  background: var(--green-soft);
  border-color: var(--green-border);
 color: var(--text);
}

.nav-wrap {
  margin: -2px 0 16px;
}

.nav-wrap div[role="radiogroup"] {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-wrap div[role="radiogroup"] label {
  border-radius: 999px !important;
  min-height: 42px;
  padding: 0.55rem 0.85rem !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  box-shadow: var(--shadow-soft);
}

.nav-wrap div[role="radiogroup"] label:hover {
  transform: translateY(-1px);
  background: var(--hover) !important;
}

.nav-wrap div[role="radiogroup"] label:has(input:checked) {
  background: var(--green-soft) !important;
  border-color: var(--green-border) !important;
}

.hero-card {
 position: relative;
 overflow: hidden;
 border-radius: 22px;
 border: 1px solid var(--border);
 background:
    radial-gradient(circle at 88% 4%, rgba(29,185,84,0.18), transparent 18rem),
    radial-gradient(circle at 88% 4%, rgba(29,185,84,0.14), transparent 18rem),
   linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
 box-shadow: var(--shadow);
  padding: clamp(1.15rem, 3vw, 1.65rem);
  margin-bottom: 16px;
  animation: fadeSlide 280ms ease both;
}

.hero-card:before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(29,185,84,0.07), transparent 42%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: clamp(1rem, 2.4vw, 1.45rem);
  margin-bottom: 14px;
  animation: fadeSlide 260ms ease both;
}

.hero-title {
  max-width: 850px;
  max-width: 920px;
 margin: 0;
 color: var(--text);
  font-size: clamp(2rem, 4.2vw, 4.6rem);
  line-height: 0.98;
  letter-spacing: -0.075em;
  font-size: clamp(1.9rem, 3.8vw, 4rem);
  line-height: 0.99;
  letter-spacing: -0.072em;
 font-weight: 980;
}

.gradient-text {
  background: linear-gradient(90deg, var(--accent), #7DE39B 60%, var(--text));
  background: linear-gradient(90deg, var(--green-dark), #6DDC91 58%, var(--text));
 -webkit-background-clip: text;
 -webkit-text-fill-color: transparent;
 background-clip: text;
}

.hero-subtitle {
 max-width: 760px;
  margin-top: 12px;
  margin-top: 10px;
 margin-bottom: 0;
 color: var(--text-2);
  font-size: 1.02rem;
  line-height: 1.58;
  font-size: 1rem;
  line-height: 1.5;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 14px 0 18px;
}

.quick-card, .glass-card, .method-card, .success-card, .empty-state, .step-card {
.bento-card, .glass-card, .success-card, .empty-state, .step-card, .footer-card, .info-card {
 border-radius: 20px;
 border: 1px solid var(--border);
 background: var(--glass);
  box-shadow: var(--shadow-2);
  box-shadow: var(--shadow-soft);
 padding: 18px;
  height: 100%;
 backdrop-filter: blur(14px);
 animation: fadeSlide 260ms ease both;
}

.quick-card:hover, .glass-card:hover, .method-card:hover, .success-card:hover, .step-card:hover {
  background: var(--surface-hover);
  transform: translateY(-2px) scale(1.004);
.bento-card:hover, .glass-card:hover, .success-card:hover, .step-card:hover, .info-card:hover {
  background: var(--hover);
  transform: translateY(-2px) scale(1.003);
 box-shadow: var(--shadow);
}

.bento-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  margin-bottom: 12px;
  color: var(--green-dark);
  background: var(--green-soft);
  border: 1px solid var(--green-border);
}

.bento-label, .status-label {
  color: var(--muted);
  font-size: 0.70rem;
  font-weight: 950;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.bento-value, .status-value {
  color: var(--text);
  margin-top: 5px;
  font-size: 1.25rem;
  font-weight: 950;
  letter-spacing: -0.04em;
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
  font-size: 0.94rem;
}

.step-grid {
 display: grid;
 grid-template-columns: repeat(5, minmax(140px, 1fr));
@@ -417,13 +354,13 @@
}

.step-card.completed {
  border-color: var(--accent-border);
  background: var(--accent-soft);
  border-color: var(--green-border);
  background: var(--green-soft);
}

.step-card.active {
  border-color: var(--accent-border);
  box-shadow: 0 0 0 3px rgba(29,185,84,0.10), var(--shadow-2);
  border-color: var(--green-border);
  box-shadow: 0 0 0 3px rgba(29,185,84,0.10), var(--shadow-soft);
}

.step-kicker {
@@ -449,71 +386,102 @@
 border-radius: 999px;
 display: grid;
 place-items: center;
  background: var(--accent);
  background: var(--green);
 color: #000;
 font-weight: 950;
 animation: tickPop 260ms ease both;
}

.step-pill {
  display: inline-flex;
.checklist-card {
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--glass);
  box-shadow: var(--shadow-soft);
  padding: 18px;
  backdrop-filter: blur(14px);
  height: 100%;
}

.check-progress-label {
  display: flex;
  justify-content: space-between;
 align-items: center;
  gap: 7px;
  padding: 7px 11px;
  gap: 8px;
  margin: 8px 0 8px;
  color: var(--text-2);
  font-size: 0.86rem;
  font-weight: 850;
}

.check-progress-track {
  height: 9px;
  width: 100%;
 border-radius: 999px;
  color: var(--text);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
  overflow: hidden;
  background: var(--surface-hover);
  border: 1px solid var(--border);
  margin-bottom: 14px;
}

.card-title {
  margin: 0 0 8px 0;
  color: var(--text);
  font-size: 1.08rem;
  font-weight: 950;
  letter-spacing: -0.035em;
.check-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--green), #7DE39B);
  animation: progressIn 420ms ease both;
}

.card-copy {
  margin: 0;
  color: var(--text-2);
.checklist-wrap {
  display: grid;
  gap: 10px;
}

.check-item {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 11px;
  align-items: center;
  min-height: 38px;
  color: var(--muted);
 font-size: 0.92rem;
}

.status-card {
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--glass);
  box-shadow: var(--shadow-2);
  padding: 16px;
  animation: fadeSlide 300ms ease both;
.check-dot {
  width: 27px;
  height: 27px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  border: 2px solid color-mix(in srgb, var(--muted) 58%, transparent);
  color: transparent;
  font-weight: 950;
}

.status-icon {
  width: 28px;
  height: 28px;
  margin-bottom: 10px;
  color: var(--accent);
.check-dot.done {
  border-color: var(--green);
  background: var(--green);
  color: #000;
  box-shadow: 0 10px 24px rgba(29,185,84,0.28);
  animation: tickPop 260ms ease both;
}

.status-label {
  color: var(--muted);
  font-size: 0.69rem;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
.check-label.done {
  color: var(--text);
  font-weight: 850;
}

.status-value {
.step-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px;
  border-radius: 999px;
 color: var(--text);
  margin-top: 3px;
  font-size: 1.28rem;
  font-weight: 950;
  letter-spacing: -0.04em;
  background: var(--green-soft);
  border: 1px solid var(--green-border);
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
}

.stButton > button {
@@ -523,19 +491,19 @@
 padding: 0.72rem 1.25rem !important;
 font-weight: 950 !important;
 color: #000000 !important;
  background: var(--accent) !important;
  box-shadow: 0 14px 34px rgba(29,185,84,0.24) !important;
  background: var(--green) !important;
  box-shadow: 0 14px 34px rgba(29,185,84,0.22) !important;
}

.stButton > button:hover {
  background: var(--accent-hover) !important;
  background: #22D660 !important;
 color: #000000 !important;
 transform: translateY(-2px);
  box-shadow: 0 18px 44px rgba(29,185,84,0.32) !important;
  box-shadow: 0 18px 44px rgba(29,185,84,0.30) !important;
}

.stButton > button:disabled {
  background: var(--surface-hover) !important;
  background: var(--surface-3) !important;
 color: var(--muted) !important;
 box-shadow: none !important;
 cursor: not-allowed !important;
@@ -554,21 +522,21 @@
 min-height: 46px !important;
 border-radius: 999px !important;
 font-weight: 950 !important;
  border: 1px solid var(--accent-border) !important;
  border: 1px solid var(--green-border) !important;
 color: var(--text) !important;
  background: var(--accent-soft) !important;
  background: var(--green-soft) !important;
}

[data-testid="stFileUploader"] section {
  border: 1.5px dashed var(--accent-border) !important;
  border: 1.5px dashed var(--green-border) !important;
 border-radius: 20px !important;
  background: color-mix(in srgb, var(--surface-2) 88%, var(--accent) 12%) !important;
  background: color-mix(in srgb, var(--surface-2) 88%, var(--green) 12%) !important;
 padding: 18px !important;
}

[data-testid="stFileUploader"] section:hover {
  border-color: var(--accent) !important;
  background: var(--surface-hover) !important;
  border-color: var(--green) !important;
  background: var(--hover) !important;
 box-shadow: 0 0 0 3px rgba(29,185,84,0.08);
}

@@ -591,15 +559,15 @@
}

textarea:focus, input:focus {
  border-color: var(--accent) !important;
  border-color: var(--green) !important;
 box-shadow: 0 0 0 3px rgba(29,185,84,0.16) !important;
}

[data-testid="stMetric"] {
 border-radius: 18px;
 border: 1px solid var(--border);
 background: var(--glass);
  box-shadow: var(--shadow-2);
  box-shadow: var(--shadow-soft);
 padding: 16px;
}

@@ -631,8 +599,8 @@
 gap: 14px;
 align-items: start;
 margin-top: 12px;
  border-color: var(--accent-border);
  background: var(--accent-soft);
  border-color: var(--green-border);
  background: var(--green-soft);
}

.success-icon {
@@ -642,7 +610,7 @@
 display: grid;
 place-items: center;
 color: #000;
  background: var(--accent);
  background: var(--green);
 font-weight: 950;
 animation: tickPop 260ms ease both;
}
@@ -677,7 +645,7 @@
 border-radius: 20px;
 border: 1px solid var(--border);
 background: var(--surface);
  box-shadow: var(--shadow-2);
  box-shadow: var(--shadow-soft);
}

.results-table {
@@ -706,15 +674,15 @@
}

.results-table tbody tr:hover {
  background: var(--surface-hover);
  background: var(--hover);
}

.results-table tbody tr.top-three {
  background: color-mix(in srgb, var(--accent-soft) 58%, transparent);
  background: color-mix(in srgb, var(--green-soft) 58%, transparent);
}

.results-table tbody tr.rank-one {
  box-shadow: inset 4px 0 0 #D4AF37;
  box-shadow: inset 4px 0 0 var(--gold);
}

.results-table td {
@@ -738,11 +706,11 @@
 border-radius: 999px;
 font-weight: 950;
 color: #000;
  background: var(--accent);
  background: var(--green);
}

.rank-chip.gold {
  background: linear-gradient(135deg, #FDE68A, #D4AF37);
  background: linear-gradient(135deg, #FDE68A, var(--gold));
}

.score-pill {
@@ -755,8 +723,8 @@
 font-weight: 950;
}

.score-high { background: rgba(29,185,84,0.18); color: var(--accent); }
.score-mid { background: var(--warning-soft); color: var(--warning); }
.score-high { background: rgba(29,185,84,0.18); color: var(--green-dark); }
.score-mid { background: var(--orange-soft); color: var(--orange); }
.score-low { background: rgba(107,114,128,0.14); color: var(--text-2); }

.match-track {
@@ -771,7 +739,7 @@
.match-fill {
 height: 100%;
 border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), #7DE39B);
  background: linear-gradient(90deg, var(--green), #7DE39B);
 animation: progressIn 580ms ease both;
}

@@ -781,7 +749,7 @@
 border-radius: 999px;
 padding: 5px 9px;
 margin: 0 5px 5px 0;
  background: var(--info-soft);
  background: var(--blue-soft);
 color: var(--text);
 font-size: 0.78rem;
 font-weight: 800;
@@ -798,20 +766,20 @@
 border-radius: 20px;
 border: 1px solid var(--border);
 background: var(--glass);
  box-shadow: var(--shadow-2);
  box-shadow: var(--shadow-soft);
 padding: 18px;
 min-height: 220px;
 animation: fadeSlide 300ms ease both;
}

.preview-card:hover {
 transform: translateY(-2px) scale(1.004);
  background: var(--surface-hover);
  background: var(--hover);
}

.preview-card.rank-one {
 border-color: rgba(212, 175, 55, 0.62);
  box-shadow: 0 18px 56px rgba(212,175,55,0.14), var(--shadow-2);
  box-shadow: 0 18px 56px rgba(212,175,55,0.14), var(--shadow-soft);
}

.preview-rank {
@@ -836,7 +804,7 @@
 line-height: 1;
 font-weight: 980;
 letter-spacing: -0.06em;
  color: var(--accent);
  color: var(--green-dark);
}

.empty-state {
@@ -853,18 +821,13 @@
 display: grid;
 place-items: center;
 margin: 0 auto 18px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--accent-border);
  background: var(--green-soft);
  color: var(--green-dark);
  border: 1px solid var(--green-border);
}

.footer-card {
 margin-top: 28px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--glass);
  box-shadow: var(--shadow-2);
  padding: 16px 18px;
 display: flex;
 flex-wrap: wrap;
 justify-content: space-between;
@@ -897,13 +860,14 @@
}

@media (max-width: 980px) {
  .step-grid, .preview-grid { grid-template-columns: 1fr; }
  .bento-grid, .step-grid, .preview-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 760px) {
 .topbar { align-items: flex-start; flex-direction: column; }
 .topbar-badges { justify-content: flex-start; }
  .hero-title { font-size: 2.35rem; }
  .hero-title { font-size: 2.15rem; }
  .bento-grid, .step-grid, .preview-grid { grid-template-columns: 1fr; }
 .footer-card { flex-direction: column; }
}
</style>
@@ -927,14 +891,14 @@
"validation_done": False,
"download_done": False,
"show_docs": False,
    "nav_choice": "Overview",
    "page": "Overview",
}
for key, value in DEFAULT_STATE.items():
if key not in st.session_state:
st.session_state[key] = value


def icon_svg(name: str, size: int = 20) -> str:
def icon_svg(name: str, size: int = 22) -> str:
icons = {
"target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
"upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
@@ -1089,6 +1053,16 @@
st.session_state.download_done = True


def checklist_state() -> list[tuple[int, str, bool]]:
    return [
        (1, "Candidate Sample", bool(st.session_state.candidate_ready)),
        (2, "Job Description", bool(st.session_state.job_ready)),
        (3, "Run Ranking", bool(st.session_state.ranking_done)),
        (4, "Validate Final Top-100 Locally", bool(st.session_state.validation_done)),
        (5, "Download CSV", bool(st.session_state.download_done)),
    ]


def checklist_item(index: int, label: str, done: bool) -> str:
dot = "✓" if done else ""
done_class = "done" if done else ""
@@ -1100,37 +1074,31 @@
)


def checklist_state() -> list[tuple[int, str, bool]]:
    return [
        (1, "Candidate sample", bool(st.session_state.candidate_ready)),
        (2, "Job description", bool(st.session_state.job_ready)),
        (3, "Run ranking", bool(st.session_state.ranking_done)),
        (4, "Validate final top-100 locally", bool(st.session_state.validation_done)),
        (5, "Download CSV", bool(st.session_state.download_done)),
    ]


def render_checklist() -> None:
def render_checklist_card() -> None:
items = checklist_state()
completed = sum(1 for _, _, done in items if done)
percent = int(completed / len(items) * 100)
st.markdown(
f"""
        <div class="check-progress-label"><span>{completed} / {len(items)} Completed</span><span>{percent}%</span></div>
        <div class="check-progress-track"><div class="check-progress-fill" style="width:{percent}%"></div></div>
        <div class="checklist-wrap">{''.join(checklist_item(*item) for item in items)}</div>
        <div class="checklist-card">
          <div class="card-title">Live checklist</div>
          <p class="card-copy">Complete each step to generate a submission-ready ranking.</p>
          <div class="check-progress-label"><span>{completed} / {len(items)} Completed</span><span>{percent}%</span></div>
          <div class="check-progress-track"><div class="check-progress-fill" style="width:{percent}%"></div></div>
          <div class="checklist-wrap">{''.join(checklist_item(*item) for item in items)}</div>
        </div>
       """,
unsafe_allow_html=True,
)


def status_html(label: str, value: str, icon_name: str) -> None:
def bento_card(label: str, value: str, icon_name: str) -> None:
st.markdown(
f"""
        <div class="status-card">
          <div class="status-icon">{icon_svg(icon_name, 28)}</div>
          <div class="status-label">{html.escape(label)}</div>
          <div class="status-value">{html.escape(value)}</div>
        <div class="bento-card">
          <div class="bento-icon">{icon_svg(icon_name, 28)}</div>
          <div class="bento-label">{html.escape(label)}</div>
          <div class="bento-value">{html.escape(value)}</div>
       </div>
       """,
unsafe_allow_html=True,
@@ -1140,7 +1108,7 @@
def render_topbar() -> None:
st.markdown(
f"""
        <div class="spotify-shell">
        <div class="top-shell">
         <div class="topbar">
           <div class="brand-lockup">
             <div class="brand-icon">{icon_svg("target", 20)}</div>
@@ -1166,12 +1134,10 @@
st.markdown(
"""
       <div class="hero-card">
          <div class="hero-content">
            <h1 class="hero-title">Rank candidates with <span class="gradient-text">offline AI logic</span>.</h1>
            <p class="hero-subtitle">
              Upload candidates and a job description, run the deterministic Redrob ranker, validate top-100 output, and export CSV.
            </p>
          </div>
          <h1 class="hero-title">Rank candidates with <span class="gradient-text">offline AI logic</span>.</h1>
          <p class="hero-subtitle">
            Upload candidates and a job description, run the deterministic Redrob ranker, validate top-100 output, and export CSV.
          </p>
       </div>
       """,
unsafe_allow_html=True,
@@ -1436,81 +1402,83 @@
render_results_table(rows)


with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
          <div class="sidebar-logo">{icon_svg("target", 22)}</div>
          <div><div class="sidebar-title">Redrob Ranker</div></div>
        </div>
        <p class="sidebar-copy">Small-sample sandbox for the official offline ranking system.</p>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
def render_resources_bottom() -> None:
    st.write("")
    with st.expander("Additional information and reproduction commands", expanded=bool(st.session_state.show_docs)):
        st.markdown("### Official reproduction command")
        st.code(
            "python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./team_yourid.csv --top-k 100\n"
            "python validate_submission.py ./team_yourid.csv",
            language="bash",
        )
        st.markdown("### Methodology summary")
        st.write(
            "The ranker combines retrieval/ranking evidence, embeddings/vector database skills, applied ML/NLP depth, "
            "production engineering, product-company experience, 5-9 year seniority fit, logistics, and Redrob behavioral signals. "
            "It down-weights keyword stuffing, inactive candidates, consulting-only histories, long notice periods, suspicious profiles, "
            "and unsupported AI claims."
        )

    page = st.radio(
        "Quick access",
        ["Overview", "Run Ranker", "Results"],
        label_visibility="collapsed",
        key="nav_choice",
    )

    st.divider()
    st.markdown("### Live checklist")
    render_checklist()
    st.divider()
    st.caption("CPU-only · no network · no hosted LLM calls")
def set_page(page_name: str) -> None:
    st.session_state.page = page_name


render_topbar()

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
page = st.radio(
    "Navigation",
    ["Overview", "Upload & Rank", "Results"],
    horizontal=True,
    label_visibility="collapsed",
    key="page",
)
st.markdown('</div>', unsafe_allow_html=True)

render_hero()

cta_cols = st.columns([1, 1, 4])
with cta_cols[0]:
if st.button("Run Demo", use_container_width=True):
        st.session_state.nav_choice = "Run Ranker"
        set_page("Upload & Rank")
st.rerun()
with cta_cols[1]:
if st.button("Documentation", use_container_width=True):
st.session_state.show_docs = not st.session_state.show_docs

status_cols = st.columns(4)
with status_cols[0]:
    status_html("Candidates", "Max 100", "target")
with status_cols[1]:
    status_html("Job Description", "TXT / MD / DOCX", "file")
with status_cols[2]:
    status_html("Ranking", "Offline Engine", "play")
with status_cols[3]:
    status_html("Output", "CSV Export", "download")
st.write("")
stat_cols = st.columns(4)
with stat_cols[0]:
    bento_card("Candidates", "Max 100", "target")
with stat_cols[1]:
    bento_card("Job Description", "TXT / MD / DOCX", "file")
with stat_cols[2]:
    bento_card("Ranking", "Offline Engine", "play")
with stat_cols[3]:
    bento_card("Output", "CSV Export", "download")

st.write("")
render_steps()

if page == "Overview":
    st.subheader("Getting started")
    st.subheader("Overview")
st.markdown(
"""
        <div class="quick-card" style="max-width:760px;">
          <h3 class="card-title">Follow the live checklist to complete the ranking workflow.</h3>
          <p class="card-copy">Upload/select a candidate sample, add the job description, run ranking, validate a top-100 run, and download the CSV.</p>
        <div class="info-card">
          <h3 class="card-title">A lightweight ranking workspace for Redrob submissions.</h3>
          <p class="card-copy">
            Use the Upload & Rank page to run the sandbox workflow. The official 100K run should still be executed locally with <code>rank.py</code>.
          </p>
       </div>
       """,
unsafe_allow_html=True,
)
    if st.session_state.show_docs:
        st.write("")
        st.subheader("Documentation")
        st.code(
            "python rank.py --candidates ./candidates.jsonl --job ./uploads/A1.txt --out ./team_yourid.csv --top-k 100\n"
            "python validate_submission.py ./team_yourid.csv",
            language="bash",
        )

elif page == "Run Ranker":
    left, right = st.columns(2)
elif page == "Upload & Rank":
    render_steps()
    upload_cols = st.columns([1.05, 1.05, 0.9])

    with left:
    with upload_cols[0]:
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<span class="step-pill">STEP 1 · Upload Candidates</span>', unsafe_allow_html=True)
use_repo_sample = sample_candidates_path.exists() and st.checkbox("Use bundled sample_candidates.json", value=True)
@@ -1525,15 +1493,18 @@
if use_repo_sample:
candidate_success_card("sample_candidates.json", sample_candidates_path.stat().st_size, count_candidates(sample_candidates_path))
elif candidate_upload is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(candidate_upload.name).suffix or ".jsonl") as handle:
                handle.write(candidate_upload.getvalue())
                temp_candidate_path = Path(handle.name)
            candidate_success_card(candidate_upload.name, candidate_upload.size, count_candidates(temp_candidate_path))
            temp_candidate_path.unlink(missing_ok=True)
            candidate_count = None
            if candidate_upload.size <= 25 * 1024 * 1024:
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(candidate_upload.name).suffix or ".jsonl") as handle:
                    handle.write(candidate_upload.getvalue())
                    temp_candidate_path = Path(handle.name)
                candidate_count = count_candidates(temp_candidate_path)
                temp_candidate_path.unlink(missing_ok=True)
            candidate_success_card(candidate_upload.name, candidate_upload.size, candidate_count)
st.caption("Sandbox samples can be ≤100 candidates. Use the CLI for the official 100K run.")
st.markdown("</div>", unsafe_allow_html=True)

    with right:
    with upload_cols[1]:
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<span class="step-pill">STEP 2 · Upload Job Description</span>', unsafe_allow_html=True)
use_repo_job = sample_job_path.exists() and st.checkbox("Use bundled A1.txt job description", value=True)
@@ -1556,6 +1527,9 @@
st.caption("DOCX, TXT, MD, or pasted text are supported.")
st.markdown("</div>", unsafe_allow_html=True)

    with upload_cols[2]:
        render_checklist_card()

st.write("")
top_k = st.slider(
"Top K rows to generate",
@@ -1593,16 +1567,18 @@
elif page == "Results":
render_results()

render_resources_bottom()

st.markdown(
    """
    f"""
   <div class="footer-card">
     <div>
       <strong>Built for the Redrob AI Challenge</strong><br>
       Offline Candidate Ranking Engine · Version 1.0
     </div>
     <div class="footer-links">
        <a href="https://github.com/" target="_blank">GitHub</a>
        <a href="#" target="_self">Documentation</a>
        <a href="https://github.com/" target="_blank">{icon_svg("github", 16)} GitHub</a>
        <a href="#" target="_self">{icon_svg("book", 16)} Documentation</a>
     </div>
   </div>
   """,
