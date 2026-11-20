# Germany Analyst Job Market Tracker

**Which analyst jobs are actually open in Germany right now, which tools do they ask for, and how much German do you really need?**

An automated pipeline collects every live data, BI, marketing, CRM, pricing and finance analyst posting from Germany's federal job board each morning. It models the postings with dbt and publishes a live dashboard.

**[Live dashboard →](https://datacraft-sr.github.io/germany-analyst-job-tracker/)**

## Latest findings

<!-- FINDINGS:START -->
*Auto-updated 2026-11-20 · 1 days tracked since 2026-11-20*

- **1,072 live analyst postings** in Germany today; **0 new** in the last 7 days. Largest family: **Data Analyst**; most postings in **Hamburg**.
- **62%** of postings don't ask for fluent German, and **6%** are written in English. Most English-friendly: Data Engineering (10% of ads in English).
- Most requested tools: SQL (32%), Power BI (26%), Excel (23%), SAP (22%), Python (17%).
- **24%** offer home office. Median advertised salary **€63k** (only 142 ads publish pay).
<!-- FINDINGS:END -->

## Why I built this

I'm an analyst job seeker in Germany who isn't yet fluent in German, and the questions I kept asking were data questions. Which roles have the most openings? Which tools come up again and again? Which postings are realistic without C1 German? Job boards can't answer these, so I built something that does, and it gets more useful every day it runs.

## How it works

```
Bundesagentur für Arbeit API ──► Python extract ──► data/ (gzipped JSONL, versioned in git)
                                                         │
                                                         ▼
                              dbt + DuckDB:  staging ─► intermediate ─► 8 marts (+ 22 data tests)
                                                         │
                                                         ▼
                                   docs/data.json ──► GitHub Pages dashboard + README findings
         ▲
GitHub Actions runs everything daily at ~05:17 Berlin time and commits the result
```

| Layer | What it does | Where |
|---|---|---|
| **Extract** | Queries the public Jobsuche API (v6 search, v4 details) for 12 search terms, de-duplicates by reference number, and snapshots everything live today | `src/tracker/api.py`, `fetch.py` |
| **Clean & classify** | The API's search is fuzzy (a "Data Analyst" search also returns hotel jobs), so every title is re-classified into 9 role families plus seniority, and off-target jobs are dropped | `src/tracker/extract.py` |
| **Enrich** | For each *new* posting, reads the description once and extracts the ad language, the German requirement (C1+ / B2 / nice to have / not stated) and 27 tools. Only these features are stored, never the advert text | `extract.describe` |
| **Model** | dbt builds a warehouse from the raw files on every run: daily snapshots → one row per posting with first/last seen → marts for trends, skills, German, salary, locations and employers | `dbt/models/` |
| **Test** | 36 pytest unit tests for the parsing rules, an end-to-end pipeline test with an offline fake API, and dbt tests (unique, not-null, accepted values) on every run | `tests/`, `dbt/models/schema.yml` |
| **Publish** | Exports the marts to JSON for a static Chart.js dashboard and rewrites the findings section above | `src/tracker/build_site.py`, `docs/` |

**Design choices**
- **Git as the data lake, DuckDB as the compute.** Raw daily files live in the repo, and the warehouse is rebuilt from scratch every run (`build/` is never committed). That makes every number reproducible from history, and there's no database to host.
- **Incremental enrichment.** Descriptions are fetched only for postings never seen before, capped per run so the backlog drains over a few days without overloading a public service.
- **Salary normalisation.** Monthly pay is converted to annual, the midpoint of the range is used, and values outside €20k–200k are treated as data-entry errors.

## Run it yourself

```bash
pip install -r requirements.txt
bash scripts/run_pipeline.sh          # fetch -> dbt build -> docs/data.json
cd docs && python -m http.server      # open http://localhost:8000
pytest -q                             # unit + end-to-end tests
```

## Limitations

- Covers the federal job board only. Many startups post on LinkedIn, StepStone or their own sites instead, so English-friendly roles are probably under-counted.
- Text rules are indicative. "Not stated" German usually means the ad is in German and German is implied.
- Few German ads publish pay, so salary figures cover a small, self-selected subset.

---
Built by **Swetha Raj** · [LinkedIn](https://www.linkedin.com/in/swetha-raj-vv) · [Portfolio](https://datacraft-sr.github.io)
