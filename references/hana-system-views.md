# SAP HANA monitoring system views

HANA exposes its own health/status as queryable SQL views under the `SYS` schema — this is what `connectors/hana_monitor.py` reads from directly. These are official, documented SAP views (see [SAP HANA SQL Reference Guide](https://help.sap.com/docs/hana-cloud-database/sap-hana-cloud-sap-hana-database-sql-reference-guide/m-service-memory-system-view)), but exact columns can shift slightly between HANA revisions — if a query in this repo errors on a missing column, run `SELECT * FROM <view> LIMIT 1` to see what your revision actually exposes.

## M_SERVICE_MEMORY

What it shows: per-service (indexserver, nameserver, etc.), per-host memory usage — used, allocated, and the configured allocation limit.

Key columns used by this repo: `HOST`, `PORT`, `SERVICE_NAME`, `TOTAL_MEMORY_USED_SIZE`, `ALLOCATION_LIMIT`.

Why it matters: HANA is an in-memory database — memory pressure is one of the most direct predictors of instability. A service approaching its allocation limit is a leading indicator, not just a lagging one.

## M_DISK_USAGE

What it shows: disk space usage broken down by usage type (data volumes, log volumes, trace, backup catalog, etc.).

Key columns used by this repo: `USAGE_TYPE`, `TOTAL_SIZE`, `USED_SIZE`.

Why it matters: HANA's log volume filling up can force the database to stop accepting transactions — this is one of the more urgent space alerts, distinct from data volume growth which is usually slower-moving.

## M_DISKS

What it shows: the physical/logical disks/volumes HANA knows about, independent of usage-type breakdown — path, size, and free space at the OS-visible level.

Why it matters: complements `M_DISK_USAGE` — useful when the question is "is the underlying filesystem itself running out of room" rather than "how is HANA's own usage split."

## M_CONNECTIONS

What it shows: currently open connections to the database, their status (e.g. `RUNNING`, `IDLE`), and which user/application they belong to.

Why it matters: a spike in connection count, or many connections stuck in a non-idle state, often points to an application not releasing connections properly rather than a HANA-side problem.

## M_BACKUP_CATALOG

What it shows: history of backup operations — type (data backup, log backup), status, and timestamps.

Why it matters: this is the authoritative source for "when did we last successfully back up," which is what `connectors/hana_monitor.py`'s `backup_last_success_hours_ago` metric is built from. A backup age alert here should always be treated as high priority — RPO risk compounds the longer it goes unaddressed.

## M_LOAD_HISTORY_SERVICE

What it shows: historical resource load (CPU, memory) per service over time, letting you look at trends rather than a single point-in-time snapshot.

Why it matters: distinguishes a genuine trend (steadily climbing memory usage over days) from normal noise (a momentary spike during a batch job) — useful for capacity planning conversations, not just incident response.

## M_EXPENSIVE_STATEMENTS

What it shows: individual SQL statements that were expensive to execute, when expensive-statement tracing is enabled (it isn't on by default on every system — check your trace configuration first).

Why it matters: when memory or CPU pressure shows up but the cause isn't obvious from the aggregate views above, this is where you go to find the specific statement responsible.

## Note on connecting

`connectors/hana_monitor.py` queries these views over a normal SQL connection via `hdbcli` — no special SDK, no special HANA edition required, works the same for on-prem HANA and S/4HANA's embedded HANA. Use a login scoped to just `MONITORING`-style read access on these views; don't use `SYSTEM` or another administrative user for a monitoring script that runs unattended.

