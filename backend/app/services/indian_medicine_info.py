from datetime import datetime, timezone
from html.parser import HTMLParser
from threading import Lock
import re
import time
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

CDSCO_URL = 'https://cdscoonline.gov.in/CDSCO/soam/drug_data.jsp'
_cache: dict[str, tuple[float, list[dict], str]] = {}
_cache_lock = Lock()


class _DrugTable(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'tr':
            self.row = []
        elif tag.lower() in ('td', 'th') and self.row is not None:
            self.cell = []
        elif tag.lower() == 'br' and self.cell is not None:
            self.cell.append(' ')

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag.lower() in ('td', 'th') and self.cell is not None and self.row is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag.lower() == 'tr' and self.row is not None:
            if len(self.row) >= 5:
                self.rows.append(self.row)
            self.row = None


def _normal(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', value.casefold())


def approved_uses(name: str, strength: str = '') -> dict:
    query = ' '.join(name.split())[:100]
    if len(query) < 2:
        raise HTTPException(422, 'Enter a medicine name or active ingredient.')
    key = f'{query.casefold()}|{strength.casefold().strip()}'
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] > now:
            results, fetched_at = cached[1], cached[2]
        else:
            try:
                response = httpx.get(CDSCO_URL, params={'exact_name': query, 'first_time': '1'},
                                     timeout=12, follow_redirects=True,
                                     headers={'User-Agent': 'AarogyaSaathi/1.0 (medicine information source lookup)'})
                response.raise_for_status()
                parser = _DrugTable()
                parser.feed(response.text)
                rows = parser.rows[1:]  # First parsed table row is the column header.
                tokens = [t for t in re.findall(r'[a-z0-9]+', query.casefold()) if len(t) > 1]
                qstrength = _normal(strength)
                results = []
                for row in rows:
                    drug_name, row_strength, indication, approval = row[1], row[2], row[3], row[4]
                    name_tokens = set(re.findall(r'[a-z0-9]+', drug_name.casefold()))
                    if not all(t in name_tokens for t in tokens):
                        continue
                    if qstrength and qstrength not in _normal(row_strength):
                        continue
                    if indication.strip() and _normal(indication) not in {'na', 'sameasapproved', 'asapproved'}:
                        results.append({'drug_name': drug_name, 'strength': row_strength,
                                        'approved_indication': indication.strip(), 'approval_date': approval})
                # Keep source results modest for predictable page size and render time.
                results = results[:20]
                fetched_at = datetime.now(timezone.utc).isoformat()
                _cache[key] = (now + 900, results, fetched_at)
            except (httpx.HTTPError, ValueError):
                raise HTTPException(503, 'The CDSCO medicine information source is temporarily unavailable. Please use its official search page.') from None
    return {'query': query, 'strength': strength, 'results': results, 'fetched_at': fetched_at,
            'source_name': 'CDSCO · New Drugs Approved',
            'source_url': CDSCO_URL + '?' + urlencode({'exact_name': query, 'first_time': '1'})}
