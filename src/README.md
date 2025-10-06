# Document Upload Manager - Refactored

Bu proje, dosya yükleme ve işleme işlemlerini yöneten modüler bir Python uygulamasıdır.

## Proje Yapısı

```
src/
├── __init__.py              # Package initializer
├── main_refactored.py       # Main application file (refactored)
├── database.py              # Database operations
├── file_manager.py          # File operations
├── api_client.py            # API operations
├── report_generator.py      # Report generation
├── gui_components.py        # GUI components
├── thread_manager.py        # Threading operations
├── requirements.txt         # Dependencies
└── README.md                # This file
```


## Modules

### 1. DatabaseManager (`database.py`)
- SQLite database operations  
- File log management  
- API statistics  
- Filtering and querying  

### 2. FileManager (`file_manager.py`)
- File selection and copying  
- Hash calculation  
- Duplicate detection  
- Format validation  

### 3. APIClient (`api_client.py`)
- File upload API calls  
- Embedding processing API calls  
- Connection testing  

### 4. ReportGenerator (`report_generator.py`)
- HTML detailed reports  
- HTML summary reports  
- CSV reports  

### 5. GUIComponents (`gui_components.py`)
- Tkinter GUI components  
- File selection dialogs  
- Log display  
- Filtering and sorting  

### 6. ThreadManager (`thread_manager.py`)
- Background operations  
- Upload and process threads  

## Usage

### Simple Usage
```python
from main_refactored import DocumentUploadManager

app = DocumentUploadManager()
app.run()
```

### Modular Usage
```python
from database import DatabaseManager
from file_manager import FileManager
from api_client import APIClient

# Modülleri ayrı ayrı kullanma
db = DatabaseManager()
file_mgr = FileManager("/path/to/storage", {".pdf", ".docx"})
api = APIClient("http://api.example.com", {".pdf", ".docx"})
```

## Features

- ✅ Modular structure  
- ✅ Type hints  
- ✅ Comprehensive docstrings  
- ✅ Error handling  
- ✅ Threading support  
- ✅ Database logging  
- ✅ Report generation  
- ✅ File format validation  
- ✅ Duplicate detection  
- ✅ Progress tracking  

## Requirements

- Python 3.10+  
- requests >= 2.28.0  
- tkinter (comes with Python)  

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main_refactored.py
```

## Development

### Adding a New Module
1. Create the new module file  
2. Add it to the `__init__.py` file  
3. Add type hints and docstrings  
4. Test it  

### Code Standards
- PEP 8 compliant code  
- Type hints required  
- Google style docstrings  
- Error handling  
- Logging  


## Lisans

This project is licensed under the MIT License.
