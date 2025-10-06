"""
Database işlemleri için modül.

Bu modül SQLite veritabanı işlemlerini yönetir.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional, Union
from pathlib import Path


class DatabaseManager:
    """Veritabanı işlemlerini yöneten sınıf."""

    def __init__(self, db_path: str = "upload_logs.db"):
        """
        DatabaseManager'ı başlat.

        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """SQLite veritabanını başlat - geliştirilmiş loglama."""
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
        self._add_column_if_not_exists(cursor, "file_extension", "TEXT DEFAULT ''")
        self._add_column_if_not_exists(cursor, "upload_start_time", "TIMESTAMP NULL")
        self._add_column_if_not_exists(cursor, "upload_end_time", "TIMESTAMP NULL")
        self._add_column_if_not_exists(cursor, "upload_duration_seconds", "REAL NULL")
        self._add_column_if_not_exists(
            cursor, "processing_start_time", "TIMESTAMP NULL"
        )
        self._add_column_if_not_exists(cursor, "processing_end_time", "TIMESTAMP NULL")
        self._add_column_if_not_exists(
            cursor, "processing_duration_seconds", "REAL NULL"
        )
        self._add_column_if_not_exists(cursor, "upload_error_message", "TEXT NULL")
        self._add_column_if_not_exists(cursor, "processing_error_message", "TEXT NULL")
        self._add_column_if_not_exists(cursor, "retry_count", "INTEGER DEFAULT 0")
        self._add_column_if_not_exists(cursor, "last_retry_time", "TIMESTAMP NULL")
        self._add_column_if_not_exists(
            cursor, "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
        self._add_column_if_not_exists(
            cursor, "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
        self._add_column_if_not_exists(cursor, "overwrite_count", "INTEGER DEFAULT 0")
        self._add_column_if_not_exists(cursor, "last_duplicate_time", "TIMESTAMP NULL")

        conn.commit()
        conn.close()

    def _add_column_if_not_exists(
        self, cursor: sqlite3.Cursor, column_name: str, column_definition: str
    ) -> None:
        """Kolon yoksa ekle."""
        try:
            cursor.execute(
                f"ALTER TABLE upload_logs ADD COLUMN {column_name} {column_definition}"
            )
        except sqlite3.OperationalError:
            pass

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
        """
        Dosya seçimini veritabanına kaydet.

        Args:
            filename: Dosya adı
            file_hash: Dosya hash'i
            file_size: Dosya boyutu
            user_name: Kullanıcı adı
            original_path: Orijinal dosya yolu
            local_path: Yerel dosya yolu
            is_duplicate: Duplicate olup olmadığı

        Returns:
            Kaydedilen kaydın ID'si
        """
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
        """
        API operasyonu logla.

        Args:
            operation_type: İşlem tipi
            user_name: Kullanıcı adı
            file_count: Dosya sayısı
            total_size: Toplam boyut

        Returns:
            Kaydedilen kaydın ID'si
        """
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
        error_message: Optional[str] = None,
    ) -> None:
        """
        API operasyonu güncelle.

        Args:
            operation_id: İşlem ID'si
            success_count: Başarılı sayısı
            error_count: Hatalı sayısı
            error_message: Hata mesajı
        """
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
        error_message: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> None:
        """
        Upload durumunu güncelle.

        Args:
            file_id: Dosya ID'si
            status: Durum
            error_message: Hata mesajı
            start_time: Başlangıç zamanı
        """
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

    def update_processing_status(
        self, status: str, error_message: Optional[str] = None
    ) -> None:
        """
        Tüm yüklenen dosyaların işleme durumunu güncelle.

        Args:
            status: Durum
            error_message: Hata mesajı
        """
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

    def check_duplicate_by_hash(self, file_hash: str) -> bool:
        """
        Aynı hash'e sahip dosya daha önce yüklendi mi kontrol et.

        Args:
            file_hash: Dosya hash'i

        Returns:
            Duplicate olup olmadığı
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM upload_logs WHERE file_hash = ?", (file_hash,)
        )
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def check_duplicate_by_name(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Aynı isimde dosya daha önce yüklendi mi kontrol et.

        Args:
            filename: Dosya adı

        Returns:
            Duplicate bilgileri veya None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, selection_time, overwrite_count, last_duplicate_time
            FROM upload_logs 
            WHERE filename = ? 
            ORDER BY selection_time DESC 
            LIMIT 1
            """,
            (filename,),
        )
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                "id": result[0],
                "last_time": result[1],
                "overwrite_count": result[2] or 0,
                "last_duplicate_time": result[3],
            }
        return None

    def update_duplicate_info(self, filename: str, is_overwrite: bool = False) -> None:
        """
        Duplicate bilgilerini güncelle.

        Args:
            filename: Dosya adı
            is_overwrite: Overwrite işlemi mi
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        if is_overwrite:
            # Overwrite sayacını artır
            cursor.execute(
                """
                UPDATE upload_logs 
                SET overwrite_count = overwrite_count + 1, 
                    last_duplicate_time = ?, 
                    updated_at = ?
                WHERE filename = ?
                """,
                (current_time, current_time, filename),
            )
        else:
            # Sadece duplicate zamanını güncelle
            cursor.execute(
                """
                UPDATE upload_logs 
                SET last_duplicate_time = ?, updated_at = ?
                WHERE filename = ?
                """,
                (current_time, current_time, filename),
            )

        conn.commit()
        conn.close()

    def get_filtered_logs(self, filters: Dict[str, Any]) -> List[Tuple]:
        """
        Filtrelenmiş logları getir.

        Args:
            filters: Filtre kriterleri

        Returns:
            Filtrelenmiş log kayıtları
        """
        base_query = """
            SELECT filename, file_extension, file_size, user_name, selection_time, 
                   upload_end_time, upload_duration_seconds, processing_end_time, 
                   processing_duration_seconds, upload_status, processing_status, 
                   is_duplicate, upload_error_message, processing_error_message,
                   overwrite_count, last_duplicate_time
            FROM upload_logs 
            WHERE 1=1
        """

        conditions = []
        params = []

        # Durum filtresi
        status_filter = filters.get("status_filter", "Tümü")
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
        user_filter = filters.get("user_filter", "Tümü")
        if user_filter and user_filter != "Tümü":
            conditions.append("user_name = ?")
            params.append(user_filter)

        # Tarih filtresi
        date_filter = filters.get("date_filter", "Tümü")
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
        format_filter = filters.get("format_filter", "Tümü")
        if format_filter and format_filter != "Tümü":
            conditions.append("file_extension = ?")
            params.append(format_filter)

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY selection_time DESC"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        conn.close()

        return results

    def get_user_list(self) -> List[str]:
        """Kullanıcı listesini getir."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_name FROM upload_logs ORDER BY user_name")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def get_api_stats(self) -> List[Tuple]:
        """API istatistiklerini getir."""
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
        results = cursor.fetchall()
        conn.close()
        return results

    def get_summary_stats(self) -> Dict[str, Any]:
        """Özet istatistikleri getir."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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

        status_counts = {}
        for upload_status, processing_status, count in cursor.fetchall():
            if processing_status == "completed":
                status_counts["processed"] = status_counts.get("processed", 0) + count
            elif processing_status == "failed":
                status_counts["proc_failed"] = (
                    status_counts.get("proc_failed", 0) + count
                )
            elif upload_status == "uploaded":
                status_counts["uploaded"] = status_counts.get("uploaded", 0) + count
            elif upload_status == "upload_failed":
                status_counts["upload_failed"] = (
                    status_counts.get("upload_failed", 0) + count
                )
            else:
                status_counts["selected"] = status_counts.get("selected", 0) + count

        # Duplicate sayısı
        cursor.execute("SELECT COUNT(*) FROM upload_logs WHERE is_duplicate = 1")
        status_counts["duplicates"] = cursor.fetchone()[0]

        stats["status_counts"] = status_counts

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
        stats["user_stats"] = cursor.fetchall()

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
        stats["format_stats"] = cursor.fetchall()

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
        stats["daily_stats"] = cursor.fetchall()

        conn.close()
        return stats

    def clear_logs(self) -> None:
        """Tüm logları temizle."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM upload_logs")
        cursor.execute("DELETE FROM api_stats")
        conn.commit()
        conn.close()

    def update_upload_status_batch(
        self, status: str, error_message: Optional[str] = None
    ) -> None:
        """Toplu upload durumu güncelle."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status == "uploaded":
            cursor.execute(
                "UPDATE upload_logs SET upload_status = 'uploaded' WHERE upload_status = 'uploading'"
            )
        elif status == "upload_failed":
            cursor.execute(
                "UPDATE upload_logs SET upload_status = 'upload_failed', upload_error_message = ? WHERE upload_status = 'uploading'",
                (error_message,),
            )

        conn.commit()
        conn.close()
