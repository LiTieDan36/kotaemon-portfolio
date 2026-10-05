"""Aggregate user feedback into an actionable knowledge quality snapshot.

The dashboard is intentionally read-only. It turns the feedback that Kotaemon
already stores on conversations and issue reports into a small set of product
signals: helpfulness, negative feedback, unanswered questions, and concrete
knowledge maintenance actions.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

UNANSWERED_MARKERS = (
    "(sorry, i don't know)",
    "i don't know",
    "not enough information",
    "no relevant information",
    "cannot answer",
    "can't answer",
)

ISSUE_REASON_LABELS = {
    "offensive": "Answer may be offensive",
    "wrong-evidence": "Evidence is incorrect",
    "missing-knowledge": "Knowledge base is missing information",
    "outdated-knowledge": "Knowledge may be outdated",
    "incorrect": "Answer was marked incorrect",
}

REASON_ACTIONS = {
    "User marked answer unhelpful": (
        "Review retrieval quality and the cited sources for these questions."
    ),
    "No answer produced": (
        "Add missing content or an explicit fallback answer for these questions."
    ),
    "Knowledge base is missing information": (
        "Add the missing knowledge to the relevant collection and reindex it."
    ),
    "Knowledge may be outdated": (
        "Refresh the source document and rebuild the affected index."
    ),
    "Evidence is incorrect": (
        "Audit the cited evidence and correct or replace the source document."
    ),
    "Answer was marked incorrect": (
        "Compare the answer with the source material and correct the source or prompt."
    ),
    "Answer may be offensive": (
        "Review the answer and add a guardrail or source-level correction."
    ),
}

RESULT_HEADERS = [
    "Date",
    "Source",
    "Severity",
    "Question",
    "Answer excerpt",
    "Reason",
    "Conversation",
]


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _truncate(value: Any, limit: int = 180) -> str:
    text = " ".join(_safe_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _message_parts(turn: Any) -> tuple[str, str]:
    """Return the user question and assistant answer from one chat turn."""
    if isinstance(turn, dict):
        role = _safe_text(turn.get("role")).lower()
        content = _truncate(turn.get("content"))
        if role == "user":
            return content, ""
        if role == "assistant":
            return "", content
        return "", content

    if isinstance(turn, (list, tuple)):
        question = _truncate(turn[0]) if len(turn) > 0 else ""
        answer = _truncate(turn[1]) if len(turn) > 1 else ""
        return question, answer

    return "", _truncate(turn)


def _turn_index_from_like(index: Any) -> int:
    if isinstance(index, (list, tuple)) and index:
        try:
            return int(index[0])
        except (TypeError, ValueError):
            return -1
    try:
        return int(index)
    except (TypeError, ValueError):
        return -1


def _is_unanswered(answer: str) -> bool:
    normalized = " ".join(answer.lower().split())
    if not normalized:
        return True
    return any(marker in normalized for marker in UNANSWERED_MARKERS)


def _parse_date(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return _safe_text(value)


def _conversation_name(conversation: Any) -> str:
    return _safe_text(_get(conversation, "name", "Untitled conversation"))


def _row(
    *,
    date: str,
    source: str,
    severity: str,
    question: str,
    answer: str,
    reason: str,
    conversation: str,
) -> list[str]:
    return [
        date,
        source,
        severity,
        _truncate(question, 140),
        _truncate(answer, 180),
        reason,
        _truncate(conversation, 80),
    ]


def build_knowledge_quality_snapshot(
    conversations: Iterable[Any],
    issue_reports: Iterable[Any],
    *,
    limit: int = 100,
) -> dict[str, Any]:
    """Build metrics, gap rows, and recommended actions from stored feedback."""
    conversations = list(conversations)
    issue_reports = list(issue_reports)

    positive_feedback = 0
    negative_feedback = 0
    unanswered_count = 0
    rows: list[list[str]] = []
    seen: set[tuple[str, str, str]] = set()

    conversation_dates: dict[str, str] = {}
    conversation_names: dict[str, str] = {}

    for conversation in conversations:
        conversation_id = _safe_text(_get(conversation, "id", ""))
        conversation_dates[conversation_id] = _parse_date(
            _get(conversation, "date_updated")
        )
        conversation_names[conversation_id] = _conversation_name(conversation)

        data_source = _get(conversation, "data_source", {}) or {}
        messages = (
            data_source.get("messages", []) if isinstance(data_source, dict) else []
        )
        likes = data_source.get("likes", []) if isinstance(data_source, dict) else []

        for like in likes:
            if not isinstance(like, (list, tuple)) or len(like) < 3:
                continue
            turn_index = _turn_index_from_like(like[0])
            if turn_index < 0 or turn_index >= len(messages):
                continue
            question, answer = _message_parts(messages[turn_index])
            liked = bool(like[2])
            if liked:
                positive_feedback += 1
                continue

            negative_feedback += 1
            reason = "User marked answer unhelpful"
            key = (conversation_id, question, reason)
            if key not in seen:
                rows.append(
                    _row(
                        date=conversation_dates[conversation_id],
                        source="Thumbs down",
                        severity="High",
                        question=question,
                        answer=answer,
                        reason=reason,
                        conversation=conversation_names[conversation_id],
                    )
                )
                seen.add(key)

        for turn in messages:
            question, answer = _message_parts(turn)
            if not question or not _is_unanswered(answer):
                continue
            unanswered_count += 1
            reason = "No answer produced"
            key = (conversation_id, question, reason)
            if key not in seen:
                rows.append(
                    _row(
                        date=conversation_dates[conversation_id],
                        source="System",
                        severity="Medium",
                        question=question,
                        answer=answer,
                        reason=reason,
                        conversation=conversation_names[conversation_id],
                    )
                )
                seen.add(key)

    issue_report_count = 0
    for report in issue_reports:
        issue_report_count += 1
        report_id = _safe_text(_get(report, "id", ""))
        issues = _get(report, "issues", {}) or {}
        chat = _get(report, "chat", {}) or {}

        if isinstance(issues, dict):
            correctness = _safe_text(issues.get("correctness"))
            issue_codes = list(issues.get("issues") or [])
            detail = _safe_text(issues.get("more_detail"))
        else:
            correctness = ""
            issue_codes = []
            detail = ""

        conv_id = _safe_text(chat.get("conv_id")) if isinstance(chat, dict) else ""
        date = conversation_dates.get(conv_id) or f"Report #{report_id}"
        conversation = conversation_names.get(conv_id) or "Unknown conversation"

        chat_history = chat.get("chat_history", []) if isinstance(chat, dict) else []
        question = ""
        answer = ""
        for turn in reversed(chat_history):
            q, a = _message_parts(turn)
            if q:
                question, answer = q, a
                break

        if detail:
            reason = detail
        elif issue_codes:
            codes = list(dict.fromkeys(issue_codes))
            reason = "; ".join(
                ISSUE_REASON_LABELS.get(code, _safe_text(code)) for code in codes
            )
        elif correctness == "incorrect":
            reason = ISSUE_REASON_LABELS["incorrect"]
        else:
            reason = "User submitted a feedback report"

        severity = "High" if correctness == "incorrect" or issue_codes else "Medium"
        key = (conv_id or f"report-{report_id}", question, reason)
        if key not in seen:
            rows.append(
                _row(
                    date=date,
                    source="Issue report",
                    severity=severity,
                    question=question,
                    answer=answer or detail,
                    reason=reason,
                    conversation=conversation,
                )
            )
            seen.add(key)

    rows.sort(key=lambda row: row[0], reverse=True)
    rows = rows[:limit]

    explicit_feedback = positive_feedback + negative_feedback
    helpful_rate = (
        round(positive_feedback / explicit_feedback * 100, 1)
        if explicit_feedback
        else None
    )

    action_counts = Counter(row[5] for row in rows)
    actions = [
        {
            "reason": reason,
            "count": count,
            "action": REASON_ACTIONS.get(
                reason,
                "Review these questions and update the relevant knowledge source.",
            ),
        }
        for reason, count in action_counts.most_common()
    ]

    return {
        "metrics": {
            "total_conversations": len(conversations),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "helpful_rate": helpful_rate,
            "issue_reports": issue_report_count,
            "unanswered_questions": unanswered_count,
            "gap_count": len(rows),
        },
        "rows": rows,
        "actions": actions,
        "headers": RESULT_HEADERS,
    }
