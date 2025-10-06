"""
Document Upload Manager - Refactored Version

Bu modül dosya yükleme ve işleme işlemlerini yönetir.
Refactor edilmiş versiyon - modüler yapı.
"""

import tkinter as tk
import threading
from typing import Dict, Any, Optional
from pathlib import Path

from database import DatabaseManager
from file_manager import FileManager
from api_client import APIClient
from report_generator import ReportGenerator
from gui_components import GUIComponents
from thread_manager import ThreadManager


class DocumentUploadManager:
    """Ana uygulama sınıfı - refactor edilmiş versiyon."""

    def __init__(self):
        """
        DocumentUploadManager'ı başlat.

        Yapılandırma:
        - API base URL
        - Yerel depolama dizini
        - Desteklenen dosya formatları
        """
        # Yapılandırma
        self.api_base_url = "http://10.1.1.172:3820"
        # self.api_base_url = "http://localhost:3820"
        self.local_storage_dir = "C:/Users/Polinity/Desktop/DOCUMENTS"
        self.supported_formats = {".pdf", ".docx", ".doc", ".txt", ".md"}

        # Modülleri başlat
        self.database_manager = DatabaseManager()
        self.file_manager = FileManager(self.local_storage_dir, self.supported_formats)
        self.api_client = APIClient(self.api_base_url, self.supported_formats)
        self.report_generator = ReportGenerator(self.file_manager)

        # GUI'yi başlat
        self.root = tk.Tk()
        self.thread_manager = ThreadManager(
            self.root, None
        )  # GUI'den sonra güncellenecek
        self.gui = GUIComponents(
            self.root,
            self.file_manager,
            self.database_manager,
            self.api_client,
            self.report_generator,
            self.thread_manager,
        )

        # Thread manager'ı GUI ile bağla
        self.thread_manager.gui = self.gui

        # GUI'yi kur
        self.gui.setup_gui()

    def run(self) -> None:
        """Uygulamayı çalıştır."""
        self.root.mainloop()


def main() -> None:
    """Ana fonksiyon."""
    app = DocumentUploadManager()
    app.run()


if __name__ == "__main__":
    main()
