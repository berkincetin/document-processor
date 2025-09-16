# DocUploader

A Streamlit application to batch upload documents and trigger processing in a backend FastAPI server. 

## Features

- Upload multiple files from a folder at once.
- Automatically process all supported documents (.txt, .pdf, .docx, .md).
- Metadata tracking: upload time, computer name, status, duplicate file checks.
- Works with FastAPI backend

## Installation:

1. Clone the repo:

```bash
https://github.com/berkincetin/document-processor.git
cd document-processor
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Usage:

```bash
streamlit run main.py
```