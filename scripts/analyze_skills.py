#!/usr/bin/env python3
"""Score and prioritize a ClawHub skill portfolio."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Content", ("content", "writer", "writing", "generator", "copy", "blog", "article", "social", "script")),
    ("Shopping", ("shopping", "jd", "taobao", "pdd", "alibaba", "meituan", "amazon", "ecommerce", "commerce", "price", "coupon", "cart", "listing")),
    ("Culture", ("i ching", "zhouyi", "hexagram", "divination", "philosophy", "yarrow", "bagua")),
    ("Productivity", ("productivity", "time-tracking", "daily-log", "calendar", "focus", "planner")),
    ("Data", ("data", "analysis", "analytics", "spreadsheet", "csv", "report", "dashboard")),
    ("Knowledge", ("knowledge", "research", "connector", "search", "rag", "memory", "note", "graph")),
    ("Automation", ("automation", "workflow", "agent", "task", "ops", "scheduler", "orchestrator")),
    ("Developer", ("code", "developer", "github", "git", "api", "debug", "test", "deploy", "cli")),
    ("Education", ("learn", "learning", "study", "course", "tutor", "education", "exam")),
    ("Business", ("business", "marketing", "sales", "crm", "finance", "startup", "strategy")),
    ("Design", ("design", "image", "visual", "brand", "ui", "ux", "creative")),
    ("Personal", ("health", "fitness", "travel", "life", "habit", "personal", "journal")),
]


DECISION_RANKS = {
    "fix_and_reply": 10,
    "upgrade_public": 20,
    "merge_into_stronger_skill": 30,
    "move_private_or_hide": 40,
    "delete_candidate": 50,
    "monitor": 60,
    "keep_public": 70,
}


LOW_SIGNAL_VERDICTS = {"low_signal", "plausible_but_low_signal"}


def to_int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except Exception:
        return 0


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(*parts: str) -> str:
    return " ".join(part for part in parts if part).lower()


def category_for(row: dict[str, str]) -> str:
    name_text = normalize_text(row.get("slug", ""), row.get("display_name", ""))
    name_tokens = set(re.findall(r"[a-z0-9]+", name_text))
    for category, keywords in CATEGORY_RULES:
        if any(keyword_matches(keyword, name_text, name_tokens) for keyword in keywords):
            return category

    text = normalize_text(row.get("slug", ""), row.get("display_name", ""), row.get("summary", ""), row.get("tags", ""))
    tokens = set(re.findall(r"[a-z0-9]+", text))
    for category, keywords in CATEGORY_RULES:
        if any(keyword_matches(keyword, text, tokens) for keyword in keywords):
            return category
    return "Other"


def keyword_matches(keyword: str, text: str, tokens: set[str]) -> bool:
    if "-" in keyword or " " in keyword:
        return keyword in text
    if len(keyword) <= 3:
        return keyword in tokens
    return keyword in text


def duplicate_key(slug: str) -> str:
    key = slug.lower()
    key = re.sub(r"[^a-z0-9]+", "-", key)
    key = re.sub(r"-(agent|skill|assistant|tool|workflow|generator|analyzer|helper)$", "", key)
    key = re.sub(r"-v?\d+$", "", key)
    key = re.sub(r"\d+", "#", key)
    return key.strip("-")


def family_candidates(slug: str) -> list[tuple[str, str]]:
    parts = [part for part in re.split(r"[^a-z0-9]+", slug.lower()) if part]
    candidates: list[tuple[str, str]] = []
    if len(parts) >= 2:
        candidates.append(("prefix2", "-".join(parts[:2])))
        candidates.append(("suffix2", "-".join(parts[-2:])))
    if len(parts) >= 3:
        candidates.append(("prefix3", "-".join(parts[:3])))
    return candidates


def choose_family_key(slug: str, family_counts: Counter[str]) -> str:
    scored: list[tuple[int, int, str]] = []
    priorities = {"suffix2": 3, "prefix3": 2, "prefix2": 1}
    for kind, key in family_candidates(slug):
        count = family_counts.get(f"{kind}:{key}", 0)
        if count >= 3:
            scored.append((count, priorities.get(kind, 0), f"{kind}:{key}"))
    if not scored:
        return ""
    scored.sort(reverse=True)
    return scored[0][2]


def recent_component(updated_at: datetime | None, now: datetime) -> tuple[float, int]:
    if updated_at is None:
        return 0.0, 9999
    days = max(0, (now - updated_at).days)
    if days <= 30:
        return 8.0, days
    if days <= 90:
        return 5.0, days
    if days <= 180:
        return 3.0, days
    return 1.0, days


def safe_log_score(value: int, max_value: int, points: float) -> float:
    if value <= 0 or max_value <= 0:
        return 0.0
    return min(points, math.log1p(value) / math.log1p(max_value) * points)


def score_row(row: dict[str, str], maxima: dict[str, int], duplicate_sizes: dict[str, int], now: datetime) -> dict[str, Any]:
    downloads = to_int(row.get("downloads"))
    installs = to_int(row.get("installs_all_time"))
    stars = to_int(row.get("stars"))
    comments = to_int(row.get("comments"))
    versions = to_int(row.get("versions"))
    tag_count = to_int(row.get("tag_count"))
    summary = row.get("summary", "").strip()
    changelog = row.get("latest_changelog", "").strip()
    updated_at = parse_iso(row.get("updated_at_utc", ""))
    category = category_for(row)
    dup_key = duplicate_key(row.get("slug", ""))
    duplicate_size = duplicate_sizes.get(dup_key, 1)

    usage_score = (
        safe_log_score(downloads, maxima["downloads"], 28)
        + safe_log_score(installs, max(1, maxima["installs_all_time"]), 18)
        + safe_log_score(stars, max(1, maxima["stars"]), 12)
        + safe_log_score(comments, max(1, maxima["comments"]), 8)
    )

    if versions >= 8:
        version_score = 10.0
    elif versions >= 4:
        version_score = 7.0
    elif versions >= 2:
        version_score = 4.0
    elif versions == 1:
        version_score = 2.0
    else:
        version_score = 0.0
    recency_score, days_since_update = recent_component(updated_at, now)
    maintenance_score = version_score + recency_score

    if len(summary) >= 120:
        summary_score = 8.0
    elif len(summary) >= 60:
        summary_score = 6.0
    elif len(summary) >= 20:
        summary_score = 3.0
    else:
        summary_score = 0.0
    tag_score = min(5.0, tag_count * 1.25)
    changelog_score = 3.0 if len(changelog) >= 40 else 1.0 if changelog else 0.0
    source_score = 4.0 if row.get("source_repo") or row.get("source_path") else 0.0
    content_score = summary_score + tag_score + changelog_score + source_score

    duplicate_penalty = 0.0
    if duplicate_size >= 8:
        duplicate_penalty = 8.0
    elif duplicate_size >= 4:
        duplicate_penalty = 4.0

    raw_score = usage_score + maintenance_score + content_score - duplicate_penalty
    score = max(0, min(100, round(raw_score, 1)))

    flags: list[str] = []
    if comments > 0:
        flags.append("has_user_comments")
    if installs > 0:
        flags.append("has_installs")
    if stars > 0:
        flags.append("has_stars")
    if downloads >= 1000:
        flags.append("high_downloads")
    elif downloads < 50:
        flags.append("low_downloads")
    if tag_count == 0:
        flags.append("missing_tags")
    if len(summary) < 40:
        flags.append("thin_summary")
    if versions <= 1:
        flags.append("single_version")
    if duplicate_size >= 4:
        flags.append("possible_duplicate_family")
    if days_since_update > 180:
        flags.append("stale")

    engagement = installs + stars + comments
    if comments > 0:
        action = "respond_fix_upload"
    elif score >= 65 or downloads >= 1000 or engagement >= 2:
        action = "keep_public"
    elif score >= 45 or downloads >= 200 or engagement == 1:
        action = "curate_or_improve"
    elif score < 40 and downloads < 80 and engagement == 0:
        action = "consider_private_or_delete"
    elif score >= 30 or duplicate_size >= 4:
        action = "review_for_merge_or_private"
    else:
        action = "consider_private_or_delete"

    if comments > 0 or installs >= 5 or stars > 0 or downloads >= 1000:
        verdict = "meaningful"
    elif score >= 50 and downloads >= 100:
        verdict = "needs_evidence"
    elif score >= 40:
        verdict = "plausible_but_low_signal"
    else:
        verdict = "low_signal"

    return {
        **row,
        "category": category,
        "duplicate_key": dup_key,
        "duplicate_family_size": duplicate_size,
        "usage_score": round(usage_score, 1),
        "maintenance_score": round(maintenance_score, 1),
        "content_score": round(content_score, 1),
        "duplicate_penalty": round(duplicate_penalty, 1),
        "meaning_score": score,
        "meaningfulness": verdict,
        "recommended_action": action,
        "days_since_update": days_since_update,
        "flags": "|".join(flags),
    }


def summarize(rows: list[dict[str, Any]], handle: str) -> dict[str, Any]:
    action_counts = Counter(row["recommended_action"] for row in rows)
    verdict_counts = Counter(row["meaningfulness"] for row in rows)
    category_counts = Counter(row["category"] for row in rows)
    decision_counts = Counter(row["portfolio_decision"] for row in rows)
    low_signal_rows = [row for row in rows if row["meaningfulness"] in LOW_SIGNAL_VERDICTS]
    low_signal_decision_counts = Counter(row["portfolio_decision"] for row in low_signal_rows)
    total_downloads = sum(to_int(row.get("downloads")) for row in rows)
    total_installs = sum(to_int(row.get("installs_all_time")) for row in rows)
    total_stars = sum(to_int(row.get("stars")) for row in rows)
    total_comments = sum(to_int(row.get("comments")) for row in rows)
    scored = sorted(rows, key=lambda row: float(row["meaning_score"]), reverse=True)
    downloaded = sorted(rows, key=lambda row: to_int(row.get("downloads")), reverse=True)
    action_queue = [
        row
        for row in sorted(
            rows,
            key=lambda row: (
                row["recommended_action"] != "respond_fix_upload",
                -to_int(row.get("comments")),
                -float(row["meaning_score"]),
                -to_int(row.get("downloads")),
            ),
        )
        if row["recommended_action"] == "respond_fix_upload"
    ]

    return {
        "handle": handle,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "skill_count": len(rows),
        "totals": {
            "downloads": total_downloads,
            "installs_all_time": total_installs,
            "stars": total_stars,
            "comments": total_comments,
        },
        "counts": {
            "recommended_action": dict(action_counts),
            "meaningfulness": dict(verdict_counts),
            "category": dict(category_counts),
            "portfolio_decision": dict(decision_counts),
            "low_signal_portfolio_decision": dict(low_signal_decision_counts),
        },
        "top_by_score": slim_rows(scored[:25]),
        "top_by_downloads": slim_rows(downloaded[:25]),
        "action_queue": slim_rows(action_queue[:50]),
        "risk_queue": slim_rows(
            [
                row
                for row in sorted(rows, key=lambda row: (float(row["meaning_score"]), to_int(row.get("downloads"))))
                if row["recommended_action"] in {"review_for_merge_or_private", "consider_private_or_delete"}
            ][:50]
        ),
        "upgrade_queue": slim_rows(queue_for_decision(rows, "upgrade_public")[:50]),
        "merge_queue": slim_rows(queue_for_decision(rows, "merge_into_stronger_skill")[:50]),
        "hide_queue": slim_rows(queue_for_decision(rows, "move_private_or_hide")[:50]),
        "delete_queue": slim_rows(queue_for_decision(rows, "delete_candidate")[:50]),
        "monitor_queue": slim_rows(queue_for_decision(rows, "monitor")[:50]),
    }


def queue_for_decision(rows: list[dict[str, Any]], decision: str) -> list[dict[str, Any]]:
    return [
        row
        for row in sorted(
            rows,
            key=lambda row: (
                row["meaningfulness"] not in LOW_SIGNAL_VERDICTS,
                -to_int(row.get("downloads")),
                -float(row.get("meaning_score", 0)),
                row.get("slug", ""),
            ),
        )
        if row.get("portfolio_decision") == decision
    ]


def slim_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "slug",
        "display_name",
        "downloads",
        "installs_all_time",
        "stars",
        "comments",
        "versions",
        "meaning_score",
        "meaningfulness",
        "recommended_action",
        "portfolio_decision",
        "portfolio_reason",
        "merge_family_key",
        "merge_family_size",
        "merge_target_slug",
        "category",
        "flags",
    ]
    return [{key: row.get(key, "") for key in keys} for row in rows]


def apply_portfolio_triage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_counts: Counter[str] = Counter()
    for row in rows:
        for kind, key in family_candidates(row.get("slug", "")):
            family_counts[f"{kind}:{key}"] += 1

    family_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        family_key = choose_family_key(row.get("slug", ""), family_counts)
        row["merge_family_key"] = family_key
        row["merge_family_size"] = family_counts.get(family_key, 1) if family_key else 1
        if family_key:
            family_members[family_key].append(row)

    family_targets: dict[str, list[dict[str, Any]]] = {}
    for family_key, members in family_members.items():
        family_targets[family_key] = sorted(
            members,
            key=lambda row: (
                to_int(row.get("installs_all_time")) + to_int(row.get("stars")) + to_int(row.get("comments")),
                float(row.get("meaning_score", 0)),
                to_int(row.get("downloads")),
                to_int(row.get("versions")),
            ),
            reverse=True,
        )

    for row in rows:
        family_key = row.get("merge_family_key", "")
        target_slug = ""
        if family_key:
            for member in family_targets.get(family_key, []):
                if member.get("slug") != row.get("slug"):
                    target_slug = member.get("slug", "")
                    break
        row["merge_target_slug"] = target_slug
        decision, reason = portfolio_decision_for(row)
        row["portfolio_decision"] = decision
        row["portfolio_reason"] = reason
        row["portfolio_rank"] = DECISION_RANKS.get(decision, 999)
    return rows


def portfolio_decision_for(row: dict[str, Any]) -> tuple[str, str]:
    downloads = to_int(row.get("downloads"))
    installs = to_int(row.get("installs_all_time"))
    stars = to_int(row.get("stars"))
    comments = to_int(row.get("comments"))
    versions = to_int(row.get("versions"))
    tag_count = to_int(row.get("tag_count"))
    score = float(row.get("meaning_score", 0))
    family_size = to_int(row.get("merge_family_size"))
    engagement = installs + stars + comments
    verdict = row.get("meaningfulness", "")
    category = row.get("category", "")
    summary_len = len(str(row.get("summary", "")).strip())
    flags = set(str(row.get("flags", "")).split("|")) if row.get("flags") else set()

    if comments > 0:
        return "fix_and_reply", "User comment exists; inspect feedback, fix, publish a new version, then reply."
    if verdict == "meaningful":
        return "keep_public", "Meaningful usage signal already exists; keep public and maintain normally."
    if verdict == "needs_evidence":
        if engagement > 0 or downloads >= 300:
            return "upgrade_public", "Moderate demand signal; improve metadata, examples, tests, and publish a stronger version."
        return "monitor", "Some evidence exists, but public demand is not yet strong; monitor before consolidation."

    if verdict not in LOW_SIGNAL_VERDICTS:
        return "monitor", "No special low-signal action required."

    if engagement > 0:
        return "upgrade_public", "Low score but has install/star/comment signal; upgrade before considering removal."
    if downloads >= 300 or (downloads >= 220 and versions >= 2):
        return "upgrade_public", "High relative downloads for a low-signal skill; upgrade public packaging and examples."
    if family_size >= 3 and downloads < 300:
        return "merge_into_stronger_skill", "Part of a repeated skill family with weak standalone signal; merge into a stronger public hub skill."
    public_utility_category = category in {"Developer", "Data", "Shopping", "Automation", "Knowledge"}
    if score < 40 and downloads < 60 and versions <= 1 and tag_count <= 1 and not public_utility_category and summary_len < 140:
        return "delete_candidate", "Very low usage, single version, minimal metadata; delete only after manual source review."
    if score < 40 and downloads < 80 and public_utility_category and summary_len >= 80:
        return "move_private_or_hide", "Useful public-utility shape but weak evidence; keep source, improve later, or move private."
    if score < 40 and downloads < 100 and versions <= 1:
        return "move_private_or_hide", "Weak public signal; keep as private capability or hide from public catalog."
    if "single_version" in flags and downloads < 180:
        return "move_private_or_hide", "Single-version skill with limited usage; move private unless it is part of a curated theme."
    if family_size >= 2:
        return "merge_into_stronger_skill", "Related skill family exists; consolidate to reduce public catalog noise."
    return "monitor", "Plausible but no strong engagement yet; leave visible briefly and re-evaluate after the next refresh."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", default="harrylabsj")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    input_path = data_dir / "processed" / f"{args.handle}_skills.csv"
    rows = read_csv(input_path)
    if not rows:
        raise RuntimeError(f"No rows found in {input_path}")

    maxima = {
        "downloads": max(to_int(row.get("downloads")) for row in rows),
        "installs_all_time": max(to_int(row.get("installs_all_time")) for row in rows),
        "stars": max(to_int(row.get("stars")) for row in rows),
        "comments": max(to_int(row.get("comments")) for row in rows),
    }
    duplicate_counts = Counter(duplicate_key(row.get("slug", "")) for row in rows)
    now = datetime.now(timezone.utc)
    analyzed = [score_row(row, maxima, duplicate_counts, now) for row in rows]
    analyzed = apply_portfolio_triage(analyzed)
    analyzed.sort(
        key=lambda row: (
            to_int(row.get("portfolio_rank")),
            row["recommended_action"],
            -float(row["meaning_score"]),
            -to_int(row.get("downloads")),
        )
    )
    summary = summarize(analyzed, args.handle)
    low_signal_triage = [row for row in analyzed if row["meaningfulness"] in LOW_SIGNAL_VERDICTS]

    write_csv(data_dir / "processed" / f"{args.handle}_skill_analysis.csv", analyzed)
    write_csv(data_dir / "processed" / f"{args.handle}_low_signal_triage.csv", low_signal_triage)
    write_json(data_dir / "processed" / f"{args.handle}_summary.json", summary)
    print(json.dumps(summary["totals"], indent=2))
    print(json.dumps(summary["counts"]["recommended_action"], indent=2))
    print(json.dumps(summary["counts"]["low_signal_portfolio_decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
