import { BundleAnalyzerPlugin } from 'webpack-bundle-analyzer';

export const getBundleAnalysisConfig = (analyze: boolean = false) => ({
  webpack: (config: any, { dev, isServer }: { dev: boolean; isServer: boolean }) => {
    // Only analyze client-side bundles in production
    if (analyze && !dev && !isServer) {
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

    // Enable source maps for better debugging
    if (dev) {
      config.devtool = 'eval-source-map';
    }

    return config;
  }
});

export const getWebpackOptimizations = () => ({
  webpack: (config: any) => {
    // Optimize bundle splitting
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

    // Minimize bundle size
    config.optimization.usedExports = true;
    config.optimization.sideEffects = false;

    return config;
  }
});

export const generateBundleReport = () => {
  const fs = require('fs');
  const path = require('path');
  
  try {
    const statsPath = path.join(process.cwd(), 'bundle-stats.json');
    if (!fs.existsSync(statsPath)) {
      console.log('❌ Bundle stats not found. Run: npm run build:analyze');
      return;
    }

    const stats = JSON.parse(fs.readFileSync(statsPath, 'utf8'));
    const assets = stats.assets || [];
    
    console.log('\n=== BUNDLE ANALYSIS REPORT ===\n');
    
    let totalSize = 0;
    const jsAssets = assets.filter((asset: any) => asset.name.endsWith('.js'));
    
    console.log('JavaScript Bundles:');
    jsAssets.forEach((asset: any) => {
      const sizeKB = (asset.size / 1024).toFixed(2);
      totalSize += asset.size;
      console.log(`  📦 ${asset.name}: ${sizeKB} KB`);
    });
    
    console.log(`\n📊 Total JS Bundle Size: ${(totalSize / 1024).toFixed(2)} KB`);
    console.log(`🎯 Target: < 250 KB`);
    
    if (totalSize > 250 * 1024) {
      console.log('❌ Bundle size exceeds target!');
    } else {
      console.log('✅ Bundle size within target');
    }
    
    // Chunk analysis
    const chunks = stats.chunks || [];
    console.log(`\n📂 Total Chunks: ${chunks.length}`);
    
    return {
      totalSizeKB: totalSize / 1024,
      chunkCount: chunks.length,
      withinBudget: totalSize <= 250 * 1024
    };
    
  } catch (error) {
    console.error('Error generating bundle report:', error);
  }
};