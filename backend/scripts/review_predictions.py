#!/usr/bin/env python3
"""
review_predictions.py — Interactive Prediction Quality Review Tool
===================================================================
Prints the last N sessions and lets you mark each prediction
correct or incorrect. Writes feedback directly to Supabase.

Usage:
    cd backend/
    python scripts/review_predictions.py
    python scripts/review_predictions.py --limit 10 --reviewer "admin"

This creates the training data your system needs to self-improve.
"""

import os
import sys
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras


# ─────────────────────────────────────────────────────────────────────────────
# COLOURS (graceful fallback on Windows)
# ─────────────────────────────────────────────────────────────────────────────
try:
    GREEN  = "\033[92m"; RED  = "\033[91m"; YELLOW = "\033[93m"
    CYAN   = "\033[96m"; BOLD = "\033[1m";  RESET  = "\033[0m"
    DIM    = "\033[2m"
except Exception:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = DIM = ""

BAND_COLOUR = {
    "Very High": GREEN,
    "High":      CYAN,
    "Moderate":  YELLOW,
    "Low":       DIM,
}


# ─────────────────────────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        print(f"{RED}❌ DATABASE_URL not set in .env{RESET}")
        sys.exit(1)
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def fetch_sessions(limit: int, unreviewed_only: bool) -> list:
    conn = _get_conn()
    cur = conn.cursor()
    where = "WHERE is_prediction_correct IS NULL" if unreviewed_only else ""
    cur.execute(f"""
        SELECT session_id, courses, primary_intent, all_intents,
               sentiment, lead_score, conversion_probability,
               conversion_timeline, next_expected_queries,
               message_count, updated_at,
               is_prediction_correct, review_notes
        FROM session_summaries
        {where}
        ORDER BY updated_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def save_feedback(session_id: str, correct: bool, notes: str, reviewer: str):
    conn = _get_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        UPDATE session_summaries
        SET is_prediction_correct = %s,
            reviewed_at  = %s,
            reviewed_by  = %s,
            review_notes = %s
        WHERE session_id = %s
    """, (correct, datetime.now(timezone.utc), reviewer, notes or None, session_id))
    conn.close()


