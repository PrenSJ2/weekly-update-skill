# Org defaults (same for everyone)

These values are shared across the organisation. Only the iCal feed is per-user (configured via setup).

## Lattice check-in URL

Use this URL when calling `lattice_update.py` (no need to pass `--url`; the tool in `~/.cursor/tools/lattice_update.py` already uses it by default):

```
https://66degrees.latticehq.com/users/36390560-010f-4084-a051-dd9ff80450e2/updates?checkinId=f073cac3-fb46-44f9-985b-a9f4edbd753c
```

Update the URL above if the check-in link changes (e.g. new check-in cycle). The workflow reads this file for the canonical Lattice URL.

---

## Utilization Targets (Delivery Incentive Program)

These are the same for all Delivery Individual Contributors (excl. PMO):

| Metric | Target | Accelerator 1 | Accelerator 2 (Max) |
|--------|--------|---------------|---------------------|
| Utilization | 80% | +7% (87%) | +14% (94%) |

- **Going above 94%** yields no additional bonus — warn user and suggest taking PTO before quarter end.
- **Upcoming PTO** reduces available billable days — warn user to front-load hours if they risk missing target/accelerators.

## Salesforce Utilization Dashboard

```
https://66degrees.lightning.force.com/lightning/r/Dashboard/01ZUV000003QOjJ2AW/view?queryScope=userFolders
```

The `utilization_tracker.py` tool scrapes this dashboard for current utilization %.

## Holiday Calendar (per-user, but URL pattern is shared)

Users set up their own holiday calendar via:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/utilization_tracker.py --setup-holidays "https://calendar.google.com/calendar/ical/..."
```

This iCal feed should contain PTO/holiday events. The tool reads it to calculate upcoming time off.

## Fiscal Quarters

66degrees uses **calendar quarters**:

| Quarter | Start | End |
|---------|-------|-----|
| Q1 | Jan 1 | Mar 31 |
| Q2 | Apr 1 | Jun 30 |
| Q3 | Jul 1 | Sep 30 |
| Q4 | Oct 1 | Dec 31 |
