"""
Migration script - Orijinal main.py'den refactor edilmiş versiyona geçiş.

Bu script orijinal main.py dosyasını yedekler ve refactor edilmiş versiyonu aktif hale getirir.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def backup_original():
    """Orijinal main.py dosyasını yedekle."""
    print("📦 Orijinal main.py dosyası yedekleniyor...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"main_original_{timestamp}.py"

    if os.path.exists("main.py"):
        shutil.copy2("main.py", backup_name)
        print(f"✅ Orijinal dosya {backup_name} olarak yedeklendi")
        return True
    else:
        print("⚠️  main.py dosyası bulunamadı")
        return False


def activate_refactored():
    """Refactor edilmiş versiyonu aktif hale getir."""
    print("🔄 Refactor edilmiş versiyon aktif hale getiriliyor...")

    if os.path.exists("main_refactored.py"):
        shutil.copy2("main_refactored.py", "main.py")
        print("✅ main_refactored.py -> main.py olarak kopyalandı")
        return True
    else:
        print("❌ main_refactored.py dosyası bulunamadı")
        return False


def create_launcher():
    """Kolay başlatma için launcher script'i oluştur."""
    print("🚀 Launcher script'i oluşturuluyor...")

    launcher_content = '''"""
Document Upload Manager - Launcher

Bu script uygulamayı başlatır.
"""

import sys
from pathlib import Path

# src klasörünü Python path'ine ekle
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from main_refactored import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    print("Lütfen src/ klasöründeki tüm modüllerin mevcut olduğundan emin olun.")
    sys.exit(1)
'''

    with open("launcher.py", "w", encoding="utf-8") as f:
        f.write(launcher_content)

    print("✅ launcher.py oluşturuldu")


def verify_modules():
    """Tüm modüllerin mevcut olduğunu kontrol et."""
    print("🔍 Modüller kontrol ediliyor...")

    required_modules = [
        "database.py",
        "file_manager.py",
        "api_client.py",
        "report_generator.py",
        "gui_components.py",
        "thread_manager.py",
        "main_refactored.py",
        "__init__.py",
    ]

    missing_modules = []
    for module in required_modules:
        if not os.path.exists(module):
            missing_modules.append(module)

    if missing_modules:
        print("❌ Eksik modüller:")
        for module in missing_modules:
            print(f"   - {module}")
        return False
    else:
        print("✅ Tüm modüller mevcut")
        return True


def create_requirements():
    """requirements.txt dosyasını oluştur."""
    print("📋 requirements.txt oluşturuluyor...")

    requirements_content = """# Document Upload Manager - Requirements
# Refactor edilmiş versiyon için gerekli paketler

requests>=2.28.0

# Opsiyonel paketler (geliştirme için)
# pytest>=7.0.0
# black>=22.0.0
# flake8>=4.0.0
# mypy>=0.950
"""

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)

    print("✅ requirements.txt oluşturuldu")


def main():
    """Ana migration fonksiyonu."""
    print("🔄 Document Upload Manager - Migration Script")
    print("=" * 50)

    # Modülleri kontrol et
    if not verify_modules():
        print("❌ Migration iptal edildi - eksik modüller var")
        return False

    # Orijinal dosyayı yedekle
    if not backup_original():
        print("⚠️  Yedekleme başarısız, devam ediliyor...")

    # Refactor edilmiş versiyonu aktif hale getir
    if not activate_refactored():
        print("❌ Migration başarısız")
        return False

    # Launcher oluştur
    create_launcher()

    # Requirements oluştur
    create_requirements()

    print("\n" + "=" * 50)
    print("🎉 Migration tamamlandı!")
    print("\n📝 Kullanım:")
    print("   python launcher.py          # Uygulamayı başlat")
    print("   python src/test_refactored.py  # Testleri çalıştır")
    print("\n📁 Dosyalar:")
    print("   main.py                     # Refactor edilmiş ana dosya")
    print("   main_original_*.py          # Yedeklenmiş orijinal dosya")
    print("   launcher.py                 # Kolay başlatma script'i")
    print("   requirements.txt            # Gerekli paketler")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
