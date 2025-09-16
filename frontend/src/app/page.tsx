"use client";

import { useMemo, useState, useEffect } from "react";

type Environment = "local" | "production";

type FileStatus = "pending" | "uploaded" | "processed" | "error";

interface FileMetadata {
  id: string;
  name: string;
  sizeBytes: number;
  relativePath?: string;
  lastModified: number;
  selectedAt?: string;
  uploadedAt?: string;
  processedAt?: string;
  host: Environment;
  status: FileStatus;
  errorMessage?: string;
  computerName?: string;
  userName?: string;
  userAgent?: string;
  uploadDuration?: number;
  processDuration?: number;
  fileType?: string;
  mimeType?: string;
  checksum?: string;
  retryCount?: number;
}

const SUPPORTED_EXTENSIONS = [".txt", ".pdf", ".docx", ".md"] as const;

function getApiBaseUrl(env: Environment): string {
  return env === "local"
    ? "http://localhost:8000"
    : "http://10.1.1.172:3820";
}

function getUploadEndpoint(env: Environment): string {
  return `${getApiBaseUrl(env)}/embeddings/upload`;
}

function getProcessEndpoint(env: Environment): string {
  return `${getApiBaseUrl(env)}/embeddings/process-uploads`;
}

function isSupportedFile(file: File): boolean {
  const lower = file.name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function getComputerInfo(): { computerName: string; userName: string } {
  if (typeof window !== 'undefined') {
    const platform = window.navigator.platform || 'Unknown';
    const userAgent = window.navigator.userAgent;
    
    // Try to extract username from various sources
    let userName = 'Unknown';
    
    // Try to get from localStorage if available
    if (localStorage.getItem('userName')) {
      userName = localStorage.getItem('userName') || 'Unknown';
    }
    
    // Try to extract from userAgent (Windows specific)
    if (userAgent.includes('Windows')) {
      const match = userAgent.match(/Windows NT \d+\.\d+; (.+?)(?:\s|$)/);
      if (match) {
        userName = match[1] || 'Unknown';
      }
    }
    
    return {
      computerName: platform,
      userName: userName
    };
  }
  return { computerName: 'Unknown', userName: 'Unknown' };
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('tr-TR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('tr-TR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('tr-TR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function getFileType(file: File): string {
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  const mimeType = file.type;
  
  if (extension === 'pdf') return 'PDF Document';
  if (extension === 'docx') return 'Word Document';
  if (extension === 'txt') return 'Text File';
  if (extension === 'md') return 'Markdown File';
  
  return mimeType || 'Unknown';
}

export default function Home() {
  const [environment, setEnvironment] = useState<Environment>("local");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileMetadata, setFileMetadata] = useState<FileMetadata[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [showAdvancedLogs, setShowAdvancedLogs] = useState<boolean>(false);

  const filteredFiles = useMemo(() => {
    return selectedFiles.filter(isSupportedFile);
  }, [selectedFiles]);

  // Load data from database on component mount
  useEffect(() => {
    async function loadDataFromDatabase() {
      try {
        // Load files
        const filesResponse = await fetch('/api/files');
        if (filesResponse.ok) {
          const result = await filesResponse.json();
                  if (result.success && result.files.length > 0) {
          setFileMetadata(result.files);
          addLogSync(`Veritabanından ${result.files.length} dosya yüklendi`, 'info');
        }
        }
        
        // Load logs
        const logsResponse = await fetch('/api/logs');
        if (logsResponse.ok) {
          const result = await logsResponse.json();
          if (result.success && result.logs.length > 0) {
            const formattedLogs = result.logs.map((log: any) => {
              const timestamp = new Date(log.timestamp).toLocaleTimeString();
              const levelIcon = {
                info: 'ℹ️',
                success: '✅',
                warning: '⚠️',
                error: '❌'
              }[log.level as 'info' | 'success' | 'warning' | 'error'] || 'ℹ️';
              return `[${timestamp}] ${levelIcon} ${log.message}`;
            });
            setLogs(formattedLogs);
            addLogSync(`Veritabanından ${result.logs.length} log yüklendi`, 'info');
          }
        }
      } catch (error) {
        console.error('Failed to load data from database:', error);
        addLogSync('Veritabanından veri yüklenirken hata oluştu', 'error');
      }
    }
    
    loadDataFromDatabase();
  }, []);

  async function addLog(message: string, level: 'info' | 'success' | 'warning' | 'error' = 'info', fileId?: string): Promise<void> {
    const timestamp = new Date().toLocaleTimeString();
    const levelIcon = {
      info: 'ℹ️',
      success: '✅',
      warning: '⚠️',
      error: '❌'
    }[level];
    
    const logMessage = `[${timestamp}] ${levelIcon} ${message}`;
    setLogs(prev => [logMessage, ...prev.slice(0, 99)]);
    
    // Save to database (only if not in useEffect)
    if (typeof window !== 'undefined') {
      try {
        await fetch('/api/logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, level, fileId }),
        });
      } catch (error) {
        console.error('Failed to save log to database:', error);
      }
    }
  }

  // Non-async version for useEffect
  function addLogSync(message: string, level: 'info' | 'success' | 'warning' | 'error' = 'info'): void {
    const timestamp = new Date().toLocaleTimeString();
    const levelIcon = {
      info: 'ℹ️',
      success: '✅',
      warning: '⚠️',
      error: '❌'
    }[level];
    
    const logMessage = `[${timestamp}] ${levelIcon} ${message}`;
    setLogs(prev => [logMessage, ...prev.slice(0, 99)]);
  }

  async function handleFolderChange(event: React.ChangeEvent<HTMLInputElement>): Promise<void> {
    const fileList = event.target.files;
    if (!fileList) {
      setSelectedFiles([]);
      setFileMetadata([]);
      setLogs([]);
      return;
    }

    // Convert FileList to Array and keep only supported files
    const files = Array.from(fileList);
    const supported = files.filter(isSupportedFile);
    setSelectedFiles(supported);

    const nowIso = new Date().toISOString();
    const { computerName, userName } = getComputerInfo();
    
    addLog(`Klasör seçildi: ${supported.length} desteklenen dosya bulundu (${files.length} toplam)`, 'info');
    
    const metas: FileMetadata[] = supported.map((file, index) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${index}`,
      name: file.name,
      sizeBytes: file.size,
      relativePath: (file as File & { webkitRelativePath?: string }).webkitRelativePath ?? undefined,
      lastModified: file.lastModified,
      selectedAt: nowIso,
      uploadedAt: undefined,
      processedAt: undefined,
      host: environment,
      status: "pending",
      errorMessage: undefined,
      computerName,
      userName,
      userAgent: navigator.userAgent,
      uploadDuration: undefined,
      processDuration: undefined,
      fileType: getFileType(file),
      mimeType: file.type,
      checksum: undefined,
      retryCount: 0,
    }));
    setFileMetadata(metas);
    
    // Save files to database and log details
    for (const [index, file] of supported.entries()) {
      try {
        const response = await fetch('/api/files', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(metas[index]),
        });
        
        if (response.ok) {
          const result = await response.json();
          // Update the ID with the database ID
          metas[index].id = result.file.id;
          await addLog(`Dosya: ${file.name} (${formatFileSize(file.size)}) - ${file.type || 'Unknown type'}`, 'info', result.file.id);
        }
      } catch (error) {
        console.error('Failed to save file to database:', error);
        await addLog(`Dosya: ${file.name} (${formatFileSize(file.size)}) - ${file.type || 'Unknown type'}`, 'info');
      }
    }
    
    setFileMetadata([...metas]);
  }

  async function uploadFiles(): Promise<Response> {
    const formData = new FormData();
    for (const file of filteredFiles) {
      formData.append("files", file, file.name);
    }
    const endpoint = getUploadEndpoint(environment);
    addLog(`Upload endpoint: ${endpoint}`, 'info');
    return fetch(endpoint, {
      method: "POST",
      body: formData,
    });
  }

  async function processUploaded(): Promise<Response> {
    const endpoint = getProcessEndpoint(environment);
    addLog(`Process endpoint: ${endpoint}`, 'info');
    return fetch(endpoint, { method: "POST" });
  }

  async function handleUploadOnly(): Promise<void> {
    if (filteredFiles.length === 0) {
      addLog("Hata: Geçerli dosya bulunamadı (.txt, .pdf, .docx, .md)", 'error');
      return;
    }
    
    setIsUploading(true);
    addLog(`Yükleme başlatılıyor... ${filteredFiles.length} dosya, toplam boyut: ${formatFileSize(filteredFiles.reduce((sum, f) => sum + f.size, 0))}`, 'info');

    try {
      const startTime = Date.now();
      const uploadResp = await uploadFiles();
      const endTime = Date.now();
      const duration = endTime - startTime;

      if (!uploadResp.ok) {
        const text = await uploadResp.text();
        throw new Error(`Yükleme başarısız: ${uploadResp.status} ${text}`);
      }

      // Mark all as uploaded
      const uploadedAt = new Date().toISOString();
      const updatedMetas = fileMetadata.map((m) => ({ ...m, status: "uploaded" as FileStatus, uploadedAt, uploadDuration: duration }));
      setFileMetadata(updatedMetas);
      
      // Update database
      for (const meta of updatedMetas) {
        try {
          await fetch('/api/files', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id: meta.id,
              status: meta.status,
              uploadedAt: meta.uploadedAt,
              uploadDuration: meta.uploadDuration,
            }),
          });
        } catch (error) {
          console.error('Failed to update file in database:', error);
        }
      }
      
      addLog(`✅ Yükleme tamamlandı! ${filteredFiles.length} dosya ${formatDuration(duration)}'de yüklendi`, 'success');
      
      // Log individual file upload times
      for (const file of filteredFiles) {
        const meta = updatedMetas.find(m => m.name === file.name);
        await addLog(`📤 ${file.name}: ${formatFileSize(file.size)} yüklendi`, 'success', meta?.id);
      }
      
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Bilinmeyen hata";
      const updatedMetas = fileMetadata.map((m) => ({ ...m, status: "error" as FileStatus, errorMessage: message, retryCount: (m.retryCount || 0) + 1 }));
      setFileMetadata(updatedMetas);
      
      // Update database
      for (const meta of updatedMetas) {
        try {
          await fetch('/api/files', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id: meta.id,
              status: meta.status,
              errorMessage: meta.errorMessage,
              retryCount: meta.retryCount,
            }),
          });
        } catch (error) {
          console.error('Failed to update file in database:', error);
        }
      }
      
      await addLog(`❌ Yükleme hatası: ${message}`, 'error');
    } finally {
      setIsUploading(false);
    }
  }

  async function handleProcessOnly(): Promise<void> {
    const uploadedFiles = fileMetadata.filter(f => f.status === "uploaded");
    if (uploadedFiles.length === 0) {
      addLog("Hata: İşlenecek yüklenmiş dosya bulunamadı", 'error');
      return;
    }

    setIsProcessing(true);
    addLog(`İşleme başlatılıyor... ${uploadedFiles.length} yüklenmiş dosya`, 'info');

    try {
      const startTime = Date.now();
      const processResp = await processUploaded();
      const endTime = Date.now();
      const duration = endTime - startTime;

      if (!processResp.ok) {
        const text = await processResp.text();
        throw new Error(`İşleme başarısız: ${processResp.status} ${text}`);
      }
      
      const processedAt = new Date().toISOString();
      const updatedMetas = fileMetadata.map((m) => ({ ...m, status: "processed" as FileStatus, processedAt, processDuration: duration }));
      setFileMetadata(updatedMetas);
      
      // Update database
      for (const meta of updatedMetas) {
        try {
          await fetch('/api/files', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id: meta.id,
              status: meta.status,
              processedAt: meta.processedAt,
              processDuration: meta.processDuration,
            }),
          });
        } catch (error) {
          console.error('Failed to update file in database:', error);
        }
      }
      
      addLog(`✅ İşleme tamamlandı! ${uploadedFiles.length} dosya ${formatDuration(duration)}'de işlendi`, 'success');
      
      // Log individual file processing
      for (const file of uploadedFiles) {
        const meta = updatedMetas.find(m => m.name === file.name);
        await addLog(`🔄 ${file.name}: işlendi`, 'success', meta?.id);
      }
      
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Bilinmeyen hata";
      const updatedMetas = fileMetadata.map((m) => ({ ...m, status: "error" as FileStatus, errorMessage: message, retryCount: (m.retryCount || 0) + 1 }));
      setFileMetadata(updatedMetas);
      
      // Update database
      for (const meta of updatedMetas) {
        try {
          await fetch('/api/files', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id: meta.id,
              status: meta.status,
              errorMessage: meta.errorMessage,
              retryCount: meta.retryCount,
            }),
          });
        } catch (error) {
          console.error('Failed to update file in database:', error);
        }
      }
      
      await addLog(`❌ İşleme hatası: ${message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  }

  async function handleUploadAndProcess(): Promise<void> {
    await handleUploadOnly();
    if (fileMetadata.some(f => f.status === "uploaded")) {
      await handleProcessOnly();
    }
  }

  async function clearLogs(): Promise<void> {
    setLogs([]);
    await addLog("Loglar temizlendi", 'info');
  }

  async function exportLogs(): Promise<void> {
    const logText = logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `upload-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    await addLog("Loglar dışa aktarıldı", 'success');
  }

  async function clearDatabase(): Promise<void> {
    if (!confirm('Tüm veritabanı verilerini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!')) {
      return;
    }
    
    try {
      // Clear files
      await fetch('/api/files', { method: 'DELETE' });
      // Clear logs
      await fetch('/api/logs', { method: 'DELETE' });
      
      setFileMetadata([]);
      setLogs([]);
      await addLog("Veritabanı temizlendi", 'success');
    } catch (error) {
      console.error('Failed to clear database:', error);
      await addLog('Veritabanı temizlenirken hata oluştu', 'error');
    }
  }

  return (
    <div className="min-h-screen w-full bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            📁 Batch Document Upload
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Klasör seçin, dosyaları yükleyin ve işleyin
          </p>
        </div>

        {/* Main Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
          {/* Environment Selector */}
          <div className="lg:col-span-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              🌍 Ortam
            </label>
            <select
              className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value as Environment)}
            >
              <option value="local">🖥️ Local</option>
              <option value="production">🚀 Production</option>
            </select>
          </div>

          {/* Folder Picker */}
          <div className="lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              📂 Klasör Seç
            </label>
            <input
              type="file"
              {...({ webkitdirectory: "true" } as any)}
              {...({ directory: "true" } as any)}
              accept=".txt,.pdf,.docx,.md"
              multiple
              onChange={handleFolderChange}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900 dark:file:text-blue-300"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Desteklenen: .txt, .pdf, .docx, .md
            </p>
          </div>
        </div>

        {/* Action Buttons & Status */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={handleUploadOnly}
              disabled={isUploading || filteredFiles.length === 0}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Yükleniyor...
                </>
              ) : (
                <>
                  📤 Yükle
                </>
              )}
            </button>

            <button
              onClick={handleProcessOnly}
              disabled={isProcessing || !fileMetadata.some(f => f.status === "uploaded")}
              className="px-4 py-2 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  İşleniyor...
                </>
              ) : (
                <>
                  🔄 İşle
                </>
              )}
            </button>

            <button
              onClick={handleUploadAndProcess}
              disabled={isUploading || isProcessing || filteredFiles.length === 0}
              className="px-4 py-2 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isUploading || isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {isUploading ? "Yükleniyor..." : "İşleniyor..."}
                </>
              ) : (
                <>
                  🚀 Yükle & İşle
                </>
              )}
            </button>

            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 ml-auto">
              <span className="font-medium">{filteredFiles.length} dosya</span>
              {fileMetadata.some(f => f.status === "uploaded") && (
                <span className="text-green-600 dark:text-green-400">
                  {fileMetadata.filter(f => f.status === "uploaded").length} yüklendi
                </span>
              )}
              {fileMetadata.some(f => f.status === "processed") && (
                <span className="text-blue-600 dark:text-blue-400">
                  {fileMetadata.filter(f => f.status === "processed").length} işlendi
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Files Table */}
          <div className="xl:col-span-2">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">
                📊 Dosya Detayları
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">📄 Dosya</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">📏 Boyut</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">📁 Yol</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">👤 Kullanıcı</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">🌍 Host</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">📊 Durum</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">📅 Tarihler</th>
                      <th className="text-left p-2 font-medium text-gray-900 dark:text-white">⚡ Süre</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fileMetadata.length === 0 ? (
                      <tr>
                        <td className="p-2 text-gray-500 dark:text-gray-400" colSpan={8}>
                          Henüz dosya seçilmedi.
                        </td>
                      </tr>
                    ) : (
                      fileMetadata.map((m) => (
                        <tr key={m.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="p-2 font-medium max-w-32 truncate" title={m.name}>
                            <div className="flex flex-col">
                              <span>{m.name}</span>
                              <span className="text-xs text-gray-500">{m.fileType}</span>
                            </div>
                          </td>
                          <td className="p-2 text-gray-600 dark:text-gray-300">
                            {formatFileSize(m.sizeBytes)}
                          </td>
                          <td className="p-2 text-gray-600 dark:text-gray-300 max-w-24 truncate" title={m.relativePath}>
                            {m.relativePath ?? "-"}
                          </td>
                          <td className="p-2 text-gray-600 dark:text-gray-300 max-w-20 truncate" title={m.userName}>
                            {m.userName}
                          </td>
                          <td className="p-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              m.host === "local" 
                                ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" 
                                : "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            }`}>
                              {m.host}
                            </span>
                          </td>
                          <td className="p-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              m.status === "pending" && "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                              || m.status === "uploaded" && "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                              || m.status === "processed" && "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              || m.status === "error" && "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                            }`}>
                              {m.status === "pending" && "⏳"}
                              {m.status === "uploaded" && "📤"}
                              {m.status === "processed" && "✅"}
                              {m.status === "error" && "❌"}
                            </span>
                            {m.retryCount && m.retryCount > 0 && (
                              <span className="ml-1 text-xs text-red-600">({m.retryCount})</span>
                            )}
                          </td>
                          <td className="p-2 text-gray-600 dark:text-gray-300 text-xs">
                            <div className="flex flex-col">
                              {m.selectedAt && (
                                <span title={formatDateTime(m.selectedAt)}>
                                  📅 {formatDate(m.selectedAt)}
                                </span>
                              )}
                              {m.uploadedAt && (
                                <span title={formatDateTime(m.uploadedAt)}>
                                  📤 {formatDate(m.uploadedAt)}
                                </span>
                              )}
                              {m.processedAt && (
                                <span title={formatDateTime(m.processedAt)}>
                                  🔄 {formatDate(m.processedAt)}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="p-2 text-gray-600 dark:text-gray-300 text-xs">
                            <div className="flex flex-col">
                              {m.uploadDuration ? `📤 ${formatDuration(m.uploadDuration)}` : "-"}
                              {m.processDuration ? `🔄 ${formatDuration(m.processDuration)}` : ""}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Logs Section */}
          <div className="xl:col-span-1">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  📋 İşlem Logları
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={clearLogs}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded"
                  >
                    🗑️ Temizle
                  </button>
                  <button
                    onClick={exportLogs}
                    className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 rounded"
                  >
                    📥 Export
                  </button>
                  <button
                    onClick={clearDatabase}
                    className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 rounded"
                  >
                    🗃️ DB Temizle
                  </button>
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 h-80 overflow-y-auto font-mono text-xs">
                {logs.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400">Henüz işlem yapılmadı...</p>
                ) : (
                  logs.map((log, index) => (
                    <div key={index} className="text-gray-700 dark:text-gray-300 mb-1 break-words border-b border-gray-100 dark:border-gray-800 pb-1">
                      {log}
                    </div>
                  ))
                )}
              </div>
              
              <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                Toplam: {logs.length} log kaydı
                <br />
                <span className="text-green-600">💾 SQLite veritabanında saklanıyor</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
