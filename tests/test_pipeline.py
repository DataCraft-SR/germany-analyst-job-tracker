"""End-to-end: fake API -> fetch -> dbt build -> site export, all in a temp dir."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from fake_api import FakeClient
from tracker import build_site, fetch

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("dbt") is None, reason="dbt not installed")
def test_end_to_end(tmp_path):
    raw, feats = tmp_path / "raw", tmp_path / "features"
    for i, day in enumerate(["2026-11-17", "2026-11-18", "2026-11-19"]):
        summary = fetch.run(client=FakeClient(i), today=day, raw_dir=raw, features_dir=feats, max_details=10_000)
        assert summary["postings"] > 0

    # every posting gets described once, never twice
    described = fetch.known_feature_refnrs(feats)
    all_refs = {r["refnr"] for p in raw.glob("*.jsonl.gz") for r in fetch.read_jsonl_gz(p)}
    assert described == all_refs

    wh = tmp_path / "wh.duckdb"
    env = {**os.environ, "TRACKER_WAREHOUSE": str(wh)}
    vars_ = f'{{"raw_glob": "{raw}/*.jsonl.gz", "features_glob": "{feats}/*.jsonl.gz"}}'
    res = subprocess.run(
        ["dbt", "build", "--project-dir", "dbt", "--profiles-dir", "dbt", "--vars", vars_,
         "--target-path", str(tmp_path / "target"), "--log-path", str(tmp_path / "logs")],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stdout[-4000:]

    data = build_site.export(wh)
    k = data["kpis"]
    assert k["as_of"] == "2026-11-19" and k["n_days"] == 3
    assert k["live_postings"] > 0
    assert 0 <= k["share_english_ads"] <= 1
    assert {r["role_family"] for r in data["roles"]} >= {"All analyst roles", "Data Analyst"}
    assert all("Hotel" not in e["employer"] for e in data["employers"])
    assert any(s["skill"] == "SQL" for s in data["skills"])
    md = build_site.findings_markdown(data)
    assert "live analyst postings" in md
