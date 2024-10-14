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
  output: "export",
  distDir: "out",
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