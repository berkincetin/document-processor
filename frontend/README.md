## Batch Document Upload Frontend (Next.js + Tailwind)

Basit bir arayüz ile bir klasör seçip içindeki desteklenen dosyaları (.txt, .pdf, .docx, .md) otomatik bulur, backend API'ye yükler ve ardından işleme (embedding üretimi + MongoDB kaydı) çağrısını tetikler.

### Özellikler
- Klasör seçici (directory picker)
- Desteklenen dosyaları otomatik bulma (.txt, .pdf, .docx, .md)
- Yükle ve İşle akışı: `/embeddings/upload` ve `/embeddings/process-uploads`
- Ortam seçici (Local / Production)
- Dosya meta bilgilerini tablo halinde gösterme (ad, yol, boyut, durum, zaman)

### Gereksinimler
- Node 18+
- Chromium tabanlı tarayıcı (Chrome/Edge) – `webkitdirectory` desteği için önerilir
- Backend FastAPI servisleri (CORS açık olmalı):
  - Local: `http://localhost:8000`
  - Production: `http://10.1.1.172:3820`

### Kurulum ve Çalıştırma
```bash
cd frontend
npm install
npm run dev
```
Tarayıcıda `http://localhost:3000` adresini açın.

### Kullanım
1. Sayfadaki “Ortam” açılır menüsünden Local veya Production seçin.
2. “Klasör Seç” alanından bir dizin seçin (içindeki .txt/.pdf/.docx/.md dosyaları otomatik filtrelenir).
3. “Upload & Process Files” butonuna tıklayın.
4. Tablo üzerinden dosya adlarını, yollarını, boyutlarını, host ortamını ve durumlarını izleyin.

### API Uç Noktaları
- Yükleme (POST):
  - Local: `http://localhost:8000/embeddings/upload`
  - Prod:  `http://10.1.1.172:3820/embeddings/upload`
- İşleme (POST):
  - Local: `http://localhost:8000/embeddings/process-uploads`
  - Prod:  `http://10.1.1.172:3820/embeddings/process-uploads`

Gönderim şekli: Frontend `FormData` ile `files` alanında çoklu dosya gönderir.

### Notlar ve İpuçları
- `webkitdirectory` HTML özelliği standart değildir ancak Chrome/Edge/Safari'de desteklenir. Firefox'ta klasör seçici için farklı çözümler gerekebilir.
- CORS: Backend tarafında bu frontend’in domaininden gelen isteklere izin verildiğinden emin olun.
- Büyük klasörlerde dosya adedi fazla ise tarayıcı tarafında ilk seçimde biraz gecikme görülebilir.

### Geliştirme
- Ana sayfa: `src/app/page.tsx`
- Tailwind sınıfları doğrudan JSX üzerinde kullanılır.

