"""
Document Upload Manager Package

Bu paket dosya yükleme ve işleme işlemlerini yönetir.
"""

__version__ = "2.0.0"
__author__ = "Document Upload Manager Team"

from .main_refactored import DocumentUploadManager
from .database import DatabaseManager
from .file_manager import FileManager
from .api_client import APIClient
from .report_generator import ReportGenerator
from .gui_components import GUIComponents
from .thread_manager import ThreadManager

__all__ = [
    "DocumentUploadManager",
    "DatabaseManager",
    "FileManager",
    "APIClient",
    "ReportGenerator",
    "GUIComponents",
    "ThreadManager",
]
