"""
Rapor oluşturma işlemleri için modül.

Bu modül HTML ve CSV raporları oluşturur.
"""

import csv
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict


class ReportGenerator:
    """Rapor oluşturma işlemlerini yöneten sınıf."""

    def __init__(self, file_manager):
        """
        ReportGenerator'ı başlat.

        Args:
            file_manager: FileManager instance'ı
        """
        self.file_manager = file_manager

    def format_duration(self, seconds: float) -> str:
        """
        Süreyi formatla.

        Args:
            seconds: Saniye cinsinden süre

        Returns:
            Formatlanmış süre string'i
        """
        if seconds is None:
            return ""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"

    def generate_detail_report(
        self, columns: List[str], data: List[Tuple], filepath: str
    ) -> bool:
        """
        Detaylı rapor oluştur.

        Args:
            columns: Kolon başlıkları
            data: Rapor verileri
            filepath: Kayıt dosya yolu

        Returns:
            Rapor oluşturma başarılı olup olmadığı
        """
        try:
            if filepath.endswith(".csv"):
                return self._generate_csv_report(filepath, columns, data)
            else:
                return self._generate_html_detail_report(filepath, columns, data)
        except Exception as e:
            print(f"Detay rapor oluşturma hatası: {e}")
            return False

    def _generate_csv_report(
        self, filepath: str, columns: List[str], data: List[Tuple]
    ) -> bool:
        """CSV rapor oluştur."""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"CSV raporu oluşturulamadı: {e}")
            return False

    def _generate_html_detail_report(
        self, filepath: str, columns: List[str], data: List[Tuple]
    ) -> bool:
        """HTML detay rapor oluştur."""
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
                        html_content += (
                            f"<td>{self.file_manager.format_file_size(cell)}</td>"
                        )
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
            return True
        except Exception as e:
            print(f"HTML raporu oluşturulamadı: {e}")
            return False

    def generate_summary_report(self, stats: Dict[str, Any], filepath: str) -> bool:
        """
        Özet rapor oluştur.

        Args:
            stats: İstatistik verileri
            filepath: Kayıt dosya yolu

        Returns:
            Rapor oluşturma başarılı olup olmadığı
        """
        try:
            return self._generate_html_summary_report(filepath, stats)
        except Exception as e:
            print(f"Özet rapor oluşturma hatası: {e}")
            return False

    def _generate_html_summary_report(
        self, filepath: str, stats: Dict[str, Any]
    ) -> bool:
        """HTML özet rapor oluştur."""
        try:
            status_counts = stats["status_counts"]
            user_stats = stats["user_stats"]
            format_stats = stats["format_stats"]
            daily_stats = stats["daily_stats"]

            total_processed = status_counts.get("processed", 0)
            total_failed = status_counts.get("upload_failed", 0) + status_counts.get(
                "proc_failed", 0
            )
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
                <div class="stat-number success">{status_counts.get('processed', 0)}</div>
                <div class="stat-label">İşlenmiş Dosya</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{status_counts.get('uploaded', 0)}</div>
                <div class="stat-label">Yüklenmiş (Bekleyen)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{total_failed}</div>
                <div class="stat-label">Başarısız</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{status_counts.get('duplicates', 0)}</div>
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
        <p style="text-align: center; margin-top: 10px;">Başarı Oranı: {success_rate:.1f}% ({status_counts.get('processed', 0)}/{stats['total_files']} dosya)</p>
        
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
                size_formatted = self.file_manager.format_file_size(total_size or 0)

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
                size_formatted = self.file_manager.format_file_size(total_size or 0)
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
                <div class="stat-number">{status_counts.get('selected', 0)}</div>
                <div class="stat-label">Seçilmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #2196F3;">{status_counts.get('uploaded', 0)}</div>
                <div class="stat-label">Yüklenmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{status_counts.get('processed', 0)}</div>
                <div class="stat-label">İşlenmiş</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{status_counts.get('upload_failed', 0)}</div>
                <div class="stat-label">Yükleme Hatası</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{status_counts.get('proc_failed', 0)}</div>
                <div class="stat-label">İşleme Hatası</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{status_counts.get('duplicates', 0)}</div>
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
            return True
        except Exception as e:
            print(f"HTML özet raporu oluşturulamadı: {e}")
            return False
