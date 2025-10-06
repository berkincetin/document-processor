"""
Test dosyası - Refactor edilmiş Document Upload Manager için.

Bu dosya modüllerin doğru çalışıp çalışmadığını test eder.
"""

import sys
import os
from pathlib import Path

# Test için gerekli modülleri import et
try:
    from database import DatabaseManager
    from file_manager import FileManager
    from api_client import APIClient
    from report_generator import ReportGenerator
    from gui_components import GUIComponents
    from thread_manager import ThreadManager
    from main_refactored import DocumentUploadManager

    print("✅ Tüm modüller başarıyla import edildi")
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    sys.exit(1)


def test_database_manager():
    """DatabaseManager'ı test et."""
    print("\n🔍 DatabaseManager test ediliyor...")
    try:
        db = DatabaseManager("test_upload_logs.db")

        # Test verisi ekle
        file_id = db.log_file_selection(
            "test.pdf",
            "test_hash_123",
            1024,
            "test_user",
            "/original/path/test.pdf",
            "/local/path/test.pdf",
            False,
        )

        # Veriyi kontrol et
        logs = db.get_filtered_logs({"status_filter": "Tümü"})
        assert len(logs) > 0, "Log kaydı bulunamadı"

        # Test veritabanını temizle
        db.clear_logs()

        print("✅ DatabaseManager test başarılı")
        return True
    except Exception as e:
        print(f"❌ DatabaseManager test hatası: {e}")
        return False


def test_file_manager():
    """FileManager'ı test et."""
    print("\n🔍 FileManager test ediliyor...")
    try:
        # Test klasörü oluştur
        test_dir = Path("test_files")
        test_dir.mkdir(exist_ok=True)

        # Test dosyası oluştur
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")

        fm = FileManager(str(test_dir), {".txt"})

        # Dosya bilgilerini al
        filename, size, file_hash = fm.get_file_info(str(test_file))
        assert filename == "test.txt", "Dosya adı yanlış"
        assert size > 0, "Dosya boyutu 0"
        assert len(file_hash) > 0, "Hash boş"

        # Format testi
        formatted_size = fm.format_file_size(1024)
        assert "KB" in formatted_size, "Boyut formatı yanlış"

        # Test klasörünü temizle
        import shutil

        shutil.rmtree(test_dir)

        print("✅ FileManager test başarılı")
        return True
    except Exception as e:
        print(f"❌ FileManager test hatası: {e}")
        return False


def test_api_client():
    """APIClient'ı test et."""
    print("\n🔍 APIClient test ediliyor...")
    try:
        api = APIClient("http://httpbin.org", {".txt"})

        # Bağlantı testi (gerçek API'ya bağlanmadan)
        # Bu test sadece sınıfın oluşturulabildiğini kontrol eder
        assert api.api_base_url == "http://httpbin.org", "API URL yanlış"
        assert ".txt" in api.supported_formats, "Desteklenen formatlar yanlış"

        print("✅ APIClient test başarılı")
        return True
    except Exception as e:
        print(f"❌ APIClient test hatası: {e}")
        return False


def test_report_generator():
    """ReportGenerator'ı test et."""
    print("\n🔍 ReportGenerator test ediliyor...")
    try:
        # Mock FileManager oluştur
        class MockFileManager:
            def format_file_size(self, size):
                return f"{size} B"

        rg = ReportGenerator(MockFileManager())

        # Duration format testi
        duration = rg.format_duration(65.5)
        assert "1m" in duration, "Duration formatı yanlış"

        duration_short = rg.format_duration(30.0)
        assert "30.0s" in duration_short, "Kısa duration formatı yanlış"

        print("✅ ReportGenerator test başarılı")
        return True
    except Exception as e:
        print(f"❌ ReportGenerator test hatası: {e}")
        return False


def test_thread_manager():
    """ThreadManager'ı test et."""
    print("\n🔍 ThreadManager test ediliyor...")
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()  # Pencereyi gizle

        tm = ThreadManager(root)

        # Basit test fonksiyonu
        def test_func():
            return {"success": True, "result": "test"}

        def test_callback(result):
            assert result["success"], "Callback test başarısız"

        # Thread testi (hızlı test için)
        tm.run_upload_thread(test_func, test_callback)

        root.destroy()

        print("✅ ThreadManager test başarılı")
        return True
    except Exception as e:
        print(f"❌ ThreadManager test hatası: {e}")
        return False


def test_integration():
    """Entegrasyon testi."""
    print("\n🔍 Entegrasyon testi yapılıyor...")
    try:
        # Tüm modülleri birlikte test et
        db = DatabaseManager("test_integration.db")
        fm = FileManager("test_integration_files", {".txt"})
        api = APIClient("http://httpbin.org", {".txt"})
        rg = ReportGenerator(fm)

        # Test klasörü oluştur
        test_dir = Path("test_integration_files")
        test_dir.mkdir(exist_ok=True)

        # Test dosyası oluştur
        test_file = test_dir / "integration_test.txt"
        test_file.write_text("Integration test content")

        # Dosya bilgilerini al
        filename, size, file_hash = fm.get_file_info(str(test_file))

        # Veritabanına kaydet
        file_id = db.log_file_selection(
            filename,
            file_hash,
            size,
            "integration_test_user",
            str(test_file),
            str(test_file),
            False,
        )

        # Veriyi kontrol et
        logs = db.get_filtered_logs({"status_filter": "Tümü"})
        assert len(logs) > 0, "Entegrasyon testi başarısız"

        # Temizlik
        db.clear_logs()
        import shutil

        shutil.rmtree(test_dir)
        os.remove("test_integration.db")

        print("✅ Entegrasyon testi başarılı")
        return True
    except Exception as e:
        print(f"❌ Entegrasyon testi hatası: {e}")
        return False


def main():
    """Ana test fonksiyonu."""
    print("🚀 Document Upload Manager - Refactor Test Suite")
    print("=" * 50)

    tests = [
        test_database_manager,
        test_file_manager,
        test_api_client,
        test_report_generator,
        test_thread_manager,
        test_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Sonuçları: {passed}/{total} test başarılı")

    if passed == total:
        print("🎉 Tüm testler başarılı! Refactor işlemi başarılı.")
        return True
    else:
        print("⚠️  Bazı testler başarısız. Lütfen hataları kontrol edin.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
