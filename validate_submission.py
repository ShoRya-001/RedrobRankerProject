#!/usr/bin/env python3
"""Validate submission CSV per Redrob challenge rules."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")
DATA_ROW_START = 2
EXPECTED_DATA_ROWS = 100


def validate_submission(csv_path: str) -> list[str]:
    errors: list[str] = []
    path = Path(csv_path)

    if path.suffix.lower() != ".csv":
        errors.append("Filename must use a .csv extension.")
    elif not path.stem:
        errors.append("Filename must be your registered participant ID, e.g. team_xxx.csv.")

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                errors.append("Row 1 must be the header row; file is empty.")
                return errors
            if header != REQUIRED_HEADER:
                errors.append(
                    "Row 1 (header) must be exactly:\n"
                    f"  {','.join(REQUIRED_HEADER)}\n"
                    "Found:\n"
                    f"  {','.join(header)}"
                )
            data_rows = [row for row in reader if any(cell.strip() for cell in row)]
    except UnicodeDecodeError:
        errors.append("File must be UTF-8 encoded.")
        return errors
    except OSError as exc:
        errors.append(f"Cannot read file: {exc}")
        return errors

    if len(data_rows) != EXPECTED_DATA_ROWS:
        errors.append(
            f"After the header, there must be exactly {EXPECTED_DATA_ROWS} data rows; found {len(data_rows)}."
        )

    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    by_rank: list[tuple[int, float, str]] = []

    for index, cells in enumerate(data_rows):
        row_num = DATA_ROW_START + index
        if len(cells) != len(REQUIRED_HEADER):
            errors.append(
                f"Row {row_num}: expected {len(REQUIRED_HEADER)} columns ({','.join(REQUIRED_HEADER)}), got {len(cells)}."
            )
            continue
        row = dict(zip(REQUIRED_HEADER, cells, strict=True))
        cid = row["candidate_id"].strip()
        rank_s = row["rank"].strip()
        score_s = row["score"].strip()

        if not cid:
            errors.append(f"Row {row_num}: candidate_id is required.")
        elif not CANDIDATE_ID_PATTERN.match(cid):
            errors.append(f"Row {row_num}: candidate_id must be CAND_XXXXXXX (7 digits).")
        elif cid in seen_ids:
            errors.append(f"Row {row_num}: duplicate candidate_id '{cid}'.")
        else:
            seen_ids.add(cid)

        try:
            rank = int(rank_s)
            if str(rank) != rank_s:
                raise ValueError
            if not 1 <= rank <= 100:
                errors.append(f"Row {row_num}: rank must be between 1 and 100.")
            elif rank in seen_ranks:
                errors.append(f"Row {row_num}: duplicate rank {rank}.")
            else:
                seen_ranks.add(rank)
        except ValueError:
            errors.append(f"Row {row_num}: rank must be an integer (1-100).")
            rank = None

        try:
            score = float(score_s)
        except ValueError:
            errors.append(f"Row {row_num}: score must be a float.")
            score = None

        if rank is not None and score is not None and cid:
            by_rank.append((rank, score, cid))

    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(f"Each rank 1-100 must appear exactly once; missing: {sorted(missing)}")

    by_rank.sort(key=lambda row: row[0])
    for left, right in zip(by_rank, by_rank[1:], strict=False):
        r1, s1, _ = left
        r2, s2, _ = right
        if s1 < s2:
            errors.append(f"score must be non-increasing by rank: rank {r1} ({s1}) < rank {r2} ({s2}).")
    for left, right in zip(by_rank, by_rank[1:], strict=False):
        r1, s1, c1 = left
        r2, s2, c2 = right
        if s1 == s2 and c1 > c2:
            errors.append(
                f"Equal scores at ranks {r1} and {r2}: tie-break requires candidate_id ascending ({c1!r} > {c2!r})."
            )
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_submission.py <participant_id>.csv")
        return 1
    errors = validate_submission(sys.argv[1])
    if errors:
        print(f"Validation failed ({len(errors)} issue(s)):\n")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Submission is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
