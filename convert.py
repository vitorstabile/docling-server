"""Send a PDF to the Docling server and save the Markdown.

Usage: python convert.py sample.pdf [output.md]
Env:   DOCLING_URL      (default http://localhost:5001)
       DOCLING_API_KEY  (same value as in .env)
       DOCLING_OCR_LANG (optional, comma-separated, e.g. "en" or "pt,en")
"""
import os
import sys
import time
from pathlib import Path

import requests

BASE = os.environ.get("DOCLING_URL", "http://localhost:5001")
HEADERS = {"X-Api-Key": os.environ["DOCLING_API_KEY"]} if os.environ.get("DOCLING_API_KEY") else {}
TIMEOUT_S = 1800  # scanned PDFs are slow on CPU: give up after 30 minutes
OCR_LANG = [x.strip() for x in os.environ.get("DOCLING_OCR_LANG", "").split(",") if x.strip()]


def pdf_to_markdown(pdf: Path) -> str:
    # 1. Submit (async, so large PDFs don't hit HTTP timeouts)
    options = {
        "to_formats": "md",
        "do_ocr": "true",           # scanned PDFs: read text from page images
        "include_images": "false",  # we only need text: saves memory and time
    }
    if OCR_LANG:
        options["ocr_lang"] = OCR_LANG  # repeated form field, one per language
    with pdf.open("rb") as f:
        r = requests.post(
            f"{BASE}/v1/convert/file/async",
            headers=HEADERS,
            files={"files": (pdf.name, f, "application/pdf")},
            data=options,
            timeout=60,
        )
    r.raise_for_status()
    task_id = r.json()["task_id"]

    # 2. Poll until done
    start = time.time()
    while True:
        r = requests.get(f"{BASE}/v1/status/poll/{task_id}", headers=HEADERS, timeout=60)
        r.raise_for_status()
        status = r.json()["task_status"]
        if status == "success":
            break
        if status == "failure":
            raise RuntimeError(f"Docling failed: {r.text}")
        if time.time() - start > TIMEOUT_S:
            raise TimeoutError(f"Task {task_id} still '{status}' after {TIMEOUT_S}s")
        time.sleep(2)

    # 3. Fetch the result
    r = requests.get(f"{BASE}/v1/result/{task_id}", headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()["document"]["md_content"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".md")
    dst.write_text(pdf_to_markdown(src), encoding="utf-8")
    print(f"Saved {dst}")
