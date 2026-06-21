# Skill Maintainer

Maintenance dashboard for a ClawHub publisher portfolio.

Published locations:

- GitHub: https://github.com/harrylabsj/clawhub-skill-maintainer
- ClawHub: https://clawhub.ai/harrylabsj/skill-maintainer

Note: the GitHub/local project is named `clawhub-skill-maintainer`, but the ClawHub slug is `skill-maintainer` because `clawhub-` is a protected slug namespace on ClawHub. The previous temporary slug `skill-portfolio-maintainer` redirects to `skill-maintainer`.

## What It Does

- Collects public publisher profile data and all published skill listings.
- Fetches per-skill stats such as downloads, installs, stars, comments, and versions.
- Scores each skill with a directional "meaningfulness" score.
- Separates failed skill-detail fetches into a `data_unavailable` queue that receives no decision for that run.
- Builds a static HTML dashboard with charts, queues, filtering, and sorting.
- Defines an operating loop for responding to comments, fixing issues, scanning, publishing, and replying.
- Produces approval-ready evidence packets so a user can approve one small batch at a time.
- Generates AI-assisted maintenance candidate plans and per-skill maintainer prompts for large portfolios.

## Run

```bash
python3 scripts/update_all.py --handle harrylabsj
```

Output:

- `data/raw/`: raw profile, listing, and skill detail snapshots.
- `data/processed/harrylabsj_skills.csv`: normalized skill stats.
- `data/processed/harrylabsj_skill_analysis.csv`: scored analysis.
- `data/processed/harrylabsj_low_signal_triage.csv`: low/plausible-low triage decisions.
- `data/processed/harrylabsj_data_unavailable.csv`: failed detail fetches excluded from today's decisions.
- `data/processed/harrylabsj_summary.json`: portfolio summary.
- `data/snapshots/harrylabsj/`: timestamped metric snapshots plus `latest.json`.
- `data/processed/harrylabsj_skill_growth.csv`: latest per-skill deltas versus the previous snapshot.
- `data/processed/harrylabsj_trend_summary.json`: top new downloads/installs and snapshot window metadata.
- `reports/index.html`: static dashboard.
- `reports/action_plans/`: dry-run action plans and commented command files.
- `reports/approval_packets/`: batch approval board, manifest, and commented commands.
- `reports/bulk_cleanup/`: clear delisting recommendations from a bulk-publishing account-risk lens.
- `reports/auto_upgrade/`: AI-assisted maintenance candidate plan, candidate manifest, CSV, and per-skill agent prompts.

## AI-Assisted Maintenance

For portfolios that are too large to maintain manually, generate a small daily maintenance candidate queue:

```bash
python3 scripts/auto_upgrade.py --handle harrylabsj --limit 5
```

Or attach the queue to the normal refresh:

```bash
python3 scripts/update_all.py --handle harrylabsj --auto-upgrade-plan --auto-upgrade-limit 5
```

To fetch missing sources before writing the plan, use:

```bash
python3 scripts/auto_upgrade.py --handle harrylabsj --limit 5 --fetch-source
```

Source lookup order is GitHub first, local source roots second, and ClawHub install/download fallback last. If GitHub or ClawHub returns a rate limit, the script records the error and stops that source path instead of retrying.

Output:

- `reports/auto_upgrade/latest/report.md`: human-readable queue and findings.
- `reports/auto_upgrade/latest/manifest.json`: machine-readable candidate manifest.
- `reports/auto_upgrade/latest/candidates.csv`: spreadsheet-friendly candidate table.
- `reports/auto_upgrade/latest/agent_prompts/<slug>.md`: one safe upgrade prompt per candidate.

The script is plan-only by default. It does not publish, hide, merge, delete, rename, change ownership, or upgrade skills automatically.

For narrow deterministic edits, use:

```bash
python3 scripts/auto_upgrade.py --handle harrylabsj --limit 5 --apply-safe
```

