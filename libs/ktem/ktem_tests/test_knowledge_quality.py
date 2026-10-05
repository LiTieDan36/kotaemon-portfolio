"""Tests for the knowledge quality dashboard aggregation."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from ktem.utils.knowledge_quality import build_knowledge_quality_snapshot
from sqlalchemy import create_engine
from sqlmodel import Session

from ktem.db.models import Conversation


def test_snapshot_collects_feedback_unanswered_questions_and_reports() -> None:
    conversations = [
        SimpleNamespace(
            id="conv-1",
            name="Product FAQ",
            date_updated=datetime(2026, 10, 1, 9, 30),
            data_source={
                "messages": [
                    ["What is the refund window?", "The refund window is 30 days. [1]"],
                    ["Can I export invoices?", "I don't know"],
                ],
                "likes": [
                    [[0, 1], "The refund window is 30 days. [1]", True],
                    [[1, 1], "I don't know", False],
                ],
            },
        ),
        SimpleNamespace(
            id="conv-2",
            name="Onboarding",
            date_updated=datetime(2026, 10, 2, 11, 0),
            data_source={
                "messages": [["How do I invite a teammate?", ""]],
                "likes": [],
            },
        ),
    ]

    reports = [
        SimpleNamespace(
            id=7,
            issues={
                "correctness": "incorrect",
                "issues": ["wrong-evidence", "outdated-knowledge"],
                "more_detail": "",
            },
            chat={
                "conv_id": "conv-1",
                "chat_history": [["What is the refund window?", "It is 7 days. [1]"]],
            },
        )
    ]

    snapshot = build_knowledge_quality_snapshot(conversations, reports)
    metrics = snapshot["metrics"]

    assert metrics["total_conversations"] == 2
    assert metrics["positive_feedback"] == 1
    assert metrics["negative_feedback"] == 1
    assert metrics["helpful_rate"] == 50.0
    assert metrics["issue_reports"] == 1
    assert metrics["unanswered_questions"] == 2
    assert metrics["gap_count"] == 4

    reasons = {row[5] for row in snapshot["rows"]}
    assert "User marked answer unhelpful" in reasons
    assert "No answer produced" in reasons
    assert "Evidence is incorrect; Knowledge may be outdated" in reasons
    assert snapshot["actions"]


def test_snapshot_handles_empty_feedback() -> None:
    snapshot = build_knowledge_quality_snapshot([], [])

    assert snapshot["metrics"]["helpful_rate"] is None
    assert snapshot["metrics"]["gap_count"] == 0
    assert snapshot["rows"] == []
    assert snapshot["actions"] == []


def test_dashboard_refreshes_from_database(monkeypatch) -> None:
    import ktem.pages.resources.knowledge_quality as dashboard_module

    test_engine = create_engine("sqlite:///:memory:")
    Conversation.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        session.add(
            Conversation(
                id="conv-ui",
                name="Demo conversation",
                data_source={
                    "messages": [["Where is the policy?", "I don't know"]],
                    "likes": [[[0, 1], "I don't know", False]],
                },
            )
        )
        session.commit()

    monkeypatch.setattr(dashboard_module, "engine", test_engine)
    dashboard = object.__new__(dashboard_module.KnowledgeQualityDashboard)
    metrics, rows, actions, last_updated = dashboard.refresh_dashboard()

    assert "Open gaps" in metrics
    assert len(rows) == 2
    assert "No answer produced" in actions
    assert last_updated.startswith("Last refreshed:")
