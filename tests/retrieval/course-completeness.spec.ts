import { test, expect } from '@playwright/test';

test.describe('Course Completeness Retrieval Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Open the chat by clicking the floating robot
    await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 30000 });
    await page.click('.floating-robot-trigger');
    
    // Check if onboarding form is visible
    const nameInput = page.locator('input[name="name"]');
    if (await nameInput.isVisible()) {
      await page.fill('input[name="name"]', 'Audit User');
      await page.fill('input[name="email"]', 'audit@example.com');
      await page.fill('input[name="mobile"]', '9999999999');
      
      // Select BCA and scroll if needed
      const bcaCard = page.locator('.radio-card', { hasText: 'BCA' });
      await bcaCard.scrollIntoViewIfNeeded();
      await bcaCard.click({ force: true });
      
      await page.click('button[type="submit"]');
      await page.waitForSelector('input[name="name"]', { state: 'detached', timeout: 10000 });
    }
    
    await page.waitForSelector('.chat-textarea', { state: 'visible', timeout: 15000 });
  });

  const waitForResponse = async (page, timeout = 30000) => {
    await page.waitForSelector('.typing-indicator-bubble', { state: 'attached', timeout: 5000 }).catch(() => {});
    await page.waitForSelector('.typing-indicator-bubble', { state: 'detached', timeout });
  };

  test('Verify PhD programs appear in "courses offered" query', async ({ page }) => {
    const chatInput = page.locator('.chat-textarea');
    await chatInput.fill('What are all the courses offered at AIMS?');
    await page.click('.send-btn');

    await waitForResponse(page);

    const lastResponse = page.locator('.message-bubble.bot-bubble').last();
    const responseText = await lastResponse.textContent();

    console.log('Bot Response (Courses):', responseText);

    expect(responseText?.toLowerCase()).toContain('phd');
    expect(responseText?.toLowerCase()).toContain('doctoral');
  });

  test('Verify School of Arts programs (BA) are retrieved', async ({ page }) => {
    const chatInput = page.locator('.chat-textarea');
    await chatInput.fill('Do you have BA programs?');
    await page.click('.send-btn');

    await waitForResponse(page);

    const lastResponse = page.locator('.message-bubble.bot-bubble').last();
    const responseText = await lastResponse.textContent();

    console.log('Bot Response (BA):', responseText);

    expect(responseText?.toLowerCase()).toContain('bachelor of arts');
    expect(responseText?.toLowerCase()).toContain('journalism');
  });

  test('Verify School of Science programs (B.Sc) are retrieved', async ({ page }) => {
    const chatInput = page.locator('.chat-textarea');
    await chatInput.fill('Tell me about B.Sc offerings');
    await page.click('.send-btn');

    await waitForResponse(page);

    const lastResponse = page.locator('.message-bubble.bot-bubble').last();
    const responseText = await lastResponse.textContent();

    console.log('Bot Response (B.Sc):', responseText);

    expect(responseText?.toLowerCase()).toContain('bachelor of science');
    expect(responseText?.toLowerCase()).toContain('microbiology');
  });
});
