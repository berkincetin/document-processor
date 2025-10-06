"""
Threading işlemleri için modül.

Bu modül arka plan işlemlerini yönetir.
"""

import threading
from typing import Callable, Any, Dict, Optional
from tkinter import messagebox


class ThreadManager:
    """Threading işlemlerini yöneten sınıf."""

    def __init__(self, root: Any, gui_components: Optional[Any] = None):
        """
        ThreadManager'ı başlat.

        Args:
            root: Ana Tkinter window
            gui_components: GUIComponents instance'ı
        """
        self.root = root
        self.gui = gui_components

    def run_upload_thread(self, upload_func: Callable, callback: Callable) -> None:
        """
        Upload işlemini thread'de çalıştır.

        Args:
            upload_func: Upload fonksiyonu
            callback: Tamamlandığında çağrılacak callback
        """

        def thread_worker():
            try:
                result = upload_func()
                self.root.after(0, callback, result)
            except Exception as e:
                self.root.after(0, callback, {"success": False, "error": str(e)})

        thread = threading.Thread(target=thread_worker)
        thread.daemon = True
        thread.start()

    def run_process_thread(self, process_func: Callable, callback: Callable) -> None:
        """
        Process işlemini thread'de çalıştır.

        Args:
            process_func: Process fonksiyonu
            callback: Tamamlandığında çağrılacak callback
        """

        def thread_worker():
            try:
                result = process_func()
                self.root.after(0, callback, result)
            except Exception as e:
                self.root.after(0, callback, {"success": False, "error": str(e)})

        thread = threading.Thread(target=thread_worker)
        thread.daemon = True
        thread.start()
