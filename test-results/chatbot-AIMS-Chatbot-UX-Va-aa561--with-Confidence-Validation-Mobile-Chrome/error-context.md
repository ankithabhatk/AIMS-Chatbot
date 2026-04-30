# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chatbot.spec.ts >> AIMS Chatbot UX Validation >> Contradiction Flow with Confidence Validation
- Location: tests/chatbot.spec.ts:37:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.typing-indicator')
Expected: visible
Timeout: 30000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 30000ms
  - waiting for locator('.typing-indicator')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - generic [ref=e5]:
        - button "Toggle navigation menu" [ref=e6] [cursor=pointer]:
          - img [ref=e7]
        - generic [ref=e8]:
          - img "AIMS Logo" [ref=e10]
          - heading "AIMS Chat Interface" [level=1] [ref=e12]
      - generic [ref=e14]:
        - button "light" [ref=e15] [cursor=pointer]: light
        - button "dark" [ref=e17] [cursor=pointer]
        - button "Contrast" [ref=e18] [cursor=pointer]
    - generic [ref=e20]:
      - generic [ref=e21]:
        - img [ref=e23]
        - generic [ref=e25]:
          - strong [ref=e26]: "Admissions Open:"
          - text: MBA & MCA batches for 2026 are now filling fast. Apply before April 30th to secure your seat.
        - button [ref=e27] [cursor=pointer]:
          - img [ref=e28]
      - generic [ref=e31]:
        - img [ref=e36]
        - generic [ref=e46]:
          - generic [ref=e47]: AIMS Assistant
          - generic [ref=e49]:
            - heading "Welcome to AIMS Institutes. Please provide your details to continue." [level=3] [ref=e50]
            - generic [ref=e51]:
              - generic [ref=e52]:
                - generic [ref=e53]: "Full Name:"
                - textbox "Enter your name" [ref=e54]
              - generic [ref=e55]:
                - generic [ref=e56]: "Email ID:"
                - textbox "Enter your email" [ref=e57]
              - generic [ref=e58]:
                - generic [ref=e59]: "Phone:"
                - textbox "Enter phone number" [ref=e60]
              - generic [ref=e61]:
                - generic [ref=e62]: "Course Interested:"
                - generic [ref=e63]:
                  - generic [ref=e65] [cursor=pointer]: MBA
                  - generic [ref=e67] [cursor=pointer]: MCA
                  - generic [ref=e69] [cursor=pointer]: M.Com
                  - generic [ref=e71] [cursor=pointer]: BBA
                  - generic [ref=e73] [cursor=pointer]: BCA
                  - generic [ref=e75] [cursor=pointer]: B.Com
                  - generic [ref=e77] [cursor=pointer]: BHM
                  - generic [ref=e79] [cursor=pointer]: BBA Aviation
              - button "Submit" [ref=e81] [cursor=pointer]
          - generic [ref=e82]: 12:49 AM
    - generic [ref=e84]:
      - textbox "Type your inquiry here..." [ref=e85]
      - button [disabled] [ref=e87] [cursor=pointer]:
        - img [ref=e88]
  - alert [ref=e91]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('AIMS Chatbot UX Validation', () => {
  4   | 
  5   |   // Helper to bypass the welcome form
  6   |   async function fillWelcomeForm(page) {
  7   |     await page.goto('/');
  8   |     
  9   |     // Open the chat by clicking the floating robot
  10  |     await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
  11  |     await page.click('.floating-robot-trigger');
  12  |     
  13  |     // Wait for either the form or the chat body to be visible
  14  |     await page.waitForSelector('.welcome-form-container, .chat-body', { state: 'visible', timeout: 10000 });
  15  |     
  16  |     const formVisible = await page.locator('.welcome-form-container').isVisible();
  17  |     if (formVisible) {
  18  |       await page.fill('input[name="name"]', 'Test User');
  19  |       await page.fill('input[name="mobile"]', '9999999999');
  20  |       await page.fill('input[name="email"]', 'test@example.com');
  21  |       await page.selectOption('select[name="course"]', 'BCA');
  22  |       await page.click('button[type="submit"]');
  23  |       await expect(page.locator('.welcome-form-container')).toBeHidden({ timeout: 10000 });
  24  |     }
  25  |   }
  26  | 
  27  |   test('Greeting and initial render', async ({ page }) => {
  28  |     await page.goto('/');
  29  |     await page.waitForSelector('.floating-robot-trigger', { state: 'visible', timeout: 60000 });
  30  |     await page.screenshot({ path: 'testing/screenshots/1-initial-load.png', fullPage: true });
  31  |     
  32  |     // Open chat
  33  |     await page.click('.floating-robot-trigger');
  34  |     await page.waitForSelector('.chat-body, .welcome-form-container', { state: 'visible', timeout: 10000 });
  35  |   });
  36  | 
  37  |   test('Contradiction Flow with Confidence Validation', async ({ page }) => {
  38  |     await fillWelcomeForm(page);
  39  |     
  40  |     const chatInput = page.locator('.chat-textarea');
  41  |     await expect(chatInput).toBeVisible();
  42  | 
  43  |     // Step 1: Send "I like coding"
  44  |     await chatInput.fill('I like coding');
  45  |     await page.locator('.send-btn').click();
  46  |     
  47  |     // Wait for typing indicator to appear and disappear
> 48  |     await expect(page.locator('.typing-indicator')).toBeVisible();
      |                                                     ^ Error: expect(locator).toBeVisible() failed
  49  |     await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 20000 });
  50  |     
  51  |     // Wait for bot response
  52  |     const botResponses = page.locator('.message-bubble.bot-bubble');
  53  |     await expect(botResponses.last()).toBeVisible();
  54  |     
  55  |     await page.waitForTimeout(1000); // UI settle
  56  |     await page.screenshot({ path: 'testing/screenshots/2-coding-interest.png', fullPage: true });
  57  | 
  58  |     // Step 2: Send "actually I hate coding"
  59  |     await chatInput.fill('actually I hate coding');
  60  |     await page.locator('.send-btn').click();
  61  |     await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 20000 });
  62  |     
  63  |     // The confidence bar should visually update
  64  |     const confidenceBar = page.locator('.confidence-bar-fill');
  65  |     await expect(confidenceBar.last()).toBeVisible();
  66  |     
  67  |     await page.waitForTimeout(1000); // UI settle
  68  |     await page.screenshot({ path: 'testing/screenshots/3-contradiction-hate-coding.png', fullPage: true });
  69  | 
  70  |     // Step 3: Send "maybe business is better"
  71  |     await chatInput.fill('maybe business is better');
  72  |     await page.locator('.send-btn').click();
  73  |     await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 20000 });
  74  |     
  75  |     await page.waitForTimeout(1000); // UI settle
  76  |     await page.screenshot({ path: 'testing/screenshots/4-pivot-business.png', fullPage: true });
  77  |   });
  78  | 
  79  |   test('Offline Fallback Handling', async ({ page }) => {
  80  |     // Route interception to simulate backend failure
  81  |     await page.route('**/api/v1/chat', route => route.abort('failed'));
  82  |     
  83  |     await fillWelcomeForm(page);
  84  | 
  85  |     const chatInput = page.locator('.chat-textarea');
  86  |     await chatInput.waitFor({ state: 'visible', timeout: 30000 });
  87  |     await chatInput.fill('What is the fee?');
  88  |     await page.locator('.send-btn').click();
  89  |     
  90  |     // Should show error message gracefully without crashing UI
  91  |     await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 5000 });
  92  |     const botResponse = page.locator('.message-bubble.bot-bubble').last();
  93  |     
  94  |     await page.waitForTimeout(500);
  95  |     await page.screenshot({ path: 'testing/screenshots/5-offline-fallback.png', fullPage: true });
  96  |     
  97  |     // Verify there are no critical unhandled Next.js errors
  98  |     const nextErrorOverlay = page.locator('nextjs-portal');
  99  |     await expect(nextErrorOverlay).toBeHidden();
  100 |   });
  101 | });
  102 | 
```