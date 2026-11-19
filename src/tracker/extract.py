"""Pure functions that turn raw API records into clean, analysable fields.

Everything here is deterministic and covered by tests/test_extract.py.
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------- role family
# Order matters: the first matching family wins.
ROLE_RULES: list[tuple[str, str]] = [
    ("Data Engineering", r"data[\s-]?engineer|analytics[\s-]?engineer|etl[\s-]?(developer|entwickler)"),
    ("CRM & RevOps", r"\bcrm\b|revenue[\s-]?operations|\brevops\b|sales[\s-]?operations|marketing[\s-]?operations|marketing[\s-]?automation"),
    ("Pricing", r"pricing|preis(manag|analy)"),
    ("Marketing Analytics", r"marketing[\s-]?(data[\s-]?)?analy|web[\s-]?analy|digital[\s-]?analy|performance[\s-]?marketing[\s-]?analy|tracking[\s-]?(&|und)?[\s-]?analytics"),
    ("Business Intelligence", r"business[\s-]?intelligence|\bbi[\s-]?(analyst|developer|entwickler|consultant|berater|spezialist|specialist|manager|engineer)|power[\s-]?bi|reporting[\s-]?(analyst|spezialist|specialist|manager)"),
    ("Finance Analytics", r"financial[\s-]?analy|finanzanaly|fp&a|finance[\s-]?analy|\bcontroller|controlling"),
    ("Operations Analytics", r"operations[\s-]?analy|supply[\s-]?chain[\s-]?analy|logisti\w*[\s-]?analy|process[\s-]?analy|prozessanaly"),
    ("Business Analyst", r"business[\s-]?analy|it[\s-]?business[\s-]?analy|requirements[\s-]?(engineer|analyst)"),
    ("Data Analyst", r"data[\s-]?analy|datenanaly|data[\s-]?scien|daten[\s-]?(wissenschaft|analyse)|analytics[\s-]?(manager|specialist|spezialist|consultant)|\banalyst\b"),
]
_ROLE_RX = [(name, re.compile(rx, re.I)) for name, rx in ROLE_RULES]


def classify_role(title: str | None) -> str | None:
    """Return the role family for a job title, or None if it is off-target.

    The API's free-text search is fuzzy (a 'Data Analyst' search also returns
    hotel and warehouse jobs), so anything that matches no family is dropped
    from the analysis.
    """
    if not title:
        return None
    for name, rx in _ROLE_RX:
        if rx.search(title):
            return name
    return None


# ------------------------------------------------------------------ seniority
_SENIORITY_RULES = [
    ("Working student", r"werkstudent|working[\s-]?student|studentische"),
    ("Intern / Trainee", r"praktik|\bintern(ship)?\b|trainee|volontär|abschlussarbeit|thesis"),
    ("Senior / Lead", r"\bsenior\b|\bsr\.?\s|\blead\b|\bhead\b|principal|teamlead|team[\s-]?lead|leitung|leiter|director|\bexpert\b"),
    ("Junior", r"junior|\bjr\.?\s|einsteiger|berufseinst|graduate|entry[\s-]?level"),
]
_SENIORITY_RX = [(name, re.compile(rx, re.I)) for name, rx in _SENIORITY_RULES]


def classify_seniority(title: str | None) -> str:
    if title:
        for name, rx in _SENIORITY_RX:
            if rx.search(title):
                return name
    return "Mid / not stated"


# ------------------------------------------------------------------- language
_DE_WORDS = {"und", "die", "der", "das", "mit", "für", "wir", "sie", "ihre", "eine", "ist", "auf", "bei", "von", "zu", "den", "im", "uns", "dich", "du"}
_EN_WORDS = {"and", "the", "with", "for", "we", "you", "your", "our", "are", "is", "to", "of", "in", "a", "an", "will", "as", "on"}
_WORD_RX = re.compile(r"[a-zäöüß]+", re.I)


def detect_language(text: str | None) -> str | None:
    """Very small stop-word classifier: 'de', 'en' or None if too short."""
    if not text:
        return None
    words = _WORD_RX.findall(text.lower())
    if len(words) < 30:
        return None
    de = sum(w in _DE_WORDS for w in words)
    en = sum(w in _EN_WORDS for w in words)
    if de == en == 0:
        return None
    return "de" if de >= en else "en"


# ---------------------------------------------------------- German requirement
_GERMAN_NICE = re.compile(
    r"german\W+(language\W+)?(skills\W+)?(is|are|would be)\W+(a\W+)?(plus|nice|bonus|advantage)"
    r"|(basic|some)\W+german"
    r"|no\W+german\W+(required|needed|necessary)"
    r"|german\W+(not\W+)?(required|needed|necessary)\W*:?\W*no"
    r"|deutsch\w*\W+(sind\W+|ist\W+)?(von\W+vorteil|wünschenswert|ein\W+plus)"
    r"|grundkenntnisse\W+(in\W+)?deutsch",
    re.I,
)
_GERMAN_FLUENT = re.compile(
    r"(fließend|fliessend|verhandlungssicher|sehr\W+gut\w*|exzellent\w*|hervorragend\w*|muttersprach\w*|c1|c2)\W+(\w+\W+){0,4}?deutsch"
    r"|deutsch\w*\W+(\w+\W+){0,6}?(fließend|fliessend|verhandlungssicher|sehr\W+gut|c1|c2|muttersprach)"
    r"|(fluent|excellent|native|business[\s-]?fluent|proficient|very\W+good|strong)\W+(\w+\W+){0,4}?german"
    r"|german\W+(\w+\W+){0,4}?(fluent|c1|c2|native|business[\s-]?fluent|proficiency)",
    re.I,
)
_GERMAN_GOOD = re.compile(
    r"(gut\w*|solide\w*|b2)\W+(\w+\W+){0,4}?deutsch"
    r"|deutsch\w*\W+(\w+\W+){0,6}?(gut|b2)"
    r"|(good|solid)\W+(\w+\W+){0,3}?german|german\W+(\w+\W+){0,4}?b2",
    re.I,
)
_GERMAN_ANY = re.compile(r"deutsch|german", re.I)


def german_requirement(text: str | None, language: str | None) -> str:
    """Bucket how much German a posting asks for.

    Returns one of: 'Fluent (C1+)', 'Good (B2)', 'Nice to have', 'Not stated'.
    Checks 'nice to have' first because those phrases are the most specific.
    """
    if not text:
        return "Not stated"
    if _GERMAN_NICE.search(text):
        return "Nice to have"
    if _GERMAN_FLUENT.search(text):
        return "Fluent (C1+)"
    if _GERMAN_GOOD.search(text):
        return "Good (B2)"
    return "Not stated"


# --------------------------------------------------------------------- skills
SKILLS: dict[str, str] = {
    "SQL": r"\bsql\b|t-sql|pl/sql|postgres|mysql",
    "Python": r"\bpython\b|pandas|numpy",
    "R": r"(?<![\w&])R(?![\w&/-])(?=\s*(,|/|\)|und|and|oder|or|\s+studio|$))",
    "Excel": r"\bexcel\b|\bvba\b",
    "Power BI": r"power[\s-]?bi|\bdax\b",
    "Tableau": r"tableau",
    "Looker": r"looker",
    "Qlik": r"qlik",
    "SAP": r"\bsap\b|s/4\s?hana",
    "Salesforce": r"salesforce",
    "HubSpot": r"hubspot",
    "Google Analytics": r"google[\s-]?analytics|\bga4\b",
    "BigQuery": r"bigquery|big[\s-]query",
    "Snowflake": r"snowflake",
    "dbt": r"\bdbt\b",
    "Databricks": r"databricks",
    "Spark": r"\bspark\b|pyspark",
    "Azure": r"\bazure\b",
    "AWS": r"\baws\b|amazon[\s-]web[\s-]services",
    "GCP": r"\bgcp\b|google[\s-]cloud",
    "Airflow": r"airflow",
    "Git": r"\bgit\b|github|gitlab",
    "A/B testing": r"a/b[\s-]?test|ab[\s-]test|experimentation",
    "Statistics": r"statisti",
    "Machine learning": r"machine[\s-]?learning|\bml\b|maschinelles\s+lernen",
    "ETL / Data warehouse": r"\betl\b|\belt\b|data[\s-]?warehouse|dwh",
    "Jira": r"\bjira\b|confluence",
}
_SKILL_RX = {
    name: re.compile(rx) if name == "R" else re.compile(rx, re.I)
    for name, rx in SKILLS.items()
}


def extract_skills(text: str | None) -> list[str]:
    if not text:
        return []
    return [name for name, rx in _SKILL_RX.items() if rx.search(text)]


# --------------------------------------------------------------------- record
def _first(lst: list | None) -> dict:
    return lst[0] if lst else {}


def flatten_posting(rec: dict[str, Any], snapshot_date: str) -> dict[str, Any]:
    """Slim one v6 search result down to the fields the warehouse needs."""
    loc = _first(rec.get("stellenlokationen"))
    addr = loc.get("adresse") or {}
    title = rec.get("stellenangebotsTitel")
    parttime = any(
        rec.get(k)
        for k in (
            "arbeitszeitTeilzeitVormittag",
            "arbeitszeitTeilzeitNachmittag",
            "arbeitszeitTeilzeitAbend",
            "arbeitszeitTeilzeitFlexibel",
        )
    )
    return {
        "snapshot_date": snapshot_date,
        "refnr": rec.get("referenznummer") or rec.get("refnr"),
        "title": title,
        "role_family": classify_role(title),
        "seniority": classify_seniority(title),
        "employer": rec.get("firma"),
        "occupation": rec.get("hauptberuf"),
        "city": addr.get("ort"),
        "postcode": addr.get("plz"),
        "region": addr.get("region"),
        "country": addr.get("land"),
        "lat": loc.get("breite"),
        "lon": loc.get("laenge"),
        "n_locations": len(rec.get("stellenlokationen") or []),
        "first_published": rec.get("datumErsteVeroeffentlichung"),
        "modified_at": rec.get("aenderungsdatum"),
        "start_date": (rec.get("eintrittszeitraum") or {}).get("von"),
        "contract": rec.get("vertragsdauer"),
        "fulltime": bool(rec.get("arbeitszeitVollzeit")),
        "parttime": parttime,
        "minijob": bool(rec.get("istGeringfuegigeBeschaeftigung")),
        "career_changer_ok": bool(rec.get("quereinstiegGeeignet")),
        "homeoffice_possible": bool(rec.get("homeofficemoeglich")),
        "homeoffice_type": rec.get("homeofficetyp"),
        "homeoffice_pct": rec.get("homeofficeprozent"),
        "salary_unit": rec.get("verguetungsangabe"),
        "salary_min": rec.get("gehaltsspanneVon"),
        "salary_max": rec.get("gehaltsspanneBis"),
        "is_external": bool(rec.get("externeURL")),
    }


def describe(refnr: str, description: str | None, fetched_at: str) -> dict[str, Any]:
    """Derived features from a job description.

    Only features are stored, never the full advert text: keeps the repo
    small and avoids republishing employers' ads.
    """
    lang = detect_language(description)
    return {
        "refnr": refnr,
        "fetched_at": fetched_at,
        "has_description": bool(description),
        "description_chars": len(description or ""),
        "ad_language": lang,
        "german_requirement": german_requirement(description, lang),
        "skills": extract_skills(description),
    }
