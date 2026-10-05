# Contributions and Attribution

This repository is a portfolio derivative of
[Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon). It is **not** an
independent from-scratch RAG product.

## Upstream

- Project: kotaemon
- Upstream commit used as the baseline: `9ad3e4e49aa35b8acddd235918a5d9753c1cfdf9`
- License: Apache License 2.0
- Upstream owner: The Kotaemon Team / Cinnamon

The original RAG pipeline, document index, model management, Gradio UI,
conversation system, and the vast majority of the codebase remain upstream
work. The Apache-2.0 license is preserved in `LICENSE.txt`.

## My contribution

The portfolio contribution is the **Knowledge Quality dashboard**:

- Defined the product problem: feedback is collected, but knowledge owners
  still lack a prioritized maintenance queue.
- Added a deterministic aggregation layer in
  `libs/ktem/ktem/utils/knowledge_quality.py`.
- Added a read-only dashboard in
  `libs/ktem/ktem/pages/resources/knowledge_quality.py`.
- Integrated the dashboard into the admin-facing Resources area.
- Expanded feedback reasons with missing and outdated knowledge.
- Added automated tests for thumbs-up/down, unanswered questions, issue
  reports, empty states, and database-backed refresh behavior.
- Added a repeatable demo data seeder and cleanup command.
- Added a documented Windows/local development setup path.

## What is explicitly not claimed

- I did not write the original kotaemon RAG system.
- I did not create the upstream retrieval, indexing, model management, or chat
  pipeline.
- The dashboard is a deterministic feedback aggregator, not an LLM evaluation
  system.
- No real user, revenue, or conversion metrics are claimed.

## Verification

- Targeted tests: `python -m uv run --no-sync pytest libs/ktem/ktem_tests/test_knowledge_quality.py -q`
- Dashboard import and rendering smoke check passed.
- Local app returned HTTP 200 and exposed the `Knowledge Quality` tab.
- Demo feedback was inserted into the real database and removed successfully.
