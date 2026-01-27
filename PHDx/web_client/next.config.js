/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Optimize images
  images: {
    domains: [],
  },
}

module.exports = nextConfig