`--apply-safe` only appends missing example prompts or sensitive-domain safety boundaries to local `SKILL.md` files when the package surface is small and contains no forbidden files. Treat the result as a draft that still needs review, validation, and explicit publish approval.

## Data Quality Rule

If a skill detail fetch fails, the row is marked `data_unavailable` for that run. It is kept in raw and processed artifacts for visibility, but it is excluded from quality maintenance, upgrade, hide, merge, delete, monitor, bulk-cleanup, and AI candidate-plan decisions until a later collection succeeds.

## Periodic Update

Use the same command from cron, launchd, GitHub Actions, or a Codex automation. A simple daily cron shape is:

```cron
0 9 * * * cd "/Users/jianghaidong/Library/Mobile Documents/com~apple~CloudDocs/codex/clawhub-skill-maintainer" && /usr/bin/python3 scripts/update_all.py --handle harrylabsj >> logs/update.log 2>&1
```

To include a daily AI maintenance queue without changing any source files:

```cron
20 9 * * * cd "/Users/jianghaidong/Library/Mobile Documents/com~apple~CloudDocs/codex/clawhub-skill-maintainer" && /usr/bin/python3 scripts/update_all.py --handle harrylabsj --auto-upgrade-plan --auto-upgrade-limit 5 >> logs/update.log 2>&1
```

To include source fetching, add `--auto-upgrade-fetch-source`. Use it sparingly if the registry is rate-limiting.

Each update writes a new snapshot, compares it to the previous snapshot, and updates the dashboard's Growth Watch charts:

- top 20 skills by new downloads
- top 20 skills by new installs

Use these charts to find skills that are becoming popular now, not just skills with historically high totals.

When the ClawHub account has materially changed and the current run should become a new first baseline, use:

```bash
python3 scripts/update_all.py --handle harrylabsj --baseline
```

This archives active snapshots under `data/snapshots/harrylabsj/archive/` and starts a new trend baseline without deleting old snapshot files.

## Maintenance Loop

1. Collect fresh data.
2. Write a snapshot and compare new downloads/installs against the previous run.
3. Move failed detail fetches into `data_unavailable` and make no decision for them today.
4. Triage skills with comments, installs, stars, high downloads, or strong new growth.
5. Generate a maintenance candidate plan and agent prompts for the next small queue.
6. Inspect the source skill and reproduce the issue.
7. Patch the skill and update README/changelog metadata.
8. Run validation and dry-run publish.
9. Publish with `clawhub publish ./path/to/skill` only after approval.
10. Reply to the user comment with the fix, version, and any limitation.
11. Consolidate weak duplicate skills into private libraries or stronger public skills.

## Current Snapshot

First full run for `harrylabsj` collected 1,044 public skills with 1,044 detail records and 0 detail errors.

- downloads: 192,737 from per-skill detail records
- installs: 146
- stars: 15
- comments: 1
- action buckets: 38 keep public, 1 respond/fix/upload, 237 curate or improve, 709 review for merge/private, 59 private/delete candidates
- low/plausible-low triage: 83 upgrade public, 55 merge, 487 move private/hide, 342 monitor, 0 direct delete candidates
- dry-run action plan: 167 hide commands, 320 private backlog reviews, 41 merge commands, 120 upgrade inspections, 120 monitor checks
- approval packets: 4 pending batches generated from the dry-run plan
- bulk cleanup recommendation: 579 clear hide, 96 spot-check then hide, 29 upgrade within 7 days or hide
- bulk approval packets: `APPROVE BULK_HIDE_PHASE1`, `APPROVE BULK_HIDE_PHASE2`, `APPROVE BULK_PHASE3_POLICY`, `APPROVE BULK_PHASE4_POLICY`
- first comment queue item: `yi`

The public profile page currently reports 192,816 downloads, which is 79 higher than the sum of per-skill detail records. Treat this as a source aggregation/cache difference unless ClawHub documents a separate metric definition.

