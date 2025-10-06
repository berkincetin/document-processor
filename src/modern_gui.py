"""
Modern GUI bileşenleri için modül.

Bu modül modern ve renkli Tkinter GUI bileşenlerini yönetir.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional, Union
from pathlib import Path


class ModernGUIComponents:
    """Modern GUI bileşenlerini yöneten sınıf."""

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
        ModernGUIComponents'ı başlat.

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

        # Renk paleti
        self.colors = {
            "primary": "#2E86AB",  # Mavi
            "secondary": "#A23B72",  # Mor
            "success": "#F18F01",  # Turuncu
            "warning": "#C73E1D",  # Kırmızı
            "info": "#7209B7",  # Mor
            "light": "#F8F9FA",  # Açık gri
            "dark": "#212529",  # Koyu gri
            "white": "#FFFFFF",
            "gray": "#6C757D",
            "light_gray": "#E9ECEF",
        }

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
        """Modern GUI'yi oluştur."""
        self.root.title("📄 Document Upload Manager - Modern UI")
        self.root.geometry("1600x900")
        self.root.configure(bg=self.colors["light"])

        # Ana frame
        main_frame = tk.Frame(self.root, bg=self.colors["light"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Üst panel - Kullanıcı bilgileri ve kontroller
        self._create_header_panel(main_frame)

        # Orta panel - İşlem butonları
        self._create_action_panel(main_frame)

        # Alt panel - Filtreler ve log görüntüleme
        self._create_content_panel(main_frame)

        # İlk log yüklemesi
        self.refresh_logs()
        self.update_user_filter()

    def _create_header_panel(self, parent: tk.Frame) -> None:
        """Header panelini oluştur."""
        header_frame = tk.Frame(
            parent, bg=self.colors["primary"], relief=tk.RAISED, bd=2
        )
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Başlık
        title_frame = tk.Frame(header_frame, bg=self.colors["primary"])
        title_frame.pack(fill=tk.X, padx=20, pady=15)

        title_label = tk.Label(
            title_frame,
            text="📄 Document Upload Manager",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        )
        title_label.pack(side=tk.LEFT)

        # Kullanıcı bilgileri
        user_frame = tk.Frame(header_frame, bg=self.colors["primary"])
        user_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        tk.Label(
            user_frame,
            text="👤 Kullanıcı:",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        ).pack(side=tk.LEFT, padx=(0, 10))

        user_entry = tk.Entry(
            user_frame,
            textvariable=self.user_name_var,
            width=20,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            bd=5,
        )
        user_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Dosya seçme butonları
        button_frame = tk.Frame(header_frame, bg=self.colors["primary"])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Butonlar arasında boşluk için
        button_frame.columnconfigure(0, pad=10)
        button_frame.columnconfigure(1, pad=10)

        self._create_modern_button(
            button_frame,
            "📁 Dosya Seç",
            self.select_files,
            self.colors["success"],
            side=tk.LEFT,
        )
        self._create_modern_button(
            button_frame,
            "📂 Klasör Seç",
            self.select_folder,
            self.colors["info"],
            side=tk.LEFT,
        )

        # Desteklenen formatlar bilgisi
        formats_text = "Desteklenen formatlar: " + ", ".join(
            self.file_manager.supported_formats
        )
        tk.Label(
            header_frame,
            text=formats_text,
            font=("Segoe UI", 9),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        ).pack(padx=20, pady=(0, 15))

    def _create_action_panel(self, parent: tk.Frame) -> None:
        """İşlem panelini oluştur."""
        action_frame = tk.Frame(parent, bg=self.colors["white"], relief=tk.RAISED, bd=2)
        action_frame.pack(fill=tk.X, pady=(0, 20))

        # İçerik frame
        content_frame = tk.Frame(
            action_frame, bg=self.colors["white"], padx=20, pady=15
        )
        content_frame.pack(fill=tk.X)

        # Seçilen dosya sayısı
        count_label = tk.Label(
            content_frame,
            textvariable=self.selected_count_var,
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["dark"],
            bg=self.colors["white"],
        )
        count_label.pack(anchor=tk.W, pady=(0, 10))

        # İşlem butonları
        button_frame = tk.Frame(content_frame, bg=self.colors["white"])
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.upload_button = self._create_modern_button(
            button_frame,
            "🚀 1. Dosyaları API'ya Yükle",
            self.upload_files,
            self.colors["primary"],
            state="disabled",
            side=tk.LEFT,
        )

        self.process_button = self._create_modern_button(
            button_frame,
            "⚡ 2. Embedding İşle",
            self.process_embeddings,
            self.colors["secondary"],
            state="disabled",
            side=tk.LEFT,
        )

        # Rapor butonları
        report_frame = tk.Frame(content_frame, bg=self.colors["white"])
        report_frame.pack(fill=tk.X, pady=(0, 10))

        self._create_modern_button(
            report_frame,
            "📊 Detay Rapor",
            self.generate_detail_report,
            self.colors["info"],
            side=tk.LEFT,
        )
        self._create_modern_button(
            report_frame,
            "📈 Özet Rapor",
            self.generate_summary_report,
            self.colors["success"],
            side=tk.LEFT,
        )
        self._create_modern_button(
            report_frame,
            "📋 API İstatistikleri",
            self.show_api_stats,
            self.colors["warning"],
            side=tk.LEFT,
        )

        # Progress bar
        progress_frame = tk.Frame(content_frame, bg=self.colors["white"])
        progress_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            progress_frame,
            text="İşlem Durumu:",
            font=("Segoe UI", 10),
            fg=self.colors["dark"],
            bg=self.colors["white"],
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(
            progress_frame, mode="indeterminate", style="Modern.Horizontal.TProgressbar"
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Progress bar style
        style = ttk.Style()
        style.configure(
            "Modern.Horizontal.TProgressbar",
            background=self.colors["primary"],
            troughcolor=self.colors["light_gray"],
            borderwidth=0,
            lightcolor=self.colors["primary"],
            darkcolor=self.colors["primary"],
        )

    def _create_content_panel(self, parent: tk.Frame) -> None:
        """İçerik panelini oluştur."""
        content_frame = tk.Frame(parent, bg=self.colors["light"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Sol panel - Filtreler
        self._create_filter_panel(content_frame)

        # Sağ panel - Log görüntüleme
        self._create_log_panel(content_frame)

    def _create_filter_panel(self, parent: tk.Frame) -> None:
        """Filtre panelini oluştur."""
        filter_frame = tk.Frame(parent, bg=self.colors["white"], relief=tk.RAISED, bd=2)
        filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        filter_frame.configure(width=300)
        filter_frame.pack_propagate(False)

        # Başlık
        title_frame = tk.Frame(filter_frame, bg=self.colors["primary"])
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            title_frame,
            text="🔍 Filtreler ve Sıralama",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        ).pack(pady=5)

        # Filtre içeriği
        filter_content = tk.Frame(
            filter_frame, bg=self.colors["white"], padx=15, pady=10
        )
        filter_content.pack(fill=tk.BOTH, expand=True)

        # Durum filtresi
        self._create_filter_group(
            filter_content,
            "📊 Durum:",
            [
                "Tümü",
                "SELECTED",
                "UPLOADED",
                "PROCESSED",
                "OVERWRITE",
                "UP_FAILED",
                "PROC_FAILED",
            ],
            "status_filter",
            "Tümü",
        )

        # Kullanıcı filtresi
        self._create_filter_group(
            filter_content, "👤 Kullanıcı:", ["Tümü"], "user_filter", "Tümü"
        )

        # Tarih filtresi
        self._create_filter_group(
            filter_content,
            "📅 Son:",
            ["Tümü", "Son 1 saat", "Son 24 saat", "Son 7 gün", "Son 30 gün"],
            "date_filter",
            "Tümü",
        )

        # Format filtresi
        format_values = ["Tümü"] + list(self.file_manager.supported_formats)
        self._create_filter_group(
            filter_content, "📄 Format:", format_values, "format_filter", "Tümü"
        )

        # Filtre butonları
        button_frame = tk.Frame(filter_content, bg=self.colors["white"])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self._create_modern_button(
            button_frame,
            "🔄 Yenile",
            self.apply_filters,
            self.colors["info"],
            side=tk.LEFT,
        )
        self._create_modern_button(
            button_frame,
            "🗑️ Temizle",
            self.clear_logs,
            self.colors["warning"],
            side=tk.LEFT,
        )

    def _create_filter_group(
        self,
        parent: tk.Frame,
        label_text: str,
        values: List[str],
        var_name: str,
        default_value: str,
    ) -> None:
        """Filtre grubu oluştur."""
        group_frame = tk.Frame(parent, bg=self.colors["white"])
        group_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            group_frame,
            text=label_text,
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["dark"],
            bg=self.colors["white"],
        ).pack(anchor=tk.W, pady=(0, 5))

        var = tk.StringVar(value=default_value)
        setattr(self, var_name, var)

        combobox = ttk.Combobox(
            group_frame,
            textvariable=var,
            values=values,
            font=("Segoe UI", 10),
            state="readonly",
            width=25,
        )
        combobox.pack(fill=tk.X)
        combobox.bind("<<ComboboxSelected>>", self.apply_filters)

        # Combobox referansını sakla
        setattr(self, f"{var_name}_combobox", combobox)

    def _create_log_panel(self, parent: tk.Frame) -> None:
        """Log panelini oluştur."""
        log_frame = tk.Frame(parent, bg=self.colors["white"], relief=tk.RAISED, bd=2)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Başlık
        title_frame = tk.Frame(log_frame, bg=self.colors["primary"])
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            title_frame,
            text="📋 Dosya Logları",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        ).pack(side=tk.LEFT)

        # Log butonları
        button_frame = tk.Frame(title_frame, bg=self.colors["primary"])
        button_frame.pack(side=tk.RIGHT)

        self._create_modern_button(
            button_frame,
            "🔄",
            self.refresh_logs,
            self.colors["success"],
            side=tk.LEFT,
            width=40,
        )
        self._create_modern_button(
            button_frame,
            "📤",
            self.export_logs,
            self.colors["info"],
            side=tk.LEFT,
            width=40,
        )

        # Treeview için frame
        tree_frame = tk.Frame(log_frame, bg=self.colors["white"], padx=10, pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview ve scrollbar
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
            "Overwrite",
            "Hata",
        )
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=20
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
            "Overwrite": 80,
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

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

    def _create_modern_button(
        self, parent: tk.Frame, text: str, command: Callable, color: str, **kwargs
    ) -> tk.Button:
        """Modern buton oluştur."""
        # pack parametrelerini kwargs'tan çıkar
        pack_params = {}
        for param in ["side", "padx", "pady", "fill", "expand", "anchor"]:
            if param in kwargs:
                pack_params[param] = kwargs.pop(param)

        # Button parametrelerini ayır
        button_padx = kwargs.pop("padx", 15)
        button_pady = kwargs.pop("pady", 8)

        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg=self.colors["white"],
            relief=tk.FLAT,
            bd=0,
            padx=button_padx,
            pady=button_pady,
            cursor="hand2",
            **kwargs,
        )

        # Pack parametrelerini uygula
        if pack_params:
            button.pack(**pack_params)
        else:
            button.pack()

        # Hover efektleri
        def on_enter(e):
            button.configure(bg=self._darken_color(color))

        def on_leave(e):
            button.configure(bg=color)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        return button

    def _darken_color(self, color: str) -> str:
        """Rengi koyulaştır."""
        color_map = {
            self.colors["primary"]: "#1E5A7A",
            self.colors["secondary"]: "#7A2A5A",
            self.colors["success"]: "#C16A01",
            self.colors["warning"]: "#A02E1A",
            self.colors["info"]: "#5A0780",
        }
        return color_map.get(color, color)

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
            # Veritabanından duplicate bilgilerini al
            duplicate_info = self.database_manager.check_duplicate_by_name(filename)

            if duplicate_info:
                last_time = duplicate_info["last_time"]
                overwrite_count = duplicate_info["overwrite_count"]

                message = f"'{filename}' dosyası zaten mevcut.\n\n"
                message += f"Son yükleme: {last_time}\n"
                message += f"Overwrite sayısı: {overwrite_count}\n\n"
                message += "Üzerine yazmak istiyor musunuz?\n\n"
                message += "Evet: Üzerine yaz\nHayır: Atla\nİptal: İşlemi durdur"
            else:
                message = f"'{filename}' dosyası zaten mevcut.\n\nÜzerine yazmak istiyor musunuz?\n\nEvet: Üzerine yaz\nHayır: Atla\nİptal: İşlemi durdur"

            response = messagebox.askyesnocancel("Dosya Çakışması", message)

            if response is None:  # İptal
                break
            elif response:  # Evet - üzerine yaz
                if self.file_manager.copy_file_to_local(
                    original_path, local_path, overwrite=True
                ):
                    self.selected_files.append(
                        (original_path, local_path, filename, True)
                    )
                    # Overwrite bilgisini güncelle
                    self.database_manager.update_duplicate_info(
                        filename, is_overwrite=True
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
                overwrite_count,
                last_duplicate_time,
            ) = row

            # Durumu belirle
            if is_duplicate and overwrite_count and overwrite_count > 0:
                status = f"OVERWRITE ({overwrite_count}x)"
            elif is_duplicate:
                # Duplicate için son yükleme tarihini göster
                if last_duplicate_time:
                    last_time = last_duplicate_time.split(".")[0]
                    status = f"DUPLICATE (Son: {last_time})"
                else:
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

            # Overwrite bilgisi
            if overwrite_count and overwrite_count > 0:
                overwrite_info = f"{overwrite_count}x"
                if last_duplicate_time:
                    last_time = last_duplicate_time.split(".")[0]
                    overwrite_info += f" ({last_time})"
            else:
                overwrite_info = ""

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
                    overwrite_info,
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
        stats_window.configure(bg=self.colors["light"])

        # Frame oluştur
        main_frame = tk.Frame(stats_window, bg=self.colors["light"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Başlık
        title_frame = tk.Frame(main_frame, bg=self.colors["primary"])
        title_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            title_frame,
            text="📊 API İstatistikleri",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"],
        ).pack(pady=10)

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
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
        button_frame = tk.Frame(main_frame, bg=self.colors["light"])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self._create_modern_button(
            button_frame,
            "❌ Kapat",
            stats_window.destroy,
            self.colors["warning"],
            side=tk.RIGHT,
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
            "Overwrite",
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
        # Combobox referansını kullan
        if hasattr(self, "user_filter_combobox"):
            self.user_filter_combobox["values"] = users
        if not self.user_filter.get():
            self.user_filter.set("Tümü")
