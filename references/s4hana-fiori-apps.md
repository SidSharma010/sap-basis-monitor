# S/4HANA Fiori-app-level monitoring

SAP has been steadily pushing monitoring workflows out of classic SAP GUI transactions and into web-based Fiori apps, especially for S/4HANA. This doc covers that layer — where it overlaps with the classic T-codes in `classic-tcodes.md`, and where it's genuinely different.

**Honest scope note:** SAP's Fiori app catalog changes across releases (app IDs, availability, and naming aren't static across S/4HANA versions), and a hardcoded list here would go stale. The two apps below are verified against the [SAP Fiori Apps Reference Library](https://fioriappslibrary.hana.ondemand.com/) as of this writing; for anything beyond these two, the reference library itself is the authoritative, always-current source — search it for your specific S/4HANA release rather than trusting a static list anyone (including this repo) publishes.

## Monitor Systems (App ID: F1565)

What it shows: technical system and component health across the landscape — a Fiori-native successor to parts of what RZ20/CCMS covered, aimed at a cross-system view rather than one instance at a time.

Where it fits: this is closer to a "look here first for the big picture" app than a deep-dive tool — use it to spot which system/component needs attention, then drop into the relevant classic transaction or a more specific Fiori app for the detail.

## Application Jobs (App ID: F1240)

What it shows: the Fiori-native view of background job scheduling and monitoring — functionally the modern counterpart to SM37, built for S/4HANA's job framework.

Where it fits: if your organization has moved job scheduling/monitoring workflows to Fiori, this is the app your functional/business users are more likely to actually use day to day, even if you as Basis still go to SM37 for the deeper technical job log detail.

## Why this repo's connectors don't call Fiori apps directly

Fiori apps are a UI layer on top of the same OData services `connectors/s4hana_odata_monitor.py` talks to directly — there's no separate "Fiori API." So instead of trying to reverse-engineer what a specific Fiori app's frontend calls (which is fragile and changes with UI updates), the connector in this repo talks to the underlying OData service directly, which is the stable, documented integration point. The Fiori apps in this doc are the human-facing entry points for the same underlying data.

## Where to look up more

- [SAP Fiori Apps Reference Library](https://fioriappslibrary.hana.ondemand.com/) — searchable, filterable by S/4HANA release, the authoritative source for the full current app catalog.
- [SAP Fiori Apps for Technical Monitoring — SAP Help Portal](https://help.sap.com/docs/ABAP_PLATFORM_NEW/6d9d967c861d4f78b5b90a4fe9b7d2e7/169e994ee53e4989a85c3909c6ca0a22.html) — context and use cases for the technical monitoring app category specifically.
- For deeper/cross-system monitoring at scale, SAP's current direction is **SAP Cloud ALM** and **Focused Run** rather than expanding CCMS/RZ20 — worth knowing the names exist even though this repo doesn't integrate with them (they're licensed products with their own APIs, out of scope for a repo meant to work for "anyone" with just a base system).

