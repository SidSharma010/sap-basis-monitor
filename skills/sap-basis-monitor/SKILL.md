---
name: sap-basis-monitor
description: Use when the user shares SAP Basis monitoring data — pasted transaction output (SM21, ST22, SM37, SM12, SM50/SM66, DB02, ST06, RZ20, SM59, ST03N), a HANA system-view query result, an S/4HANA Fiori/OData snapshot, or JSON produced by this repo's connector scripts — and wants it triaged, explained, or turned into an incident summary. Covers classic ABAP-stack systems, SAP HANA, and S/4HANA (including Fiori-app-level monitoring).
---

# SAP Basis Monitor

Triage SAP Basis monitoring data — from classic ABAP transactions, SAP HANA, or S/4HANA — into prioritized, explained issues with root-cause guidance. Works with a live connection you've already pulled data from (via this repo's connector scripts) or with a raw paste of transaction output.

## When to use

- The user pastes output from a monitoring transaction (SM21 log lines, ST22 dump list, SM37 job list, SM12 lock list, SM50/SM66 work process overview, DB02 space report, ST06 OS metrics, RZ20 alerts, SM59 RFC test results, ST03N workload stats) and wants it read and explained.
- The user runs `connectors/hana_monitor.py` or `connectors/s4hana_odata_monitor.py` and pastes the resulting JSON, or pipes it through `lib/analyze_output.py` first and shares that output.
- The user asks "is this healthy," "what should I look at first," "what's the root cause," or wants an incident summary drafted from monitoring data.
- The user asks a general SAP Basis monitoring knowledge question (what does transaction X show, what does HANA view Y mean) without necessarily having data to triage yet.

## Not for

- Making changes to a live SAP system (killing work processes, deleting locks, restarting services) — this skill triages and recommends, it never claims to execute changes on the user's system. Recommendations are for the user (or their Basis team) to carry out themselves.
- Functional/business-process questions unrelated to Basis-level system health (that's a different domain — don't guess at MM/SD/FI configuration here).
- Claiming live, automatic access to the user's SAP system. This skill has no hidden channel into anyone's SAP landscape — see Hard rules below.

## Input

Any of:
1. Raw pasted text from a monitoring transaction (read it directly, judgment applies — this is not run through the structured `analyze_output.py` engine, which only handles structured JSON).
2. JSON matching the shape `lib/analyze_output.py` expects (see its docstring) — either produced by a connector script or built by hand from transaction data.
3. The already-computed output of `lib/analyze_output.py` itself.
4. No data at all — a general knowledge question about what a transaction/view shows or how to interpret something.

## Steps

1. **Identify the system type and data source.** Classic ABAP transaction output, HANA SQL view result, or S/4HANA Fiori/OData data? This determines which reference doc applies (`references/classic-tcodes.md`, `references/hana-system-views.md`, or `references/s4hana-fiori-apps.md`).
2. **Read the relevant reference doc(s) before interpreting the data** — don't rely on general memory alone for what a specific transaction or view means; the reference docs in this repo are the checked source for this skill.
3. **If it's structured JSON**, either run it through `lib/analyze_output.py` (`python lib/analyze_output.py snapshot.json`) or reason through it the same way that script does — check each metric against `references/severity-thresholds.md`, classify as critical/warning/fine.
4. **If it's raw pasted transaction text**, apply judgment directly: cluster similar entries (same dump type, same error message, same job name), don't just count lines. Use the "What to look for" and "Common trap" guidance in `references/classic-tcodes.md` for the relevant transaction.
5. **Prioritize.** Critical issues first (data/service availability risk — backup overdue, disk about to fill, work processes nearly exhausted), then warnings, then note anything genuinely healthy so the user knows what's fine, not just what's broken.
6. **Give root-cause guidance, not just a severity label.** Point to the specific next diagnostic step (which transaction/view to check next, what to look for there) using the recommendations already built into `lib/analyze_output.py`'s `RECOMMENDATIONS` dict and the "What to look for" sections in the reference docs.
7. **Offer an incident summary on request** — a short, factual write-up (what's affected, severity, what was checked, recommended next step) the user could paste into a ticket or hand to their team. Don't invent details not present in the data.

## Hard rules

- **Never claim or imply live, automatic access to the user's SAP system.** This skill only ever works with data the user has already pulled — either by pasting transaction output themselves, or by running one of this repo's connector scripts themselves, on their own machine, with their own credentials. There is no mechanism by which installing this repo gives Claude a live channel into anyone's SAP landscape, and this skill must never suggest otherwise.
- **Never fabricate SAP technical facts** — transaction names, view names, Fiori app IDs, OData service names, function module names. If something isn't covered in this repo's reference docs and isn't something you're confident of from verified general knowledge, say so explicitly and point the user to official SAP documentation (help.sap.com, the SAP Fiori Apps Reference Library) rather than guessing.
- **Never recommend a destructive action casually** (killing a work process, deleting a lock, cancelling a job) without the caveat already built into the relevant reference doc — e.g. identify the lock holder's actual session before deleting a lock entry.
- **Thresholds are a starting point, not gospel** — when giving a severity verdict from `analyze_output.py`'s defaults, it's fine to note the thresholds are tunable (see `references/severity-thresholds.md`) if the user seems to be operating a system where the defaults clearly don't fit (e.g. a dev/sandbox system where dump counts are naturally noisier).
- **Cross-check against current SAP documentation for anything version- or release-specific.** SAP's technical landscape (especially Fiori app catalogs and OData service names) changes across releases — this repo's reference docs say so explicitly and link to the authoritative current sources.

## Output shape

For a triage request: a prioritized list (critical → warning → healthy-and-fine), each item with what it is, why it matters, and the concrete next diagnostic step. For a knowledge question: a direct answer grounded in the reference docs, citing which doc/transaction/view it came from. For an incident summary: a short factual write-up suitable for pasting into a ticketing system.

## Resources

- `references/classic-tcodes.md` — SM21, ST22, SM37, SM12, SM50/SM66, DB02/DB02OLD, ST06, RZ20, SM59, ST03N
- `references/hana-system-views.md` — M_SERVICE_MEMORY, M_DISK_USAGE, M_DISKS, M_CONNECTIONS, M_BACKUP_CATALOG, M_LOAD_HISTORY_SERVICE, M_EXPENSIVE_STATEMENTS
- `references/s4hana-fiori-apps.md` — Fiori-app-level monitoring (Monitor Systems, Application Jobs) and how it relates to the classic transactions and OData layer
- `references/severity-thresholds.md` — the reasoning behind every threshold in `lib/analyze_output.py`
- `lib/analyze_output.py` — the structured-JSON triage engine
- `connectors/hana_monitor.py`, `connectors/s4hana_odata_monitor.py`, `connectors/rfc-connector-notes.md` — scripts the user runs themselves to pull live data into the JSON shape this skill and `analyze_output.py` expect

