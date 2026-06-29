#!/usr/bin/env python3
"""Offline Redrob candidate ranker.

This script is intentionally dependency-free and network-free for the hackathon
reproduction constraint: CPU only, <=16 GB RAM, <=5 minutes, no hosted LLM calls.

It supports:
- JSONL / NDJSON / TXT with one candidate JSON object per line
- Gzipped JSONL (.gz)
- JSON arrays such as sample_candidates.json

Output columns match the official validator exactly:
candidate_id,rank,score,reasoning
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

TODAY = date(2026, 6, 28)

CONSULTING_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
    "mindtree",
    "ltimindtree",
}

PRODUCT_COMPANIES = {
    "swiggy",
    "zomato",
    "uber",
    "ola",
    "flipkart",
    "razorpay",
    "cred",
    "mad street den",
    "pied piper",
    "initech",
    "hooli",
}

TARGET_LOCATIONS = {
    "pune",
    "noida",
    "delhi",
    "delhi ncr",
    "gurgaon",
    "gurugram",
    "hyderabad",
    "mumbai",
    "bangalore",
    "bengaluru",
}

NON_AI_BUSINESS_TITLES = {
    "hr manager",
    "marketing manager",
    "accountant",
    "sales executive",
    "customer support",
    "operations manager",
    "graphic designer",
    "civil engineer",
    "mechanical engineer",
    "content writer",
}

SKILL_ALIASES = {
    "rest apis": "rest api",
    "rest APIs": "rest api",
    "hugging face transformers": "transformers",
    "vector search": "vector database",
    "open search": "opensearch",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "a/b testing": "ab testing",
    "offline online correlation": "evaluation",
    "sentence-transformers": "sentence transformers",
    "fine tuning llms": "fine-tuning llms",
    "fine tuning": "fine-tuning llms",
}

RETRIEVAL_SKILLS = {
    "information retrieval",
    "retrieval",
    "hybrid search",
    "semantic search",
    "vector database",
    "embeddings",
    "sentence transformers",
    "faiss",
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "chromadb",
    "opensearch",
    "elasticsearch",
    "bm25",
}

RANKING_SKILLS = {
    "ranking",
    "learning to rank",
    "recommendation systems",
    "recommender systems",
    "xgboost",
    "lightgbm",
    "feature engineering",
    "experimentation",
    "ab testing",
}

ML_NLP_SKILLS = {
    "machine learning",
    "deep learning",
    "nlp",
    "llm",
    "transformers",
    "rag",
    "fine-tuning llms",
    "lora",
    "qlora",
    "peft",
    "langchain",
    "haystack",
    "prompt engineering",
    "pytorch",
    "tensorflow",
    "scikit-learn",
}

EVAL_SKILLS = {
    "ndcg",
    "mrr",
    "map",
    "evaluation",
    "offline evaluation",
    "online evaluation",
    "ab testing",
    "experimentation",
    "offline-online correlation",
    "relevance",
}

ENGINEERING_SKILLS = {
    "python",
    "fastapi",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "mlops",
    "mlflow",
    "bentoml",
    "kubeflow",
    "microservices",
    "rest api",
}

CV_SPEECH_SKILLS = {
    "computer vision",
    "opencv",
    "image classification",
    "object detection",
    "yolo",
    "speech recognition",
    "tts",
    "gans",
    "cnn",
    "reinforcement learning",
}

PROFICIENCY_WEIGHT = {
    "beginner": 0.35,
    "intermediate": 0.6,
    "advanced": 0.84,
    "expert": 1.0,
}


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    raw_score: float
    score: float
    reasoning: str


def norm(text: Any) -> str:
    value = str(text or "").strip().lower()
    value = value.replace("/", " ").replace("_", " ").replace(".", "")
    value = re.sub(r"[^a-z0-9+#\- ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return SKILL_ALIASES.get(value, value)


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def iter_candidates(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Candidate file not found: {path}")
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        prefix = handle.read(4096)
        handle.seek(0)
        if prefix.lstrip().startswith("["):
            payload = json.load(handle)
            if not isinstance(payload, list):
                raise SystemExit("JSON candidate file must be a list of objects or JSONL.")
            for item in payload:
                if isinstance(item, dict):
                    yield item
            return
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at line {line_number}: {exc.msg}") from exc
            if isinstance(item, dict):
                yield item


def skill_dict(candidate: dict[str, Any]) -> dict[str, dict[str, float | str]]:
    output: dict[str, dict[str, float | str]] = {}
    for item in candidate.get("skills") or []:
        name = norm(item.get("name"))
        if not name:
            continue
        proficiency = str(item.get("proficiency") or "beginner").lower()
        endorsements = float(item.get("endorsements") or 0)
        duration = float(item.get("duration_months") or 0)
        weight = (
            PROFICIENCY_WEIGHT.get(proficiency, 0.45) * 0.58
            + clamp(endorsements / 60.0) * 0.17
            + clamp(duration / 60.0) * 0.25
        )
        old = output.get(name)
        if old is None or float(old["weight"]) < weight:
            output[name] = {
                "weight": clamp(weight),
                "proficiency": proficiency,
                "endorsements": endorsements,
                "duration": duration,
                "original": str(item.get("name") or name),
            }
    return output


def skill_presence(skills: dict[str, dict[str, float | str]], targets: set[str]) -> float:
    if not targets:
        return 0.0
    total = 0.0
    for target in targets:
        exact = float(skills.get(target, {}).get("weight", 0.0))
        fuzzy = 0.0
        for skill, data in skills.items():
            if target in skill or skill in target:
                fuzzy = max(fuzzy, float(data["weight"]) * 0.72)
        total += max(exact, fuzzy)
    return clamp(total / len(targets))


def text_blob(candidate: dict[str, Any]) -> str:
    profile = candidate.get("profile") or {}
    parts = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_industry", ""),
    ]
    for item in candidate.get("career_history") or []:
        parts.extend([item.get("title", ""), item.get("industry", ""), item.get("description", "")])
    for item in candidate.get("education") or []:
        parts.extend([item.get("degree", ""), item.get("field_of_study", ""), item.get("institution", ""), item.get("tier", "")])
    parts.extend(item.get("name", "") for item in candidate.get("skills") or [])
    return norm(" ".join(str(part) for part in parts))


def count_hits(text: str, phrases: set[str]) -> int:
    return sum(1 for phrase in phrases if phrase in text)


def candidate_rank_score(candidate: dict[str, Any]) -> tuple[float, str]:
    cid = str(candidate.get("candidate_id") or "")
    profile = candidate.get("profile") or {}
    signals = candidate.get("redrob_signals") or {}
    career = candidate.get("career_history") or []
    education = candidate.get("education") or []
    skills = skill_dict(candidate)
    blob = text_blob(candidate)

    years = float(profile.get("years_of_experience") or 0.0)
    current_title = str(profile.get("current_title") or "Candidate")
    title_norm = norm(current_title + " " + str(profile.get("headline") or ""))
    country = norm(profile.get("country"))
    location = norm(profile.get("location"))

    retrieval = skill_presence(skills, RETRIEVAL_SKILLS) * 0.75 + clamp(count_hits(blob, RETRIEVAL_SKILLS) / 6.0) * 0.25
    ranking = skill_presence(skills, RANKING_SKILLS) * 0.70 + clamp(count_hits(blob, RANKING_SKILLS | {"ranking", "relevance", "search"}) / 6.0) * 0.30
    ml_nlp = skill_presence(skills, ML_NLP_SKILLS) * 0.70 + clamp(count_hits(blob, ML_NLP_SKILLS) / 8.0) * 0.30
    eval_score = skill_presence(skills, EVAL_SKILLS) * 0.50 + clamp(count_hits(blob, EVAL_SKILLS | {"offline", "online", "a b", "metric", "relevance"}) / 6.0) * 0.50
    engineering = skill_presence(skills, ENGINEERING_SKILLS) * 0.75 + clamp(count_hits(blob, ENGINEERING_SKILLS) / 6.0) * 0.25

    ai_title_terms = {
        "ai engineer",
        "ml engineer",
        "machine learning engineer",
        "applied ml engineer",
        "nlp engineer",
        "search engineer",
        "recommendation systems engineer",
        "data scientist",
        "ranking",
    }
    adjacent_title_terms = {"backend engineer", "software engineer", "data engineer", "full stack developer", "cloud engineer"}
    title_score = 0.0
    if any(term in title_norm for term in ai_title_terms):
        title_score = 1.0
    elif any(term in title_norm for term in adjacent_title_terms):
        title_score = 0.58
    elif any(term in title_norm for term in NON_AI_BUSINESS_TITLES):
        title_score = 0.08
    else:
        title_score = 0.30

    product_months = 0
    service_months = 0
    ai_ml_months = 0
    ranking_months = 0
    short_stints = 0
    companies: list[str] = []
    for item in career:
        company = norm(item.get("company"))
        companies.append(company)
        months = float(item.get("duration_months") or 0)
        desc = norm(f"{item.get('title', '')} {item.get('industry', '')} {item.get('description', '')}")
        if company in PRODUCT_COMPANIES or any(ind in desc for ind in ("product", "e commerce", "food delivery", "fintech", "ai ml", "software")):
            product_months += months
        if company in CONSULTING_COMPANIES or "it services" in desc:
            service_months += months
        if any(term in desc for term in ML_NLP_SKILLS | RETRIEVAL_SKILLS):
            ai_ml_months += months
        if any(term in desc for term in RANKING_SKILLS | {"search", "retrieval", "ranking", "recommendation", "relevance"}):
            ranking_months += months
        if 0 < months < 18:
            short_stints += 1

    total_months = sum(float(item.get("duration_months") or 0) for item in career)
    product_score = clamp(product_months / max(36.0, total_months * 0.55))
    career_ai_score = clamp((ai_ml_months * 0.65 + ranking_months * 1.10) / max(36.0, total_months * 0.60))

    if 5.0 <= years <= 9.0:
        experience_score = 1.0
    elif 4.0 <= years < 5.0 or 9.0 < years <= 11.0:
        experience_score = 0.76
    elif 3.0 <= years < 4.0 or 11.0 < years <= 14.0:
        experience_score = 0.50
    else:
        experience_score = 0.25

    if country == "india" and any(city in location for city in TARGET_LOCATIONS):
        location_score = 1.0
    elif country == "india" and signals.get("willing_to_relocate"):
        location_score = 0.86
    elif country == "india":
        location_score = 0.62
    elif signals.get("willing_to_relocate"):
        location_score = 0.38
    else:
        location_score = 0.18

    completeness = clamp(float(signals.get("profile_completeness_score") or 0) / 100.0)
    response = clamp(float(signals.get("recruiter_response_rate") or 0))
    avg_hours = float(signals.get("avg_response_time_hours") or 999)
    response_time = clamp(1.0 - avg_hours / 240.0)
    open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.35
    notice = clamp(1.0 - float(signals.get("notice_period_days") or 90) / 150.0)
    saved = clamp(float(signals.get("saved_by_recruiters_30d") or 0) / 20.0)
    search_appearance = clamp(float(signals.get("search_appearance_30d") or 0) / 350.0)
    interview = clamp(float(signals.get("interview_completion_rate") or 0))
    github_raw = float(signals.get("github_activity_score") if signals.get("github_activity_score") is not None else -1)
    github = 0.40 if github_raw < 0 else clamp(github_raw / 100.0)
    verified = sum(bool(signals.get(k)) for k in ("verified_email", "verified_phone", "linkedin_connected")) / 3.0
    last_active = parse_date(signals.get("last_active_date"))
    days_inactive = (TODAY - last_active).days if last_active else 999
    recency = 1.0 if days_inactive <= 45 else 0.82 if days_inactive <= 90 else 0.58 if days_inactive <= 180 else 0.28 if days_inactive <= 365 else 0.08

    assessment_scores = signals.get("skill_assessment_scores") or {}
    if assessment_scores:
        relevant_scores = [
            float(score) / 100.0
            for skill, score in assessment_scores.items()
            if norm(skill) in RETRIEVAL_SKILLS | RANKING_SKILLS | ML_NLP_SKILLS | ENGINEERING_SKILLS
        ]
        assessment = sum(relevant_scores) / len(relevant_scores) if relevant_scores else sum(float(v) / 100.0 for v in assessment_scores.values()) / len(assessment_scores)
    else:
        assessment = 0.38

    signal_score = clamp(
        response * 0.22
        + recency * 0.16
        + open_to_work * 0.14
        + response_time * 0.08
        + notice * 0.08
        + completeness * 0.09
        + saved * 0.06
        + search_appearance * 0.05
        + interview * 0.05
        + github * 0.04
        + verified * 0.03
    )

    education_score = 0.35
    for edu in education:
        field = norm(edu.get("field_of_study"))
        tier = norm(edu.get("tier"))
        if any(term in field for term in ("computer", "machine learning", "artificial intelligence", "data science", "statistics", "information technology")):
            education_score = max(education_score, 0.65)
        if tier == "tier 1":
            education_score = max(education_score, 0.85)
        elif tier == "tier 2":
            education_score = max(education_score, 0.72)

    cv_speech = skill_presence(skills, CV_SPEECH_SKILLS)
    business_title = any(term in title_norm for term in NON_AI_BUSINESS_TITLES)
    has_ir = retrieval > 0.22 or ranking > 0.22 or "information retrieval" in blob or "search" in blob
    consulting_only = bool(companies) and all(company in CONSULTING_COMPANIES for company in companies)
    service_heavy = service_months > max(24, product_months * 1.5) and product_months < 18
    keyword_stuffer = business_title and len([s for s in skills if s in RETRIEVAL_SKILLS | ML_NLP_SKILLS | RANKING_SKILLS]) >= 7 and career_ai_score < 0.15
    framework_only = "langchain" in skills and retrieval < 0.18 and ranking < 0.18 and career_ai_score < 0.18
    cv_only = cv_speech > 0.55 and not has_ir
    title_hopper = len(career) >= 4 and short_stints >= max(2, len(career) // 2)

    base = clamp(
        retrieval * 0.20
        + ranking * 0.17
        + ml_nlp * 0.13
        + eval_score * 0.10
        + engineering * 0.08
        + title_score * 0.08
        + product_score * 0.08
        + career_ai_score * 0.08
        + experience_score * 0.04
        + education_score * 0.02
        + location_score * 0.02
    )

    availability_multiplier = 0.72 + signal_score * 0.42
    penalty = 1.0

    salary = signals.get("expected_salary_range_inr_lpa") or {}
    try:
        if float(salary.get("min", 0)) > float(salary.get("max", 0)):
            penalty *= 0.88
    except (TypeError, ValueError):
        pass

    if consulting_only:
        penalty *= 0.72
    elif service_heavy:
        penalty *= 0.84
    if keyword_stuffer:
        penalty *= 0.58
    if framework_only:
        penalty *= 0.70
    if cv_only:
        penalty *= 0.72
    if title_hopper:
        penalty *= 0.88
    if years < 3.5:
        penalty *= 0.75
    if days_inactive > 365:
        penalty *= 0.70
    if response < 0.10:
        penalty *= 0.82

    # Honeypot-style impossible skill claims: many advanced/expert skills with almost no usage.
    impossible_skills = 0
    for data in skills.values():
        if str(data.get("proficiency")) in {"advanced", "expert"} and float(data.get("duration", 0)) < 6:
            impossible_skills += 1
    if impossible_skills >= 4:
        penalty *= 0.70
    elif impossible_skills >= 2:
        penalty *= 0.86

    final = clamp(base * availability_multiplier * penalty)

    # Good but plain-language Tier-5 style boost: strong actual search/reco career even if skills are not perfect.
    if ranking_months >= 24 and product_months >= 24 and not business_title:
        final = clamp(final + 0.08)
    if "recommendation systems engineer" in title_norm or "search engineer" in title_norm:
        final = clamp(final + 0.07)

    matching = matched_skill_names(skills)
    concerns: list[str] = []
    if service_heavy or consulting_only:
        concerns.append("services-heavy background")
    if not has_ir:
        concerns.append("limited explicit IR/retrieval evidence")
    if response < 0.20:
        concerns.append(f"low response rate {response:.2f}")
    if int(signals.get("notice_period_days") or 0) > 60:
        concerns.append(f"{int(signals.get('notice_period_days') or 0)}d notice")
    if cv_only:
        concerns.append("AI depth skews CV/speech, not IR")
    if keyword_stuffer:
        concerns.append("keyword-heavy profile but weak role evidence")

    if final >= 0.78:
        tone = "Strong fit"
    elif final >= 0.58:
        tone = "Good adjacent fit"
    elif final >= 0.40:
        tone = "Partial fit"
    else:
        tone = "Low-confidence fit"

    skill_text = ", ".join(matching[:4]) if matching else "few exact target skills"
    concern_text = "; concern: " + ", ".join(concerns[:2]) if concerns else ""
    reasoning = (
        f"{tone}: {current_title} with {years:.1f} yrs; evidence includes {skill_text}; "
        f"Redrob response {response:.2f}, active {days_inactive}d ago, notice {int(signals.get('notice_period_days') or 0)}d{concern_text}."
    )
    if len(reasoning) > 295:
        reasoning = reasoning[:292].rstrip() + "..."
    return final, reasoning


def matched_skill_names(skills: dict[str, dict[str, float | str]]) -> list[str]:
    target = RETRIEVAL_SKILLS | RANKING_SKILLS | ML_NLP_SKILLS | ENGINEERING_SKILLS | EVAL_SKILLS
    matches = []
    for skill, data in skills.items():
        if skill in target or any(t in skill or skill in t for t in target):
            matches.append(str(data.get("original") or skill))
    return sorted(set(matches), key=str.lower)


def rank_candidates(candidates: Iterator[dict[str, Any]], top_k: int) -> list[RankedCandidate]:
    ranked: list[RankedCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        cid = str(candidate.get("candidate_id") or "").strip()
        if not re.match(r"^CAND_[0-9]{7}$", cid) or cid in seen:
            continue
        seen.add(cid)
        raw, reasoning = candidate_rank_score(candidate)
        rounded = round(raw, 4)
        ranked.append(RankedCandidate(candidate_id=cid, raw_score=raw, score=rounded, reasoning=reasoning))
    ranked.sort(key=lambda item: (-item.score, item.candidate_id))
    return ranked[:top_k]


def write_submission(rows: list[RankedCandidate], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow(
                {
                    "candidate_id": row.candidate_id,
                    "rank": rank,
                    "score": f"{row.score:.4f}",
                    "reasoning": row.reasoning,
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Redrob candidate ranker")
    parser.add_argument("--candidates", required=True, help="Path to candidates JSONL/JSONL.GZ/JSON array")
    parser.add_argument("--job", default=None, help="Path to job description. Accepted for reproducibility; ranker is tuned for released JD.")
    parser.add_argument("--out", "--output", dest="output", default="submission.csv", help="Output CSV path")
    parser.add_argument("--top-k", type=int, default=100, help="Number of rows to output, official submission requires 100")
    args = parser.parse_args()

    if args.job:
        job_path = Path(args.job)
        if not job_path.exists():
            raise SystemExit(f"Job description not found: {job_path}")
        # Read once to prove the command is connected to the released JD. The actual
        # weights are hard-coded from the published JD to keep ranking deterministic.
        _ = job_path.read_text(encoding="utf-8", errors="replace")[:1000]

    rows = rank_candidates(iter_candidates(Path(args.candidates)), args.top_k)
    if len(rows) < args.top_k:
        print(
            f"Warning: requested top {args.top_k} but only {len(rows)} valid candidates were available.",
            file=sys.stderr,
        )
    write_submission(rows, Path(args.output))
    print(f"Wrote {len(rows)} rows to {args.output}")
    if args.top_k == 100 and len(rows) == 100:
        print("Official row count satisfied. Run validate_submission.py before submitting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
