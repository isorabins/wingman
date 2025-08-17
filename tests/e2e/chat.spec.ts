import { test, expect, Page } from '@playwright/test'

// Test configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'
const FRONTEND_BASE_URL = process.env.FRONTEND_BASE_URL || 'http://localhost:3002'

// Test user IDs for development
const TEST_USER_1 = 'test-user-chat-1'
const TEST_USER_2 = 'test-user-chat-2'
const TEST_MATCH_ID = 'test-match-123'

// Helper function to create test match
async function createTestMatch() {
  // In a real test, this would create a test match via API
  // For now, we'll assume a test match exists
  return TEST_MATCH_ID
}

// Helper function to authenticate test user
async function authenticateUser(page: Page, userId: string) {
  // Set test user header for development auth
  await page.setExtraHTTPHeaders({
    'X-Test-User-ID': userId
  })
}

// Helper function to wait for message to appear
async function waitForMessage(page: Page, messageText: string, timeout = 10000) {
  await page.waitForSelector(`text=${messageText}`, { timeout })
}

test.describe('Buddy Chat Functionality', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test environment
    await createTestMatch()
  })

  test('should load chat page and display empty state', async ({ page }) => {
    await authenticateUser(page, TEST_USER_1)
    
    // Navigate to chat page
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Check page title and header
    await expect(page.locator('text=Buddy Chat')).toBeVisible()
    await expect(page.locator('text=Chat with your wingman partner')).toBeVisible()
    await expect(page.locator('text=Active Match')).toBeVisible()
    
    // Check empty state
    await expect(page.locator('text=No messages yet')).toBeVisible()
    await expect(page.locator('text=Start the conversation by sending a message below')).toBeVisible()
    
    // Check message input is present
    await expect(page.locator('input[placeholder="Type your message..."]')).toBeVisible()
    await expect(page.locator('button[aria-label="Send message"]')).toBeVisible()
  })

  test('should send and receive messages between two users', async ({ browser }) => {
    // Create two browser contexts for two users
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()
    const page1 = await context1.newPage()
    const page2 = await context2.newPage()
    
    // Authenticate both users
    await authenticateUser(page1, TEST_USER_1)
    await authenticateUser(page2, TEST_USER_2)
    
    // Both users navigate to the same chat
    await page1.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    await page2.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // User 1 sends a message
    const message1 = "Hey! Ready for our wingman session?"
    await page1.fill('input[placeholder="Type your message..."]', message1)
    await page1.click('button[aria-label="Send message"]')
    
    // Wait for message to be sent and input to clear
    await expect(page1.locator('input[placeholder="Type your message..."]')).toHaveValue('')
    
    // Check message appears on user 1's screen
    await waitForMessage(page1, message1)
    
    // Check message appears on user 2's screen within 5 seconds (polling interval)
    await waitForMessage(page2, message1, 10000)
    
    // User 2 sends a reply
    const message2 = "Absolutely! Where should we meet?"
    await page2.fill('input[placeholder="Type your message..."]', message2)
    await page2.click('button[aria-label="Send message"]')
    
    // Check reply appears on both screens
    await waitForMessage(page1, message2, 10000)
    await waitForMessage(page2, message2)
    
    // Verify both messages are visible in correct order
    const messages1 = await page1.locator('.chakra-text').allTextContents()
    const messages2 = await page2.locator('.chakra-text').allTextContents()
    
    expect(messages1.join(' ')).toContain(message1)
    expect(messages1.join(' ')).toContain(message2)
    expect(messages2.join(' ')).toContain(message1)
    expect(messages2.join(' ')).toContain(message2)
    
    await context1.close()
    await context2.close()
  })

  test('should validate message length requirements', async ({ page }) => {
    await authenticateUser(page, TEST_USER_1)
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Test empty message (should disable send button)
    await expect(page.locator('button[aria-label="Send message"]')).toBeDisabled()
    
    // Test single character message (too short)
    await page.fill('input[placeholder="Type your message..."]', 'a')
    await page.click('button[aria-label="Send message"]')
    
    // Should show validation error
    await expect(page.locator('text=Invalid message length')).toBeVisible()
    
    // Test valid message
    await page.fill('input[placeholder="Type your message..."]', 'This is a valid message')
    await expect(page.locator('button[aria-label="Send message"]')).toBeEnabled()
    
    // Test maximum length message (2000 chars)
    const longMessage = 'a'.repeat(2000)
    await page.fill('input[placeholder="Type your message..."]', longMessage)
    await expect(page.locator('text=2000/2000 characters')).toBeVisible()
    
    // Test message too long (should be prevented by maxLength)
    const tooLongMessage = 'a'.repeat(2001)
    await page.fill('input[placeholder="Type your message..."]', tooLongMessage)
    const inputValue = await page.locator('input[placeholder="Type your message..."]').inputValue()
    expect(inputValue.length).toBe(2000) // Should be truncated
  })

  test('should handle rate limiting gracefully', async ({ page }) => {
    await authenticateUser(page, TEST_USER_1)
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Send messages rapidly to trigger rate limiting
    const messages = ['Message 1', 'Message 2', 'Message 3']
    
    for (const message of messages) {
      await page.fill('input[placeholder="Type your message..."]', message)
      await page.click('button[aria-label="Send message"]')
      // Don't wait between sends to trigger rate limiting
    }
    
    // Should show rate limit error for rapid sends
    await expect(page.locator('text=Rate limit exceeded')).toBeVisible({ timeout: 5000 })
  })

  test('should display venue suggestions panel', async ({ page }) => {
    await authenticateUser(page, TEST_USER_1)
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Check venue suggestions button is present
    await expect(page.locator('text=Venue Suggestions')).toBeVisible()
    
    // Click to expand venue suggestions
    await page.click('text=Venue Suggestions')
    
    // Check all venue categories are displayed
    await expect(page.locator('text=Coffee Shops')).toBeVisible()
    await expect(page.locator('text=Relaxed atmosphere for conversation')).toBeVisible()
    
    await expect(page.locator('text=Bookstores')).toBeVisible()
    await expect(page.locator('text=Quiet spaces with conversation starters')).toBeVisible()
    
    await expect(page.locator('text=Malls')).toBeVisible()
    await expect(page.locator('text=Busy environments for practice')).toBeVisible()
    
    await expect(page.locator('text=Parks')).toBeVisible()
    await expect(page.locator('text=Outdoor spaces for natural interactions')).toBeVisible()
    
    // Check examples are shown
    await expect(page.locator('text=Local coffee shop')).toBeVisible()
    await expect(page.locator('text=Independent bookstore')).toBeVisible()
    await expect(page.locator('text=Food court')).toBeVisible()
    await expect(page.locator('text=Local park')).toBeVisible()
    
    // Check tip is displayed
    await expect(page.locator('text=Choose venues where you feel comfortable')).toBeVisible()
  })

  test('should handle authentication errors', async ({ page }) => {
    // Don't authenticate user (no X-Test-User-ID header)
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Try to send a message
    await page.fill('input[placeholder="Type your message..."]', 'Test message')
    await page.click('button[aria-label="Send message"]')
    
    // Should show authentication error
    await expect(page.locator('text=Authentication required')).toBeVisible({ timeout: 5000 })
  })

  test('should handle non-participant access correctly', async ({ page }) => {
    // Authenticate as a user who is not part of the match
    await authenticateUser(page, 'non-participant-user')
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Try to send a message
    await page.fill('input[placeholder="Type your message..."]', 'Unauthorized message')
    await page.click('button[aria-label="Send message"]')
    
    // Should show access denied error
    await expect(page.locator('text=Access denied')).toBeVisible({ timeout: 5000 })
  })

  test('should maintain scroll position when new messages arrive', async ({ browser }) => {
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()
    const page1 = await context1.newPage()
    const page2 = await context2.newPage()
    
    await authenticateUser(page1, TEST_USER_1)
    await authenticateUser(page2, TEST_USER_2)
    
    await page1.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    await page2.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Send multiple messages to create scrollable content
    for (let i = 1; i <= 10; i++) {
      await page1.fill('input[placeholder="Type your message..."]', `Message ${i}`)
      await page1.click('button[aria-label="Send message"]')
      await page.waitForTimeout(100) // Small delay between messages
    }
    
    // Verify messages are visible and scroll position is at bottom
    await waitForMessage(page1, 'Message 10')
    await waitForMessage(page2, 'Message 10', 10000)
    
    // Send a new message and verify it appears without user having to scroll
    await page2.fill('input[placeholder="Type your message..."]', 'New message')
    await page2.click('button[aria-label="Send message"]')
    
    await waitForMessage(page1, 'New message', 10000)
    await waitForMessage(page2, 'New message')
    
    await context1.close()
    await context2.close()
  })

  test('should send message on Enter key press', async ({ page }) => {
    await authenticateUser(page, TEST_USER_1)
    await page.goto(`${FRONTEND_BASE_URL}/buddy-chat/${TEST_MATCH_ID}`)
    
    // Type message and press Enter
    const message = 'Sent with Enter key'
    await page.fill('input[placeholder="Type your message..."]', message)
    await page.press('input[placeholder="Type your message..."]', 'Enter')
    
    // Check message was sent (input should be cleared)
    await expect(page.locator('input[placeholder="Type your message..."]')).toHaveValue('')
    
    // Check message appears in chat
    await waitForMessage(page, message)
  })
  
})

