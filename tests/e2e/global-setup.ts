/**
 * Global setup for Playwright tests
 * Runs once before all tests
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🔧 Setting up global test environment...');
  
  // Setup test database if needed
  if (process.env.TEST_SUPABASE_URL) {
    console.log('📊 Connecting to test database...');
    // Add any database setup logic here
  }
  
  // Start mock services if needed
  if (process.env.TEST_ENV === 'ci') {
    console.log('🎭 Starting mock services for CI...');
    // Add mock service startup logic here
  }
  
  // Verify server is running
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    const baseURL = process.env.TEST_BASE_URL || 'http://localhost:3000';
    await page.goto(baseURL, { waitUntil: 'networkidle' });
    console.log('✅ Frontend server is accessible');
  } catch (error) {
    console.error('❌ Frontend server is not accessible:', error);
    throw error;
  } finally {
    await page.close();
    await browser.close();
  }
  
  // Verify API server is running
  try {
    const apiURL = process.env.TEST_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiURL}/health`);
    if (response.ok) {
      console.log('✅ Backend API server is accessible');
    } else {
      throw new Error(`API server returned ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Backend API server is not accessible:', error);
    throw error;
  }
  
  console.log('🚀 Global setup complete - ready to run tests');
}

export default globalSetup;
