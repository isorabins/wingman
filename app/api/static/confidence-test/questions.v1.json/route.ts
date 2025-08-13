import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET() {
  try {
    const filePath = join(process.cwd(), 'app', 'confidence-test', 'questions.v1.json')
    const fileContent = await readFile(filePath, 'utf8')
    const data = JSON.parse(fileContent)
    
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    })
  } catch (error) {
    console.error('Error reading questions file:', error)
    return NextResponse.json(
      { error: 'Questions file not found' },
      { status: 404 }
    )
  }
}