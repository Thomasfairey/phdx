import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";

const COOKIE_NAME = "phdx-auth";
const PUBLIC_PATHS = ["/login", "/api/auth/login", "/api/auth/logout"];

function getSecret() {
  const secret = process.env.PHDX_AUTH_SECRET;
  if (!secret) {
    // In development without env vars, allow access
    if (process.env.NODE_ENV === "development") {
      return null;
    }
    throw new Error("PHDX_AUTH_SECRET environment variable is not set");
  }
  return new TextEncoder().encode(secret);
}

async function verifyToken(token: string): Promise<boolean> {
  try {
    const secret = getSecret();
    if (!secret) return true; // Development bypass

    const { payload } = await jwtVerify(token, secret);
    return payload.authenticated === true;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // Allow static files and Next.js internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check for auth in development without env vars
  if (process.env.NODE_ENV === "development" && !process.env.PHDX_AUTH_SECRET) {
    return NextResponse.next();
  }

  // Check authentication
  const token = request.cookies.get(COOKIE_NAME)?.value;

  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const isValid = await verifyToken(token);
  if (!isValid) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete(COOKIE_NAME);
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
