-- CreateTable
CREATE TABLE "FileMetadata" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "sizeBytes" INTEGER NOT NULL,
    "relativePath" TEXT,
    "lastModified" INTEGER NOT NULL,
    "selectedAt" DATETIME NOT NULL,
    "uploadedAt" DATETIME,
    "processedAt" DATETIME,
    "host" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "errorMessage" TEXT,
    "computerName" TEXT,
    "userName" TEXT,
    "userAgent" TEXT,
    "uploadDuration" INTEGER,
    "processDuration" INTEGER,
    "fileType" TEXT,
    "mimeType" TEXT,
    "checksum" TEXT,
    "retryCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Log" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "message" TEXT NOT NULL,
    "level" TEXT NOT NULL,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "fileId" TEXT,
    CONSTRAINT "Log_fileId_fkey" FOREIGN KEY ("fileId") REFERENCES "FileMetadata" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "FileMetadata_status_idx" ON "FileMetadata"("status");

-- CreateIndex
CREATE INDEX "FileMetadata_host_idx" ON "FileMetadata"("host");

-- CreateIndex
CREATE INDEX "FileMetadata_selectedAt_idx" ON "FileMetadata"("selectedAt");

-- CreateIndex
CREATE INDEX "FileMetadata_uploadedAt_idx" ON "FileMetadata"("uploadedAt");

-- CreateIndex
CREATE INDEX "Log_timestamp_idx" ON "Log"("timestamp");

-- CreateIndex
CREATE INDEX "Log_level_idx" ON "Log"("level");

-- CreateIndex
CREATE INDEX "Log_fileId_idx" ON "Log"("fileId");
