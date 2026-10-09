# Docling Conversion Server

This project runs a self-hosted [Docling](https://github.com/docling-project/docling) conversion service using Docker. It exposes a REST API that processes documents (like PDFs) and converts them into Markdown, JSON, or HTML. 

By using a Docker Named Volume, all AI models (Layout, Table Recognition, and OCR) are downloaded safely into Docker's persistent storage on the first run. After that, the server can run **100% offline (air-gapped)**.

## Prerequisites
* [Docker](https://docs.docker.com/get-docker/) installed.
* Python 3.9+ (if using the provided Python client script).

---

## 1. Directory Structure

Ensure your project folder contains the following files:
```text
.
├── docker-compose.yml
├── requirements.txt
├── README.md
├── sample.pdf          (Bring your own PDF for testing)
├── convert_api.py      (Python script provided below)
└── deploy/
    └── Dockerfile      (Your custom Dockerfile)

```

*(Note: You do not need to create a local models folder. Docker manages the storage automatically via a named volume).*

---

## 2. Setup & True Offline Configuration

### Step 2a: First Run (Download Models)

Ensure the offline flags in your `docker-compose.yml` are **commented out** so the container can connect to the internet to download the models (approx. 2-4 GB).

Start the container:

```bash
docker compose up -d

```

**Trigger the download:** The server waits for the first request before downloading. Run the Python script or the `curl` command (see Section 4) to send a PDF. You can monitor the download progress by running:

```bash
docker compose logs -f docling

```

Once you see `Finished converting document` in the logs, the models are permanently saved in the Docker volume.

### Step 2b: Lock it Down (100% Offline Mode)

Once the models are successfully cached:

1. Stop the container: `docker compose down`
2. Open your `docker-compose.yml` and **uncomment** the Hugging Face offline variables:

```yaml
      - HF_HUB_OFFLINE=1
      - HF_DATASETS_OFFLINE=1

```

3. Start the container again: `docker compose up -d`

The server will now start instantly, use the locally cached models, and **never attempt to use the internet again**.

---

## 3. Usage & Endpoints

Once running, the service is accessible at `http://localhost:5001`.

* **Web UI Playground:** `http://localhost:5001/ui`
* **Swagger API Docs:** `http://localhost:5001/docs` (Test endpoints visually)

### Converting via cURL (Multipart Upload)

Send a local file directly to the API:

```bash
curl -F "files=@sample.pdf" http://localhost:5001/v1/convert/file > output.md

```

---

## 4. Python Client Example

It is best practice to run Python scripts inside a virtual environment to avoid package conflicts.

### Step 4a: Create and Activate a Virtual Environment

**On Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate

```

**On Windows:**

```cmd
python -m venv .venv
.venv\Scripts\activate

```

### Step 4b: Install Dependencies

Create a `requirements.txt` file containing `requests==2.31.0`, then run:

```bash
pip install -r requirements.txt

```

### Step 4c: Run the Script

Create `convert_api.py`:

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
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    # Ensure you have a 'sample.pdf' in the same directory
    convert_pdf_to_md_via_api("sample.pdf", "output.md")

```

Run the script:

```bash
python convert_api.py

```

---

## 5. Docker Volume Management

Because the AI models are stored inside a Docker Named Volume, they persist even if you delete the container.

* **View the volume:** `docker volume ls` (Look for `docling_cache`)
* **Delete everything (Container + Models):**
If you ever want to completely wipe the installation and free up the disk space, run:
```bash
docker compose down -v

```
