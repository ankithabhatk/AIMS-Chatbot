import { test, expect } from '@playwright/test';

test.describe('AIMS Chatbot UX Validation', () => {

  // Helper to fill and submit the welcome/onboarding form
  async function fillWelcomeForm(page) {
    await page.goto('/');
    
    // Open the chat by clicking the floating robot
    await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
    await page.click('.floating-robot-trigger');
    
    // Wait for the chat to open
    await page.waitForSelector('.chat-body', { state: 'visible', timeout: 15000 });
    
    // Check if the onboarding form is visible (WelcomeMessage component)
    // The form has: input[name='name'], input[name='email'], input[name='mobile'], .radio-card divs
    const nameInput = page.locator('input[name="name"]');
    const formVisible = await nameInput.isVisible().catch(() => false);
    
    if (formVisible) {
      await page.fill('input[name="name"]', 'Test User');
      await page.fill('input[name="email"]', 'test@example.com');
      await page.fill('input[name="mobile"]', '9999999999');
      
      // Click BCA radio card (course selection uses .radio-card divs with text)
      // Use force:true to bypass pointer interception on mobile viewport
      const bcaCard = page.locator('.radio-card', { hasText: 'BCA' });
      await bcaCard.scrollIntoViewIfNeeded();
      await bcaCard.click({ force: true });
      
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for the form to disappear (profile is set, chat takes over)
      await page.waitForSelector('input[name="name"]', { state: 'detached', timeout: 10000 });
    }
    
    // Wait for chat input to be ready
    await page.waitForSelector('.chat-textarea', { state: 'visible', timeout: 15000 });
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

    // Helper: wait for loading to finish (typing-indicator-bubble is the real DOM class)
    const waitForResponse = async (timeout = 30000) => {
      // Wait for typing bubble to appear (loading started)
      await page.waitForSelector('.typing-indicator-bubble', { state: 'attached', timeout: 5000 }).catch(() => {});
      // Wait for it to disappear (loading done)
      await page.waitForSelector('.typing-indicator-bubble', { state: 'detached', timeout });
    };

    // Step 1: Send "idk"
    await chatInput.fill('idk');
    await page.locator('.send-btn').click();
    await waitForResponse(30000);
    
    // Step 2: Send "maybe coding"
    await chatInput.fill('maybe coding');
    await page.locator('.send-btn').click();
    await waitForResponse(30000);

    // Step 3: Send "I like coding"
    await chatInput.fill('I like coding');
    await page.locator('.send-btn').click();
    await waitForResponse(30000);
    
    // Confirm bot responded
    await expect(page.locator('.message-bubble.bot-bubble').last()).toBeVisible();
    await page.waitForTimeout(800); // UI settle
    await page.screenshot({ path: 'testing/screenshots/2-coding-interest.png', fullPage: true });

    // Step 4: Send "actually I hate coding" (contradiction)
    await chatInput.fill('actually I hate coding');
    await page.locator('.send-btn').click();
    await waitForResponse(30000);
    await expect(page.locator('.message-bubble.bot-bubble').last()).toBeVisible();

    // The confidence bar should now be visible (counselor mode returns profile_confidence_score)
    const confidenceBar = page.locator('.confidence-bar-fill');
    await expect(confidenceBar.last()).toBeVisible({ timeout: 10000 });
    
    await page.waitForTimeout(800); // UI settle
    await page.screenshot({ path: 'testing/screenshots/3-contradiction-hate-coding.png', fullPage: true });

    // Step 5: Send "maybe business is better" (pivot)
    await chatInput.fill('maybe business is better');
    await page.locator('.send-btn').click();
    await waitForResponse(30000);
    
    await page.waitForTimeout(800); // UI settle
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
