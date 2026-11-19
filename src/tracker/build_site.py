"""Export dbt marts to docs/data.json (for the dashboard) and refresh README findings.

Run after `dbt build`:  python -m tracker.build_site
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path

import duckdb

from . import config

QUERIES = {
    "kpis": "select * from mart_kpis",
    "roles": "select * from mart_role_summary order by live_postings desc",
    "trend": "select * from mart_daily_trend order by snapshot_date, role_family",
    "skills": "select * from mart_skills order by role_family, n_mentions desc",
    "german": "select * from mart_german order by role_family",
    "salary": "select * from mart_salary order by role_family, median desc",
    "cities": "select location, live_postings, share_remote_possible from mart_locations where level = 'city' order by live_postings desc limit 15",
    "states": "select location, live_postings, share_remote_possible from mart_locations where level = 'state' order by live_postings desc",
    "employers": "select * from mart_employers order by live_postings desc limit 25",
}


def _clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def export(warehouse: Path) -> dict:
    con = duckdb.connect(str(warehouse), read_only=True)
    out = {}
    for key, sql in QUERIES.items():
        cur = con.execute(sql)
        cols = [c[0] for c in cur.description]
        out[key] = [{c: _clean(v) for c, v in zip(cols, row)} for row in cur.fetchall()]
    con.close()
    out["kpis"] = out["kpis"][0] if out["kpis"] else {}
    out["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return out


def pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.0f}%"


def euro(x) -> str:
    return "n/a" if x is None else f"€{x / 1000:.0f}k"


def findings_markdown(data: dict) -> str:
    k = data["kpis"]
    roles = [r for r in data["roles"] if r["role_family"] != "All analyst roles"]
    top_role = roles[0]["role_family"] if roles else "n/a"
    all_skills = [s for s in data["skills"] if s["role_family"] == "All analyst roles"]
    top_skills = ", ".join(f"{s['skill']} ({pct(s['share_of_postings'])})" for s in all_skills[:5]) or "n/a"
    english = sorted((r for r in roles if r.get("share_english_ads") is not None and (r.get("n_described") or 0) >= 20),
                     key=lambda r: r["share_english_ads"], reverse=True)
    most_english = f"{english[0]['role_family']} ({pct(english[0]['share_english_ads'])} of ads in English)" if english else "n/a"
    lines = [
        f"*Auto-updated {k.get('as_of', 'n/a')} · {k.get('n_days', 0)} days tracked since {k.get('tracking_since', 'n/a')}*",
        "",
        f"- **{k.get('live_postings', 0):,} live analyst postings** in Germany today; **{k.get('new_last_7_days', 0):,} new** in the last 7 days. Largest family: **{top_role}**; most postings in **{k.get('top_city', 'n/a')}**.",
        f"- **{pct(k.get('share_no_fluent_german'))}** of postings don't ask for fluent German, and **{pct(k.get('share_english_ads'))}** are written in English. Most English-friendly: {most_english}.",
        f"- Most requested tools: {top_skills}.",
        f"- **{pct(k.get('share_remote_possible'))}** offer home office. Median advertised salary **{euro(k.get('median_salary'))}** (only {k.get('n_with_salary', 0):,} ads publish pay).",
    ]
    return "\n".join(lines)


def update_readme(readme: Path, md: str) -> None:
    text = readme.read_text(encoding="utf-8")
    new = re.sub(r"(<!-- FINDINGS:START -->).*?(<!-- FINDINGS:END -->)",
                 lambda m: f"{m.group(1)}\n{md}\n{m.group(2)}", text, flags=re.S)
    readme.write_text(new, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--warehouse", type=Path, default=config.WAREHOUSE)
    ap.add_argument("--out", type=Path, default=config.DOCS_DIR / "data.json")
    ap.add_argument("--readme", type=Path, default=config.ROOT / "README.md")
    args = ap.parse_args()

    data = export(args.warehouse)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if args.readme.exists():
        update_readme(args.readme, findings_markdown(data))
    print(f"Wrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
