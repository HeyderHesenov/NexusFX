/** @type {import('next').NextConfig} */
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

// Content-Security-Policy — Next (HMR: eval+ws), inline tema skripti, Google GIS
// və xarici xəbər şəkilləri işləsin deyə tənzimlənib.
const CSP = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'self'",
  "form-action 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https:",
  "font-src 'self' data:",
  "connect-src 'self' http://localhost:* ws://localhost:* https://www.googleapis.com https://accounts.google.com",
  "frame-src https://accounts.google.com",
].join("; ");

const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CSP },
  { key: "X-Frame-Options", value: "SAMEORIGIN" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig = {
  reactStrictMode: true,
  images: {
    // Xəbər şəkilləri xarici mənbələrdən gəlir — istənilən hosta icazə.
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  async rewrites() {
    // Frontend /api/* → backend (CORS-suz lokal proxy).
    return [{ source: "/backend/:path*", destination: `${API_BASE}/:path*` }];
  },
};

export default nextConfig;
