from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datetime import datetime
from utils.update_sec_ticker_table import _http_get_json, ticker_to_cik, USER_AGENT
from utils.html_to_pdf import PDFBlob, html_to_pdf

# === SEC endpoints ===
SEC_BASE = "https://data.sec.gov"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"


@dataclass(frozen=True)
class TenKInfo:
    company_name: str
    ticker: str
    filing_date: str
    PDF_data: PDFBlob


def _latest_10k(subs: dict[str, Any]) -> dict[str, str] | None:
    """
    Return the most recent 10-K from submissions JSON
    """
    recent = subs.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    if not forms:
        return None

    candidates = []
    for i, form in enumerate(forms):
        if form != "10-K":
            continue

        filing_date = recent["filingDate"][i]
        date_obj = datetime.fromisoformat(filing_date)

        candidates.append((date_obj, i))

    if not candidates:
        return None

    _, best_i = max(candidates, key=lambda t: t[0])

    return {
        "filingDate": recent["filingDate"][best_i],
        "accessionNumber": recent["accessionNumber"][best_i],
        "primaryDocument": recent["primaryDocument"][best_i],
    }


def get_latest_10k_by_ticker(ticker: str) -> TenKInfo:
    """Fetch the latest 10-K metadata"""
    cik10 = ticker_to_cik(ticker)

    subs_url = f"{SEC_BASE}/submissions/CIK{cik10}.json"
    subs = _http_get_json(subs_url, USER_AGENT)

    latest = _latest_10k(subs)
    if not latest:
        raise RuntimeError(f"No 10-K found for ticker {ticker}.")

    accession = latest["accessionNumber"]
    accession_nodash = accession.replace("-", "")
    cik_nozeros = str(int(cik10))
    html_url = (
        f"{ARCHIVES}/{cik_nozeros}/{accession_nodash}/{latest['primaryDocument']}"
    )

    filing_date = latest["filingDate"]
    pdf_filename = f"{ticker.upper()}_10K_{filing_date}.pdf"
    pdf_data = html_to_pdf(html_url, filename=pdf_filename, user_agent=USER_AGENT)

    return TenKInfo(
        company_name=subs.get("name", ""),
        ticker=ticker.upper(),
        filing_date=filing_date,
        PDF_data=pdf_data,
    )


def save_pdf_blob(blob: PDFBlob, dest_dir: Path | str = ".") -> Path:
    """
    Persist a PDFBlob to disk. Returns the written file path.
    """
    dest = Path(dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / blob.filename
    out_path.write_bytes(blob.data)
    return out_path


if __name__ == "__main__":
    ## Ticker examples:
    # Apple AAPL
    # Meta META
    # Alphabet GOOG
    # Amazon AMZN
    # Netflix NFLX
    # Goldman Sachs GS

    ## Get latest 10-K of company:
    tenK_info = get_latest_10k_by_ticker("AAPL")
    print(f"{tenK_info.company_name} ({tenK_info.ticker}) - {tenK_info.filing_date}")

    ## To save 10-K as PDF file, run:
    saved = save_pdf_blob(tenK_info.PDF_data, "./reports")
    print("Saved PDF to:", saved)
