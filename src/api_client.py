"""
API işlemleri için modül.

Bu modül dosya yükleme ve işleme API çağrılarını yönetir.
"""

import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class APIClient:
    """API işlemlerini yöneten sınıf."""

    def __init__(self, api_base_url: str, supported_formats: set):
        """
        APIClient'ı başlat.

        Args:
            api_base_url: API base URL'i
            supported_formats: Desteklenen dosya formatları
        """
        self.api_base_url = api_base_url
        self.supported_formats = supported_formats

    def upload_files_to_api(self, local_files: List[Path]) -> Dict[str, Any]:
        """
        Yerel klasördeki dosyaları API'ya yükle.

        Args:
            local_files: Yüklenecek dosya yolları

        Returns:
            API yanıtı
        """
        try:
            files = []
            total_size = 0

            if not local_files:
                return {"success": False, "error": "Yüklenecek dosya bulunamadı"}

            for file_path in local_files:
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.supported_formats
                ):
                    files.append(
                        (
                            "files",
                            (
                                file_path.name,
                                open(file_path, "rb"),
                                "application/octet-stream",
                            ),
                        )
                    )
                    total_size += file_path.stat().st_size

            if not files:
                return {
                    "success": False,
                    "error": "Desteklenen formatta dosya bulunamadı",
                }

            start_time = datetime.now()
            response = requests.post(
                f"{self.api_base_url}/embeddings/upload",
                files=files,
                timeout=300,  # 5 dakika timeout
            )

            # Dosyaları kapat
            for _, file_tuple in files:
                file_tuple[1].close()

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return {
                    "success": False,
                    "error": error_msg,
                }

        except requests.exceptions.Timeout:
            error_msg = "İstek zaman aşımına uğradı"
            return {"success": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "API sunucusuna bağlanılamadı"
            return {"success": False, "error": error_msg}
        except Exception as e:
            # Hata durumunda dosyaları kapat
            for _, file_tuple in files:
                if not file_tuple[1].closed:
                    file_tuple[1].close()
            error_msg = str(e)
            return {"success": False, "error": error_msg}

    def process_uploads_api(self, recursive: bool = True) -> Dict[str, Any]:
        """
        Yüklenen dosyaları işlemek için API'yı çağır.

        Args:
            recursive: Recursive işlem yapılıp yapılmayacağı

        Returns:
            API yanıtı
        """
        try:
            response = requests.post(
                f"{self.api_base_url}/embeddings/process-uploads",
                data={"recursive": recursive},
                timeout=600,  # 10 dakika timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return {
                    "success": False,
                    "error": error_msg,
                }
        except requests.exceptions.Timeout:
            error_msg = "İşlem zaman aşımına uğradı"
            return {"success": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "API sunucusuna bağlanılamadı"
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = str(e)
            return {"success": False, "error": error_msg}

    def test_connection(self) -> bool:
        """
        API bağlantısını test et.

        Returns:
            Bağlantı başarılı olup olmadığı
        """
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
