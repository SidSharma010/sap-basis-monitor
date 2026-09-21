# RFC-based connectivity — notes, not a ready script

The two connectors in this folder (`hana_monitor.py`, `s4hana_odata_monitor.py`) were deliberately chosen because they need nothing beyond a pip-installable, freely redistributable Python package. Classic RFC connectivity (`pyrfc`) is a third real option, but it has friction the other two don't, so it's documented here rather than shipped as a plug-and-play script.

## Why this one is different

`pyrfc` is a Python wrapper around SAP's **NetWeaver RFC SDK** — a C library that SAP licenses and distributes separately, outside of pip/PyPI, gated behind an SAP account (S-user) with the right authorization. You cannot `pip install` your way to a working RFC connection; you first have to:

1. Download the NW RFC SDK from SAP's support portal (requires an S-user with download authorization for that software component).
2. Install it on the machine that will run the script, matching your OS/architecture.
3. Set the SDK path so `pyrfc` can find it (`SAPNWRFC_HOME` or equivalent, per `pyrfc`'s own install docs).
4. Only then does `pip install pyrfc` actually build/work.

That's a real barrier for "anyone" trying to use this repo — which is why the two connectors above are the primary path, and this one is the documented fallback for people who already have SDK access (which is common inside companies with an existing SAP landscape, less common for an individual hobbyist).

## What an RFC connector would look like, in outline

If you do have the SDK set up, the shape is the same pattern as the other two connectors — call a function module, shape the result into the JSON keys `analyze_output.py` expects:

```python
from pyrfc import Connection

conn = Connection(ashost="myhost", sysnr="00", client="100", user="MONITOR_USER", passwd="***")

# Example: reading background job status via a standard or custom
# function module (RFC-enabled) that returns job status records.
# The exact function module you use depends on what's RFC-enabled on
# your system -- BAPI_XBP_JOB_SELECT (via the External Job Scheduling
# Interface / XBP) is the standard-supported route for job data over RFC,
# but XBP requires its own setup (a scheduler ID registered via SM69/XBP
# config) -- check with your Basis team before assuming it's available.
result = conn.call("BAPI_XBP_JOB_SELECT", ...)

conn.close()
```

## Recommendation

Start with `hana_monitor.py` and `s4hana_odata_monitor.py`. Only reach for RFC if your organization already has NW RFC SDK access set up and a specific reason to need it (e.g. a function module with data the OData layer doesn't expose on your system).

