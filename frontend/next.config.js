/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Указываем, что API доступен через nginx
  env: {
    NEXT_PUBLIC_API_URL: '',
  },
}

module.exports = nextConfig