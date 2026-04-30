import { test, expect } from '@playwright/test';

test.describe('AIMS Chatbot UX Validation', () => {

  // Helper to bypass the welcome form
  async function fillWelcomeForm(page) {
    await page.goto('/');
    
    // Open the chat by clicking the floating robot
    await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
    await page.click('.floating-robot-trigger');
    
    // Wait for either the form or the chat body to be visible
    await page.waitForSelector('.welcome-form-container, .chat-body', { state: 'visible', timeout: 10000 });
    
    const formVisible = await page.locator('.welcome-form-container').isVisible();
    if (formVisible) {
      await page.fill('input[name="name"]', 'Test User');
      await page.fill('input[name="mobile"]', '9999999999');
      await page.fill('input[name="email"]', 'test@example.com');
      await page.selectOption('select[name="course"]', 'BCA');
      await page.click('button[type="submit"]');
      await expect(page.locator('.welcome-form-container')).toBeHidden({ timeout: 10000 });
    }
  }

  test('Greeting and initial render', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
    await page.screenshot({ path: 'testing/screenshots/1-initial-load.png', fullPage: true });
    
    // Open chat
    await page.click('.floating-robot-trigger');
    await page.waitForSelector('.chat-body, .welcome-form-container', { state: 'visible', timeout: 10000 });
  });

  test('Contradiction Flow with Confidence Validation', async ({ page }) => {
    await fillWelcomeForm(page);
    
    const chatInput = page.locator('.chat-textarea');
    await expect(chatInput).toBeVisible();

    // Step 1: Send "I like coding"
    await chatInput.fill('I like coding');
    await page.locator('.send-btn').click();
    
    // Wait for typing indicator to disappear (it might flash too fast to catch toBeVisible)
    await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 30000 });
    
    // Wait for bot response
    const botResponses = page.locator('.message-bubble.bot-bubble');
    await expect(botResponses.last()).toBeVisible();
    
    await page.waitForTimeout(1000); // UI settle
    await page.screenshot({ path: 'testing/screenshots/2-coding-interest.png', fullPage: true });

    // Step 2: Send "actually I hate coding"
    await chatInput.fill('actually I hate coding');
    await page.locator('.send-btn').click();
    await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 20000 });
    
    // The confidence bar should visually update
    const confidenceBar = page.locator('.confidence-bar-fill');
    await expect(confidenceBar.last()).toBeVisible();
    
    await page.waitForTimeout(1000); // UI settle
    await page.screenshot({ path: 'testing/screenshots/3-contradiction-hate-coding.png', fullPage: true });

    // Step 3: Send "maybe business is better"
    await chatInput.fill('maybe business is better');
    await page.locator('.send-btn').click();
    await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 20000 });
    
    await page.waitForTimeout(1000); // UI settle
    await page.screenshot({ path: 'testing/screenshots/4-pivot-business.png', fullPage: true });
  });

  test('Offline Fallback Handling', async ({ page }) => {
    // Route interception to simulate backend failure
    await page.route('**/api/v1/chat', route => route.abort('failed'));
    
    await fillWelcomeForm(page);

    const chatInput = page.locator('.chat-textarea');
    await chatInput.waitFor({ state: 'visible', timeout: 30000 });
    await chatInput.fill('What is the fee?');
    await page.locator('.send-btn').click();
    
    // Should show error message gracefully without crashing UI
    await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 5000 });
    const botResponse = page.locator('.message-bubble.bot-bubble').last();
    
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'testing/screenshots/5-offline-fallback.png', fullPage: true });
    
    // Verify there are no critical unhandled Next.js errors
    const nextErrorOverlay = page.locator('nextjs-portal');
    await expect(nextErrorOverlay).toBeHidden();
  });
});
