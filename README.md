# sap-basis-monitor

A Claude skill + connector scripts for SAP Basis monitoring — classic ABAP-stack systems, SAP HANA, and S/4HANA (including Fiori-app-level monitoring), triaged with severity thresholds and root-cause guidance.

## How this actually works (read this first)

Claude cannot reach into your live SAP system on its own just because you installed this repo — there's no hidden channel, and any tool that claims otherwise isn't being honest with you. This repo is built as two honest layers instead:

1. **Connector scripts you run yourself**, on your own machine, with your own credentials, against your own system. This is the only part that actually talks to SAP — `connectors/hana_monitor.py` (SAP HANA, via `hdbcli`) and `connectors/s4hana_odata_monitor.py` (S/4HANA/NetWeaver, via its OData/Gateway interface). They print a structured JSON snapshot to stdout. Nothing about running them sends anything to Claude or to Anthropic — they're plain Python scripts that talk directly to your SAP system.
2. **The Claude skill** (`skills/sap-basis-monitor/`), which reads whatever you paste or pipe in — raw transaction output, or the JSON a connector produced — and triages it: severity, prioritization, root-cause guidance, and an optional incident summary.

You stay in control of every connection. Claude only ever sees what you choose to paste or share, exactly like every other Claude conversation.

## What it covers

- **Classic ABAP-stack transactions**: SM21 (system log), ST22 (dumps), SM37 (background jobs), SM12 (locks), SM50/SM66 (work processes), DB02/DB02OLD (database/tablespace space), ST06 (OS monitor), RZ20 (CCMS alerts), SM59 (RFC destinations), ST03N (workload monitor) — works the same whether you're on ECC or S/4HANA, since the ABAP stack still runs these.
- **SAP HANA**: direct SQL queries against HANA's own `SYS`-schema monitoring views (memory, disk, connections, backup history, load history, expensive statements) via the official `hdbcli` client — no proprietary SDK required.
- **S/4HANA Fiori-app-level monitoring**: the newer web-UI monitoring apps (Monitor Systems, Application Jobs) and how they relate to the classic transactions and the underlying OData/Gateway layer.
- **RFC connectivity**: documented as an option for organizations that already have SAP's NetWeaver RFC SDK set up (real licensing/setup friction involved — see `connectors/rfc-connector-notes.md`), not shipped as a plug-and-play script.

## Quick start

**Just want triage from data you already have (paste from SAP GUI)?** No install needed — open a Claude conversation with this skill available, paste your SM21/ST22/SM37/etc. output or your HANA/S4H JSON, and ask.

**Want to pull live data with the connector scripts?**

```bash
# SAP HANA
pip install hdbcli
python connectors/hana_monitor.py --host myhanahost --port 30015 --user MONITOR_USER --password '***' > snapshot.json

# S/4HANA / NetWeaver (via OData/Gateway)
pip install requests
python connectors/s4hana_odata_monitor.py \
    --service-url "https://myhost:port/sap/opu/odata/sap/YOUR_SERVICE_SRV" \
    --entity-set "YourEntitySet" \
    --user MONITOR_USER --password '***' > snapshot.json
```

Then either run it through the local triage engine directly:

```bash
python lib/analyze_output.py snapshot.json
```

or paste `snapshot.json` into a Claude conversation with the `sap-basis-monitor` skill and ask for a full triage with root-cause guidance.

**Use a dedicated read-only monitoring user**, not `SYSTEM` or an administrative account, for anything you run unattended.

## Repo structure

```
sap-basis-monitor/
├── skills/
│   └── sap-basis-monitor/
│       └── SKILL.md              # the Claude skill definition
├── connectors/
│   ├── hana_monitor.py           # pulls a JSON snapshot from SAP HANA
│   ├── s4hana_odata_monitor.py   # pulls a JSON snapshot via S/4HANA OData
│   └── rfc-connector-notes.md    # RFC/pyrfc option — notes, not a plug-and-play script
├── lib/
│   └── analyze_output.py         # dependency-free severity/triage engine
├── references/
│   ├── classic-tcodes.md         # SM21, ST22, SM37, SM12, SM50/SM66, DB02, ST06, RZ20, SM59, ST03N
│   ├── hana-system-views.md      # HANA SYS-schema monitoring views
│   ├── s4hana-fiori-apps.md      # Fiori-app-level monitoring
│   └── severity-thresholds.md    # the reasoning behind every threshold
└── examples/
    ├── sample-healthy-snapshot.json
    └── sample-alert-snapshot.json
```

## What "thresholds" means here

`lib/analyze_output.py` classifies metrics (disk usage, memory usage, dump count, lock wait time, backup age, free work processes) against a set of hardcoded warning/critical thresholds. **These are a reasonable starting point, not a verified industry SLA standard** — see `references/severity-thresholds.md` for the reasoning behind each one, and tune the `THRESHOLDS` dict in `analyze_output.py` for your own system's actual SLA and sizing.

## Honesty notes / status

- This repo's SAP technical content (transaction behavior, HANA view names, Fiori app IDs) was written from verified general SAP Basis knowledge, with the highest-risk specifics (Fiori app IDs, HANA view names) checked against current SAP documentation. SAP's technical landscape changes across releases — always cross-check anything version-specific against your own system's actual documentation before relying on it.
- The connector scripts have been tested for correct syntax and structure (`python -m py_compile`), and `lib/analyze_output.py` has been tested against the example JSON snapshots in `examples/`. **Neither connector script has been tested against a live SAP or HANA system** — none was available to build this repo against. If you hit an issue running them against your real system (a missing column, a different service name, an auth quirk), that's expected friction to work through, not a sign the approach is wrong; the code is straightforward enough to adjust for your environment.
- `s4hana_odata_monitor.py` deliberately does not hardcode an OData service name — SAP Gateway service names differ by release and what your Basis team has activated. You point it at your own system's real service (discoverable via transaction `/IWFND/MAINT_SERVICE` or the SAP API Business Hub).

## License

MIT — use it, fork it, adapt it for your own SAP landscape.

