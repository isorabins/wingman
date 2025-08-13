/**
 * Global teardown for Playwright tests
 * Runs once after all tests complete
 */

import { FullConfig } from '@playwright/test';
import { rm, existsSync } from 'fs';
import { promisify } from 'util';

const rmAsync = promisify(rm);

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Running global test cleanup...');
  
  // Clean up test files
  const testDataPaths = [
    './tests/e2e/test-data',
    './test-results',
    './playwright-report'
  ];
  
  for (const path of testDataPaths) {
    if (existsSync(path)) {
      try {
        await rmAsync(path, { recursive: true, force: true });
        console.log(`🗑️ Cleaned up ${path}`);
      } catch (error) {
        console.warn(`⚠️ Could not clean up ${path}:`, error);
      }
    }
  }
  
  // Clean up test database records if needed
  if (process.env.TEST_SUPABASE_URL && process.env.TEST_ENV !== 'production') {
    console.log('🗃️ Cleaning up test database records...');
    try {
      // Add test data cleanup logic here
      // Example: Delete test user profiles, uploaded files, etc.
      console.log('✅ Test database cleanup complete');
    } catch (error) {
      console.warn('⚠️ Test database cleanup failed:', error);
    }
  }
  
  // Stop mock services if needed
  if (process.env.TEST_ENV === 'ci') {
    console.log('🛑 Stopping mock services...');
    // Add mock service cleanup logic here
  }
  
  console.log('✨ Global teardown complete');
}

export default globalTeardown;
