"""Knowledge Quality dashboard for the Resources area."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any

import gradio as gr
from ktem.app import BasePage
from ktem.db.models import Conversation, IssueReport, engine
from ktem.utils.knowledge_quality import build_knowledge_quality_snapshot
from sqlmodel import Session, select

METRIC_STYLES = {
    "neutral": ("#475569", "#f8fafc"),
    "good": ("#166534", "#f0fdf4"),
    "warning": ("#92400e", "#fffbeb"),
    "risk": ("#991b1b", "#fef2f2"),
}


def _metric_card(label: str, value: str, tone: str = "neutral") -> str:
    color, background = METRIC_STYLES.get(tone, METRIC_STYLES["neutral"])
    return (
        '<div style="border:1px solid #e2e8f0;border-radius:12px;'
        f'padding:14px 16px;background:{background};min-width:140px;">'
        f'<div style="font-size:12px;color:{color};margin-bottom:6px;">'
        f"{html.escape(label)}</div>"
        f'<div style="font-size:24px;font-weight:700;color:{color};">'
        f"{html.escape(value)}</div></div>"
    )


def render_metrics(metrics: dict[str, Any]) -> str:
    helpful_rate = metrics.get("helpful_rate")
    helpful_value = "N/A" if helpful_rate is None else f"{helpful_rate}%"
    helpful_tone = (
        "neutral"
        if helpful_rate is None
        else (
            "good"
            if helpful_rate >= 80
            else "warning" if helpful_rate >= 50 else "risk"
        )
    )
    gap_count = int(metrics.get("gap_count", 0))
    cards = [
        _metric_card("Conversations", str(metrics.get("total_conversations", 0))),
        _metric_card("Helpful rate", helpful_value, helpful_tone),
        _metric_card("Thumbs down", str(metrics.get("negative_feedback", 0)), "risk"),
        _metric_card(
            "Unanswered", str(metrics.get("unanswered_questions", 0)), "warning"
        ),
        _metric_card("Issue reports", str(metrics.get("issue_reports", 0)), "warning"),
        _metric_card("Open gaps", str(gap_count), "risk" if gap_count else "good"),
    ]
    return (
        '<div style="display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 16px;">'
        + "".join(cards)
        + "</div>"
    )


def render_actions(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return (
            "### Recommended actions\n\n"
            "No knowledge gaps have been reported yet. The queue will populate "
            "automatically as users rate answers or submit issue reports."
        )

    lines = ["### Recommended actions", ""]
    for item in actions:
        reason = html.escape(str(item["reason"]))
        action = html.escape(str(item["action"]))
        count = int(item["count"])
        lines.append(f"- **{reason}** ({count} item(s)): {action}")
    return "\n".join(lines)


class KnowledgeQualityDashboard(BasePage):
    """Read-only view of answer feedback and knowledge maintenance needs."""

    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        gr.Markdown(
            "### Knowledge Quality\n"
            "Review answer feedback, unresolved questions, and the knowledge "
            "maintenance actions they imply. This view reads the feedback that "
            "chat users already submit."
        )
        self.metrics = gr.HTML()
        with gr.Row():
            self.refresh_btn = gr.Button("Refresh", variant="primary", scale=0)
            self.last_updated = gr.Markdown("")
        self.gap_table = gr.Dataframe(
            headers=[
                "Date",
                "Source",
                "Severity",
                "Question",
                "Answer excerpt",
                "Reason",
                "Conversation",
            ],
            interactive=False,
            wrap=True,
            height=420,
            elem_id="knowledge-quality-gaps",
        )
        self.actions = gr.Markdown()

    def _on_app_created(self):
        self._app.app.load(
            self.refresh_dashboard,
            inputs=[],
            outputs=[self.metrics, self.gap_table, self.actions, self.last_updated],
        )

    def on_register_events(self):
        self.refresh_btn.click(
            self.refresh_dashboard,
            inputs=[],
            outputs=[self.metrics, self.gap_table, self.actions, self.last_updated],
        )

    def refresh_dashboard(self):
        with Session(engine) as session:
            conversations = session.exec(
                select(Conversation)
                .order_by(Conversation.date_updated.desc())
                .limit(500)
            ).all()
            issue_reports = session.exec(
                select(IssueReport).order_by(IssueReport.id.desc()).limit(200)
            ).all()

        snapshot = build_knowledge_quality_snapshot(conversations, issue_reports)
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            render_metrics(snapshot["metrics"]),
            snapshot["rows"],
            render_actions(snapshot["actions"]),
            f"Last refreshed: **{generated_at}**",
        )
