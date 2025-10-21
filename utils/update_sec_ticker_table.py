import json
import time
from pathlib import Path
from typing import Any

import requests

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = "JaneSmith-10KDownloader (foobar@gmail.com)"
DEFAULT_TICKER_PATH = Path("data/sec_ticker_table.json")


def _http_get_json(
    url: str,
    ua: str,
    retries: int = 3,
    backoff: float = 0.8,
) -> Any:
    """GET JSON with polite User-Agent + retry/backoff."""
    last_err = None
    sess = requests
    for attempt in range(retries):
        try:
            r = sess.get(
                url,
                headers={"User-Agent": ua, "Accept": "application/json"},
                timeout=30,
            )
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff * (2**attempt))
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            last_err = e
            time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"GET {url} failed: {last_err}")


def _build_flat_table(data: dict[str, dict[str, Any]]) -> dict[str, str]:
    """
    Convert SEC's object-of-objects into a flat dict:
    {"AAPL": "0000320193", "MSFT": "0000789019", ...}
    """
    flat: dict[str, str] = {}
    for rec in data.values():
        ticker = str(rec.get("ticker", "")).upper()
        if not ticker:
            continue
        cik = f"{int(rec['cik_str']):010d}"
        flat[ticker] = cik
    return flat


def update_sec_ticker_table(
    out_path: Path = DEFAULT_TICKER_PATH,
    user_agent: str = USER_AGENT,
    *,
    source_url: str = SEC_TICKERS_URL,
) -> dict[str, str]:
    """
    Download the SEC ticker→CIK mapping and write a compact local JSON file.
    """
    data = _http_get_json(source_url, user_agent)
    flat = _build_flat_table(data)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(flat), encoding="utf-8")
    return flat


def _load_local_table(path: Path = DEFAULT_TICKER_PATH) -> dict[str, str]:
    """Load local ticker→CIK mapping."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No ticker table found at {p}.")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ticker table at {p} is not a JSON object.")
    return {k.upper(): str(v) for k, v in data.items()}


def ticker_to_cik(ticker: str, path: Path = DEFAULT_TICKER_PATH) -> str:
    """
    Return the 10-digit CIK for a given stock ticker.
    If the local ticker table doesn't exist, it will be downloaded automatically.
    """
    p = Path(path)
    if not p.exists():
        print(f"Ticker cache not found at {p}, downloading from SEC...")
        update_sec_ticker_table(out_path=p, user_agent=USER_AGENT)

    table = _load_local_table(p)
    ticker_up = ticker.strip().upper()

    try:
        return table[ticker_up]
    except KeyError:
        raise ValueError(f"Unknown ticker '{ticker_up}'")


# --- DEBUG ---
# if __name__ == "__main__":
#     update_sec_ticker_table()
