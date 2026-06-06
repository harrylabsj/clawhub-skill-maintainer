---
name: clawhub-skill-maintainer
description: Maintain a large ClawHub skill portfolio. Use when the user wants to audit published skills, analyze downloads/installs/stars/comments, detect bulk-publishing account risk, recommend hide/merge/upgrade actions, generate approval-ready action plans, or build/update a ClawHub skill dashboard.
---

# ClawHub Skill Maintainer

Use this skill to audit and maintain a ClawHub publisher portfolio, especially when a large number of bulk-generated skills may create spam, quality, or account-review risk.

## Operating Principle

Analyze first, ask for approval second, execute last.

The default output is an evidence-backed recommendation set. Do not run public visibility changes, merge commands, delete commands, or publish updates unless the user explicitly approves the specific batch or operation.

## Core Workflow

1. Refresh portfolio data:

   ```bash
   python3 scripts/update_all.py --handle <clawhub-handle>
   ```

   To restart the trend history from a clean baseline while preserving old snapshots in an archive:

   ```bash
   python3 scripts/update_all.py --handle <clawhub-handle> --baseline
   ```

2. Review generated artifacts:

   - Dashboard: `reports/index.html`
   - Scored analysis: `data/processed/<handle>_skill_analysis.csv`
   - Low-signal triage: `data/processed/<handle>_low_signal_triage.csv`
   - Latest snapshot: `data/snapshots/<handle>/latest.json`
   - Growth deltas: `data/processed/<handle>_skill_growth.csv`
   - Trend summary: `data/processed/<handle>_trend_summary.json`
   - General approval board: `reports/approval_packets/<handle>_approval_board.md`
   - Bulk cleanup board: `reports/bulk_cleanup/<handle>_bulk_approval_board.md`

3. Explain the recommendation to the user in business terms:

   - what should stay public
   - what should be upgraded
   - what should be hidden first
   - what should be merged only after review
   - what should be monitored

4. Ask the user to approve one batch at a time using the exact approval phrase shown in the generated approval board.

5. After approval, execute only the approved commands and report the outcome.

## Account-Risk Cleanup Lens

When the user says bulk publishing caused an account review, start with `scripts/plan_bulk_cleanup.py` outputs.

The strongest bulk-risk pattern is:

- low or plausible-low signal
- single version
- zero installs
- zero stars
- zero comments

Recommended default policy:

- Phase 1: hide low-download skills matching the strongest risk pattern.
- Phase 2: spot-check, then hide moderate-download skills matching the same pattern.
- Phase 3: upgrade within a short deadline or hide.
- Phase 4: merge or hide repeated families only after target review.
- Do not delete by default.

Prefer hide before delete because `clawhub hide` is reversible with `clawhub unhide <slug>`.

## Approval And Execution

Generated command files are intentionally commented out. Treat them as previews, not scripts to run blindly.

Safe command forms after explicit approval:

```bash
clawhub hide <slug> --yes
clawhub unhide <slug> --yes
clawhub inspect <slug> --files
clawhub publish <path>
clawhub skill rescan <slug>
```

Higher-risk command form:

```bash
clawhub skill merge <source-slug> <target-slug> --yes
```

Merge is higher risk because no obvious `unmerge` command is available. Review the canonical target before approving merge batches.

## Responding To Users

For skills with comments or reported issues:

1. Inspect the skill with `clawhub inspect <slug> --files`.
2. Find or reconstruct the local source.
3. Reproduce or understand the issue.
4. Patch the source skill.
5. Publish the update with `clawhub publish <path>`.
6. Rescan if needed with `clawhub skill rescan <slug>`.
7. Reply with what changed, the new version, and any remaining limitation.

If comment bodies are unavailable through the API or CLI, say that only comment counts are visible and ask for a browser workflow or comment export.

## Dashboard Maintenance

The dashboard is a local generated artifact:

```bash
python3 scripts/update_all.py --handle <clawhub-handle>
```

Open `reports/index.html` after refresh. It is safe to regenerate; it should not be packaged into the skill.

Each full refresh writes a timestamped snapshot under `data/snapshots/<handle>/`. When at least two snapshots exist, the dashboard shows the top 20 skills by new downloads and new installs since the previous snapshot. Use those growth charts to decide which skills are becoming popular and deserve priority maintenance.

Use `--baseline` when the account has materially changed and the next run should become the first active trend baseline. Existing active snapshots are archived under `data/snapshots/<handle>/archive/` instead of deleted.

## Safety Rules

- Never execute hide, merge, delete, or publish actions merely because a report recommends them.
- Never batch-hide skills with installs, stars, comments, or strong usage without manual review.
- Use hide/private-style cleanup before deletion.
- Treat generated shell files as commented approval previews.
- Keep generated data, caches, logs, and reports out of the published skill package.
- If network or authentication fails, work from existing snapshots and clearly state the limitation.
