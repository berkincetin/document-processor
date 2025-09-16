# 📄 Document Processor

This project is a **Python + Tkinter** desktop application for managing document uploads, logging each operation, and tracking the process through a simple GUI.

## 🚀 Features
- **Document Selection & Upload:** Select and upload multiple files at once.
- **Hash Verification:** Automatically calculates file hashes to prevent duplicate uploads.
- **Logging:** Stores file information in a local `upload_logs.db` SQLite database.
- **Status Tracking:** Monitors file selection, upload, and processing status.
- **Error Handling:** Saves error messages in the database and displays them in the interface.

## 🛠️ Requirements
- Python 3.8+
- Required dependencies:
  ```bash
  pip install -r requirements.txt
  ```
  *(If `requirements.txt` is missing, main dependencies include: `tkinter`, `requests`, `python-dotenv`)*

## 📦 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/document-processor.git
   cd document-processor/python
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:
   ```bash
   python main.py
   ```

## 💾 Database
The application uses a local SQLite database (`upload_logs.db`) to store:
- File names, hashes, and sizes
- Selection, upload, and processing timestamps
- Upload and processing status
- Error messages (if any)

If the database file is missing or deleted, it will be automatically recreated on the next run.