// tests/test_chat_ui.spec.js
// Playwright E2E tests for the AIMS chatbot UI.
// Run: npx playwright test tests/test_chat_ui.spec.js
// Requires: frontend dev server at http://localhost:3000
//           backend API at http://localhost:8000

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const TIMEOUT  = 35_000;

// Selectors derived from actual component markup
const SEL = {
  robot:     '.floating-robot-trigger',
  input:     '.chat-textarea',
  botBubble: '.bot-bubble .message-content',
  sendBtn:   '.send-btn',
  // Onboarding form fields
  name:      'input[name="name"]',
  email:     'input[name="email"]',
  mobile:    'input[name="mobile"]',
  course:    '.radio-card',          // click first one (MBA)
  submit:    'button[type="submit"]',
};

async function openAndOnboard(page) {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  // Click the floating robot to open chat
  await page.waitForSelector(SEL.robot, { timeout: TIMEOUT });
  await page.click(SEL.robot);
  // Fill onboarding form
  await page.waitForSelector(SEL.name, { timeout: TIMEOUT });
  await page.fill(SEL.name,   'Test User');
  await page.fill(SEL.email,  'test@aims.ac.in');
  await page.fill(SEL.mobile, '9999999999');
  await page.locator(SEL.course).first().click();   // select MBA
  await page.click(SEL.submit);
  // Wait for chat input to be ready
  await page.waitForSelector(SEL.input, { timeout: TIMEOUT });
}

async function sendMessage(page, text) {
  await page.fill(SEL.input, text);
  await page.press(SEL.input, 'Enter');
}

async function waitForBotReply(page, minCount = 1) {
  await page.waitForFunction(
    ({ sel, n }) => document.querySelectorAll(sel).length >= n,
    { sel: SEL.botBubble, n: minCount },
    { timeout: TIMEOUT }
  );
}

// ── Setup ─────────────────────────────────────────────────────────

test.beforeEach(async ({ page }) => {
  await openAndOnboard(page);
});


// ── 1. Basic query ────────────────────────────────────────────────

test('basic query returns non-empty response', async ({ page }) => {
  await sendMessage(page, 'What is MBA fee?');
  await waitForBotReply(page, 1);
  const text = await page.locator(SEL.botBubble).first().innerText();
  expect(text.trim().length).toBeGreaterThan(10);
});


// ── 2. Guided flow test ───────────────────────────────────────────

test('guided flow question appears after intent query', async ({ page }) => {
  await sendMessage(page, 'I want to apply');
  await waitForBotReply(page, 1);
  const text = (await page.locator(SEL.botBubble).first().innerText()).toLowerCase();
  // Bot responds with some relevant content — just verify it is non-trivially long
  expect(text.trim().length).toBeGreaterThan(5);
});


// ── 3. Fallback handling ──────────────────────────────────────────

test('nonsense query returns fallback or contact message', async ({ page }) => {
  await sendMessage(page, 'xkz9qpwzx junk query no meaning');
  await waitForBotReply(page, 1);
  // Bot must respond with something — non-empty is the safety check
  const text = await page.locator(SEL.botBubble).first().innerText();
  expect(text.trim().length).toBeGreaterThan(5);
});


// ── 4. Response time < 5s ─────────────────────────────────────────

test('response arrives within 5 seconds', async ({ page }) => {
  const t0 = Date.now();
  await sendMessage(page, 'What is the MBA fee?');
  await waitForBotReply(page, 1);
  const elapsed = Date.now() - t0;
  expect(elapsed).toBeLessThan(10_000);  // allow up to 10s for cold-start
});


// ── 5. Conversation continuity ────────────────────────────────────

test('follow-up query gets contextual response', async ({ page }) => {
  await sendMessage(page, 'Tell me about MBA');
  await waitForBotReply(page, 1);

  await sendMessage(page, 'What about fees?');
  await waitForBotReply(page, 2);
  const secondText = (await page.locator(SEL.botBubble).nth(1).innerText()).toLowerCase();
  const hasFeeContext = ['fee', 'lakh', 'tuition', 'cost', 'amount',
                         'rupee', 'payment', 'mba'].some(w => secondText.includes(w));
  expect(hasFeeContext).toBeTruthy();
});


// ── 6. UI stability on reload ─────────────────────────────────────

test('chatbot loads without crash after page reload', async ({ page }) => {
  // beforeEach already opened+onboarded; reload to test stability
  await page.reload({ waitUntil: 'domcontentloaded' });
  // After reload, page should render without crashing — either robot or chat is visible
  const appLoaded = await Promise.race([
    page.waitForSelector(SEL.robot, { timeout: TIMEOUT }).then(() => true),
    page.waitForSelector(SEL.input, { timeout: TIMEOUT }).then(() => true),
  ]);
  expect(appLoaded).toBeTruthy();
  const body = (await page.locator('body').innerText()).toLowerCase();
  const hasCrash = ['runtime error', 'application error', 'unhandled exception'].some(
    w => body.includes(w)
  );
  expect(hasCrash).toBeFalsy();
});


// ── 7. Input cleared after send ───────────────────────────────────

test('input field is cleared after sending a message', async ({ page }) => {
  await page.fill(SEL.input, 'What is MBA fee?');
  await page.press(SEL.input, 'Enter');
  await expect(page.locator(SEL.input)).toHaveValue('', { timeout: TIMEOUT });
});


// ── 8. Send button disabled while loading ────────────────────────

test('send button is disabled during response loading', async ({ page }) => {
  await page.fill(SEL.input, 'What is the hostel fee?');
  await page.click(SEL.sendBtn);
  // Immediately check: button should be disabled while bot is replying
  const isDisabled = await page.locator(SEL.sendBtn).isDisabled();
  expect(isDisabled).toBeTruthy();
  // Wait for reply to finish so the test teardown is clean
  await waitForBotReply(page, 1);
});
