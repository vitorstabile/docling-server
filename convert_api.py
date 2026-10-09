import requests
import os


def convert_pdf_to_md_via_api(pdf_path, output_md_path):

    url = "http://localhost:5001/v1/convert/file"

    print(f"Sending {pdf_path} to Docling Docker server...")

    with open(pdf_path, 'rb') as f:
        files = {'files': (os.path.basename(pdf_path), f, 'application/pdf')}

        # Sending the POST request
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # Docling can sometimes return raw text or a JSON payload depending on the version.
        # This safely extracts the markdown either way.
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            data = response.json()
            # If it returns a list of results (because 'files' supports multiple uploads)
            if isinstance(data, list) and len(data) > 0:
                md_content = data[0].get('markdown', str(data[0]))
            elif isinstance(data, dict):
                md_content = data.get('markdown', str(data))
            else:
                md_content = str(data)
        else:
            # If the API returns raw markdown text directly
            md_content = response.text

        with open(output_md_path, 'w', encoding='utf-8') as out_f:
            out_f.write(md_content)

        print(f"Success! Markdown saved to {output_md_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    convert_pdf_to_md_via_api("sample.pdf", "output.md")
