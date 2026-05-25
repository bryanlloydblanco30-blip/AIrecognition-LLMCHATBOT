import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/chat',
        destination: 'http://localhost:3001/', // Proxy to the separate llmchatbot project
      },
      {
        source: '/chat/:path*',
        destination: 'http://localhost:3001/:path*', // Proxy any sub-routes or assets
      },
    ];
  },
};

export default nextConfig;
