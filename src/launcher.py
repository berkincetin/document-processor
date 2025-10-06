"""
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
