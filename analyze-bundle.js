const fs = require('fs');
const path = require('path');

try {
  const statsPath = path.join(process.cwd(), 'bundle-stats.json');
  if (!fs.existsSync(statsPath)) {
    console.log('❌ Bundle stats not found. Run: npm run build:analyze');
    process.exit(1);
  }

  const stats = JSON.parse(fs.readFileSync(statsPath, 'utf8'));
  const assets = stats.assets || [];
  
  console.log('\n=== WINGMAN BUNDLE ANALYSIS REPORT ===\n');
  
  let totalSize = 0;
  const jsAssets = assets.filter(asset => asset.name.endsWith('.js'));
  
  console.log('📦 JavaScript Bundles:');
  jsAssets.forEach(asset => {
    const sizeKB = (asset.size / 1024).toFixed(2);
    totalSize += asset.size;
    console.log(`  ${asset.name}: ${sizeKB} KB`);
  });
  
  console.log(`\n📊 Total JS Bundle Size: ${(totalSize / 1024).toFixed(2)} KB`);
  console.log(`🎯 Performance Target: < 250 KB per route`);
  
  // CSS Analysis
  const cssAssets = assets.filter(asset => asset.name.endsWith('.css'));
  let totalCssSize = 0;
  
  if (cssAssets.length > 0) {
    console.log('\n🎨 CSS Bundles:');
    cssAssets.forEach(asset => {
      const sizeKB = (asset.size / 1024).toFixed(2);
      totalCssSize += asset.size;
      console.log(`  ${asset.name}: ${sizeKB} KB`);
    });
    console.log(`📊 Total CSS Size: ${(totalCssSize / 1024).toFixed(2)} KB`);
  }
  
  // Chunk analysis
  const chunks = stats.chunks || [];
  console.log(`\n📂 Total Chunks: ${chunks.length}`);
  
  // Vendor analysis
  const vendorChunks = jsAssets.filter(asset => asset.name.includes('vendor'));
  const vendorSize = vendorChunks.reduce((acc, asset) => acc + asset.size, 0);
  
  console.log(`📦 Vendor Bundle Size: ${(vendorSize / 1024).toFixed(2)} KB`);
  console.log(`📦 App Bundle Size: ${((totalSize - vendorSize) / 1024).toFixed(2)} KB`);
  
  // Performance assessment
  console.log('\n🚀 PERFORMANCE ASSESSMENT:');
  if (totalSize > 500 * 1024) {
    console.log('❌ Bundle size LARGE - needs optimization');
  } else if (totalSize > 250 * 1024) {
    console.log('⚠️  Bundle size MEDIUM - could be optimized');
  } else {
    console.log('✅ Bundle size GOOD - within target');
  }
  
  // Code splitting opportunities
  console.log('\n🔧 OPTIMIZATION OPPORTUNITIES:');
  
  const largeChunks = jsAssets.filter(asset => asset.size > 50 * 1024);
  if (largeChunks.length > 0) {
    console.log('📋 Large chunks that could be split:');
    largeChunks.forEach(chunk => {
      console.log(`  - ${chunk.name}: ${(chunk.size / 1024).toFixed(2)} KB`);
    });
  }
  
  const chakraChunks = jsAssets.filter(asset => asset.name.includes('chakra'));
  if (chakraChunks.length > 0) {
    const chakraSize = chakraChunks.reduce((acc, asset) => acc + asset.size, 0);
    console.log(`🎨 Chakra UI total: ${(chakraSize / 1024).toFixed(2)} KB`);
  }
  
  console.log('\n📈 NEXT STEPS:');
  console.log('1. Implement lazy loading for heavy components');
  console.log('2. Code-split chat and assessment interfaces');
  console.log('3. Optimize Chakra UI imports');
  console.log('4. Add route-based code splitting');
  
} catch (error) {
  console.error('Error generating bundle report:', error);
}