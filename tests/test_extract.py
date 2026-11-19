import pytest

from tracker.extract import (
    classify_role, classify_seniority, describe, detect_language,
    extract_skills, flatten_posting, german_requirement,
)


@pytest.mark.parametrize("title,expected", [
    ("Data Analyst (m/w/d)", "Data Analyst"),
    ("Datenanalyst*in Vertrieb", "Data Analyst"),
    ("Senior Data Engineer (f/m/d)", "Data Engineering"),
    ("Business Intelligence Developer", "Business Intelligence"),
    ("Power BI Consultant (m/w/d)", "Business Intelligence"),
    ("Junior CRM Manager", "CRM & RevOps"),
    ("Revenue Operations Analyst", "CRM & RevOps"),
    ("Pricing Analyst (m/f/d)", "Pricing"),
    ("Marketing Analyst", "Marketing Analytics"),
    ("Web Analyst / Tracking", "Marketing Analytics"),
    ("Controller / Data Analyst", "Finance Analytics"),
    ("Financial Analyst FP&A", "Finance Analytics"),
    ("Supply Chain Analyst", "Operations Analytics"),
    ("IT Business Analyst SAP", "Business Analyst"),
    ("Servicekraft Hotel (m/w/d)", None),
    ("Lagerhelfer", None),
    (None, None),
])
def test_classify_role(title, expected):
    assert classify_role(title) == expected


@pytest.mark.parametrize("title,expected", [
    ("Werkstudent Data Analytics", "Working student"),
    ("Praktikum Business Intelligence", "Intern / Trainee"),
    ("Senior Data Analyst", "Senior / Lead"),
    ("Teamlead BI", "Senior / Lead"),
    ("Junior Data Analyst", "Junior"),
    ("Data Analyst (m/w/d)", "Mid / not stated"),
])
def test_classify_seniority(title, expected):
    assert classify_seniority(title) == expected


DE_AD = ("Wir suchen dich als Data Analyst für unser Team in München. Du arbeitest mit SQL und Python "
         "und baust Dashboards in Power BI. Wir bieten dir eine spannende Aufgabe, die du mit uns gestaltest. "
         "Sehr gute Deutschkenntnisse und gute Englischkenntnisse setzen wir voraus. Bei uns ist das Team für "
         "dich da und die Arbeit macht Spaß mit den Kollegen im Büro und im Homeoffice.")
EN_AD = ("We are looking for a Marketing Analyst to join our team in Berlin. You will work with BigQuery, dbt and "
         "Looker and you will own our A/B testing framework. Our team is international and the working language "
         "is English. German is a plus but not required. You are curious and you will report to the Head of Growth.")


def test_detect_language():
    assert detect_language(DE_AD) == "de"
    assert detect_language(EN_AD) == "en"
    assert detect_language("too short") is None


@pytest.mark.parametrize("text,expected", [
    (DE_AD, "Fluent (C1+)"),
    (EN_AD, "Nice to have"),
    ("Fluent German (C1) and English required.", "Fluent (C1+)"),
    ("Deutsch fließend in Wort und Schrift", "Fluent (C1+)"),
    ("Gute Deutschkenntnisse (B2)", "Good (B2)"),
    ("Deutschkenntnisse sind von Vorteil", "Nice to have"),
    ("No German required.", "Nice to have"),
    ("You know SQL.", "Not stated"),
    (None, "Not stated"),
])
def test_german_requirement(text, expected):
    assert german_requirement(text, None) == expected


def test_extract_skills():
    assert extract_skills(DE_AD) == ["SQL", "Python", "Power BI"]
    assert set(extract_skills(EN_AD)) == {"Looker", "BigQuery", "dbt", "A/B testing"}
    assert "R" in extract_skills("Kenntnisse in Python, R und SQL")
    assert "R" not in extract_skills("Erfahrung in R&D und HR")
    assert extract_skills(None) == []


def test_flatten_posting_minimal_v6_record():
    rec = {
        "stellenangebotsTitel": "Junior Data Analyst (m/w/d)",
        "referenznummer": "10000-123-S",
        "firma": "Example GmbH",
        "stellenlokationen": [{"adresse": {"plz": "80331", "ort": "München", "region": "BAYERN", "land": "DEUTSCHLAND"}, "breite": 48.1, "laenge": 11.5}],
        "arbeitszeitVollzeit": True,
        "arbeitszeitTeilzeitFlexibel": True,
        "homeofficemoeglich": True,
        "verguetungsangabe": "JAHRESGEHALT",
        "gehaltsspanneVon": 50000,
        "gehaltsspanneBis": 60000,
        "eintrittszeitraum": {"von": "2026-12-01"},
    }
    row = flatten_posting(rec, "2026-11-19")
    assert row["refnr"] == "10000-123-S"
    assert row["role_family"] == "Data Analyst"
    assert row["seniority"] == "Junior"
    assert row["city"] == "München" and row["region"] == "BAYERN"
    assert row["fulltime"] and row["parttime"] and row["homeoffice_possible"]
    assert (row["salary_min"], row["salary_max"]) == (50000, 60000)
    assert row["start_date"] == "2026-12-01"


def test_describe_stores_features_not_text():
    f = describe("x", EN_AD, "2026-11-19T06:00:00+00:00")
    assert f["ad_language"] == "en"
    assert "description" not in f and EN_AD not in str(f)
