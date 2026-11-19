"""Offline stand-in for the Jobsuche API, used only by the end-to-end test.

Generates v6-shaped records (field names copied from a real response) with
random content. None of this data is ever committed or published.
"""
import random

TITLES = [
    "Data Analyst (m/w/d)", "Junior Data Analyst", "Senior Data Engineer (f/m/d)",
    "Business Intelligence Developer", "Werkstudent Data Analytics", "Marketing Analyst",
    "CRM Manager (m/w/d)", "Pricing Analyst", "Controller / Data Analyst", "IT Business Analyst",
    "Supply Chain Analyst", "Servicekraft Hotel (m/w/d)", "Lagerhelfer (m/w/d)",
]
CITIES = [("München", "80331", "BAYERN"), ("Berlin", "10115", "BERLIN"), ("Hamburg", "20095", "HAMBURG"),
          ("Frankfurt am Main", "60311", "HESSEN"), ("Köln", "50667", "NORDRHEIN_WESTFALEN"),
          ("Stuttgart", "70173", "BADEN_WUERTTEMBERG")]
EMPLOYERS = ["Alpha GmbH", "Beta AG", "Gamma SE", "Hays AG", "Delta Digital GmbH", "Epsilon Retail"]
EN = ("We are looking for an analyst to join our team. You will work with SQL, Python and Power BI and "
      "you will build dashboards for our stakeholders. The working language is English and German is a plus. "
      "You are curious and you will own the reporting for the team and our customers in the region.")
DE = ("Wir suchen dich für unser Team. Du arbeitest mit SQL, Excel und SAP und erstellst Berichte für die "
      "Geschäftsführung. Sehr gute Deutschkenntnisse in Wort und Schrift setzen wir voraus. Wir bieten dir "
      "ein tolles Team und die Arbeit im Homeoffice ist bei uns möglich und wir freuen uns auf dich.")


class FakeClient:
    def __init__(self, day_index: int, seed: int = 7, pool: int = 400):
        rnd = random.Random(seed)
        self.records = []
        for i in range(pool):
            city, plz, region = rnd.choice(CITIES)
            sal = rnd.random() < 0.3
            low = rnd.randrange(40, 90) * 1000
            self.records.append({
                "stellenangebotsTitel": rnd.choice(TITLES),
                "referenznummer": f"10000-{i:06d}-S",
                "firma": rnd.choice(EMPLOYERS),
                "hauptberuf": "Data-Analyst/in",
                "stellenlokationen": [{"adresse": {"plz": plz, "ort": city, "region": region, "land": "DEUTSCHLAND"},
                                       "breite": 50.0, "laenge": 10.0}],
                "datumErsteVeroeffentlichung": "2026-11-01",
                "arbeitszeitVollzeit": rnd.random() < 0.85,
                "arbeitszeitTeilzeitFlexibel": rnd.random() < 0.2,
                "homeofficemoeglich": rnd.random() < 0.6,
                "verguetungsangabe": "JAHRESGEHALT" if sal else "KEINE_ANGABEN",
                "gehaltsspanneVon": low if sal else None,
                "gehaltsspanneBis": low + 10000 if sal else None,
                "_start": rnd.randrange(0, 3), "_len": rnd.randrange(1, 4),
                "_lang": rnd.choice(["en", "de", "de"]),
            })
        self.day = day_index

    def search(self, term):
        # each term returns a slice; postings appear/disappear across days
        for r in self.records:
            if r["_start"] <= self.day < r["_start"] + r["_len"] and hash(term + r["referenznummer"]) % 3 == 0:
                yield {k: v for k, v in r.items() if not k.startswith("_")}

    def description(self, refnr):
        r = next(x for x in self.records if x["referenznummer"] == refnr)
        return EN if r["_lang"] == "en" else DE
