# docling-server

Self-hosted [Docling](https://github.com/docling-project/docling-serve) API: PDF in, Markdown out.
First step of a PDF → Markdown → LLM → Excel pipeline.

## Run

```bash
cp .env.example .env        # set DOCLING_VERSION and DOCLING_API_KEY
docker compose --profile cpu up -d     # no GPU
# or
docker compose --profile gpu up -d     # NVIDIA GPU (needs drivers + nvidia-container-toolkit)
```

Check it is up: `docker compose ps` (should show `healthy`) and open http://localhost:5001/docs.

Models live in the `docling_cache` volume, so they are downloaded at most once.
Remove everything including models: `docker compose down -v`.

## Convert a PDF

Install Python deps once (Python 3.9+):

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run (put your own PDF next to `convert.py`):

```bash
# Linux / macOS
export DOCLING_API_KEY=<value from .env>
export DOCLING_OCR_LANG=en       # language of the scans; override per run if needed
python convert.py study.pdf      # writes study.md
```

```powershell
# Windows PowerShell
$env:DOCLING_API_KEY = "<value from .env>"
$env:DOCLING_OCR_LANG = "en"
python convert.py study.pdf
```

Scanned PDFs go through OCR, so expect minutes per document on CPU.
The OCR language code format depends on the OCR engine the server uses; if the
language seems ignored, check the engine's expected codes at http://localhost:5001/docs.

## Notes

- The port is bound to `127.0.0.1` and protected by an API key (`X-Api-Key` header).
- `convert.py` uses the async endpoints (submit, poll, fetch), which is what the future interfaces should use too.
- The web UI is off by default. Set `DOCLING_ENABLE_UI=1` in `.env` for local experiments.