def fetch_accuracy_stats() -> dict:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                                            AS total,
            COUNT(*) FILTER (WHERE is_prediction_correct IS NOT NULL) AS reviewed,
            COUNT(*) FILTER (WHERE is_prediction_correct = TRUE)      AS correct,
            COUNT(*) FILTER (WHERE is_prediction_correct = FALSE)     AS incorrect
        FROM session_summaries
    """)
    row = dict(cur.fetchone())
    conn.close()
    reviewed = row["reviewed"] or 0
    correct  = row["correct"]  or 0
    row["accuracy_pct"] = round(correct / reviewed * 100, 1) if reviewed else None
    return row


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def _band_str(band: str) -> str:
    colour = BAND_COLOUR.get(band, "")
    return f"{colour}{BOLD}{band:9}{RESET}"


def print_session(idx: int, row: dict):
    sid       = row["session_id"]
    score     = float(row["lead_score"])
    band      = row["conversion_probability"] or "?"
    intent    = row["primary_intent"] or "?"
    intents   = row["all_intents"] or []
    courses   = row["courses"] or []
    timeline  = row["conversion_timeline"] or "?"
    next_q    = row["next_expected_queries"] or []
    msgs      = row["message_count"]
    ts        = row["updated_at"]
    already   = row["is_prediction_correct"]
    notes     = row["review_notes"] or ""

    already_str = ""
    if already is True:
        already_str = f"  {GREEN}[reviewed: ✅ correct]{RESET}"
    elif already is False:
        already_str = f"  {RED}[reviewed: ❌ incorrect]{RESET}"

    print(f"\n{BOLD}{'─'*65}{RESET}")
    print(f"{BOLD}[{idx}] Session: {CYAN}{sid}{RESET}{already_str}")
    print(f"{'─'*65}")
    print(f"  Courses       : {', '.join(courses)}")
    print(f"  Primary Intent: {BOLD}{intent}{RESET}")
    print(f"  All Intents   : {', '.join(intents)}")
    print(f"  Lead Score    : {BOLD}{score:.1f}/10{RESET}  |  Band: {_band_str(band)}")
    print(f"  Timeline      : {timeline}")
    print(f"  Next Q        : {' | '.join(next_q) if next_q else 'N/A'}")
    print(f"  Messages      : {msgs}   |  Updated: {ts}")
    if notes:
        print(f"  Notes         : {DIM}{notes}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE REVIEW LOOP
# ─────────────────────────────────────────────────────────────────────────────

def review_loop(sessions: list, reviewer: str, skip_reviewed: bool):
    total    = len(sessions)
    reviewed = 0
    skipped  = 0

    for idx, row in enumerate(sessions, 1):
        already = row["is_prediction_correct"]
        if skip_reviewed and already is not None:
            skipped += 1
            continue

        print_session(idx, row)
        print(f"\n  Was this prediction CORRECT?")
        print(f"  {GREEN}y{RESET} = yes (correct)   {RED}n{RESET} = no (incorrect)   s = skip   q = quit")

        while True:
            try:
                answer = input(f"  → ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(f"\n\n{YELLOW}Review interrupted. {reviewed}/{total} sessions reviewed.{RESET}")
                return reviewed

            if answer == "q":
                print(f"\n{YELLOW}Quit. {reviewed}/{total} sessions reviewed.{RESET}")
                return reviewed

            if answer == "s":
                print(f"  {DIM}Skipped.{RESET}")
                skipped += 1
                break

            if answer in ("y", "n"):
                correct = answer == "y"
                notes   = ""
                if not correct:
                    try:
                        notes = input(f"  {DIM}Notes (optional, press Enter to skip): {RESET}").strip()
                    except (EOFError, KeyboardInterrupt):
                        notes = ""
                save_feedback(row["session_id"], correct, notes, reviewer)
                mark = f"{GREEN}✅ Marked correct{RESET}" if correct else f"{RED}❌ Marked incorrect{RESET}"
                print(f"  {mark}  — saved to Supabase")
                reviewed += 1
                break

            print(f"  {YELLOW}Enter y, n, s, or q{RESET}")

    print(f"\n{'='*65}")
    print(f"Review complete: {reviewed} reviewed, {skipped} skipped")
    return reviewed


# ─────────────────────────────────────────────────────────────────────────────
# STATS REPORT
# ─────────────────────────────────────────────────────────────────────────────

def print_stats():
    s = fetch_accuracy_stats()
    print(f"\n{BOLD}{'='*45}{RESET}")
    print(f"{BOLD}PREDICTION ACCURACY REPORT{RESET}")
    print(f"{'='*45}")
    print(f"  Total sessions : {s['total']}")
    print(f"  Reviewed       : {s['reviewed']}")
    print(f"  Correct        : {GREEN}{s['correct']}{RESET}")
    print(f"  Incorrect      : {RED}{s['incorrect']}{RESET}")
    if s["accuracy_pct"] is not None:
        colour = GREEN if s["accuracy_pct"] >= 85 else (YELLOW if s["accuracy_pct"] >= 70 else RED)
        print(f"  Accuracy       : {colour}{BOLD}{s['accuracy_pct']}%{RESET}")
    else:
        print(f"  Accuracy       : {DIM}no reviews yet{RESET}")
    print(f"{'='*45}\n")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Review AIMS lead prediction accuracy")
    parser.add_argument("--limit",    type=int, default=20,    help="Max sessions to show (default 20)")
    parser.add_argument("--reviewer", type=str, default="admin", help="Your name (stored in DB)")
    parser.add_argument("--all",      action="store_true",     help="Include already-reviewed sessions")
    parser.add_argument("--stats",    action="store_true",     help="Show accuracy stats and exit")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    sessions = fetch_sessions(args.limit, unreviewed_only=not args.all)

    print(f"\n{BOLD}AIMS — Lead Intelligence Prediction Review{RESET}")
    print(f"Reviewer  : {args.reviewer}")
    print(f"Sessions  : {len(sessions)} loaded  (--limit {args.limit})")
    print(f"Mode      : {'all sessions' if args.all else 'unreviewed only'}")
    print(f"\nFor each session: review the detected band vs what you think is correct.")
    print(f"Your feedback trains the next version of the scoring model.\n")

    if not sessions:
        print(f"{YELLOW}No sessions to review. Generate some chats first.{RESET}")
        return

    review_loop(sessions, reviewer=args.reviewer, skip_reviewed=not args.all)
    print_stats()


if __name__ == "__main__":
    main()
