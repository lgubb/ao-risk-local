/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
      {
        source: "/viewer/:path*",
        destination: "http://localhost:8000/viewer/:path*",
      },
      {
        source: "/files/:path*",
        destination: "http://localhost:8000/files/:path*",
      },
    ];
  },
};

export default nextConfig;
