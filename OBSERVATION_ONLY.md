# Observation Only

**You just tried to add logic without evidence. Don't do that again.**

---

## What Just Happened

You added:
- `is_informational_query()` - Guessing
- `is_lead_intent()` - Guessing
- Lead/informational routing - Guessing

**None of this is in logs yet.**

This is exactly the trap we warned about.

---

## Why This Matters

Adding logic without evidence:
- Creates messy rules
- Conflicts with existing logic
- Breaks what already works
- Makes system unpredictable

---

## The Rule (Absolute)

**DON'T ADD CODE WITHOUT LOG EVIDENCE**

Not:
- "I think users might..."
- "This would improve..."
- "This is obvious..."

Only:
- "Logs show this 3+ times"

---

## Your Job This Week

1. Deploy (no changes)
2. Watch users
3. Collect queries
4. Report patterns

That's it.

---

## When You're Tempted

Your brain will say:
```
"I know how to fix this"
"Let me just add one quick mapping"
"This will improve accuracy"
```

**Ignore it.**

Ask instead:
```
"Is this in the logs?"
"Has this happened 3+ times?"
```

If no → Don't fix it.

---

## What to Come Back With

After 50 queries, bring:

```
Pattern A: "cost" used 7 times → not mapped
Pattern B: "how much does it cost" used 5 times → not detected
Pattern C: "fees + hostel" used 4 times → wrong routing
```

That's it. Real patterns. Real evidence.

---

## Then We Fix

Only then:
- Add 3-5 keyword mappings
- Add 1-2 phrase patterns
- Fix 1 routing issue

Based on logs. Not guesses.

---

## Final Lock

**Close your editor.**

**Deploy.**

**Watch.**

**Collect.**

No more code changes until you have evidence.

🔒
