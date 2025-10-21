from dataclasses import dataclass
from typing import Dict, Any
import requests

from weasyprint import HTML
from utils.update_sec_ticker_table import USER_AGENT


@dataclass
class PDFBlob:
    filename: str
    data: bytes


def _sec_url_fetcher(user_agent: str, timeout_sec: int):
    """
    WeasyPrint URL fetcher that adds SEC's required User-Agent to ALL http[s] requests
    (images, CSS, fonts, etc.).
    """

    def fetch(url: str) -> Dict[str, Any]:
        r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout_sec)
        r.raise_for_status()
        return {
            "string": r.content,
            "mime_type": r.headers.get("Content-Type"),
            "redirected_url": r.url,  # help WeasyPrint resolve relatives
        }

    return fetch


def html_to_pdf(
    url: str,
    *,
    filename: str = "document.pdf",
    user_agent: str = USER_AGENT,
    timeout_sec: int = 90,
) -> PDFBlob:
    # Fetch the main HTML (with UA), then let WeasyPrint re-fetch images/assets
    html_text = requests.get(
        url, headers={"User-Agent": user_agent}, timeout=timeout_sec
    ).text

    pdf_bytes = HTML(
        string=html_text,
        base_url=url,  # resolve relative asset paths
        url_fetcher=_sec_url_fetcher(user_agent, timeout_sec),
    ).write_pdf()

    if pdf_bytes is None:
        raise ValueError("Failed to generate PDF: write_pdf() returned None")

    return PDFBlob(filename=filename, data=pdf_bytes)
