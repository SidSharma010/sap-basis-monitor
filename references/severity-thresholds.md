# Severity thresholds — what's hardcoded and why

`lib/analyze_output.py` classifies every metric as **critical**, **warning**, or fine, using the `THRESHOLDS` dict at the top of that file. This doc explains the reasoning behind each number.

**Honest framing up front:** these are not a verified industry SLA standard, not sourced from an SAP OSS note, and not benchmarked against any real production system (this repo has no live SAP system to test against). They're a reasonable, defensible starting point based on general Basis operating experience — a baseline to tune, not a number to trust blindly. Every SAP landscape has different sizing, different criticality, and different SLAs with the business. **Change these for your own system** — the thresholds live in one dict specifically so that's easy.

## disk_usage_pct — warning 80, critical 90

Disk fills up faster than most other resources recover, and running out of disk (especially HANA log volume) can stop the database from accepting transactions entirely. 80% is early enough to plan a resize or cleanup calmly; 90% is late enough that it should already be someone's immediate priority.

## used_memory_pct — warning 85, critical 95

HANA is in-memory — this is closer to "how close to the edge is the database" than a normal server's memory metric. The gap between warning and critical is intentionally narrow (85→95) because memory pressure on HANA can escalate faster than disk pressure does.

## dumps_last_24h — warning 5, critical 20

A handful of dumps in a day can be normal background noise (a user fat-fingering input, one flaky interface call). Five is "worth a look." Twenty in 24 hours usually means something systemic is actively broken, not isolated user error — check `references/classic-tcodes.md` (ST22) and cluster by dump type before assuming volume alone tells the story.

## lock_wait_max_seconds — warning 60, critical 300

A lock held for under a minute is often just normal transaction overlap. A lock held for 5 minutes (300s) is very likely a stuck session, not a slow-but-legitimate one — but always check who's holding it (SM12) before clearing anything; a wrong guess here can cause data inconsistency.

## backup_last_success_hours_ago — warning 24, critical 48

Most SAP shops run at least a daily backup cadence, so 24 hours since the last success lines up with "the normal daily backup didn't run or didn't succeed." 48 hours means two cycles have been missed — treat this as high priority regardless of what else is going on, since backup age is a direct RPO (recovery point objective) risk that compounds the longer it's ignored.

## free_dialog_work_process_pct — warning 20, critical 10 (inverted)

This is the one inverted-direction metric — low is bad, not high. If free dialog work processes drop too low, new users can't log on to the system at all, which is about as user-visible an outage as Basis monitoring catches. 20% free is "keep an eye on it," 10% free is "this is close to locking users out."

## Tuning these for your system

Edit the `THRESHOLDS` dict in `lib/analyze_output.py` directly — each entry is `{"warning": X, "critical": Y, "direction": "above"|"below"}`. A few starting questions to guide your own numbers:

- What's your actual SLA with the business for "system unavailable"? Work backward from that.
- How fast does your system's disk/memory typically grow? A system that fills disk slowly can tolerate a higher warning threshold than one that fills fast.
- What's your real backup cadence — daily, twice-daily, continuous log backup with periodic full? Adjust `backup_last_success_hours_ago` to match, not the default assumption of daily.

If you tune these based on real incident history at your organization, they'll be more accurate than anything a generic public repo can hardcode.

