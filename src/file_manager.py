"""
Dosya işlemleri için modül.

Bu modül dosya seçimi, kopyalama, hash hesaplama ve duplicate kontrolü işlemlerini yönetir.
"""

import hashlib
import shutil
from pathlib import Path
from typing import List, Tuple, Set, Optional, Union


class FileManager:
    """Dosya işlemlerini yöneten sınıf."""

    def __init__(self, local_storage_dir: str, supported_formats: Set[str]):
        """
        FileManager'ı başlat.

        Args:
            local_storage_dir: Yerel depolama dizini
            supported_formats: Desteklenen dosya formatları
        """
        self.local_storage_dir = Path(local_storage_dir)
        self.supported_formats = supported_formats
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

    def calculate_file_hash(self, filepath: str) -> str:
        """
        Dosyanın MD5 hash'ini hesapla.

        Args:
            filepath: Dosya yolu

        Returns:
            MD5 hash değeri
        """
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def check_duplicate_by_name(self, filename: str) -> Tuple[bool, str]:
        """
        Aynı isimde dosya var mı kontrol et.

        Args:
            filename: Dosya adı

        Returns:
            (Duplicate olup olmadığı, Yerel dosya yolu)
        """
        local_path = self.local_storage_dir / filename
        if local_path.exists():
            return True, str(local_path)
        return False, str(local_path)

    def get_files_from_directory(self, directory_path: str) -> List[str]:
        """
        Klasördeki desteklenen dosyaları getir (recursive).

        Args:
            directory_path: Klasör yolu

        Returns:
            Desteklenen dosya yolları listesi
        """
        files = []
        directory = Path(directory_path)

        for file_path in directory.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                files.append(str(file_path))

        return files

    def copy_file_to_local(
        self, source_path: str, target_path: str, overwrite: bool = False
    ) -> bool:
        """
        Dosyayı yerel klasöre kopyala.

        Args:
            source_path: Kaynak dosya yolu
            target_path: Hedef dosya yolu
            overwrite: Üzerine yazma izni

        Returns:
            Kopyalama başarılı olup olmadığı
        """
        try:
            if Path(target_path).exists() and not overwrite:
                return False

            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            print(f"Dosya kopyalama hatası: {e}")
            return False

    def get_local_files(self) -> List[Path]:
        """
        Yerel klasördeki desteklenen dosyaları getir.

        Returns:
            Yerel dosya yolları listesi
        """
        return [
            f
            for f in self.local_storage_dir.glob("*")
            if f.is_file() and f.suffix.lower() in self.supported_formats
        ]

    def clear_local_files(self) -> bool:
        """
        Yerel klasördeki dosyaları temizle.

        Returns:
            Temizleme başarılı olup olmadığı
        """
        try:
            for file_path in self.local_storage_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            return True
        except Exception as e:
            print(f"Dosya temizleme hatası: {e}")
            return False

    def format_file_size(self, size_bytes: Union[int, float]) -> str:
        """
        Dosya boyutunu formatla.

        Args:
            size_bytes: Boyut (byte)

        Returns:
            Formatlanmış boyut string'i
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def is_supported_format(self, filepath: str) -> bool:
        """
        Dosya formatının desteklenip desteklenmediğini kontrol et.

        Args:
            filepath: Dosya yolu

        Returns:
            Desteklenip desteklenmediği
        """
        return Path(filepath).suffix.lower() in self.supported_formats

    def get_file_info(self, filepath: str) -> Tuple[str, int, str]:
        """
        Dosya bilgilerini getir.

        Args:
            filepath: Dosya yolu

        Returns:
            (Dosya adı, Boyut, Hash)
        """
        path = Path(filepath)
        filename = path.name
        file_size = path.stat().st_size
        file_hash = self.calculate_file_hash(filepath)
        return filename, file_size, file_hash
