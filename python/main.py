import os
import hashlib
import json
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from pathlib import Path
import threading
from typing import List, Dict, Any, Tuple
import sqlite3
import shutil


class DocumentUploadManager:
    def __init__(self):
        self.api_base_url = "http://10.1.1.172:3820"
        # self.local_storage_dir = Path("C:/Users/User/Desktop/DOCUMENTS")
        self.local_storage_dir = Path("C:/Users/Polinity/Desktop/DOCUMENTS")

        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

        # Desteklenen formatlar
        self.supported_formats = {".pdf", ".docx", ".doc", ".txt", ".md"}

        # Veritabanı başlatma
        self.init_database()

        # GUI başlatma
        self.setup_gui()

        # Seçilen dosyalar listesi
        self.selected_files = []

    def init_database(self):
        """SQLite veritabanını başlat"""
        self.db_path = "upload_logs.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS upload_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                selection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upload_time TIMESTAMP NULL,
                processing_time TIMESTAMP NULL,
                user_name TEXT NOT NULL,
                original_path TEXT NOT NULL,
                local_path TEXT NOT NULL,
                is_duplicate BOOLEAN DEFAULT FALSE,
                upload_status TEXT DEFAULT 'selected',
                processing_status TEXT DEFAULT 'not_processed',
                error_message TEXT NULL
            )
        """
        )

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
        """Dosya seçimini veritabanına kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO upload_logs 
            (filename, file_hash, file_size, user_name, original_path, local_path, is_duplicate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filename,
                file_hash,
                file_size,
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

    def update_upload_status(
        self, file_id: int, status: str, error_message: str = None
    ):
        """Upload durumunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if error_message:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, upload_time = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            """,
                (status, error_message, file_id),
            )
        else:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET upload_status = ?, upload_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (status, file_id),
            )

        conn.commit()
        conn.close()

    def update_processing_status(self, status: str, error_message: str = None):
        """Tüm yüklenen dosyaların işleme durumunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if error_message:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET processing_status = ?, processing_time = CURRENT_TIMESTAMP, error_message = ?
                WHERE upload_status = 'uploaded'
            """,
                (status, error_message),
            )
        else:
            cursor.execute(
                """
                UPDATE upload_logs 
                SET processing_status = ?, processing_time = CURRENT_TIMESTAMP
                WHERE upload_status = 'uploaded'
            """
            )

        conn.commit()
        conn.close()

    def upload_files_to_api(self) -> Dict[str, Any]:
        """Yerel klasördeki dosyaları API'ya yükle"""
        try:
            files = []
            local_files = list(self.local_storage_dir.glob("*"))

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

            if not files:
                return {
                    "success": False,
                    "error": "Desteklenen formatta dosya bulunamadı",
                }

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
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "İstek zaman aşımına uğradı"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "API sunucusuna bağlanılamadı"}
        except Exception as e:
            # Hata durumunda dosyaları kapat
            for _, file_tuple in files:
                if not file_tuple[1].closed:
                    file_tuple[1].close()
            return {"success": False, "error": str(e)}

    def process_uploads_api(self, recursive: bool = True) -> Dict[str, Any]:
        """Yüklenen dosyaları işlemek için API'yı çağır"""
        try:
            response = requests.post(
                f"{self.api_base_url}/embeddings/process-uploads",
                data={"recursive": recursive},
                timeout=600,  # 10 dakika timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "İşlem zaman aşımına uğradı"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "API sunucusuna bağlanılamadı"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def setup_gui(self):
        """GUI'yi oluştur"""
        self.root = tk.Tk()
        self.root.title("Document Upload Manager")
        self.root.geometry("1000x700")

        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Üst panel - Kullanıcı bilgileri ve kontroller
        top_frame = ttk.LabelFrame(
            main_frame, text="Dosya Seçimi ve Yükleme", padding="10"
        )
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

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
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Seçilen dosya sayısı
        self.selected_count_var = tk.StringVar(value="Seçilen dosya: 0")
        ttk.Label(action_frame, textvariable=self.selected_count_var).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        # İşlem butonları
        button_subframe = ttk.Frame(action_frame)
        button_subframe.grid(row=1, column=0, columnspan=2, pady=5)

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

        # Progress bar
        self.progress = ttk.Progressbar(action_frame, mode="indeterminate")
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Alt panel - Log görüntüleme
        log_frame = ttk.LabelFrame(main_frame, text="Dosya Logları", padding="10")
        log_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )

        # Treeview için frame
        tree_frame = ttk.Frame(log_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Treeview ve scrollbar
        columns = ("Dosya", "Kullanıcı", "Seçim", "Yükleme", "İşleme", "Durum")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=12
        )

        # Kolon başlıkları ve genişlikleri
        column_widths = {
            "Dosya": 200,
            "Kullanıcı": 100,
            "Seçim": 150,
            "Yükleme": 120,
            "İşleme": 120,
            "Durum": 100,
        }
        for col in columns:
            self.tree.heading(col, text=col)
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
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        top_frame.columnconfigure(3, weight=1)
        action_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # İlk log yüklemesi
        self.refresh_logs()

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
                "UPDATE upload_logs SET upload_status = 'uploaded' WHERE upload_status = 'selected'"
            )
            conn.commit()
            conn.close()

            # Process butonunu etkinleştir
            self.process_button.config(state="normal")
        else:
            messagebox.showerror("Hata", f"Yükleme hatası: {result['error']}")

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
        """Logları veritabanından yenile"""
        # Mevcut kayıtları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Veritabanından logları al
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT filename, user_name, selection_time, upload_time, processing_time, 
                   upload_status, processing_status, is_duplicate
            FROM upload_logs 
            ORDER BY selection_time DESC
        """
        )

        for row in cursor.fetchall():
            (
                filename,
                user_name,
                selection_time,
                upload_time,
                processing_time,
                upload_status,
                processing_status,
                is_duplicate,
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
            else:
                status = "SELECTED"

            # Tarih formatları
            sel_time = selection_time.split(".")[0] if selection_time else ""
            up_time = upload_time.split(".")[0] if upload_time else ""
            proc_time = processing_time.split(".")[0] if processing_time else ""

            self.tree.insert(
                "",
                "end",
                values=(filename, user_name, sel_time, up_time, proc_time, status),
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
            conn.commit()
            conn.close()

            self.refresh_logs()
            messagebox.showinfo("Başarılı", "Loglar temizlendi")

    def export_logs(self):
        """Logları JSON formatında export et"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tüm Dosyalar", "*.*")],
            title="Logları export et",
        )

        if filepath:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM upload_logs ORDER BY selection_time DESC")
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

    def run(self):
        """Uygulamayı çalıştır"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DocumentUploadManager()
    app.run()
