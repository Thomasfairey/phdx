import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { createSession, getCookieOptions } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const { password } = await request.json();

    if (!password) {
      return NextResponse.json(
        { error: "Password is required" },
        { status: 400 }
      );
    }

    const storedHash = process.env.PHDX_PASSWORD_HASH;

    if (!storedHash) {
      // Development mode without password set
      if (process.env.NODE_ENV === "development") {
        const token = await createSession();
        const response = NextResponse.json({ success: true });
        const cookieOptions = getCookieOptions();
        response.cookies.set(cookieOptions.name, token, cookieOptions);
        return response;
      }

      return NextResponse.json(
        { error: "Authentication not configured" },
        { status: 500 }
      );
    }

    // Verify password against stored hash
    const isValid = await bcrypt.compare(password, storedHash);

    if (!isValid) {
      return NextResponse.json(
        { error: "Invalid password" },
        { status: 401 }
      );
    }

    // Create session token
    const token = await createSession();

    // Set cookie and return success
    const response = NextResponse.json({ success: true });
    const cookieOptions = getCookieOptions();
    response.cookies.set(cookieOptions.name, token, cookieOptions);

    return response;
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { error: "An error occurred" },
      { status: 500 }
    );
  }
}
