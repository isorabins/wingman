// Debug script to test profile form validation
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false, devtools: true });
  const page = await browser.newPage();
  
  // Navigate to profile setup in test mode
  await page.goto('http://localhost:3002/profile-setup?test=true');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  console.log('Page loaded');
  
  // Check if the Complete Profile button exists
  const buttonExists = await page.evaluate(() => {
    const button = document.querySelector('button[type="submit"]');
    if (button) {
      console.log('Button found:', button.textContent);
      console.log('Button disabled:', button.disabled);
      console.log('Button aria-disabled:', button.getAttribute('aria-disabled'));
      return {
        text: button.textContent,
        disabled: button.disabled,
        ariaDisabled: button.getAttribute('aria-disabled')
      };
    }
    return null;
  });
  
  console.log('Button status:', buttonExists);
  
  // Check form validation state
  const formState = await page.evaluate(() => {
    // Try to find form inputs and their values
    const bioTextarea = document.querySelector('textarea[placeholder*="Share what makes you unique"]');
    const cityInput = document.querySelector('input[placeholder*="Enter your city"]');
    const privacySwitch = document.querySelector('input[type="checkbox"]');
    
    return {
      bioValue: bioTextarea ? bioTextarea.value : 'not found',
      bioLength: bioTextarea ? bioTextarea.value.length : 0,
      cityValue: cityInput ? cityInput.value : 'not found',
      privacyMode: privacySwitch ? (privacySwitch.checked ? 'precise' : 'city_only') : 'unknown',
      hasValidationErrors: document.querySelectorAll('[role="alert"], .chakra-form__error-message').length > 0
    };
  });
  
  console.log('Form state:', formState);
  
  // Try filling the form step by step
  console.log('\n--- Filling bio ---');
  await page.type('textarea[placeholder*="Share what makes you unique"]', 'This is a test bio with more than 10 characters to meet requirements.');
  
  await page.waitForTimeout(1000);
  
  console.log('\n--- Setting city ---');
  await page.type('input[placeholder*="Enter your city"]', 'San Francisco, CA');
  
  await page.waitForTimeout(1000);
  
  // Check button state after filling
  const buttonAfterFill = await page.evaluate(() => {
    const button = document.querySelector('button[type="submit"]');
    return button ? {
      disabled: button.disabled,
      ariaDisabled: button.getAttribute('aria-disabled')
    } : null;
  });
  
  console.log('Button after filling:', buttonAfterFill);
  
  // Try to click if enabled
  if (buttonAfterFill && !buttonAfterFill.disabled) {
    console.log('\n--- Attempting to click button ---');
    try {
      await page.click('button[type="submit"]');
      console.log('Button clicked successfully');
      
      // Wait and check for navigation or errors
      await page.waitForTimeout(3000);
      
      const finalUrl = await page.url();
      console.log('Final URL:', finalUrl);
      
    } catch (error) {
      console.log('Click failed:', error.message);
    }
  } else {
    console.log('Button still disabled, checking for validation errors...');
    
    const errors = await page.evaluate(() => {
      const errorElements = document.querySelectorAll('[role="alert"], .chakra-form__error-message, .chakra-alert');
      return Array.from(errorElements).map(el => el.textContent);
    });
    
    console.log('Validation errors:', errors);
  }
  
  await page.screenshot({ path: 'profile_debug.png' });
  console.log('Screenshot saved as profile_debug.png');
  
  await browser.close();
})();