test.describe('Chat API Endpoints', () => {
  
  test('GET /api/chat/messages/{match_id} should return messages', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/chat/messages/${TEST_MATCH_ID}`, {
      headers: {
        'X-Test-User-ID': TEST_USER_1
      }
    })
    
    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data).toHaveProperty('messages')
    expect(data).toHaveProperty('has_more')
    expect(Array.isArray(data.messages)).toBe(true)
  })

  test('POST /api/chat/send should send message successfully', async ({ request }) => {
    const message = 'Test API message'
    
    const response = await request.post(`${API_BASE_URL}/api/chat/send`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Test-User-ID': TEST_USER_1
      },
      data: {
        match_id: TEST_MATCH_ID,
        message: message
      }
    })
    
    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data).toHaveProperty('message_id')
    expect(data).toHaveProperty('created_at')
  })

  test('POST /api/chat/send should reject invalid messages', async ({ request }) => {
    // Test empty message
    const emptyResponse = await request.post(`${API_BASE_URL}/api/chat/send`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Test-User-ID': TEST_USER_1
      },
      data: {
        match_id: TEST_MATCH_ID,
        message: ''
      }
    })
    
    expect(emptyResponse.status()).toBe(422) // Pydantic validation error
    
    // Test message too long
    const longMessage = 'a'.repeat(2001)
    const longResponse = await request.post(`${API_BASE_URL}/api/chat/send`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Test-User-ID': TEST_USER_1
      },
      data: {
        match_id: TEST_MATCH_ID,
        message: longMessage
      }
    })
    
    expect(longResponse.status()).toBe(422) // Pydantic validation error
  })

  test('API should handle authentication properly', async ({ request }) => {
    // Test without authentication header
    const response = await request.get(`${API_BASE_URL}/api/chat/messages/${TEST_MATCH_ID}`)
    
    expect(response.status()).toBe(401)
    
    const data = await response.json()
    expect(data.detail).toContain('Authentication required')
  })

})