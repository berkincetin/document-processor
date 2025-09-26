import os
import hashlib
import json
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timedelta
from pathlib import Path
import threading
from typing import List, Dict, Any, Tuple
import sqlite3
import shutil
import csv
from collections import defaultdict


class DocumentUploadManager:
    def __init__(self):
        self.api_base_url = "http://10.1.1.172:3820"
        # self.api_base_url = "http://localhost:3820"
        self.local_storage_dir = Path("C:/Users/User/Desktop/DOCUMENTS")
        # self.local_storage_dir = Path("C:/Users/Polinity/Desktop/DOCUMENTS")

        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

        # Desteklenen formatlar
        self.supported_formats = {".pdf", ".docx", ".doc", ".txt", ".md"}

        # Veritabanı başlatma
        self.init_database()

        # GUI başlatma
        self.setup_gui()

        # Seçilen dosyalar listesi
        self.selected_files = []

        # Sıralama durumu
        self.sort_column = None
        self.sort_reverse = False

    def init_database(self):
        """SQLite veritabanını başlat - geliştirilmiş loglama"""
        self.db_path = "upload_logs.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ana log tablosu
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS upload_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_extension TEXT NOT NULL,
                selection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upload_start_time TIMESTAMP NULL,
                upload_end_time TIMESTAMP NULL,
                upload_duration_seconds REAL NULL,
                processing_start_time TIMESTAMP NULL,
                processing_end_time TIMESTAMP NULL,
                processing_duration_seconds REAL NULL,
                user_name TEXT NOT NULL,
                original_path TEXT NOT NULL,
                local_path TEXT NOT NULL,
                is_duplicate BOOLEAN DEFAULT FALSE,
                upload_status TEXT DEFAULT 'selected',
                processing_status TEXT DEFAULT 'not_processed',
                upload_error_message TEXT NULL,
                processing_error_message TEXT NULL,
                retry_count INTEGER DEFAULT 0,
                last_retry_time TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # API istatistikleri tablosu
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NULL,
                duration_seconds REAL NULL,
                file_count INTEGER DEFAULT 0,
                total_size_bytes INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                error_message TEXT NULL,
                user_name TEXT NOT NULL
            )
        """
        )

        # Mevcut tabloyu güncelle (yeni kolonlar ekle)
        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN file_extension TEXT DEFAULT ''"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN upload_start_time TIMESTAMP NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN upload_end_time TIMESTAMP NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN upload_duration_seconds REAL NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN processing_start_time TIMESTAMP NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN processing_end_time TIMESTAMP NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN processing_duration_seconds REAL NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN upload_error_message TEXT NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN processing_error_message TEXT NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN retry_count INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN last_retry_time TIMESTAMP NULL"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE upload_logs ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

    def calculate_file_hash(self, filepath: str) -> str:
        """Dosyanın MD5 hash'ini hesapla"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def check_duplicate_by_name(self, filename: str) -> Tuple[bool, str]:
        """Aynı isimde dosya var mı kontrol et"""
        local_path = self.local_storage_dir / filename
        if local_path.exists():
            return True, str(local_path)
        return False, str(local_path)

    def check_duplicate_by_hash(self, file_hash: str) -> bool:
        """Aynı hash'e sahip dosya daha önce yüklendi mi kontrol et"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM upload_logs WHERE file_hash = ?", (file_hash,)
        )
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def get_files_from_directory(self, directory_path: str) -> List[str]:
        """Klasördeki desteklenen dosyaları getir (recursive)"""
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
        """Dosyayı yerel klasöre kopyala"""
        try:
            if Path(target_path).exists() and not overwrite:
                return False

            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            print(f"Dosya kopyalama hatası: {e}")
            return False

    def log_file_selection(
        self,
        filename: str,
        file_hash: str,
        file_size: int,
        user_name: str,
        original_path: str,
        local_path: str,
        is_duplicate: bool,
    ) -> int:
        """Dosya seçimini veritabanına kaydet - geliştirilmiş"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        file_extension = Path(filename).suffix.lower()

        cursor.execute(
            """
            INSERT INTO upload_logs 
            (filename, file_hash, file_size, file_extension, user_name, original_path, local_path, is_duplicate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filename,
                file_hash,
                file_size,
                file_extension,
                user_name,
                original_path,
                local_path,
                is_duplicate,
            ),
        )

        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id

    def log_api_operation(
        self,
        operation_type: str,
        user_name: str,
        file_count: int = 0,
        total_size: int = 0,
    ) -> int:
        """API operasyonu logla"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO api_stats 
            (operation_type, start_time, file_count, total_size_bytes, user_name)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                operation_type,
                datetime.now().isoformat(),
                file_count,
                total_size,
                user_name,
            ),
        )

        operation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return operation_id

    def update_api_operation(
        self,
        operation_id: int,
        success_count: int,
        error_count: int,
        error_message: str = None,
    ):
        """API operasyonu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        end_time = datetime.now().isoformat()

        # Duration hesapla
        cursor.execute("SELECT start_time FROM api_stats WHERE id = ?", (operation_id,))
        start_time_str = cursor.fetchone()[0]
        start_time = datetime.fromisoformat(start_time_str)
        duration = (datetime.now() - start_time).total_seconds()

        cursor.execute(
            """
            UPDATE api_stats 
            SET end_time = ?, duration_seconds = ?, success_count = ?, error_count = ?, error_message = ?
            WHERE id = ?
        """,
            (
                end_time,
                duration,
                success_count,
                error_count,
                error_message,
                operation_id,
            ),
        )

        conn.commit()
        conn.close()

    def update_upload_status(
        self,
        file_id: int,
        status: str,
        error_message: str = None,
        start_time: datetime = None,
    ):
        """Upload durumunu güncelle - geliştirilmiş"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = datetime.now().isoformat()

        if status == "uploading" and start_time:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, upload_start_time = ?, updated_at = ?
                WHERE id = ?
            """,
                (status, start_time.isoformat(), current_time, file_id),
            )
        elif status == "uploaded":
            # Duration hesapla
            cursor.execute(
                "SELECT upload_start_time FROM upload_logs WHERE id = ?", (file_id,)
            )
            start_time_str = cursor.fetchone()[0]
            duration = None
            if start_time_str:
                start_time_obj = datetime.fromisoformat(start_time_str)
                duration = (datetime.now() - start_time_obj).total_seconds()

            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, upload_end_time = ?, upload_duration_seconds = ?, updated_at = ?
                WHERE id = ?
            """,
                (status, current_time, duration, current_time, file_id),
            )
        elif status == "upload_failed":
            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, upload_end_time = ?, upload_error_message = ?, 
                    retry_count = retry_count + 1, last_retry_time = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    status,
                    current_time,
                    error_message,
                    current_time,
                    current_time,
                    file_id,
                ),
            )
        else:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, updated_at = ?
                WHERE id = ?
            """,
                (status, current_time, file_id),
            )

        conn.commit()
        conn.close()

    def update_processing_status(self, status: str, error_message: str = None):
        """Tüm yüklenen dosyaların işleme durumunu güncelle - geliştirilmiş"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = datetime.now().isoformat()

        if status == "processing":
            cursor.execute(
                """
                UPDATE upload_logs 
                SET processing_status = ?, processing_start_time = ?, updated_at = ?
                WHERE upload_status = 'uploaded' AND processing_status = 'not_processed'
            """,
                (status, current_time, current_time),
            )
        elif status == "completed":
            # Duration hesapla
            cursor.execute(
                "SELECT id, processing_start_time FROM upload_logs WHERE processing_status = 'processing'"
            )
            for row in cursor.fetchall():
                file_id, start_time_str = row
                duration = None
                if start_time_str:
                    start_time_obj = datetime.fromisoformat(start_time_str)
                    duration = (datetime.now() - start_time_obj).total_seconds()

                cursor.execute(
                    """
                    UPDATE upload_logs 
                    SET processing_status = ?, processing_end_time = ?, processing_duration_seconds = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (status, current_time, duration, current_time, file_id),
                )
        elif status == "failed":
            cursor.execute(
                """
                UPDATE upload_logs 
                SET processing_status = ?, processing_end_time = ?, processing_error_message = ?, 
                    retry_count = retry_count + 1, last_retry_time = ?, updated_at = ?
                WHERE processing_status = 'processing'
            """,
                (status, current_time, error_message, current_time, current_time),
            )

        conn.commit()
        conn.close()

    def upload_files_to_api(self) -> Dict[str, Any]:
        """Yerel klasördeki dosyaları API'ya yükle - geliştirilmiş loglama"""
        try:
            files = []
            local_files = list(self.local_storage_dir.glob("*"))
            total_size = 0

            if not local_files:
                return {"success": False, "error": "Yüklenecek dosya bulunamadı"}

            # API operasyonu başlat
            user_name = self.user_name_var.get().strip()

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

            # API operasyonu logla
            operation_id = self.log_api_operation(
                "upload", user_name, len(files), total_size
            )

            # Dosya durumlarını güncelle
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE upload_logs SET upload_status = 'uploading' WHERE upload_status = 'selected'"
            )
            conn.commit()
            conn.close()

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
                # Başarılı upload
                self.update_api_operation(operation_id, len(files), 0)
                return response.json()
            else:
                # Hatalı upload
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.update_api_operation(operation_id, 0, len(files), error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                }

        except requests.exceptions.Timeout:
            error_msg = "İstek zaman aşımına uğradı"
            self.update_api_operation(operation_id, 0, len(files), error_msg)
            return {"success": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "API sunucusuna bağlanılamadı"
            self.update_api_operation(operation_id, 0, len(files), error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            # Hata durumunda dosyaları kapat
            for _, file_tuple in files:
                if not file_tuple[1].closed:
                    file_tuple[1].close()
            error_msg = str(e)
            self.update_api_operation(operation_id, 0, len(files), error_msg)
            return {"success": False, "error": error_msg}

    def process_uploads_api(self, recursive: bool = True) -> Dict[str, Any]:
        """Yüklenen dosyaları işlemek için API'yı çağır - geliştirilmiş loglama"""
        try:
            # API operasyonu başlat
            user_name = self.user_name_var.get().strip()

            # İşlenecek dosya sayısını al
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM upload_logs WHERE upload_status = 'uploaded'"
            )
            file_count = cursor.fetchone()[0]
            conn.close()

            operation_id = self.log_api_operation("process", user_name, file_count)

            # Processing durumunu güncelle
            self.update_processing_status("processing")

            response = requests.post(
                f"{self.api_base_url}/embeddings/process-uploads",
                data={"recursive": recursive},
                timeout=600,  # 10 dakika timeout
            )

            if response.status_code == 200:
                # Başarılı processing
                self.update_api_operation(operation_id, file_count, 0)
                return response.json()
            else:
                # Hatalı processing
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.update_api_operation(operation_id, 0, file_count, error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                }
        except requests.exceptions.Timeout:
            error_msg = "İşlem zaman aşımına uğradı"
            self.update_api_operation(operation_id, 0, file_count, error_msg)
            return {"success": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "API sunucusuna bağlanılamadı"
            self.update_api_operation(operation_id, 0, file_count, error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = str(e)
            self.update_api_operation(operation_id, 0, file_count, error_msg)
            return {"success": False, "error": error_msg}

    def setup_gui(self):
        """GUI'yi oluştur - geliştirilmiş"""
        self.root = tk.Tk()
        self.root.title("Document Upload Manager - Enhanced")
        self.root.geometry("1400x800")

        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Üst panel - Kullanıcı bilgileri ve kontroller
        top_frame = ttk.LabelFrame(
            main_frame, text="Dosya Seçimi ve Yükleme", padding="10"
        )
        top_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Kullanıcı adı girişi
        ttk.Label(top_frame, text="Kullanıcı Adı:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.user_name_var = tk.StringVar(value="Kullanıcı1")
        ttk.Entry(top_frame, textvariable=self.user_name_var, width=20).grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0)
        )

        # Dosya/Klasör seçme butonları
        ttk.Button(top_frame, text="Dosya Seç", command=self.select_files).grid(
            row=0, column=2, padx=10, pady=5
        )
        ttk.Button(top_frame, text="Klasör Seç", command=self.select_folder).grid(
            row=0, column=3, padx=5, pady=5
        )

        # Desteklenen formatlar bilgisi
        formats_text = "Desteklenen formatlar: " + ", ".join(self.supported_formats)
        ttk.Label(top_frame, text=formats_text, font=("TkDefaultFont", 8)).grid(
            row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0)
        )

        # Yerel klasör bilgisi
        ttk.Label(
            top_frame,
            text=f"Yerel klasör: {self.local_storage_dir}",
            font=("TkDefaultFont", 8),
        ).grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(2, 0))

        # Orta panel - İşlem butonları
        action_frame = ttk.LabelFrame(main_frame, text="İşlemler", padding="10")
        action_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Seçilen dosya sayısı
        self.selected_count_var = tk.StringVar(value="Seçilen dosya: 0")
        ttk.Label(action_frame, textvariable=self.selected_count_var).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        # İşlem butonları
        button_subframe = ttk.Frame(action_frame)
        button_subframe.grid(row=1, column=0, columnspan=3, pady=5)

        self.upload_button = ttk.Button(
            button_subframe,
            text="1. Dosyaları API'ya Yükle",
            command=self.upload_files,
            state="disabled",
        )
        self.upload_button.pack(side=tk.LEFT, padx=5)

        self.process_button = ttk.Button(
            button_subframe,
            text="2. Embedding İşle",
            command=self.process_embeddings,
            state="disabled",
        )
        self.process_button.pack(side=tk.LEFT, padx=5)

        # Rapor butonları
        report_subframe = ttk.Frame(action_frame)
        report_subframe.grid(row=2, column=0, columnspan=3, pady=5)

        ttk.Button(
            report_subframe, text="Detay Rapor", command=self.generate_detail_report
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            report_subframe, text="Özet Rapor", command=self.generate_summary_report
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            report_subframe, text="API İstatistikleri", command=self.show_api_stats
        ).pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(action_frame, mode="indeterminate")
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Sol panel - Filtreler
        filter_frame = ttk.LabelFrame(
            main_frame, text="Filtreler ve Sıralama", padding="10"
        )
        filter_frame.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10), padx=(0, 5)
        )

        # Durum filtresi
        ttk.Label(filter_frame, text="Durum:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.status_filter = ttk.Combobox(
            filter_frame,
            values=[
                "Tümü",
                "SELECTED",
                "UPLOADED",
                "PROCESSED",
                "DUPLICATE",
                "UP_FAILED",
                "PROC_FAILED",
            ],
            width=12,
        )
        self.status_filter.set("Tümü")
        self.status_filter.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        self.status_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Kullanıcı filtresi
        ttk.Label(filter_frame, text="Kullanıcı:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.user_filter = ttk.Combobox(filter_frame, width=12)
        self.user_filter.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        self.user_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Tarih filtresi
        ttk.Label(filter_frame, text="Son:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.date_filter = ttk.Combobox(
            filter_frame,
            values=["Tümü", "Son 1 saat", "Son 24 saat", "Son 7 gün", "Son 30 gün"],
            width=12,
        )
        self.date_filter.set("Tümü")
        self.date_filter.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
        self.date_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Format filtresi
        ttk.Label(filter_frame, text="Format:").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        format_values = ["Tümü"] + list(self.supported_formats)
        self.format_filter = ttk.Combobox(filter_frame, values=format_values, width=12)
        self.format_filter.set("Tümü")
        self.format_filter.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=2)
        self.format_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Sağ panel - Log görüntüleme
        log_frame = ttk.LabelFrame(main_frame, text="Dosya Logları", padding="10")
        log_frame.grid(
            row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )

        # Treeview için frame
        tree_frame = ttk.Frame(log_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Treeview ve scrollbar - genişletilmiş kolonlar
        columns = (
            "Dosya",
            "Format",
            "Boyut",
            "Kullanıcı",
            "Seçim",
            "Yükleme",
            "Y.Süre",
            "İşleme",
            "İ.Süre",
            "Durum",
            "Hata",
        )
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=15
        )

        # Kolon başlıkları ve genişlikleri
        column_widths = {
            "Dosya": 150,
            "Format": 60,
            "Boyut": 80,
            "Kullanıcı": 80,
            "Seçim": 120,
            "Yükleme": 120,
            "Y.Süre": 60,
            "İşleme": 120,
            "İ.Süre": 60,
            "Durum": 100,
            "Hata": 200,
        }

        for col in columns:
            self.tree.heading(
                col, text=col, command=lambda c=col: self.sort_treeview(c)
            )
            self.tree.column(col, width=column_widths[col])

        # Scrollbar
        v_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Log butonları
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, pady=10)

        ttk.Button(
            log_button_frame, text="Logları Yenile", command=self.refresh_logs
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            log_button_frame, text="Logları Temizle", command=self.clear_logs
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_button_frame, text="Export JSON", command=self.export_logs).pack(
            side=tk.LEFT, padx=5
        )

        # Grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        top_frame.columnconfigure(3, weight=1)
        action_frame.columnconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        filter_frame.columnconfigure(0, weight=1)

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # İlk log yüklemesi
        self.refresh_logs()
        self.update_user_filter()

    def sort_treeview(self, col):
        """Treeview kolonuna göre sırala"""
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        # Verileri al ve sırala
        data = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            data.append((child, values))

        # Sıralama fonksiyonu
        def sort_key(item):
            value = item[1][columns.index(col)]
            # Sayısal değerler için özel işleme
            if col in ["Boyut", "Y.Süre", "İ.Süre"]:
                try:
                    # Boyut için MB/KB değerlerini parse et
                    if col == "Boyut":
                        if "MB" in str(value):
                            return (
                                float(str(value).replace("MB", "").strip())
                                * 1024
                                * 1024
                            )
                        elif "KB" in str(value):
                            return float(str(value).replace("KB", "").strip()) * 1024
                        else:
                            return float(str(value).replace("B", "").strip() or 0)
                    else:
                        return float(str(value).replace("s", "").strip() or 0)
                except:
                    return 0
            # Tarih değerleri için
            elif col in ["Seçim", "Yükleme", "İşleme"]:
                try:
                    if value:
                        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
                    else:
                        return datetime.min
                except:
                    return datetime.min
            else:
                return str(value)

        data.sort(key=sort_key, reverse=self.sort_reverse)

        # Sıralanmış verileri yeniden ekle
        for index, (child, values) in enumerate(data):
            self.tree.move(child, "", index)

        # Kolon başlığını güncelle
        for c in columns:
            if c == col:
                direction = "↓" if self.sort_reverse else "↑"
                self.tree.heading(c, text=f"{c} {direction}")
            else:
                self.tree.heading(c, text=c)

    def apply_filters(self, event=None):
        """Filtreleri uygula"""
        self.refresh_logs()

    def update_user_filter(self):
        """Kullanıcı filtresini güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_name FROM upload_logs ORDER BY user_name")
        users = ["Tümü"] + [row[0] for row in cursor.fetchall()]
        self.user_filter["values"] = users
        if not self.user_filter.get():
            self.user_filter.set("Tümü")
        conn.close()

    def format_file_size(self, size_bytes):
        """Dosya boyutunu formatla"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def format_duration(self, seconds):
        """Süreyi formatla"""
        if seconds is None:
            return ""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"

    def get_filtered_query(self):
        """Filtreli sorgu oluştur"""
        base_query = """
            SELECT filename, file_extension, file_size, user_name, selection_time, 
                   upload_end_time, upload_duration_seconds, processing_end_time, 
                   processing_duration_seconds, upload_status, processing_status, 
                   is_duplicate, upload_error_message, processing_error_message
            FROM upload_logs 
            WHERE 1=1
        """

        conditions = []
        params = []

        # Durum filtresi
        status_filter = self.status_filter.get()
        if status_filter != "Tümü":
            if status_filter == "SELECTED":
                conditions.append("upload_status = 'selected'")
            elif status_filter == "UPLOADED":
                conditions.append("upload_status = 'uploaded'")
            elif status_filter == "PROCESSED":
                conditions.append("processing_status = 'completed'")
            elif status_filter == "DUPLICATE":
                conditions.append("is_duplicate = 1")
            elif status_filter == "UP_FAILED":
                conditions.append("upload_status = 'upload_failed'")
            elif status_filter == "PROC_FAILED":
                conditions.append("processing_status = 'failed'")

        # Kullanıcı filtresi
        user_filter = self.user_filter.get()
        if user_filter and user_filter != "Tümü":
            conditions.append("user_name = ?")
            params.append(user_filter)

        # Tarih filtresi
        date_filter = self.date_filter.get()
        if date_filter != "Tümü":
            now = datetime.now()
            if date_filter == "Son 1 saat":
                cutoff = now - timedelta(hours=1)
            elif date_filter == "Son 24 saat":
                cutoff = now - timedelta(hours=24)
            elif date_filter == "Son 7 gün":
                cutoff = now - timedelta(days=7)
            elif date_filter == "Son 30 gün":
                cutoff = now - timedelta(days=30)

            conditions.append("selection_time >= ?")
            params.append(cutoff.isoformat())

        # Format filtresi
        format_filter = self.format_filter.get()
        if format_filter and format_filter != "Tümü":
            conditions.append("file_extension = ?")
            params.append(format_filter)

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY selection_time DESC"

        return base_query, params

    def select_files(self):
        """Dosya seçme dialog'u"""
        filepaths = filedialog.askopenfilenames(
            title="Yüklenecek dosyaları seçin",
            filetypes=[
                ("Desteklenen Dosyalar", "*.pdf;*.docx;*.doc;*.txt;*.md"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx;*.doc"),
                ("Text", "*.txt"),
                ("Markdown", "*.md"),
                ("Tüm Dosyalar", "*.*"),
            ],
        )

        if filepaths:
            self.process_selected_files(list(filepaths))

    def select_folder(self):
        """Klasör seçme dialog'u"""
        folder_path = filedialog.askdirectory(title="Dosya klasörünü seçin")

        if folder_path:
            files = self.get_files_from_directory(folder_path)
            if files:
                self.process_selected_files(files)
            else:
                messagebox.showinfo(
                    "Bilgi",
                    f"Seçilen klasörde desteklenen format bulunamadı.\nDesteklenen formatlar: {', '.join(self.supported_formats)}",
                )

    def process_selected_files(self, filepaths: List[str]):
        """Seçilen dosyaları işle"""
        user_name = self.user_name_var.get().strip()
        if not user_name:
            messagebox.showerror("Hata", "Kullanıcı adı girmeniz gerekiyor!")
            return

        self.selected_files = []
        conflicts = []

        for filepath in filepaths:
            filename = Path(filepath).name

            # Format kontrolü
            if Path(filepath).suffix.lower() not in self.supported_formats:
                continue

            # Dosya çakışması kontrolü
            is_duplicate, local_path = self.check_duplicate_by_name(filename)

            if is_duplicate:
                conflicts.append((filepath, local_path, filename))
            else:
                # Dosyayı yerel klasöre kopyala
                if self.copy_file_to_local(filepath, local_path):
                    self.selected_files.append((filepath, local_path, filename, False))

        # Çakışmaları çöz
        if conflicts:
            self.handle_file_conflicts(conflicts, user_name)

        # Başarılı dosyaları veritabanına kaydet
        self.save_selected_files(user_name)

        # GUI'yi güncelle
        self.update_file_count()
        self.refresh_logs()
        self.update_user_filter()

    def handle_file_conflicts(
        self, conflicts: List[Tuple[str, str, str]], user_name: str
    ):
        """Dosya çakışmalarını çöz"""
        for original_path, local_path, filename in conflicts:
            response = messagebox.askyesnocancel(
                "Dosya Çakışması",
                f"'{filename}' dosyası zaten mevcut.\n\nÜzerine yazmak istiyor musunuz?\n\nEvet: Üzerine yaz\nHayır: Atla\nİptal: İşlemi durdur",
            )

            if response is None:  # İptal
                break
            elif response:  # Evet - üzerine yaz
                if self.copy_file_to_local(original_path, local_path, overwrite=True):
                    self.selected_files.append(
                        (original_path, local_path, filename, True)
                    )
            # Hayır durumunda hiçbir şey yapma (atla)

    def save_selected_files(self, user_name: str):
        """Seçilen dosyaları veritabanına kaydet"""
        for original_path, local_path, filename, is_duplicate in self.selected_files:
            # Dosya bilgilerini al
            file_size = Path(local_path).stat().st_size
            file_hash = self.calculate_file_hash(local_path)

            # Hash bazlı duplicate kontrolü
            hash_duplicate = self.check_duplicate_by_hash(file_hash)

            # Veritabanına kaydet
            self.log_file_selection(
                filename,
                file_hash,
                file_size,
                user_name,
                original_path,
                local_path,
                hash_duplicate or is_duplicate,
            )

    def update_file_count(self):
        """Seçilen dosya sayısını güncelle"""
        local_files = [
            f
            for f in self.local_storage_dir.glob("*")
            if f.is_file() and f.suffix.lower() in self.supported_formats
        ]
        count = len(local_files)
        self.selected_count_var.set(f"Yerel klasördeki dosya sayısı: {count}")

        # Buton durumlarını güncelle
        self.upload_button.config(state="normal" if count > 0 else "disabled")

    def upload_files(self):
        """Dosyaları API'ya yükle"""
        self.progress.start()
        self.upload_button.config(state="disabled")

        thread = threading.Thread(target=self.upload_thread)
        thread.daemon = True
        thread.start()

    def upload_thread(self):
        """Yükleme işlemini thread'de çalıştır"""
        try:
            result = self.upload_files_to_api()
            self.root.after(0, self.upload_complete, result)
        except Exception as e:
            self.root.after(
                0, self.upload_complete, {"success": False, "error": str(e)}
            )

    def upload_complete(self, result: Dict[str, Any]):
        """Yükleme tamamlandığında çağrılan fonksiyon"""
        self.progress.stop()
        self.upload_button.config(state="normal")

        if result["success"]:
            messagebox.showinfo("Başarılı", "Dosyalar API'ya başarıyla yüklendi!")

            # Veritabanındaki upload durumlarını güncelle
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE upload_logs SET upload_status = 'uploaded' WHERE upload_status = 'uploading'"
            )
            conn.commit()
            conn.close()

            # Process butonunu etkinleştir
            self.process_button.config(state="normal")
        else:
            messagebox.showerror("Hata", f"Yükleme hatası: {result['error']}")

            # Hatalı durumları güncelle
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE upload_logs SET upload_status = 'upload_failed', upload_error_message = ? WHERE upload_status = 'uploading'",
                (result["error"],),
            )
            conn.commit()
            conn.close()

        self.refresh_logs()

    def process_embeddings(self):
        """Embeddings işlemini başlat"""
        self.progress.start()
        self.process_button.config(state="disabled")

        thread = threading.Thread(target=self.process_thread)
        thread.daemon = True
        thread.start()

    def process_thread(self):
        """İşleme thread'i"""
        try:
            result = self.process_uploads_api()
            self.root.after(0, self.process_complete, result)
        except Exception as e:
            self.root.after(
                0, self.process_complete, {"success": False, "error": str(e)}
            )

    def process_complete(self, result: Dict[str, Any]):
        """İşleme tamamlandığında çağrılan fonksiyon"""
        self.progress.stop()
        self.process_button.config(state="normal")

        if result["success"]:
            messagebox.showinfo("Başarılı", "Embedding işlemi tamamlandı!")
            self.update_processing_status("completed")
        else:
            messagebox.showerror("Hata", f"İşleme hatası: {result['error']}")
            self.update_processing_status("failed", result["error"])

        self.refresh_logs()

    def clear_local_files(self):
        """Yerel klasördeki dosyaları temizle"""
        if messagebox.askyesno(
            "Onay", "Yerel klasördeki tüm dosyaları silmek istediğinizden emin misiniz?"
        ):
            try:
                for file_path in self.local_storage_dir.glob("*"):
                    if file_path.is_file():
                        file_path.unlink()

                self.update_file_count()
                self.process_button.config(state="disabled")
                messagebox.showinfo("Başarılı", "Yerel dosyalar temizlendi")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya temizleme hatası: {str(e)}")

    def refresh_logs(self):
        """Logları veritabanından yenile - filtreli"""
        # Mevcut kayıtları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filtrelenmiş sorgu al
        query, params = self.get_filtered_query()

        # Veritabanından logları al
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)

        columns = (
            "Dosya",
            "Format",
            "Boyut",
            "Kullanıcı",
            "Seçim",
            "Yükleme",
            "Y.Süre",
            "İşleme",
            "İ.Süre",
            "Durum",
            "Hata",
        )

        for row in cursor.fetchall():
            (
                filename,
                file_extension,
                file_size,
                user_name,
                selection_time,
                upload_end_time,
                upload_duration,
                processing_end_time,
                processing_duration,
                upload_status,
                processing_status,
                is_duplicate,
                upload_error,
                processing_error,
            ) = row

            # Durumu belirle
            if is_duplicate:
                status = "DUPLICATE"
            elif processing_status == "completed":
                status = "PROCESSED"
            elif processing_status == "failed":
                status = "PROC_FAILED"
            elif upload_status == "uploaded":
                status = "UPLOADED"
            elif upload_status == "upload_failed":
                status = "UP_FAILED"
            elif upload_status == "uploading":
                status = "UPLOADING"
            elif processing_status == "processing":
                status = "PROCESSING"
            else:
                status = "SELECTED"

            # Tarih formatları
            sel_time = selection_time.split(".")[0] if selection_time else ""
            up_time = upload_end_time.split(".")[0] if upload_end_time else ""
            proc_time = processing_end_time.split(".")[0] if processing_end_time else ""

            # Süreleri formatla
            up_dur = self.format_duration(upload_duration) if upload_duration else ""
            proc_dur = (
                self.format_duration(processing_duration) if processing_duration else ""
            )

            # Hata mesajı
            error_msg = upload_error or processing_error or ""
            if error_msg and len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."

            self.tree.insert(
                "",
                "end",
                values=(
                    filename,
                    file_extension,
                    self.format_file_size(file_size),
                    user_name,
                    sel_time,
                    up_time,
                    up_dur,
                    proc_time,
                    proc_dur,
                    status,
                    error_msg,
                ),
            )

        conn.close()
        self.update_file_count()

    def clear_logs(self):
        """Logları temizle"""
        if messagebox.askyesno(
            "Onay", "Tüm logları silmek istediğinizden emin misiniz?"
        ):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM upload_logs")
            cursor.execute("DELETE FROM api_stats")
            conn.commit()
            conn.close()

            self.refresh_logs()
            self.update_user_filter()
            messagebox.showinfo("Başarılı", "Loglar temizlendi")

    def export_logs(self):
        """Logları JSON formatında export et"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tüm Dosyalar", "*.*")],
            title="Logları export et",
        )

        if filepath:
            query, params = self.get_filtered_query()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(query.replace("SELECT filename,", "SELECT *,"), params)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            conn.close()
            messagebox.showinfo(
                "Başarılı", f"Loglar {filepath} dosyasına export edildi"
            )

    def generate_detail_report(self):
        """Detaylı rapor oluştur"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("CSV", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Detaylı rapor kaydet",
        )

        if not filepath:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tüm verileri al
        cursor.execute(
            """
            SELECT * FROM upload_logs 
            ORDER BY selection_time DESC
        """
        )

        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        conn.close()

        if filepath.endswith(".csv"):
            self._generate_csv_report(filepath, columns, data)
        else:
            self._generate_html_detail_report(filepath, columns, data)

    def _generate_csv_report(self, filepath, columns, data):
        """CSV rapor oluştur"""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                writer.writerows(data)

            messagebox.showinfo(
                "Başarılı", f"CSV raporu {filepath} dosyasına kaydedildi"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"CSV raporu oluşturulamadı: {str(e)}")

    def _generate_html_detail_report(self, filepath, columns, data):
        """HTML detay rapor oluştur"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Upload Manager - Detaylı Rapor</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .status-processed {{ color: green; font-weight: bold; }}
        .status-failed {{ color: red; font-weight: bold; }}
        .status-uploaded {{ color: blue; }}
        .status-duplicate {{ color: orange; }}
        .error {{ color: red; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Document Upload Manager - Detaylı Rapor</h1>
    <p>Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    <p>Toplam Kayıt Sayısı: {len(data)}</p>
    
    <table>
        <thead>
            <tr>
                {''.join(f'<th>{col}</th>' for col in columns)}
            </tr>
        </thead>
        <tbody>
"""

            for row in data:
                html_content += "<tr>"
                for i, cell in enumerate(row):
                    if columns[i] in ["upload_status", "processing_status"]:
                        css_class = ""
                        if cell == "completed":
                            css_class = "status-processed"
                        elif "failed" in str(cell):
                            css_class = "status-failed"
                        elif cell == "uploaded":
                            css_class = "status-uploaded"
                        elif cell == "duplicate":
                            css_class = "status-duplicate"

                        html_content += f'<td class="{css_class}">{cell or ""}</td>'
                    elif "error" in columns[i]:
                        html_content += f'<td class="error">{cell or ""}</td>'
                    elif "duration" in columns[i] and cell:
                        html_content += f"<td>{self.format_duration(cell)}</td>"
                    elif "size" in columns[i] and cell:
                        html_content += f"<td>{self.format_file_size(cell)}</td>"
                    else:
                        html_content += f'<td>{cell or ""}</td>'
                html_content += "</tr>"

            html_content += """
        </tbody>
    </table>
</body>
</html>
"""

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            messagebox.showinfo(
                "Başarılı", f"Detaylı rapor {filepath} dosyasına kaydedildi"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"HTML raporu oluşturulamadı: {str(e)}")

    def generate_summary_report(self):
        """Özet rapor oluştur"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Tüm Dosyalar", "*.*")],
            title="Özet rapor kaydet",
        )

        if not filepath:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # İstatistikleri hesapla
        stats = {}

        # Toplam dosya sayısı
        cursor.execute("SELECT COUNT(*) FROM upload_logs")
        stats["total_files"] = cursor.fetchone()[0]

        # Durum bazlı sayılar
        cursor.execute(
            """
            SELECT 
                upload_status,
                processing_status,
                COUNT(*) as count
            FROM upload_logs
            GROUP BY upload_status, processing_status
        """
        )

        status_counts = defaultdict(int)
        for upload_status, processing_status, count in cursor.fetchall():
            if processing_status == "completed":
                status_counts["processed"] += count
            elif processing_status == "failed":
                status_counts["proc_failed"] += count
            elif upload_status == "uploaded":
                status_counts["uploaded"] += count
            elif upload_status == "upload_failed":
                status_counts["upload_failed"] += count
            else:
                status_counts["selected"] += count

        # Duplicate sayısı
        cursor.execute("SELECT COUNT(*) FROM upload_logs WHERE is_duplicate = 1")
        status_counts["duplicates"] = cursor.fetchone()[0]

        # Kullanıcı bazlı istatistikler
        cursor.execute(
            """
            SELECT 
                user_name,
                COUNT(*) as total,
                SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as processed,
                SUM(file_size) as total_size
            FROM upload_logs
            GROUP BY user_name
            ORDER BY total DESC
        """
        )
        user_stats = cursor.fetchall()

        # Format bazlı istatistikler
        cursor.execute(
            """
            SELECT 
                file_extension,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(upload_duration_seconds) as avg_upload_time,
                AVG(processing_duration_seconds) as avg_processing_time
            FROM upload_logs
            WHERE file_extension IS NOT NULL AND file_extension != ''
            GROUP BY file_extension
            ORDER BY count DESC
        """
        )
        format_stats = cursor.fetchall()

        # Zaman bazlı istatistikler
        cursor.execute(
            """
            SELECT 
                DATE(selection_time) as date,
                COUNT(*) as count
            FROM upload_logs
            WHERE selection_time IS NOT NULL
            GROUP BY DATE(selection_time)
            ORDER BY date DESC
            LIMIT 30
        """
        )
        daily_stats = cursor.fetchall()

        conn.close()

        # HTML rapor oluştur
        self._generate_html_summary_report(
            filepath, stats, status_counts, user_stats, format_stats, daily_stats
        )

    def _generate_html_summary_report(
        self, filepath, stats, status_counts, user_stats, format_stats, daily_stats
    ):
        """HTML özet rapor oluştur"""
        try:
            total_processed = status_counts["processed"]
            total_failed = status_counts["upload_failed"] + status_counts["proc_failed"]
            success_rate = (
                (total_processed / stats["total_files"] * 100)
                if stats["total_files"] > 0
                else 0
            )

            html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Upload Manager - Özet Rapor</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        h2 {{ color: #555; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .warning {{ color: #FF9800; font-weight: bold; }}
        .error {{ color: #f44336; font-weight: bold; }}
        .chart-container {{ margin: 20px 0; }}
        .progress-bar {{ background-color: #ddd; border-radius: 10px; overflow: hidden; height: 20px; }}
        .progress-fill {{ height: 100%; background-color: #4CAF50; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Document Upload Manager - Özet Rapor</h1>
        <p style="text-align: center; color: #666;">Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        
        <h2>🎯 Genel İstatistikler</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['total_files']}</div>
                <div class="stat-label">Toplam Dosya</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{status_counts['processed']}</div>
                <div class="stat-label">İşlenmiş Dosya</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{status_counts['uploaded']}</div>
                <div class="stat-label">Yüklenmiş (Bekleyen)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{total_failed}</div>
                <div class="stat-label">Başarısız</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{status_counts['duplicates']}</div>
                <div class="stat-label">Tekrarlanan</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #2196F3;">{success_rate:.1f}%</div>
                <div class="stat-label">Başarı Oranı</div>
            </div>
        </div>
        
        <h2>📈 Başarı Oranı</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {success_rate}%;"></div>
        </div>
        <p style="text-align: center; margin-top: 10px;">Başarı Oranı: {success_rate:.1f}% ({status_counts['processed']}/{stats['total_files']} dosya)</p>
        
        <h2>👥 Kullanıcı Bazlı İstatistikler</h2>
        <table>
            <thead>
                <tr>
                    <th>Kullanıcı</th>
                    <th>Toplam Dosya</th>
                    <th>İşlenmiş</th>
                    <th>Başarı Oranı</th>
                    <th>Toplam Boyut</th>
                </tr>
            </thead>
            <tbody>"""

            for user_name, total, processed, total_size in user_stats:
                success_rate_user = (processed / total * 100) if total > 0 else 0
                size_formatted = self.format_file_size(total_size or 0)

                html_content += f"""
                <tr>
                    <td>{user_name}</td>
                    <td>{total}</td>
                    <td class="success">{processed}</td>
                    <td>{'<span class="success">' if success_rate_user >= 80 else '<span class="warning"' if success_rate_user >= 50 else '<span class="error"'}{success_rate_user:.1f}%</span></td>
                    <td>{size_formatted}</td>
                </tr>"""

            html_content += """
            </tbody>
        </table>
        
        <h2>📁 Format Bazlı İstatistikler</h2>
        <table>
            <thead>
                <tr>
                    <th>Format</th>
                    <th>Dosya Sayısı</th>
                    <th>Toplam Boyut</th>
                    <th>Ort. Yükleme Süresi</th>
                    <th>Ort. İşleme Süresi</th>
                </tr>
            </thead>
            <tbody>"""

            for ext, count, total_size, avg_upload, avg_processing in format_stats:
                size_formatted = self.format_file_size(total_size or 0)
                upload_time = self.format_duration(avg_upload) if avg_upload else "N/A"
                proc_time = (
                    self.format_duration(avg_processing) if avg_processing else "N/A"
                )

                html_content += f"""
                <tr>
                    <td><strong>{ext.upper()}</strong></td>
                    <td>{count}</td>
                    <td>{size_formatted}</td>
                    <td>{upload_time}</td>
                    <td>{proc_time}</td>
                </tr>"""

            html_content += """
            </tbody>
        </table>
        
        <h2>📅 Günlük Aktivite (Son 30 Gün)</h2>
        <table>
            <thead>
                <tr>
                    <th>Tarih</th>
                    <th>Dosya Sayısı</th>
                    <th>Aktivite</th>
                </tr>
            </thead>
            <tbody>"""

            max_daily = max([count for _, count in daily_stats]) if daily_stats else 1

            for date, count in daily_stats:
                activity_width = (count / max_daily * 100) if max_daily > 0 else 0

                html_content += f"""
                <tr>
                    <td>{date}</td>
                    <td>{count}</td>
                    <td>
                        <div style="background-color: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                            <div style="background-color: #4CAF50; height: 100%; width: {activity_width}%; transition: width 0.3s ease;"></div>
                        </div>
                    </td>
                </tr>"""

            html_content += f"""
            </tbody>
        </table>
        
        <h2>⚠️ Durum Dağılımı</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{status_counts['selected']}</div>
                <div class="stat-label">Seçilmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #2196F3;">{status_counts['uploaded']}</div>
                <div class="stat-label">Yüklenmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{status_counts['processed']}</div>
                <div class="stat-label">İşlenmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{status_counts['upload_failed']}</div>
                <div class="stat-label">Yükleme Hatası</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{status_counts['proc_failed']}</div>
                <div class="stat-label">İşleme Hatası</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{status_counts['duplicates']}</div>
                <div class="stat-label">Tekrarlanan</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666; font-size: 0.9em;">
            <p>Bu rapor Document Upload Manager tarafından otomatik olarak oluşturulmuştur.</p>
        </div>
    </div>
</body>
</html>
"""

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            messagebox.showinfo(
                "Başarılı", f"Özet rapor {filepath} dosyasına kaydedildi"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Özet rapor oluşturulamadı: {str(e)}")

    def show_api_stats(self):
        """API istatistiklerini göster"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("API İstatistikleri")
        stats_window.geometry("800x600")

        # Frame oluştur
        main_frame = ttk.Frame(stats_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview oluştur
        columns = (
            "İşlem",
            "Başlangıç",
            "Bitiş",
            "Süre",
            "Dosya",
            "Başarılı",
            "Hatalı",
            "Kullanıcı",
        )
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            if col == "İşlem":
                tree.column(col, width=100)
            elif col in ["Başlangıç", "Bitiş"]:
                tree.column(col, width=130)
            elif col == "Süre":
                tree.column(col, width=80)
            elif col in ["Dosya", "Başarılı", "Hatalı"]:
                tree.column(col, width=70)
            else:
                tree.column(col, width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Grid yerleştirme
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Verileri yükle
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT operation_type, start_time, end_time, duration_seconds,
                   file_count, success_count, error_count, user_name
            FROM api_stats
            ORDER BY start_time DESC
        """
        )

        for row in cursor.fetchall():
            (
                operation_type,
                start_time,
                end_time,
                duration,
                file_count,
                success_count,
                error_count,
                user_name,
            ) = row

            start_formatted = start_time.split(".")[0] if start_time else ""
            end_formatted = end_time.split(".")[0] if end_time else ""
            duration_formatted = self.format_duration(duration) if duration else ""

            tree.insert(
                "",
                "end",
                values=(
                    operation_type.title(),
                    start_formatted,
                    end_formatted,
                    duration_formatted,
                    file_count or 0,
                    success_count or 0,
                    error_count or 0,
                    user_name,
                ),
            )

        conn.close()

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame, text="Yenile", command=lambda: self._refresh_api_stats(tree)
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=stats_window.destroy).pack(
            side=tk.RIGHT, padx=5
        )

    def _refresh_api_stats(self, tree):
        """API istatistiklerini yenile"""
        # Mevcut kayıtları temizle
        for item in tree.get_children():
            tree.delete(item)

        # Verileri yeniden yükle
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT operation_type, start_time, end_time, duration_seconds,
                   file_count, success_count, error_count, user_name
            FROM api_stats
            ORDER BY start_time DESC
        """
        )

        for row in cursor.fetchall():
            (
                operation_type,
                start_time,
                end_time,
                duration,
                file_count,
                success_count,
                error_count,
                user_name,
            ) = row

            start_formatted = start_time.split(".")[0] if start_time else ""
            end_formatted = end_time.split(".")[0] if end_time else ""
            duration_formatted = self.format_duration(duration) if duration else ""

            tree.insert(
                "",
                "end",
                values=(
                    operation_type.title(),
                    start_formatted,
                    end_formatted,
                    duration_formatted,
                    file_count or 0,
                    success_count or 0,
                    error_count or 0,
                    user_name,
                ),
            )

        conn.close()

    def run(self):
        """Uygulamayı çalıştır"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DocumentUploadManager()
    app.run()
