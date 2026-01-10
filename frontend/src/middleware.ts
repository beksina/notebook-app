import { auth } from "@/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnLoginPage = req.nextUrl.pathname === "/login";
  const isAuthRoute = req.nextUrl.pathname.startsWith("/api/auth");

  // Allow auth API routes
  if (isAuthRoute) {
    return NextResponse.next();
  }

  // Redirect logged-in users away from login page
  if (isOnLoginPage && isLoggedIn) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  // Redirect unauthenticated users to login
  if (!isLoggedIn && !isOnLoginPage) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
