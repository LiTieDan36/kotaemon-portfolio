# Portfolio Case Study: Knowledge Quality Dashboard

## One-line positioning

I made a document-QA product close its feedback loop: user ratings and issue
reports now become a prioritized knowledge-maintenance queue instead of
disappearing into chat history.

## Product context

Kotaemon already lets users rate answers and submit problem reports. However,
the product captured feedback without turning it into a workflow for the person
responsible for the knowledge base.

That creates a trust gap:

- Repeated unanswered questions are hard to spot.
- Incorrect citations are not grouped into a maintenance queue.
- Outdated or missing knowledge is not connected to the source collection that
  needs updating.
- Knowledge owners cannot see whether answer quality is improving.

## Target user

- Knowledge-base owners and operations admins.
- Internal helpdesk teams maintaining a document collection.
- Product teams using RAG for customer or employee support.

## Product hypothesis

If feedback is converted into an actionable queue with reasons and recommended
repairs, knowledge owners will update sources faster and the system will produce
fewer repeated knowledge gaps.

## Solution

### Knowledge Quality dashboard

A new admin-facing tab under Resources shows:

- Conversation count.
- Helpful rate from thumbs-up and thumbs-down feedback.
- Negative feedback count.
- Unanswered-question count.
- Issue-report count.
- Open knowledge-gap count.
- A queue with date, source, severity, question, answer excerpt, reason, and
  conversation.
- Deterministic recommended actions grouped by reason.

### Feedback reasons

The existing report form now supports:

- Missing information.
- Outdated knowledge.
- Incorrect evidence.
- Offensive content.
- Incorrect answer.

These reasons map directly to maintenance actions such as adding content,
refreshing a source, or auditing a citation.

## Product decisions

- **Do not require another LLM call:** feedback triage is deterministic, cheap,
  and explainable.
- **Preserve existing data:** the feature reads the current conversation and
  issue-report tables, so no migration is required.
- **Admin-facing placement:** the dashboard lives under Resources instead of
  exposing all feedback on the chat screen.
- **Action before analytics:** every gap reason is paired with a concrete next
  action.
- **Honest heuristics:** unanswered questions are detected from known fallback
  patterns and empty answers, not presented as perfect semantic evaluation.

## Implementation

- `libs/ktem/ktem/utils/knowledge_quality.py` aggregates conversations,
  thumbs feedback, unanswered questions, and issue reports.
- `libs/ktem/ktem/pages/resources/knowledge_quality.py` renders metrics,
  the gap table, and recommended actions.
- `libs/ktem/ktem/pages/resources/__init__.py` registers the dashboard tab.
- `libs/ktem/ktem/pages/chat/report.py` adds missing/outdated knowledge reasons.
- `libs/ktem/ktem_tests/test_knowledge_quality.py` verifies the aggregation and
  database refresh path.
- `examples/seed_knowledge_quality_demo.py` creates or removes repeatable demo
  feedback.

## Verification evidence

- 3/3 targeted tests passed.
- Dashboard import and rendering smoke check passed.
- The local Kotaemon app returned HTTP 200.
- The live HTML included the `Knowledge Quality` tab.
- Demo data was seeded into the real SQLite database and cleaned up again.

## Known limitations

- Thumbs-down does not yet capture a structured reason at the moment of
  clicking; users can add reasons through the existing feedback form.
- The unanswered heuristic covers empty answers and known fallback phrases.
- Issue reports do not have a first-class timestamp, so their display uses the
  related conversation date or report id.
- The dashboard reads the latest 500 conversations and 200 issue reports.
- No assignment, resolution status, or exported maintenance ticket exists yet.

## Next iteration

1. Ask for a reason immediately after a thumbs-down.
2. Add trend lines for helpful rate and repeated unanswered questions.
3. Assign each gap to a knowledge owner.
4. Add resolution status and verified-after-update tracking.
5. Export the queue as CSV or a lightweight issue list.
6. Measure whether resolved gaps reduce repeated questions.

## Interview story outline

- **Situation:** The RAG product collected feedback but did not act on it.
- **Task:** Turn scattered ratings and reports into a knowledge-maintenance
  workflow without a database migration.
- **Action:** Aggregated existing feedback, added actionable report reasons,
  built an admin dashboard, and tested the refresh path.
- **Result:** Users can now see what knowledge is missing, outdated, or
  unsupported and what to fix next.
