import type { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// Resolve the private API address at runtime so one image works in local and ECS deployments.
async function proxy(request: NextRequest) {
  const target = new URL(process.env.API_INTERNAL_URL || 'http://localhost:8000');
  target.pathname = request.nextUrl.pathname;
  target.search = request.nextUrl.search;
  const headers = new Headers(request.headers);
  for (const name of ['host', 'connection', 'transfer-encoding', 'content-length']) headers.delete(name);
  try {
    const init: RequestInit & { duplex?: 'half' } = {
      method: request.method, headers, redirect: 'manual', cache: 'no-store',
      signal: request.signal,
    };
    if (!['GET', 'HEAD'].includes(request.method)) {
      init.body = request.body;
      init.duplex = 'half';
    }
    const upstream = await fetch(target, init);
    const responseHeaders = new Headers(upstream.headers);
    for (const name of ['connection', 'transfer-encoding', 'content-encoding', 'content-length']) responseHeaders.delete(name);
    responseHeaders.set('Cache-Control', 'no-store');
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json({ detail: { code: 'api_unavailable', message: 'CivicQuest is temporarily unavailable. Please retry.' } }, { status: 502 });
  }
}

export { proxy as GET, proxy as HEAD, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as OPTIONS };
