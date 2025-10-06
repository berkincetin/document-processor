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

        # Modern renk paleti - Koyu tema
        self.colors = {
            "bg_primary": "#1a1d29",  # Ana koyu arka plan
            "bg_secondary": "#252936",  # İkincil arka plan
            "bg_card": "#2d3142",  # Kart arka planı
            "accent_blue": "#4895ef",  # Mavi vurgu
            "accent_purple": "#7209b7",  # Mor vurgu
            "accent_green": "#06d6a0",  # Yeşil vurgu
            "accent_red": "#ef476f",  # Kırmızı vurgu
            "accent_orange": "#f77f00",  # Turuncu vurgu
            "text_primary": "#e8eaed",  # Ana metin
            "text_secondary": "#9ba4b5",  # İkincil metin
            "border": "#3d4256",  # Kenarlık
            "hover": "#363a4f",  # Hover efekti
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

        # TÜMÜNÜ İŞLE modu
        self._process_all_mode = False

    def setup_gui(self) -> None:
        """Modern GUI'yi oluştur."""
        self.root.title("📄 Document Upload Manager")
        self.root.state("zoomed")
        self.root.configure(bg=self.colors["bg_primary"])

        # Ana container - Grid yapısı
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_container = tk.Frame(self.root, bg=self.colors["bg_primary"])
        main_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        main_container.grid_rowconfigure(1, weight=0)  # Filtreler
        main_container.grid_rowconfigure(2, weight=1)  # Log paneli
        main_container.grid_rowconfigure(3, weight=0)  # Alt panel
        main_container.grid_columnconfigure(0, weight=1)

        # Üst panel
        self._create_header_panel(main_container)

        # Filtreler paneli
        self._create_filter_panel(main_container)

        # Log paneli
        self._create_log_panel(main_container)

        # Alt panel
        self._create_action_panel(main_container)

        # İlk yükleme
        self.refresh_logs()
        self.update_user_filter()

    def _create_header_panel(self, parent: tk.Frame) -> None:
        """Header panelini oluştur."""
        header = tk.Frame(parent, bg=self.colors["bg_card"], relief=tk.FLAT, bd=0)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        # Sol taraf - Başlık
        left_frame = tk.Frame(header, bg=self.colors["bg_card"])
        left_frame.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        title = tk.Label(
            left_frame,
            text="📄 Document Upload Manager",
            font=("Segoe UI", 22, "bold"),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_card"],
        )
        title.pack(side=tk.LEFT)

        subtitle = tk.Label(
            left_frame,
            text="Modern File Management System",
            font=("Segoe UI", 10),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_card"],
        )
        subtitle.pack(side=tk.LEFT, padx=(15, 0))

        # Sağ taraf - Kullanıcı ve dosya seçim
        right_frame = tk.Frame(header, bg=self.colors["bg_card"])
        right_frame.grid(row=0, column=1, sticky="e", padx=20, pady=15)

        # Kullanıcı - Daha büyük ve belirgin
        user_container = tk.Frame(
            right_frame,
            bg=self.colors["bg_secondary"],
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground=self.colors["accent_blue"],
        )
        user_container.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(
            user_container,
            text="👤 Kullanıcı:",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_secondary"],
        ).pack(side=tk.LEFT, padx=(15, 8), pady=12)

        user_entry = tk.Entry(
            user_container,
            textvariable=self.user_name_var,
            width=18,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["accent_blue"],
            relief=tk.FLAT,
            bd=0,
        )
        user_entry.pack(side=tk.LEFT, padx=(0, 15), pady=12)

        # Dosya seçim butonları
        self._create_gradient_button(
            right_frame,
            "📁 Dosya Seç",
            self.select_files,
            self.colors["accent_green"],
            width=130,
        ).pack(side=tk.LEFT, padx=5)

        self._create_gradient_button(
            right_frame,
            "📂 Klasör Seç",
            self.select_folder,
            self.colors["accent_blue"],
            width=130,
        ).pack(side=tk.LEFT, padx=5)

    def _create_filter_panel(self, parent: tk.Frame) -> None:
        """Filtre panelini oluştur."""
        filter_frame = tk.Frame(parent, bg=self.colors["bg_card"], relief=tk.FLAT)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(0, weight=1)

        # İçerik container
        content = tk.Frame(filter_frame, bg=self.colors["bg_card"])
        content.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_columnconfigure(3, weight=1)
        content.grid_columnconfigure(4, weight=0)

        # Başlık
        title_label = tk.Label(
            content,
            text="🔍 Filtreler",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_card"],
        )
        title_label.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 10))

        # Filtreler
        self._create_compact_filter(
            content,
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
            0,
            0,
        )

        self._create_compact_filter(
            content, "👤 Kullanıcı:", ["Tümü"], "user_filter", 0, 1
        )

        self._create_compact_filter(
            content,
            "📅 Tarih:",
            ["Tümü", "Son 1 saat", "Son 24 saat", "Son 7 gün", "Son 30 gün"],
            "date_filter",
            0,
            2,
        )

        format_values = ["Tümü"] + list(self.file_manager.supported_formats)
        self._create_compact_filter(
            content, "📄 Format:", format_values, "format_filter", 0, 3
        )

        # Filtre butonu - Temizle kaldırıldı
        btn_frame = tk.Frame(content, bg=self.colors["bg_card"])
        btn_frame.grid(row=0, column=4, sticky="e", padx=(10, 0))

        self._create_gradient_button(
            btn_frame,
            "🔄 Yenile",
            self.apply_filters,
            self.colors["accent_blue"],
            width=120,
        ).pack(side=tk.LEFT, padx=2)

    def _create_compact_filter(self, parent, label_text, values, var_name, row, col):
        """Kompakt ve modern filtre oluştur."""
        container = tk.Frame(parent, bg=self.colors["bg_card"])
        container.grid(row=row, column=col, sticky="ew", padx=5)

        tk.Label(
            container,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_card"],
        ).pack(anchor=tk.W, pady=(0, 5))

        var = tk.StringVar(value=values[0])
        setattr(self, var_name, var)

        # Modern Combobox Frame
        combo_frame = tk.Frame(
            container,
            bg=self.colors["bg_secondary"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        combo_frame.pack(fill=tk.X)

        # Modern Style
        style = ttk.Style()
        style.theme_use("default")

        # Combobox için özel stil
        style_name = f"Modern{var_name}.TCombobox"
        style.configure(
            style_name,
            fieldbackground=self.colors["bg_secondary"],
            background=self.colors["bg_secondary"],
            foreground=self.colors["text_primary"],
            arrowcolor=self.colors["text_primary"],
            borderwidth=0,
            relief="flat",
        )

        style.map(
            style_name,
            fieldbackground=[("readonly", self.colors["bg_secondary"])],
            selectbackground=[("readonly", self.colors["accent_blue"])],
            selectforeground=[("readonly", self.colors["text_primary"])],
            background=[("readonly", self.colors["bg_secondary"])],
        )

        combo = ttk.Combobox(
            combo_frame,
            textvariable=var,
            values=values,
            font=("Segoe UI", 10),
            state="readonly",
            style=style_name,
        )
        combo.pack(fill=tk.X, padx=8, pady=6)
        combo.bind("<<ComboboxSelected>>", self.apply_filters)

        # Hover efekti
        def on_enter(e):
            combo_frame.configure(highlightbackground=self.colors["accent_blue"])

        def on_leave(e):
            combo_frame.configure(highlightbackground=self.colors["border"])

        combo_frame.bind("<Enter>", on_enter)
        combo_frame.bind("<Leave>", on_leave)
        combo.bind("<Enter>", on_enter)
        combo.bind("<Leave>", on_leave)

        setattr(self, f"{var_name}_combobox", combo)

    def _create_log_panel(self, parent: tk.Frame) -> None:
        """Log panelini oluştur."""
        log_frame = tk.Frame(parent, bg=self.colors["bg_card"], relief=tk.FLAT)
        log_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Başlık
        header = tk.Frame(log_frame, bg=self.colors["bg_card"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        tk.Label(
            header,
            text="📋 Dosya Logları",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_card"],
        ).pack(side=tk.LEFT)

        self.selected_count_label = tk.Label(
            header,
            textvariable=self.selected_count_var,
            font=("Segoe UI", 10),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_card"],
        )
        self.selected_count_label.pack(side=tk.RIGHT)

        # Treeview container
        tree_container = tk.Frame(log_frame, bg=self.colors["bg_card"])
        tree_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Modern.Treeview",
            background=self.colors["bg_secondary"],
            foreground=self.colors["text_primary"],
            fieldbackground=self.colors["bg_secondary"],
            borderwidth=0,
            font=("Segoe UI", 9),
            rowheight=25,
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=self.colors["bg_card"],
            foreground=self.colors["text_primary"],
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", self.colors["accent_blue"])],
            foreground=[("selected", self.colors["text_primary"])],
        )

        # Treeview
        columns = (
            "Dosya",
            "Format",
            "Boyut",
            "Kullanıcı",
            "Seçim",
            "Durum",
            "Overwrite",
            "Hata",
        )

        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            selectmode="extended",
        )

        # Sütunlar
        column_widths = {
            "Dosya": 250,
            "Format": 80,
            "Boyut": 100,
            "Kullanıcı": 120,
            "Seçim": 160,
            "Durum": 140,
            "Overwrite": 120,
            "Hata": 200,
        }

        for col in columns:
            self.tree.heading(
                col, text=col, command=lambda c=col: self.sort_treeview(c)
            )
            self.tree.column(
                col,
                width=column_widths.get(col, 100),
                anchor=tk.W if col == "Dosya" else tk.CENTER,
            )

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _create_action_panel(self, parent: tk.Frame) -> None:
        """Alt işlem panelini oluştur."""
        action_frame = tk.Frame(parent, bg=self.colors["bg_card"], relief=tk.FLAT)
        action_frame.grid(row=3, column=0, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        content = tk.Frame(action_frame, bg=self.colors["bg_card"])
        content.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=0)

        # Sol butonlar
        left_buttons = tk.Frame(content, bg=self.colors["bg_card"])
        left_buttons.grid(row=0, column=0, sticky="w")

        self.upload_button = self._create_gradient_button(
            left_buttons,
            "📤 API'a Yükle",
            self.upload_files,
            self.colors["accent_blue"],
            state="disabled",
            width=130,
        )
        self.upload_button.pack(side=tk.LEFT, padx=3)

        self.process_button = self._create_gradient_button(
            left_buttons,
            "🧠 Embedding İşle",
            self.process_embeddings,
            self.colors["accent_purple"],
            state="disabled",
            width=140,
            text_color=self.colors["text_primary"],
        )
        self.process_button.pack(side=tk.LEFT, padx=3)

        self._create_gradient_button(
            left_buttons,
            "📊 Özet Rapor",
            self.generate_summary_report,
            self.colors["accent_green"],
            width=120,
        ).pack(side=tk.LEFT, padx=3)

        self._create_gradient_button(
            left_buttons,
            "📈 API Stats",
            self.show_api_stats,
            self.colors["accent_orange"],
            width=120,
        ).pack(side=tk.LEFT, padx=3)

        # Progress bar
        progress_frame = tk.Frame(content, bg=self.colors["bg_card"])
        progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        style = ttk.Style()
        style.configure(
            "Modern.Horizontal.TProgressbar",
            background=self.colors["accent_blue"],
            troughcolor=self.colors["bg_secondary"],
            borderwidth=0,
            thickness=4,
        )

        self.progress = ttk.Progressbar(
            progress_frame, mode="indeterminate", style="Modern.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X)

        # Sağ buton - İŞLE (Daha büyük)
        right_buttons = tk.Frame(content, bg=self.colors["bg_card"])
        right_buttons.grid(row=0, column=1, sticky="e")

        process_all_btn = self._create_gradient_button(
            right_buttons,
            "⚡ TÜMÜNÜ İŞLE",
            self.process_all,
            self.colors["accent_red"],
            width=200,
        )
        process_all_btn.config(font=("Segoe UI", 13, "bold"), padx=25, pady=15)
        process_all_btn.pack(side=tk.RIGHT)

    def _create_gradient_button(self, parent, text, command, color, **kwargs):
        """Modern gradient buton oluştur."""
        width = kwargs.pop("width", 120)
        state = kwargs.pop("state", "normal")
        text_color = kwargs.pop("text_color", self.colors["text_primary"])

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg=text_color,
            activebackground=self._lighten_color(color),
            activeforeground=text_color,
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=10,
            cursor="hand2",
            state=state,
            width=width // 8,  # Yaklaşık pixel to char conversion
        )

        def on_enter(e):
            if btn["state"] == "normal":
                btn.configure(bg=self._lighten_color(color))

        def on_leave(e):
            if btn["state"] == "normal":
                btn.configure(bg=color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _lighten_color(self, color: str) -> str:
        """Rengi açıklaştır."""
        color_map = {
            self.colors["accent_blue"]: "#5ca7ff",
            self.colors["accent_purple"]: "#8b2bc7",
            self.colors["accent_green"]: "#1ae8ba",
            self.colors["accent_red"]: "#ff5a81",
            self.colors["accent_orange"]: "#ff9420",
        }
        return color_map.get(color, color)

    def _darken_color(self, color: str) -> str:
        """Rengi koyulaştır."""
        color_map = {
            self.colors["accent_blue"]: "#3783d5",
            self.colors["accent_purple"]: "#5a079d",
            self.colors["accent_green"]: "#05b486",
            self.colors["accent_red"]: "#d5365b",
            self.colors["accent_orange"]: "#c96500",
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

            if not self.file_manager.is_supported_format(filepath):
                continue

            is_duplicate, local_path = self.file_manager.check_duplicate_by_name(
                filename
            )

            if is_duplicate:
                conflicts.append((filepath, local_path, filename))
            else:
                if self.file_manager.copy_file_to_local(filepath, local_path):
                    self.selected_files.append((filepath, local_path, filename, False))

        if conflicts:
            self.handle_file_conflicts(conflicts, user_name)

        self.save_selected_files(user_name)
        self.update_file_count()
        self.refresh_logs()
        self.update_user_filter()

    def handle_file_conflicts(self, conflicts: List[tuple], user_name: str) -> None:
        """Dosya çakışmalarını çöz."""
        for original_path, local_path, filename in conflicts:
            duplicate_info = self.database_manager.check_duplicate_by_name(filename)

            if duplicate_info:
                last_time = duplicate_info["last_time"]
                overwrite_count = duplicate_info["overwrite_count"]
                message = f"'{filename}' dosyası zaten mevcut.\n\n"
                message += f"Son yükleme: {last_time}\n"
                message += f"Overwrite sayısı: {overwrite_count}\n\n"
                message += "Üzerine yazmak istiyor musunuz?"
            else:
                message = f"'{filename}' dosyası zaten mevcut.\n\nÜzerine yazmak istiyor musunuz?"

            response = messagebox.askyesnocancel("Dosya Çakışması", message)

            if response is None:
                break
            elif response:
                if self.file_manager.copy_file_to_local(
                    original_path, local_path, overwrite=True
                ):
                    self.selected_files.append(
                        (original_path, local_path, filename, True)
                    )
                    # Overwrite sayısını artır
                    self.database_manager.update_duplicate_info(
                        filename, is_overwrite=True
                    )

    def save_selected_files(self, user_name: str) -> None:
        """Seçilen dosyaları veritabanına kaydet."""
        for original_path, local_path, filename, is_duplicate in self.selected_files:
            file_size = Path(local_path).stat().st_size
            file_hash = self.file_manager.calculate_file_hash(local_path)
            hash_duplicate = self.database_manager.check_duplicate_by_hash(file_hash)

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
        self.selected_count_var.set(f"Yerel klasörde {count} dosya")
        self.upload_button.config(state="normal" if count > 0 else "disabled")

    def upload_files(self) -> None:
        """Dosyaları API'ya yükle."""
        self.progress.start()
        self.upload_button.config(state="disabled")

        if self.thread_manager:
            local_files = self.file_manager.get_local_files()
            self.thread_manager.run_upload_thread(
                lambda: self.api_client.upload_files_to_api(local_files),
                self.upload_complete,
            )
        else:
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

            # Eğer TÜMÜNÜ İŞLE butonundan geliyorsa, embedding işlemini de başlat
            if hasattr(self, "_process_all_mode") and self._process_all_mode:
                self._process_all_mode = False
                self.process_embeddings()
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
            self.thread_manager.run_process_thread(
                lambda: self.api_client.process_uploads_api(), self.process_complete
            )
        else:
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

    def process_all(self) -> None:
        """Tüm işlemleri sırayla çalıştır."""
        # TÜMÜNÜ İŞLE modunu aktif et
        self._process_all_mode = True
        # Upload işlemini başlat
        self.upload_files()

    def refresh_logs(self) -> None:
        """Logları veritabanından yenile."""
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filtrelerin varlığını kontrol et
        filters = {}
        if hasattr(self, "status_filter") and self.status_filter:
            filters["status_filter"] = self.status_filter.get()
        if hasattr(self, "user_filter") and self.user_filter:
            filters["user_filter"] = self.user_filter.get()
        if hasattr(self, "date_filter") and self.date_filter:
            filters["date_filter"] = self.date_filter.get()
        if hasattr(self, "format_filter") and self.format_filter:
            filters["format_filter"] = self.format_filter.get()

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

            # Tarih formatı
            sel_time = selection_time.split(".")[0] if selection_time else ""

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
        stats_window.geometry("900x600")
        stats_window.configure(bg=self.colors["bg_primary"])

        # Main container
        main_frame = tk.Frame(
            stats_window, bg=self.colors["bg_primary"], padx=20, pady=20
        )
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Başlık
        title_frame = tk.Frame(main_frame, bg=self.colors["bg_card"])
        title_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            title_frame,
            text="📊 API İstatistikleri",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_card"],
        ).pack(pady=15)

        # Treeview
        tree_frame = tk.Frame(main_frame, bg=self.colors["bg_card"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

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
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            height=20,
        )

        column_widths = {
            "İşlem": 100,
            "Başlangıç": 140,
            "Bitiş": 140,
            "Süre": 80,
            "Dosya": 70,
            "Başarılı": 80,
            "Hatalı": 70,
            "Kullanıcı": 100,
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 100), anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15, padx=(0, 15))

        # Verileri yükle
        api_stats = self.database_manager.get_api_stats()

        for row in api_stats:
            (
                operation_type,
                start_time,
                end_time,
                duration,
                file_count,
                total_size_bytes,
                success_count,
                error_count,
                error_message,
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
        button_frame = tk.Frame(main_frame, bg=self.colors["bg_primary"])
        button_frame.pack(fill=tk.X, pady=(15, 0))

        self._create_gradient_button(
            button_frame,
            "❌ Kapat",
            stats_window.destroy,
            self.colors["accent_red"],
            width=120,
        ).pack(side=tk.RIGHT)

    def sort_treeview(self, col: str) -> None:
        """Treeview kolonuna göre sırala."""
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        data = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            data.append((child, values))

        columns = (
            "Dosya",
            "Format",
            "Boyut",
            "Kullanıcı",
            "Seçim",
            "Durum",
            "Overwrite",
            "Hata",
        )

        def sort_key(item):
            value = item[1][columns.index(col)]

            if col == "Boyut":
                try:
                    if "MB" in str(value):
                        return float(str(value).replace("MB", "").strip()) * 1024 * 1024
                    elif "KB" in str(value):
                        return float(str(value).replace("KB", "").strip()) * 1024
                    else:
                        return float(str(value).replace("B", "").strip() or 0)
                except:
                    return 0
            elif col == "Seçim":
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

        for index, (child, values) in enumerate(data):
            self.tree.move(child, "", index)

        # Kolon başlığını güncelle
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
        if hasattr(self, "user_filter_combobox"):
            self.user_filter_combobox["values"] = users
        if not self.user_filter.get():
            self.user_filter.set("Tümü")
