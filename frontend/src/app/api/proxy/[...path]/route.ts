import { NextRequest, NextResponse } from 'next/server';

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { searchParams } = new URL(request.url);
  const apiPort = searchParams.get('port') || '5001';
  const resolvedParams = await params;
  const pathSegments = resolvedParams.path;

  try {
    const targetUrl = `http://localhost:${apiPort}/${pathSegments.join('/')}`;
    const queryString = Array.from(searchParams.entries())
      .filter(([key]) => key !== 'port')
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');

    const finalUrl = queryString ? `${targetUrl}?${queryString}` : targetUrl;

    const response = await fetch(finalUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json(data, {
      headers: corsHeaders,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to proxy request' },
      { status: 500, headers: corsHeaders }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: corsHeaders,
  });
}