## Known Limitation

The public ClawHub detail API and `clawhub inspect --json` expose comment counts, not comment bodies. Automated comment reply requires one of:

- a ClawHub API/CLI surface for comments
- a browser workflow with logged-in ClawHub state
- a maintainer-provided export of comment text

The dashboard still flags commented skills as the first maintenance queue so the fix/scan/publish/reply loop starts in the right place.

## Low-Signal Triage

The second-stage triage answers what to do with low and plausible-low signal skills:

- `upgrade_public`: keep public, but improve metadata, examples, tests, changelog, tags, and screenshots/docs.
- `merge_into_stronger_skill`: consolidate repeated family patterns into a stronger public hub skill.
- `move_private_or_hide`: preserve the source as a private capability unit, but remove public catalog noise.
- `monitor`: keep visible for now and re-check after the next refresh.
- `delete_candidate`: only for very low-usage, single-version, thin-metadata skills after manual source review.

Direct delete is intentionally conservative. Most low-signal skills should first be hidden, moved private, merged, or upgraded.

Rows marked `data_unavailable` are not low-signal rows. They are blocked by missing detail data and should be re-collected before any portfolio decision.

## Action Plans

After analysis, `scripts/plan_actions.py` creates dry-run maintenance plans:

- `*_hide_plan.csv`: first batch of non-utility low-signal hide candidates.
- `*_private_backlog_plan.csv`: utility-shaped skills that need manual review before hiding.
- `*_merge_plan.csv`: source-to-target merge candidates.
- `*_upgrade_plan.csv`: public skills worth improving before any removal decision.
- `*_monitor_plan.csv`: plausible skills to re-check after the next refresh.
- `*_hide_review_commands.sh` and `*_merge_review_commands.sh`: shell files with commands commented out by default.

The planner keeps public utility categories (`Developer`, `Data`, `Knowledge`, `Automation`, `Shopping`) out of the default hide command batch. Those go to private backlog review instead.

## Approval Packets

The approval layer turns analysis into small user-approval batches:

- `*_approval_board.md`: human-readable approval questions, risk, reversibility, command previews, and evidence rows.
- `*_approval_manifest.json`: machine-readable pending batches with item evidence and approval phrases.
- `*_approval_commands.sh`: commands grouped by batch and commented out by default.

Each batch has an exact approval phrase such as `APPROVE HIDE_BATCH_001`. Merge batches are marked higher risk because the CLI exposes `merge`, but no obvious `unmerge`.

## Bulk Cleanup Recommendation

Because bulk publishing was the likely account-risk trigger, `scripts/plan_bulk_cleanup.py` applies a stricter rule than product triage:

- strongest risk signal: low/plausible-low signal + single version + zero installs/stars/comments
- Phase 1: hide skills under 200 downloads with that signal
- Phase 2: spot-check then hide skills with 200-299 downloads and that signal
- Phase 3: upgrade within 7 days or hide skills with 300+ downloads and that signal

Current result: 704 skills match the strongest bulk-risk signal. Phase 1 and Phase 2 together recommend hiding 675 of them from public visibility while preserving source material locally.

Generated approval files:

- `*_bulk_approval_board.md`: user-facing approval board for bulk cleanup phases.
- `*_bulk_approval_manifest.json`: machine-readable bulk phase evidence.
- `*_phase1_hide_commands.sh` and `*_phase2_hide_commands.sh`: commented-out hide command scripts.

## Scoring Notes

The score is not a marketplace policy decision. It is a maintenance heuristic that combines:

- usage: downloads, installs, stars, comments
- maintenance: versions and recent updates
- content quality: summary length, tags, changelog, source metadata
- risk: possible duplicate families and thin metadata

Treat high-score skills as public-maintenance candidates and low-score skills as candidates for consolidation, private storage, or deletion.
