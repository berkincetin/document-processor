"""
GUI bileşenleri için modül.

Bu modül Tkinter GUI bileşenlerini yönetir.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional, Union
from pathlib import Path


class GUIComponents:
    """GUI bileşenlerini yöneten sınıf."""

    def __init__(
        self,
        root: tk.Tk,
        file_manager,
        database_manager,
        api_client,
        report_generator,
        thread_manager=None,
    ):
        """
        GUIComponents'ı başlat.

        Args:
            root: Ana Tkinter window
            file_manager: FileManager instance'ı
            database_manager: DatabaseManager instance'ı
            api_client: APIClient instance'ı
            report_generator: ReportGenerator instance'ı
            thread_manager: ThreadManager instance'ı
        """
        self.root = root
        self.file_manager = file_manager
        self.database_manager = database_manager
        self.api_client = api_client
        self.report_generator = report_generator
        self.thread_manager = thread_manager

        # GUI değişkenleri
        self.user_name_var = tk.StringVar(value="Kullanıcı1")
        self.selected_count_var = tk.StringVar(value="Seçilen dosya: 0")
        self.status_filter = None
        self.user_filter = None
        self.date_filter = None
        self.format_filter = None
        self.tree = None
        self.upload_button = None
        self.process_button = None
        self.progress = None

        # Sıralama durumu
        self.sort_column = None
        self.sort_reverse = False

        # Seçilen dosyalar listesi
        self.selected_files = []

    def setup_gui(self) -> None:
        """GUI'yi oluştur."""
        self.root.title("Document Upload Manager - Enhanced")
        self.root.geometry("1400x800")

        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Üst panel - Kullanıcı bilgileri ve kontroller
        self._create_top_panel(main_frame)

        # Orta panel - İşlem butonları
        self._create_action_panel(main_frame)

        # Sol panel - Filtreler
        self._create_filter_panel(main_frame)

        # Sağ panel - Log görüntüleme
        self._create_log_panel(main_frame)

        # Grid weights
        self._configure_grid_weights(main_frame)

        # İlk log yüklemesi
        self.refresh_logs()
        self.update_user_filter()

    def _create_top_panel(self, parent: ttk.Frame) -> None:
        """Üst paneli oluştur."""
        top_frame = ttk.LabelFrame(parent, text="Dosya Seçimi ve Yükleme", padding="10")
        top_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Kullanıcı adı girişi
        ttk.Label(top_frame, text="Kullanıcı Adı:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
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
        formats_text = "Desteklenen formatlar: " + ", ".join(
            self.file_manager.supported_formats
        )
        ttk.Label(top_frame, text=formats_text, font=("TkDefaultFont", 8)).grid(
            row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0)
        )

        # Yerel klasör bilgisi
        ttk.Label(
            top_frame,
            text=f"Yerel klasör: {self.file_manager.local_storage_dir}",
            font=("TkDefaultFont", 8),
        ).grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(2, 0))

        top_frame.columnconfigure(3, weight=1)

    def _create_action_panel(self, parent: ttk.Frame) -> None:
        """İşlem panelini oluştur."""
        action_frame = ttk.LabelFrame(parent, text="İşlemler", padding="10")
        action_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Seçilen dosya sayısı
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

        action_frame.columnconfigure(2, weight=1)

    def _create_filter_panel(self, parent: ttk.Frame) -> None:
        """Filtre panelini oluştur."""
        filter_frame = ttk.LabelFrame(
            parent, text="Filtreler ve Sıralama", padding="10"
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
        format_values = ["Tümü"] + list(self.file_manager.supported_formats)
        self.format_filter = ttk.Combobox(filter_frame, values=format_values, width=12)
        self.format_filter.set("Tümü")
        self.format_filter.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=2)
        self.format_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        filter_frame.columnconfigure(0, weight=1)

    def _create_log_panel(self, parent: ttk.Frame) -> None:
        """Log panelini oluştur."""
        log_frame = ttk.LabelFrame(parent, text="Dosya Logları", padding="10")
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

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

    def _configure_grid_weights(self, main_frame: ttk.Frame) -> None:
        """Grid ağırlıklarını yapılandır."""
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def select_files(self) -> None:
        """Dosya seçme dialog'u."""
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

    def select_folder(self) -> None:
        """Klasör seçme dialog'u."""
        folder_path = filedialog.askdirectory(title="Dosya klasörünü seçin")

        if folder_path:
            files = self.file_manager.get_files_from_directory(folder_path)
            if files:
                self.process_selected_files(files)
            else:
                messagebox.showinfo(
                    "Bilgi",
                    f"Seçilen klasörde desteklenen format bulunamadı.\nDesteklenen formatlar: {', '.join(self.file_manager.supported_formats)}",
                )

    def process_selected_files(self, filepaths: List[str]) -> None:
        """Seçilen dosyaları işle."""
        user_name = self.user_name_var.get().strip()
        if not user_name:
            messagebox.showerror("Hata", "Kullanıcı adı girmeniz gerekiyor!")
            return

        self.selected_files = []
        conflicts = []

        for filepath in filepaths:
            filename = Path(filepath).name

            # Format kontrolü
            if not self.file_manager.is_supported_format(filepath):
                continue

            # Dosya çakışması kontrolü
            is_duplicate, local_path = self.file_manager.check_duplicate_by_name(
                filename
            )

            if is_duplicate:
                conflicts.append((filepath, local_path, filename))
            else:
                # Dosyayı yerel klasöre kopyala
                if self.file_manager.copy_file_to_local(filepath, local_path):
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

    def handle_file_conflicts(self, conflicts: List[tuple], user_name: str) -> None:
        """Dosya çakışmalarını çöz."""
        for original_path, local_path, filename in conflicts:
            response = messagebox.askyesnocancel(
                "Dosya Çakışması",
                f"'{filename}' dosyası zaten mevcut.\n\nÜzerine yazmak istiyor musunuz?\n\nEvet: Üzerine yaz\nHayır: Atla\nİptal: İşlemi durdur",
            )

            if response is None:  # İptal
                break
            elif response:  # Evet - üzerine yaz
                if self.file_manager.copy_file_to_local(
                    original_path, local_path, overwrite=True
                ):
                    self.selected_files.append(
                        (original_path, local_path, filename, True)
                    )
            # Hayır durumunda hiçbir şey yapma (atla)

    def save_selected_files(self, user_name: str) -> None:
        """Seçilen dosyaları veritabanına kaydet."""
        for original_path, local_path, filename, is_duplicate in self.selected_files:
            # Dosya bilgilerini al
            file_size = Path(local_path).stat().st_size
            file_hash = self.file_manager.calculate_file_hash(local_path)

            # Hash bazlı duplicate kontrolü
            hash_duplicate = self.database_manager.check_duplicate_by_hash(file_hash)

            # Veritabanına kaydet
            self.database_manager.log_file_selection(
                filename,
                file_hash,
                file_size,
                user_name,
                original_path,
                local_path,
                hash_duplicate or is_duplicate,
            )

    def update_file_count(self) -> None:
        """Seçilen dosya sayısını güncelle."""
        local_files = self.file_manager.get_local_files()
        count = len(local_files)
        self.selected_count_var.set(f"Yerel klasördeki dosya sayısı: {count}")

        # Buton durumlarını güncelle
        self.upload_button.config(state="normal" if count > 0 else "disabled")

    def upload_files(self) -> None:
        """Dosyaları API'ya yükle."""
        self.progress.start()
        self.upload_button.config(state="disabled")

        if self.thread_manager:
            # Threading ile çalıştır
            local_files = self.file_manager.get_local_files()
            self.thread_manager.run_upload_thread(
                lambda: self.api_client.upload_files_to_api(local_files),
                self.upload_complete,
            )
        else:
            # Basit implementasyon
            local_files = self.file_manager.get_local_files()
            result = self.api_client.upload_files_to_api(local_files)
            self.upload_complete(result)

    def upload_complete(self, result: Dict[str, Any]) -> None:
        """Yükleme tamamlandığında çağrılan fonksiyon."""
        self.progress.stop()
        self.upload_button.config(state="normal")

        if result["success"]:
            messagebox.showinfo("Başarılı", "Dosyalar API'ya başarıyla yüklendi!")
            self.database_manager.update_upload_status_batch("uploaded")
            self.process_button.config(state="normal")
        else:
            messagebox.showerror("Hata", f"Yükleme hatası: {result['error']}")
            self.database_manager.update_upload_status_batch(
                "upload_failed", result["error"]
            )

        self.refresh_logs()

    def process_embeddings(self) -> None:
        """Embeddings işlemini başlat."""
        self.progress.start()
        self.process_button.config(state="disabled")

        if self.thread_manager:
            # Threading ile çalıştır
            self.thread_manager.run_process_thread(
                lambda: self.api_client.process_uploads_api(), self.process_complete
            )
        else:
            # Basit implementasyon
            result = self.api_client.process_uploads_api()
            self.process_complete(result)

    def process_complete(self, result: Dict[str, Any]) -> None:
        """İşleme tamamlandığında çağrılan fonksiyon."""
        self.progress.stop()
        self.process_button.config(state="normal")

        if result["success"]:
            messagebox.showinfo("Başarılı", "Embedding işlemi tamamlandı!")
            self.database_manager.update_processing_status("completed")
        else:
            messagebox.showerror("Hata", f"İşleme hatası: {result['error']}")
            self.database_manager.update_processing_status("failed", result["error"])

        self.refresh_logs()

    def refresh_logs(self) -> None:
        """Logları veritabanından yenile - filtreli."""
        # Mevcut kayıtları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filtreleri al
        filters = {
            "status_filter": self.status_filter.get(),
            "user_filter": self.user_filter.get(),
            "date_filter": self.date_filter.get(),
            "format_filter": self.format_filter.get(),
        }

        # Veritabanından logları al
        logs = self.database_manager.get_filtered_logs(filters)

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

        for row in logs:
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
            up_dur = (
                self.report_generator.format_duration(upload_duration)
                if upload_duration
                else ""
            )
            proc_dur = (
                self.report_generator.format_duration(processing_duration)
                if processing_duration
                else ""
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
                    self.file_manager.format_file_size(file_size),
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

        self.update_file_count()

    def clear_logs(self) -> None:
        """Logları temizle."""
        if messagebox.askyesno(
            "Onay", "Tüm logları silmek istediğinizden emin misiniz?"
        ):
            self.database_manager.clear_logs()
            self.refresh_logs()
            self.update_user_filter()
            messagebox.showinfo("Başarılı", "Loglar temizlendi")

    def export_logs(self) -> None:
        """Logları JSON formatında export et."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tüm Dosyalar", "*.*")],
            title="Logları export et",
        )

        if filepath:
            # Bu işlem daha sonra implement edilecek
            messagebox.showinfo("Bilgi", "Export işlemi henüz implement edilmedi")

    def generate_detail_report(self) -> None:
        """Detaylı rapor oluştur."""
        today_str = datetime.now().strftime("%d_%m_%Y")
        default_filename = f"detay_rapor_{today_str}.html"

        filepath = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("CSV", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Detaylı rapor kaydet",
        )

        if not filepath:
            return

        # Veritabanından tüm verileri al
        conn = self.database_manager.db_path
        # Bu işlem daha sonra implement edilecek
        messagebox.showinfo("Bilgi", "Detay rapor işlemi henüz implement edilmedi")

    def generate_summary_report(self) -> None:
        """Özet rapor oluştur."""
        today_str = datetime.now().strftime("%d_%m_%Y")
        default_filename = f"ozet_rapor_{today_str}.html"

        filepath = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Tüm Dosyalar", "*.*")],
            title="Özet rapor kaydet",
        )

        if not filepath:
            return

        # İstatistikleri al ve rapor oluştur
        stats = self.database_manager.get_summary_stats()
        success = self.report_generator.generate_summary_report(stats, filepath)

        if success:
            messagebox.showinfo(
                "Başarılı", f"Özet rapor {filepath} dosyasına kaydedildi"
            )
        else:
            messagebox.showerror("Hata", "Özet rapor oluşturulamadı")

    def show_api_stats(self) -> None:
        """API istatistiklerini göster."""
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
        api_stats = self.database_manager.get_api_stats()

        for row in api_stats:
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
            duration_formatted = (
                self.report_generator.format_duration(duration) if duration else ""
            )

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

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Kapat", command=stats_window.destroy).pack(
            side=tk.RIGHT, padx=5
        )

    def sort_treeview(self, col: str) -> None:
        """Treeview kolonuna göre sırala."""
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
        for c in columns:
            if c == col:
                direction = "↓" if self.sort_reverse else "↑"
                self.tree.heading(c, text=f"{c} {direction}")
            else:
                self.tree.heading(c, text=c)

    def apply_filters(self, event=None) -> None:
        """Filtreleri uygula."""
        self.refresh_logs()

    def update_user_filter(self) -> None:
        """Kullanıcı filtresini güncelle."""
        users = ["Tümü"] + self.database_manager.get_user_list()
        self.user_filter["values"] = users
        if not self.user_filter.get():
            self.user_filter.set("Tümü")
