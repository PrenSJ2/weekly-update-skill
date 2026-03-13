# Org defaults (same for everyone)

These values are shared across the organisation. Only the iCal feed is per-user (configured via setup).

## Lattice check-in URL

Use this URL when calling `lattice_update.py` (no need to pass `--url`; the tool in `~/.cursor/tools/lattice_update.py` already uses it by default):

```
https://66degrees.latticehq.com/users/36390560-010f-4084-a051-dd9ff80450e2/updates?checkinId=f073cac3-fb46-44f9-985b-a9f4edbd753c
```

Update the URL above if the check-in link changes (e.g. new check-in cycle). The workflow reads this file for the canonical Lattice URL.
