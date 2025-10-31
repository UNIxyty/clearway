import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for easier deployment
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
