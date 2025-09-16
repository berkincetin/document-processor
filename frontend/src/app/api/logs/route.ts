import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function POST(request: NextRequest) {
  try {
    const { message, level, fileId } = await request.json();
    
    const log = await prisma.log.create({
      data: {
        message,
        level,
        fileId: fileId || null,
      },
    });

    return NextResponse.json({ success: true, log });
  } catch (error) {
    console.error('Error saving log:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to save log' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const logs = await prisma.log.findMany({
      orderBy: { timestamp: 'desc' },
      take: 100,
      include: {
        file: true,
      },
    });

    return NextResponse.json({ success: true, logs });
  } catch (error) {
    console.error('Error fetching logs:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch logs' },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    await prisma.log.deleteMany({});
    return NextResponse.json({ success: true, message: 'All logs deleted' });
  } catch (error) {
    console.error('Error deleting logs:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete logs' },
      { status: 500 }
    );
  }
}
