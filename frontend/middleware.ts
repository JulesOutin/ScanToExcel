/**
 * Rafraîchit la session Supabase à chaque requête et protège les pages privées
 * (/app, /documents/*, /facturation). La racine "/" et "/login" restent publiques
 * (landing page SEO + connexion).
 */
import { NextResponse, type NextRequest } from "next/server";
import { supabaseMiddlewareClient } from "@/lib/supabase";

const PROTECTED_PREFIXES = ["/app", "/documents", "/facturation"];

export async function middleware(request: NextRequest) {
  const response = NextResponse.next({ request: { headers: request.headers } });
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
  const isLogin = pathname === "/login";

  if (!isProtected && !isLogin) {
    return response; // page publique : pas besoin de vérifier la session
  }

  const supabase = supabaseMiddlewareClient(request, response);
  const { data } = await supabase.auth.getUser();

  if (isProtected && !data.user) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  if (isLogin && data.user) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/app";
    redirectUrl.search = "";
    return NextResponse.redirect(redirectUrl);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|webp|xml|txt)$).*)"],
};
