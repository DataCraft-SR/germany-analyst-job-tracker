"""Central configuration for the job tracker."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"            # one gzipped JSONL snapshot per day
FEATURES_DIR = ROOT / "data" / "features"  # derived features from job descriptions
DOCS_DIR = ROOT / "docs"                   # GitHub Pages site
WAREHOUSE = ROOT / "build" / "warehouse.duckdb"  # rebuilt every run, never committed

API_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
SEARCH_PATH = "/pc/v6/jobs"          # v4 search returns 403 since 2026
DETAILS_PATH = "/pc/v4/jobdetails/"  # v4 details still work; v6 returns 403
API_KEY = "jobboerse-jobsuche"       # public client id used by arbeitsagentur.de

# Free-text searches sent to the API. The API matches loosely, so every
# result is re-classified by title afterwards (see extract.classify_role).
SEARCH_TERMS = [
    "Data Analyst",
    "Business Analyst",
    "Business Intelligence",
    "Marketing Analyst",
    "CRM Manager",
    "Revenue Operations",
    "Pricing Analyst",
    "Financial Analyst",
    "Operations Analyst",
    "Data Engineer",
    "Analytics Engineer",
    "Datenanalyst",
]

PAGE_SIZE = 100
MAX_PAGES_PER_TERM = 30          # safety cap (3,000 results per term)
MAX_DETAILS_PER_RUN = 700        # new descriptions fetched per run; backlog carries over
REQUEST_PAUSE_SECONDS = 0.25     # be polite to a public service
