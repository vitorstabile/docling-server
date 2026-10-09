# Docling Conversion Server

This project runs a self-hosted [Docling](https://github.com/docling-project/docling) conversion service using Docker. It exposes a REST API that processes documents (like PDFs) and converts them into Markdown, JSON, or HTML.

## Prerequisites
* [Docker](https://docs.docker.com/get-docker/) installed.
* Python 3.9+ (if using the provided Python scripts).

## 1. Setup & Configuration

This setup uses the official `docling-serve` image.

### Directory Structure
Ensure your files are laid out like this before running:
```text
.
├── docker-compose.yml
├── requirements.txt
├── README.md
├── sample.pdf        (Bring your own PDF for testing)
├── convert_api.py    (Python script provided below)
└── deploy/
    └── Dockerfile    (Your custom Dockerfile)

```

### Starting the Server

Start the container in detached mode:

```bash
docker compose up -d

```

The server will bind to `localhost:5001`. *Note: On the first boot, the container may take a few moments to download required OCR models.*

### Configuration Options

You can configure the server by modifying the environment variables in `docker-compose.yml`:

* `DOCLING_SERVE_ENABLE_UI=1` : Enables the web UI playground at `/ui`.
* `DOCLING_SERVE_ENG_LOC_NUM_WORKERS=2` : The number of concurrent background workers (tune this to match your CPU cores).

---

## 2. Usage & Endpoints

Once the container is running, the service is accessible at `http://localhost:5001`.

* **Web UI Playground:** `http://localhost:5001/ui`
* **Swagger API Docs:** `http://localhost:5001/docs` (Use this to test endpoints visually)

### Converting a file via cURL (Multipart Upload)

You can directly send a file to the `/v1/convert/file` endpoint using `curl`:

```bash
curl -F "files=@sample.pdf" http://localhost:5001/v1/convert/file > output.json

```

### Converting a remote file via URL

To convert a document directly from a public URL:

```bash
curl -X 'POST' \
  'http://localhost:5001/v1/convert/source' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{ "sources": [{"kind": "http", "url": "[https://arxiv.org/pdf/2501.17887](https://arxiv.org/pdf/2501.17887)"}] }'

```

---

## 3. Python Client Example

It is best practice to run Python scripts inside a virtual environment to avoid conflicting packages.

### Step 3a: Create and Activate a Virtual Environment

**On Linux / macOS:**

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

```

**On Windows:**

```cmd
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate

```

*(Note: If you are using PowerShell and get an execution policy error, run `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` first).*

### Step 3b: Install Dependencies

With your `.venv` activated, install the required packages:

```bash
pip install -r requirements.txt

```

### Step 3c: Run the Script

Create a file named `convert_api.py` to send a local PDF to your Docker container and extract the Markdown:

```python
import requests
import os

def convert_pdf_to_md_via_api(pdf_path, output_md_path):
    # The correct endpoint for local file uploads
    url = "http://localhost:5001/v1/convert/file"
    
    print(f"Sending '{pdf_path}' to Docling Docker server...")
    
    with open(pdf_path, 'rb') as f:
        # The server expects the form field to be named 'files'
        files = {'files': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        
        # Safely extract markdown whether it returns JSON or raw text
        if 'application/json' in content_type:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                md_content = data[0].get('markdown', str(data[0]))
            elif isinstance(data, dict):
                md_content = data.get('markdown', str(data))
            else:
                md_content = str(data)
        else:
            md_content = response.text
            
        with open(output_md_path, 'w', encoding='utf-8') as out_f:
            out_f.write(md_content)
            
        print(f"Success! Markdown saved to {output_md_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Ensure you have a 'sample.pdf' in the same directory
    convert_pdf_to_md_via_api("sample.pdf", "output.md")

```

Run the script:

```bash
python convert_api.py

```

## 4. Stopping the Server

When you are done, shut down the container using:

```bash
docker compose down

```
