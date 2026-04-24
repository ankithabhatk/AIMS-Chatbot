import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  devIndicators: false,
  distDir: ".next-web",
  experimental: {
    workerThreads: true,
    webpackBuildWorker: false,
  },
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
