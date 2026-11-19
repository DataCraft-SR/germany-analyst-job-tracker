"""Daily extract: snapshot all active analyst postings + features for new ones.

Run:  python -m tracker.fetch
Writes:
  data/raw/YYYY-MM-DD.jsonl.gz        every on-target posting active today
  data/features/YYYY-MM-DD.jsonl.gz   description features for postings seen for the first time
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import logging
from pathlib import Path

from . import config
from .api import JobsucheClient
from .extract import describe, flatten_posting

log = logging.getLogger("tracker.fetch")


def write_jsonl_gz(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def known_feature_refnrs(features_dir: Path) -> set[str]:
    seen: set[str] = set()
    for p in sorted(features_dir.glob("*.jsonl.gz")):
        seen.update(r["refnr"] for r in read_jsonl_gz(p))
    return seen


def snapshot(client: JobsucheClient, terms: list[str], today: str) -> list[dict]:
    """Search every term, de-duplicate by refnr, keep on-target roles only."""
    by_ref: dict[str, dict] = {}
    raw_count = 0
    for term in terms:
        n = 0
        for rec in client.search(term):
            raw_count += 1
            n += 1
            row = flatten_posting(rec, today)
            if not row["refnr"] or row["role_family"] is None:
                continue
            existing = by_ref.get(row["refnr"])
            if existing:
                existing["search_terms"] = sorted(set(existing["search_terms"]) | {term})
            else:
                row["search_terms"] = [term]
                by_ref[row["refnr"]] = row
        log.info("%-22s %5d results", term, n)
    log.info("Raw results: %d -> on-target unique postings: %d", raw_count, len(by_ref))
    return list(by_ref.values())


def run(client: JobsucheClient | None = None, today: str | None = None,
        raw_dir: Path = config.RAW_DIR, features_dir: Path = config.FEATURES_DIR,
        max_details: int = config.MAX_DETAILS_PER_RUN) -> dict:
    client = client or JobsucheClient()
    today = today or dt.date.today().isoformat()

    rows = snapshot(client, config.SEARCH_TERMS, today)
    if not rows:
        raise SystemExit("No postings returned - API may have changed. Not writing an empty snapshot.")
    write_jsonl_gz(raw_dir / f"{today}.jsonl.gz", rows)

    # Fetch descriptions only for postings we have never described before.
    seen = known_feature_refnrs(features_dir)
    todo = [r["refnr"] for r in rows if r["refnr"] not in seen][:max_details]
    feats = []
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for i, ref in enumerate(todo, 1):
        feats.append(describe(ref, client.description(ref), fetched_at))
        if i % 100 == 0:
            log.info("Descriptions: %d/%d", i, len(todo))
    if feats:
        out = features_dir / f"{today}.jsonl.gz"
        if out.exists():  # re-run on the same day: append
            feats = read_jsonl_gz(out) + feats
        write_jsonl_gz(out, feats)

    backlog = sum(1 for r in rows if r["refnr"] not in seen) - len(todo)
    summary = {"date": today, "postings": len(rows), "new_descriptions": len(todo), "backlog": max(backlog, 0)}
    log.info("Done: %s", summary)
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-details", type=int, default=config.MAX_DETAILS_PER_RUN)
    args = ap.parse_args()
    run(max_details=args.max_details)


if __name__ == "__main__":
    main()
