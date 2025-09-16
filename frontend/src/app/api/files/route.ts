import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function POST(request: NextRequest) {
  try {
    const fileData = await request.json();
    
    const file = await prisma.fileMetadata.create({
      data: {
        name: fileData.name,
        sizeBytes: fileData.sizeBytes,
        relativePath: fileData.relativePath,
        lastModified: fileData.lastModified,
        selectedAt: new Date(fileData.selectedAt),
        uploadedAt: fileData.uploadedAt ? new Date(fileData.uploadedAt) : null,
        processedAt: fileData.processedAt ? new Date(fileData.processedAt) : null,
        host: fileData.host,
        status: fileData.status,
        errorMessage: fileData.errorMessage,
        computerName: fileData.computerName,
        userName: fileData.userName,
        userAgent: fileData.userAgent,
        uploadDuration: fileData.uploadDuration,
        processDuration: fileData.processDuration,
        fileType: fileData.fileType,
        mimeType: fileData.mimeType,
        checksum: fileData.checksum,
        retryCount: fileData.retryCount || 0,
      },
    });

    return NextResponse.json({ success: true, file });
  } catch (error) {
    console.error('Error saving file:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to save file' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const { id, ...updateData } = await request.json();
    
    const file = await prisma.fileMetadata.update({
      where: { id },
      data: {
        ...updateData,
        uploadedAt: updateData.uploadedAt ? new Date(updateData.uploadedAt) : null,
        processedAt: updateData.processedAt ? new Date(updateData.processedAt) : null,
      },
    });

    return NextResponse.json({ success: true, file });
  } catch (error) {
    console.error('Error updating file:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update file' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const files = await prisma.fileMetadata.findMany({
      orderBy: { selectedAt: 'desc' },
      include: {
        logs: {
          orderBy: { timestamp: 'desc' },
          take: 10,
        },
      },
    });

    return NextResponse.json({ success: true, files });
  } catch (error) {
    console.error('Error fetching files:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch files' },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    await prisma.fileMetadata.deleteMany({});
    return NextResponse.json({ success: true, message: 'All files deleted' });
  } catch (error) {
    console.error('Error deleting files:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete files' },
      { status: 500 }
    );
  }
}
