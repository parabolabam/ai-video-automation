import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    // Get authorization header from client
    const authHeader = request.headers.get('Authorization')

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.error('No authorization header found')
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { name, description } = body

    // For server-side API routes in Docker, use internal container name
    // For local development outside Docker, use localhost
    const apiUrl = process.env.API_URL || 'http://backend:8000'

    // Call backend API with the token from client
    const response = await fetch(`${apiUrl}/api/workflows`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({ name, description }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(error, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Workflow creation error:', error)
    return NextResponse.json(
      { error: 'Failed to create workflow' },
      { status: 500 }
    )
  }
}
