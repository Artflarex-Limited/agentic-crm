import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const AUTH_TOKEN_KEY = 'openclaw_auth_token'
const PUBLIC_PATHS = ['/', '/login', '/api/auth/login', '/api/auth/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (PUBLIC_PATHS.some(path => pathname === path || pathname.startsWith('/api/auth/'))) {
    return NextResponse.next()
  }

  if (pathname.startsWith('/api/')) {
    const token = request.cookies.get(AUTH_TOKEN_KEY)?.value

    if (!token) {
      return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 })
    }

    const requestHeaders = new Headers(request.headers)
    requestHeaders.set('Authorization', `Bearer ${token}`)
    return NextResponse.next({ request: { headers: requestHeaders } })
  }

  if (pathname === '/login') {
    const token = request.cookies.get(AUTH_TOKEN_KEY)?.value
    if (token) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
    return NextResponse.next()
  }

  if (!pathname.startsWith('/dashboard') && pathname !== '/') {
    return NextResponse.next()
  }

  const token = request.cookies.get(AUTH_TOKEN_KEY)?.value

  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|public).*)'],
}