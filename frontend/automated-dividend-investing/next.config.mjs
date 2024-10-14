/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  distDir: 'out',
  trailingSlash: true,
  experimental: {
    outputFileTracingRoot: path.join(__dirname, 'out'),
  },
  // Enable detailed logging for API routes
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
  // Ensure API routes are not accidentally treated as pages
  pageExtensions: ["js", "jsx", "ts", "tsx"],
  // Add security headers and CORS configuration
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://nextjs.org; font-src 'self' data:;",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
      {
        // Add CORS headers for API routes
        source: "/api/:path*",
        headers: [
          { key: "Access-Control-Allow-Credentials", value: "true" },
          {
            key: "Access-Control-Allow-Origin",
            value:
              process.env.NEXT_PUBLIC_FRONTEND_URL ||
              "https://hhs-webapp-dzdteyffa5gmgkh4.eastus-01.azurewebsites.net",
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET,DELETE,PATCH,POST,PUT",
          },
          {
            key: "Access-Control-Allow-Headers",
            value:
              "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version",
          },
        ],
      },
    ];
  },
  // Enable more detailed NextAuth.js logging
  serverRuntimeConfig: {
    nextauth: {
      debug: true,
    },
  },
  webpack: (config, { isServer, dev }) => {
    if (isServer) {
      const originalEntry = config.entry;
      config.entry = async () => {
        const entries = await originalEntry();
        const redisPath = path.join(__dirname, "src", "lib", "redis.ts");
        if (entries["main.js"] && !entries["main.js"].includes(redisPath)) {
          entries["main.js"].unshift(redisPath);
        }
        return entries;
      };
    }

    if (dev) {
      config.devServer = {
        hot: true,
        hotOnly: true,
      };
    }

    return config;
  },
};

export default nextConfig;