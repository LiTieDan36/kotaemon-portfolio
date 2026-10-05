"""Seed or remove demo feedback for the Knowledge Quality dashboard.

Run from the repository root:

    python examples/seed_knowledge_quality_demo.py --seed
    python examples/seed_knowledge_quality_demo.py --cleanup
"""

from __future__ import annotations

import argparse
from datetime import datetime

from ktem.db.models import Conversation, IssueReport, engine
from sqlmodel import Session, delete

DEMO_USER = "portfolio-demo"
DEMO_CONVERSATION_IDS = [
    "demo-knowledge-quality-refund",
    "demo-knowledge-quality-onboarding",
]


def cleanup(session: Session) -> None:
    session.exec(delete(Conversation).where(Conversation.id.in_(DEMO_CONVERSATION_IDS)))
    session.exec(delete(IssueReport).where(IssueReport.user == DEMO_USER))
    session.commit()


def seed(session: Session) -> None:
    session.add(
        Conversation(
            id=DEMO_CONVERSATION_IDS[0],
            name="Demo - Refund policy",
            user=DEMO_USER,
            date_updated=datetime(2026, 10, 3, 10, 30),
            data_source={
                "messages": [
                    [
                        "What is the refund window for annual plans?",
                        "Annual plans can be refunded within 14 days. [1]",
                    ],
                    [
                        "Does the refund window change after renewal?",
                        "I don't know",
                    ],
                ],
                "likes": [
                    [[0, 1], "Annual plans can be refunded within 14 days. [1]", True],
                    [[1, 1], "I don't know", False],
                ],
            },
        )
    )
    session.add(
        Conversation(
            id=DEMO_CONVERSATION_IDS[1],
            name="Demo - Onboarding checklist",
            user=DEMO_USER,
            date_updated=datetime(2026, 10, 4, 15, 5),
            data_source={
                "messages": [
                    [
                        "How do I invite a teammate to the workspace?",
                        "",
                    ]
                ],
                "likes": [],
            },
        )
    )
    session.add(
        IssueReport(
            issues={
                "correctness": "incorrect",
                "issues": ["wrong-evidence", "outdated-knowledge"],
                "more_detail": "The pricing page cited here changed in September.",
            },
            chat={
                "conv_id": DEMO_CONVERSATION_IDS[0],
                "chat_history": [
                    [
                        "What is the refund window for annual plans?",
                        "Annual plans can be refunded within 30 days. [1]",
                    ]
                ],
            },
            settings={},
            user=DEMO_USER,
        )
    )
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seed", action="store_true")
    group.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()

    with Session(engine) as session:
        cleanup(session)
        if args.seed:
            seed(session)
            print("Seeded Knowledge Quality demo feedback.")
        else:
            print("Removed Knowledge Quality demo feedback.")


if __name__ == "__main__":
    main()
