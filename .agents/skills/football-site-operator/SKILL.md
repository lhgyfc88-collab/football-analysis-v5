---
name: football-site-operator
description: Operate the football analytics website, prepare data-grounded self-media drafts, and delegate repository changes to Codex with review controls.
metadata: {"openclaw":{"requires":{"bins":["git"]}}}
---

# Football Site Operator

Use this skill when the user asks to operate, inspect, improve, publish content for, or troubleshoot the football analytics project.

## Repository orientation

1. Resolve the repository workspace and read `AGENTS.md` and `README.md` first.
2. Inspect `git status` before any write operation.
3. Treat `football_predictor/app.py`, `data_api.py`, `models.py`, the templates, and tests as the primary implementation surface.
4. Never expose secrets from `config.json`, environment files, shell history, logs, or authentication stores.

## Daily content workflow

1. Determine the active data source and timestamp.
2. If the source is `demo`, create only product demonstrations, model explainers, or development updates.
3. If the source is `api_basic`, state that only fixture data is available and do not create specific match recommendations.
4. Only use verified CSV/API fields for factual claims. Mark every missing field as unverified.
5. Produce a review packet rather than publishing automatically:
   - one short-video script of 20–40 seconds;
   - one Xiaohongshu/WeChat-style post;
   - three titles or hooks;
   - one website call to action;
   - a data-source and uncertainty note.
6. Send the packet to the configured owner channel for approval. Do not publish without explicit approval and an authorized platform integration.

## Code-change workflow

1. Use the native Codex harness for repository changes.
2. Bind Codex to the repository working directory and ask it to read `AGENTS.md` before editing.
3. Work on a new branch; never push directly to `main`.
4. Keep the task focused. Run compile checks, the Flask route smoke test, and relevant tests.
5. Present the diff and test results before opening or merging a Pull Request.
6. Require explicit approval for deployment, payment changes, destructive operations, database migrations, public posting, or secret rotation.

## Site health workflow

Check, in order:

1. repository state and recent commits;
2. Python dependency/install failures;
3. data-source availability and freshness;
4. Flask root-route response;
5. template rendering and static assets;
6. logs with secret redaction.

Report the exact failing layer and the smallest safe next action. Do not conceal demo-data fallback as a successful production-data run.

## Content and monetization boundaries

Position the product as sports data analysis, model transparency, education, and post-match review. Do not promise profits, fabricate results, encourage loss-chasing, or present probabilistic output as certainty. Paid features should focus on dashboards, historical data, alerts, exports, model notes, and transparent evaluation rather than guaranteed picks.
