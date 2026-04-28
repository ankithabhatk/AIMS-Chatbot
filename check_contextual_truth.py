#!/usr/bin/env python3
import requests
import time
import re

BASE_URL = 'http://127.0.0.1:8000'
session = 'ctx-truth-test'

print('\n' + '='*80)
print('🔍 CONTEXTUAL TRUTH VALIDATION - Direct API Test')
print('='*80)

# Query 1
print('\n📝 QUERY 1: "MBA fees" (Establish context)')
print('-'*80)

resp1 = requests.post(
    f'{BASE_URL}/api/v1/chat',
    json={'query': 'MBA fees', 'session_id': session},
    timeout=15
)

data1 = resp1.json()
answer1 = data1.get('answer', '')
mode1 = data1.get('mode', '')
print(f'Mode: {mode1}')
print(f'Response:\n{answer1}\n')

time.sleep(2)

# Query 2
print('📝 QUERY 2: "What about placements?" (With MBA context)')
print('-'*80)

resp2 = requests.post(
    f'{BASE_URL}/api/v1/chat',
    json={'query': 'What about placements?', 'session_id': session},
    timeout=15
)

data2 = resp2.json()
answer2 = data2.get('answer', '')
mode2 = data2.get('mode', '')
fallback2 = data2.get('fallback', False)

print(f'Mode: {mode2}')
print(f'Fallback: {fallback2}')
print(f'\nResponse:')
print('---')
print(answer2)
print('---\n')

# Analysis
print('='*80)
print('🔍 CONTEXTUAL TRUTH ANALYSIS')
print('='*80)

answer2_lower = answer2.lower()
packages = re.findall(r'₹(\d+)', answer2)
has_23 = '₹23' in answer2
has_27 = '₹27' in answer2
has_mba = 'mba' in answer2_lower
has_bba = 'bba' in answer2_lower
has_overall = 'overall' in answer2_lower

print(f'\nPackages found: {packages}')
print(f'Has MBA context: {has_mba}')
print(f'Has BBA context: {has_bba}')
print(f'Has overall: {has_overall}')
print(f'Has ₹23 LPA (MBA-specific): {has_23}')
print(f'Has ₹27 LPA (overall): {has_27}')

print('\n' + '='*80)
if fallback2:
    print('🔴 FAIL: System returned fallback (lost context)')
elif has_27 and not has_mba:
    print('🔴 FAIL: Shows overall ₹27 LPA instead of MBA-specific ₹23 LPA')
    print('   ^ This is the contextual truth problem you identified')
elif has_23:
    print('✅ PASS: Shows MBA-specific ₹23 LPA')
else:
    print('🟡 UNCLEAR: Could not determine contextual accuracy')
print('='*80)
