#!/usr/bin/env python3
"""One-time setup: configure your iCal feed (the only per-user setting).

Run from the skill repo root (weekly-update-skill) or with SKILL_DIR set.
Calls calendar_tool.py --setup so weekly notes can include your calendar.

GitHub username is read automatically from the logged-in gh user.
Lattice URL is the same for everyone (see org-defaults.md in the skill).
"""

import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path.home() / ".cursor" / "tools"
VENV_PYTHON = TOOLS_DIR / ".venv" / "bin" / "python"
CALENDAR_TOOL = TOOLS_DIR / "calendar_tool.py"


def main():
    print("Weekly Update Skill — Setup\n")
    print("The only per-user setting is your iCal feed. GitHub comes from `gh` (logged-in user); Lattice URL is shared (see org-defaults.md).\n")

    ical_url = input("iCal feed URL (for calendar in weekly notes): ").strip()
    if not ical_url:
        print("No URL entered. Run setup again when you have your iCal feed, or run manually:")
        print("  ~/.cursor/tools/.venv/bin/python ~/.cursor/tools/calendar_tool.py --setup \"https://...\"")
        return

    if not VENV_PYTHON.exists() or not CALENDAR_TOOL.exists():
        print(
            "Error: ~/.cursor/tools/.venv or calendar_tool.py not found. "
            "Install the tools first, then run:",
            file=sys.stderr,
        )
        print(f"  {VENV_PYTHON} {CALENDAR_TOOL} --setup \"{ical_url}\"", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(
            [str(VENV_PYTHON), str(CALENDAR_TOOL), "--setup", ical_url],
            check=True,
            capture_output=False,
        )
        print("\nCalendar configured. You can run the weekly-update skill now.")
    except subprocess.CalledProcessError as e:
        print(f"Calendar setup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
