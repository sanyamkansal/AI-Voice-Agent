import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const { imageBase64 } = await request.json();
    const filePath = path.join(process.cwd(), '..', 'backend', 'latest_receipt.txt');
    fs.writeFileSync(filePath, imageBase64, 'utf8');
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Failed to upload' }, { status: 500 });
  }
}
