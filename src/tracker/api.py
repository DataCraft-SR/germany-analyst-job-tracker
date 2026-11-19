"""Thin client for the Bundesagentur für Arbeit Jobsuche API."""
from __future__ import annotations

import base64
import logging
import time
from typing import Iterator

import requests

from . import config

log = logging.getLogger(__name__)


class JobsucheClient:
    def __init__(self, session: requests.Session | None = None, pause: float = config.REQUEST_PAUSE_SECONDS):
        self.session = session or requests.Session()
        self.session.headers.update({"X-API-Key": config.API_KEY, "User-Agent": "germany-analyst-job-tracker (GitHub portfolio project)"})
        self.pause = pause

    def _get(self, path: str, params: dict | None = None, retries: int = 4) -> dict | None:
        url = config.API_BASE + path
        for attempt in range(retries):
            try:
                r = self.session.get(url, params=params, timeout=30)
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 404:
                    return None
                log.warning("HTTP %s for %s (attempt %d)", r.status_code, path, attempt + 1)
            except requests.RequestException as exc:
                log.warning("Request error %s for %s (attempt %d)", exc, path, attempt + 1)
            time.sleep(2 ** attempt)
        return None

    def search(self, term: str, page_size: int = config.PAGE_SIZE, max_pages: int = config.MAX_PAGES_PER_TERM) -> Iterator[dict]:
        """Yield every active job posting ('Arbeit' offers) for a search term."""
        for page in range(1, max_pages + 1):
            data = self._get(config.SEARCH_PATH, {"was": term, "angebotsart": 1, "page": page, "size": page_size})
            time.sleep(self.pause)
            if not data:
                return
            results = data.get("ergebnisliste") or []
            yield from results
            total = data.get("maxErgebnisse") or 0
            if len(results) < page_size or page * page_size >= total:
                return

    def description(self, refnr: str) -> str | None:
        encoded = base64.b64encode(refnr.encode()).decode()
        data = self._get(config.DETAILS_PATH + encoded, retries=2)
        time.sleep(self.pause)
        return (data or {}).get("stellenangebotsBeschreibung")
