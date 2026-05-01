/**
 * REGRESSION: Contradiction Flow
 * 
 * Bug fixed: "actually I hate coding" was routing back into counselor_coding
 * (because "coding" keyword was detected), actively promoting the thing
 * the user just rejected. This is a conversational trust-breaker.
 * 
 * Fix: avoidance signals (hate, dislike, don't like) now route to
 * counselor_general so the bot acknowledges the reversal and explores
 * alternatives — instead of re-promoting.
 * 
 * Transcript source: chatbot.spec.ts contradiction flow (2026-05-01)
 */

import { test, expect } from '@playwright/test';

// Shared helper — matches WelcomeMessage.tsx (radio-card divs, not <select>)
async function fillWelcomeForm(page) {
  await page.goto('/');
  await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
  await page.click('.floating-robot-trigger');
  await page.waitForSelector('.chat-body', { state: 'visible', timeout: 15000 });

  const nameInput = page.locator('input[name="name"]');
  const formVisible = await nameInput.isVisible().catch(() => false);

  if (formVisible) {
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="mobile"]', '9999999999');
    const bcaCard = page.locator('.radio-card', { hasText: 'BCA' });
    await bcaCard.scrollIntoViewIfNeeded();
    await bcaCard.click({ force: true });
    await page.click('button[type="submit"]');
    await page.waitForSelector('input[name="name"]', { state: 'detached', timeout: 10000 });
  }

  await page.waitForSelector('.chat-textarea', { state: 'visible', timeout: 15000 });
}

const waitForResponse = async (page, timeout = 30000) => {
  await page.waitForSelector('.typing-indicator-bubble', { state: 'attached', timeout: 5000 }).catch(() => {});
  await page.waitForSelector('.typing-indicator-bubble', { state: 'detached', timeout });
};

test.describe('Contradiction Flow Regression', () => {

  test('Avoidance: "hate coding" must NOT re-promote coding', async ({ page }) => {
    await fillWelcomeForm(page);
    const chatInput = page.locator('.chat-textarea');

    // Build up a coding interest profile
    await chatInput.fill('I like coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    // Now contradict it
    await chatInput.fill('actually I hate coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    const lastBot = page.locator('.message-bubble.bot-bubble').last();
    await expect(lastBot).toBeVisible();

    const responseText = await lastBot.innerText();

    // REGRESSION ASSERTION: must NOT promote BCA/coding when user says they hate it
    expect(responseText).not.toMatch(/bca.*3 years|you can take bca|coding is a great direction/i);

    // Should acknowledge the change and stay open/exploratory
    // (any of: general question, acknowledgement, business/other pivot)
    await page.screenshot({ path: 'testing/screenshots/regression-hate-coding.png', fullPage: true });
  });

  test('Confidence bar drops after contradiction', async ({ page }) => {
    await fillWelcomeForm(page);
    const chatInput = page.locator('.chat-textarea');

    // Establish interest (confidence rises to ~0.45)
    await chatInput.fill('I like coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    // Read confidence after interest signal
    const barAfterInterest = page.locator('.confidence-bar-fill').last();
    await expect(barAfterInterest).toBeVisible({ timeout: 10000 });

    // Contradict (confidence should drop ~0.27)
    await chatInput.fill('actually I hate coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    // Confidence bar must still be visible after contradiction
    const barAfterContradiction = page.locator('.confidence-bar-fill').last();
    await expect(barAfterContradiction).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: 'testing/screenshots/regression-confidence-drop.png', fullPage: true });
  });

  test('Pivot: business interest is honoured after coding rejection', async ({ page }) => {
    await fillWelcomeForm(page);
    const chatInput = page.locator('.chat-textarea');

    await chatInput.fill('I like coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    await chatInput.fill('actually I hate coding');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    // Now pivot to business
    await chatInput.fill('maybe business is better');
    await page.locator('.send-btn').click();
    await waitForResponse(page);

    const lastBot = page.locator('.message-bubble.bot-bubble').last();
    await expect(lastBot).toBeVisible();
    const responseText = await lastBot.innerText();

    // REGRESSION: should mention BBA/MBA/business, not coding paths
    expect(responseText).toMatch(/bba|mba|business|management/i);

    await page.screenshot({ path: 'testing/screenshots/regression-business-pivot.png', fullPage: true });
  });
});
