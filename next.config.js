/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  // Ensure static files in app directory are served correctly
  async rewrites() {
    return [
      {
        source: '/confidence-test/questions.v1.json',
        destination: '/api/static/confidence-test/questions.v1.json',
      },
    ]
  },
}

module.exports = nextConfig