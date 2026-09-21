# Classic ABAP-stack monitoring transactions

The core set of transaction codes a Basis admin actually lives in day to day, on any ABAP-stack system (ECC or S/4HANA — the ABAP stack still runs these the same way even where SAP is pushing Fiori apps as the newer front end; see `s4hana-fiori-apps.md` for the modern equivalents). This doc is what the skill and `lib/analyze_output.py`'s recommendations point back to.

## SM21 — System Log

What it shows: a chronological log of system-level events and errors across all application servers in the instance — failed logons, RFC errors, dumps, database errors, authorization failures, and more.

What to look for: repeated entries of the same message ID (a pattern, not a one-off), anything with a red/error severity marker, and the time window right before a reported user issue.

Common trap: SM21 is noisy by default. Filter by severity and time window first, or you'll drown in informational noise.

## ST22 — ABAP Dump Analysis (ABAP Runtime Errors)

What it shows: short dumps — unhandled exceptions in ABAP code (e.g. `TIME_OUT`, `DBIF_RSQL_SQL_ERROR`, `MESSAGE_TYPE_X`, `CONVT_NO_NUMBER`).

What to look for: cluster the dumps by **type**, not just count. Ten different dump types are ten different problems; ten of the exact same dump type is one root cause hitting repeatedly — usually the higher-priority fix.

Common trap: treating dump *count* alone as the severity signal. A single `DBIF_RSQL_SQL_ERROR` during a DB outage matters more than fifty `TIME_OUT` dumps from users leaving sessions idle.

## SM37 — Background Job Monitoring

What it shows: scheduled/background job status — scheduled, released, active, finished, cancelled.

What to look for: **cancelled** jobs (something actively went wrong) vs. jobs still showing **scheduled** long past their start time (a scheduling/resource problem, not a code problem). Always open the job log for a cancelled job — "cancelled" alone tells you nothing about why.

Common trap: rescheduling a failed job without reading its log first. The same failure will usually just repeat.

## SM12 — Lock Entries

What it shows: currently held database locks (enqueue), which user/session holds each, and how long.

What to look for: locks held far longer than the transaction they belong to should reasonably take — that's usually a stuck session, not a normal in-progress update. Identify the **lock holder's session** before deleting anything; deleting a lock out from under a transaction that's still legitimately running can cause data inconsistency.

Common trap: deleting locks reflexively when a user complains "I'm stuck." Check what the lock-holding session is actually doing first.

## SM50 / SM66 — Work Process Overview

What it shows: SM50 = work processes on the current instance; SM66 = across all instances. Shows what each dialog/background/update work process is currently running, and for how long.

What to look for: work processes stuck in the same status for an unusually long time (a long-running statement, a deadlock, or a runaway report), and how many are free vs. occupied — if free dialog work processes drop very low, new users can't log on at all.

Common trap: killing a long-running process without checking what it's doing — it might be a legitimate long batch job, not a hang.

## DB02 / DB02OLD — Database and Tablespace/Space Monitoring

What it shows: database size, growth, tablespace/schema space usage (naming and exact screens differ HANA vs. classic DB, but the job is the same: is there enough room to keep growing).

What to look for: space usage trending toward 100% on any critical tablespace/schema, and unusually fast unexpected growth (which often points to a runaway table, not just organic growth).

## ST06 — Operating System Monitor

What it shows: OS-level CPU, memory, disk, and network stats for the application server host.

What to look for: sustained high CPU/memory (not a momentary spike), swap usage climbing (a sign of real memory pressure), and disk I/O wait — often the real cause behind "the system feels slow" complaints that don't show up as an obvious ABAP-level problem.

## RZ20 — CCMS Alert Monitor

What it shows: SAP's built-in alert/monitoring tree across system, database, and application areas, with configurable thresholds.

What to look for: RZ20 is where you'd configure the kind of thresholds this repo's `analyze_output.py` hardcodes for its own JSON-based flow — if RZ20 is already properly configured on a system, it's often the better native source of truth; this repo's connectors are for when you want that data pulled out programmatically (scripted, scheduled, or handed to Claude) rather than viewed only inside SAP GUI.

## SM59 — RFC Destinations

What it shows: configured RFC connections to other systems (interfaces, connected systems).

What to look for: connection test failures, which point to network, authentication, or the target system being down — often the actual root cause behind "interface X isn't working" tickets that get reported as an application problem.

## ST03N — Workload Monitor

What it shows: response time statistics broken down by transaction, user, and time period.

What to look for: transactions with response times that have degraded over time (a trend, not a single bad measurement), and which transaction/report is consuming disproportionate system resources.

