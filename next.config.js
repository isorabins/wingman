// Bundle analyzer configuration (inline to avoid TS import issues)
const getBundleAnalysisConfig = (analyze = false) => ({
  webpack: (config, { dev, isServer }) => {
    if (analyze && !dev && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: 'bundle-analysis.html',
          generateStatsFile: true,
          statsFilename: 'bundle-stats.json'
        })
      );
    }
    return config;
  }
});

const getWebpackOptimizations = () => ({
  webpack: (config) => {
    config.optimization.splitChunks = {
      chunks: 'all',
      minSize: 20000,
      maxSize: 244000,
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 20
        },
        chakra: {
          test: /[\\/]node_modules[\\/]@chakra-ui[\\/]/,
          name: 'chakra-ui',
          chunks: 'all',
          priority: 30
        },
        emotion: {
          test: /[\\/]node_modules[\\/]@emotion[\\/]/,
          name: 'emotion',
          chunks: 'all',
          priority: 30
        },
        supabase: {
          test: /[\\/]node_modules[\\/]@supabase[\\/]/,
          name: 'supabase',
          chunks: 'all',
          priority: 30
        },
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react-vendor',
          chunks: 'all',
          priority: 40
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: 10,
          reuseExistingChunk: true
        }
      }
    };
    config.optimization.usedExports = true;
    config.optimization.sideEffects = false;
    return config;
  }
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Performance optimizations
  experimental: {
    optimizeCss: true,
    scrollRestoration: true,
    webpackBuildWorker: true,
    optimizePackageImports: ['@chakra-ui/react', 'lucide-react'],
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  
  // Production optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Enable compression
  compress: true,
  
  // Image optimization
  images: {
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Static file serving optimization
  async rewrites() {
    return [
      {
        source: '/confidence-test/questions.v1.json',
        destination: '/api/static/confidence-test/questions.v1.json',
      },
    ]
  },
  
  // Headers for performance
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          }
        ]
      },
      {
        source: '/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ]
  },
  
  // Bundle analysis and optimization
  ...getBundleAnalysisConfig(process.env.ANALYZE === 'true'),
  ...getWebpackOptimizations(),

  // Advanced performance features
  poweredByHeader: false,
  reactStrictMode: true,
  
  // Optimize font loading
  optimizeFonts: true,
  
  // Enable SWC minification for better performance
  swcMinify: true,
}

module.exports = nextConfig