"""
Generate a deterministic local evaluation dataset for the AIMS assistant.
"""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_FILE = Path(__file__).with_name("eval_dataset_local.json")

COURSES = {
    "mba": "MBA",
    "bba": "BBA",
    "mca": "MCA",
    "bca": "BCA",
    "phd": "PhD",
}

TOPIC_QUERIES = {
    "fees": {
        "queries": [
            "{course} fees",
            "{course} fee structure",
            "{course} feees",
            "cost of {course}",
        ],
        "keywords": ["fee", "fees", "admissions", "contact"],
    },
    "placements": {
        "queries": [
            "{course} placements",
            "plcements {course}",
            "{course} job opportunities",
            "{course} package details",
        ],
        "keywords": ["placement", "package", "recruiter", "company"],
    },
    "hostel": {
        "queries": [
            "{course} hostel",
            "hostl {course}",
            "stay for {course}",
            "{course} hostel facility",
        ],
        "keywords": ["hostel", "facility", "stay", "campus"],
    },
    "admission": {
        "queries": [
            "{course} admission process",
            "{course} eligibility",
            "{course} addmission",
            "how to apply for {course}",
        ],
        "keywords": ["admission", "eligibility", "apply", "documents"],
    },
    "course": {
        "queries": [
            "{course} course details",
            "{course} duration",
            "{course} specializations",
            "{course} curriculm",
        ],
        "keywords": ["semester", "duration", "specialization", "program"],
    },
}


def build_dataset():
    dataset = []
    counter = 1

    for course_key, course_label in COURSES.items():
        for topic_key, topic_data in TOPIC_QUERIES.items():
            for query in topic_data["queries"]:
                dataset.append(
                    {
                        "id": f"eval-{counter:03d}",
                        "query": query.format(course=course_label.lower()),
                        "expected_course": course_key,
                        "expected_topic": topic_key,
                        "expected_behavior": "answer",
                        "expected_keywords": topic_data["keywords"],
                        "context_queries": [],
                    }
                )
                counter += 1

    follow_up_contexts = [
        ("MBA course details", "what about fees", "mba", "fees"),
        ("BBA admission process", "what about placements", "bba", "placements"),
        ("MCA hostel", "fees too", "mca", "fees"),
        ("BCA placements", "hostel also", "bca", "hostel"),
        ("PhD admission process", "course details", "phd", "course"),
    ]

    for context_query, query, course_key, topic_key in follow_up_contexts:
        dataset.append(
            {
                "id": f"eval-{counter:03d}",
                "query": query,
                "expected_course": course_key,
                "expected_topic": topic_key,
                "expected_behavior": "answer",
                "expected_keywords": TOPIC_QUERIES[topic_key]["keywords"],
                "context_queries": [context_query],
            }
        )
        counter += 1

    clarification_cases = [
        ("what about fees", "fees"),
        ("hostl faclity", "hostel"),
        ("placement info", "placements"),
        ("admission?", "admission"),
        ("course details", "course"),
    ]

    for query, topic_key in clarification_cases:
        dataset.append(
            {
                "id": f"eval-{counter:03d}",
                "query": query,
                "expected_course": None,
                "expected_topic": topic_key,
                "expected_behavior": "clarification",
                "expected_keywords": [],
                "context_queries": [],
            }
        )
        counter += 1

    greetings = [
        "hi",
        "hello there",
        "hey aims",
        "thank you",
        "goodbye",
    ]

    for query in greetings:
        dataset.append(
            {
                "id": f"eval-{counter:03d}",
                "query": query,
                "expected_course": None,
                "expected_topic": None,
                "expected_behavior": "greeting",
                "expected_keywords": [],
                "context_queries": [],
            }
        )
        counter += 1

    return dataset


def main() -> int:
    dataset = build_dataset()
    OUTPUT_FILE.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    print(f"Wrote {len(dataset)} evaluation cases to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
