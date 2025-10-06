"""
Modern UI Demo Script

Bu script modern UI'nin özelliklerini gösterir.
"""

import tkinter as tk
from pathlib import Path
import sys

# Modülleri import et
from database import DatabaseManager
from file_manager import FileManager
from api_client import APIClient
from report_generator import ReportGenerator
from modern_gui import ModernGUIComponents
from thread_manager import ThreadManager


def create_demo_data():
    """Demo verisi oluştur."""
    print("🎭 Demo verisi oluşturuluyor...")

    # Veritabanı oluştur
    db = DatabaseManager("demo_upload_logs.db")

    # Demo dosyaları oluştur
    demo_dir = Path("demo_files")
    demo_dir.mkdir(exist_ok=True)

    # Test dosyaları oluştur
    test_files = [
        ("test1.pdf", "PDF dosyası içeriği"),
        ("test2.docx", "Word dosyası içeriği"),
        ("test3.txt", "Text dosyası içeriği"),
        ("test1.pdf", "Aynı isimde PDF dosyası"),  # Duplicate
        ("test2.docx", "Aynı isimde Word dosyası"),  # Overwrite
    ]

    for filename, content in test_files:
        file_path = demo_dir / filename
        file_path.write_text(content)

        # Dosya bilgilerini al
        file_size = file_path.stat().st_size
        file_hash = "demo_hash_" + filename

        # Veritabanına kaydet
        db.log_file_selection(
            filename,
            file_hash,
            file_size,
            "demo_user",
            str(file_path),
            str(file_path),
            False,
        )

    # Overwrite bilgilerini güncelle
    db.update_duplicate_info("test1.pdf", is_overwrite=False)
    db.update_duplicate_info("test2.docx", is_overwrite=True)
    db.update_duplicate_info("test2.docx", is_overwrite=True)  # 2. kez overwrite

    print("✅ Demo verisi oluşturuldu")
    return db


def main():
    """Ana demo fonksiyonu."""
    print("🚀 Modern UI Demo Başlatılıyor...")

    # Demo verisi oluştur
    db = create_demo_data()

    # Modülleri başlat
    file_manager = FileManager("demo_files", {".pdf", ".docx", ".txt", ".md"})
    api_client = APIClient("http://httpbin.org", {".pdf", ".docx", ".txt", ".md"})
    report_generator = ReportGenerator(file_manager)

    # GUI'yi başlat
    root = tk.Tk()
    thread_manager = ThreadManager(root, None)
    gui = ModernGUIComponents(
        root, file_manager, db, api_client, report_generator, thread_manager
    )

    # Thread manager'ı GUI ile bağla
    thread_manager.gui = gui

    # GUI'yi kur
    gui.setup_gui()

    print("🎨 Modern UI başlatıldı!")
    print("📋 Özellikler:")
    print("   - Modern ve renkli tasarım")
    print("   - Gelişmiş filtreleme sistemi")
    print("   - Duplicate/Overwrite takibi")
    print("   - Responsive layout")
    print("   - Hover efektleri")

    # GUI'yi çalıştır
    root.mainloop()


if __name__ == "__main__":
    main()
