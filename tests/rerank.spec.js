// tests/rerank.spec.js
/**
 * Playwright API tests for the re-ranking pipeline.
 *
 * Validates:
 *  - /api/v1/chat returns a meaningful response after reranking
 *  - Confidence score is reasonable (> 0.3)
 *  - chunks_used reflects the top-K cap (≤ 5)
 *  - Results differ semantically for distinct queries (reranker is topic-aware)
 *
 * Run:
 *   npx playwright test tests/rerank.spec.js
 *   API_BASE_URL=http://localhost:8000 npx playwright test tests/rerank.spec.js
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

async function chatRequest(request, query, sessionId) {
  return request.post(`${BASE_URL}/api/v1/chat`, {
    data: {
      query,
      context: { session_id: sessionId },
    },
    headers: { 'Content-Type': 'application/json' },
  });
}

test.describe('Re-ranking Pipeline — /api/v1/chat', () => {

  test('returns a non-empty answer with reasonable confidence', async ({ request }) => {
    const res = await chatRequest(request, 'What is the admission process for MBA?', 'rerank-spec-001');

    expect(res.status()).toBe(200);

    const body = await res.json();

    // Answer must exist and be meaningful
    expect(body).toHaveProperty('answer');
    expect(typeof body.answer).toBe('string');
    expect(body.answer.trim().length).toBeGreaterThan(20);

    // Confidence must be present and at least above noise floor
    expect(body).toHaveProperty('confidence');
    expect(body.confidence).toBeGreaterThan(0.3);
  });


  test('reranked pipeline keeps chunks_used within top-K (≤ 5)', async ({ request }) => {
    const res = await chatRequest(request, 'Tell me about AIMS placement statistics', 'rerank-spec-002');

    expect(res.status()).toBe(200);

    const body = await res.json();

    // meta.chunks_used should reflect the reranker top_k cap
    if (body.meta && body.meta.chunks_used !== undefined) {
      expect(body.meta.chunks_used).toBeLessThanOrEqual(5);
    }

    expect(body.answer).toBeTruthy();
    expect(body.confidence).toBeGreaterThan(0.3);
  });


  test('hostel facilities query returns topic-relevant answer', async ({ request }) => {
    const res = await chatRequest(request, 'What hostel facilities are available?', 'rerank-spec-003');

    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.answer).toBeTruthy();
    expect(body.answer.trim().length).toBeGreaterThan(20);

    // Reranker should surface hostel-relevant content
    const answerLower = body.answer.toLowerCase();
    const isTopicRelevant =
      answerLower.includes('hostel') ||
      answerLower.includes('campus') ||
      answerLower.includes('accommodation') ||
      answerLower.includes('facility') ||
      answerLower.includes('aims');

    expect(isTopicRelevant).toBe(true);
  });


  test('high-confidence factual answer is not a fallback', async ({ request }) => {
    const res = await chatRequest(request, 'What courses does AIMS offer?', 'rerank-spec-004');

    expect(res.status()).toBe(200);

    const body = await res.json();

    expect(body.answer).toBeTruthy();
    // A well-indexed factual query should not fall back
    if (body.confidence >= 0.5) {
      expect(body.fallback).toBe(false);
    }
  });


  test('distinct queries produce different top answers (reranker is topic-aware)', async ({ request }) => {
    const [resPlacement, resHostel] = await Promise.all([
      chatRequest(request, 'MBA placement packages and recruiters', 'rerank-spec-005a'),
      chatRequest(request, 'Hostel rooms and accommodation', 'rerank-spec-005b'),
    ]);

    expect(resPlacement.status()).toBe(200);
    expect(resHostel.status()).toBe(200);

    const bPlacement = await resPlacement.json();
    const bHostel    = await resHostel.json();

    expect(bPlacement.answer).toBeTruthy();
    expect(bHostel.answer).toBeTruthy();

    // The two answers must not be identical (reranker serves different top docs)
    expect(bPlacement.answer).not.toBe(bHostel.answer);
  });


  test('confidence score is within valid range [0, 1]', async ({ request }) => {
    const res = await chatRequest(request, 'What is the BCA eligibility criteria?', 'rerank-spec-006');

    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.confidence).toBeGreaterThanOrEqual(0.0);
    expect(body.confidence).toBeLessThanOrEqual(1.0);
  });

});
