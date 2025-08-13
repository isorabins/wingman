/** @type {import('next').NextConfig} */
const nextConfig = {
  // App directory is now stable in Next.js 14
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