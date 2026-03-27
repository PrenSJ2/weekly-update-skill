#!/usr/bin/env python3
"""Setup script for weekly-update skill.

Installs tools to ~/.cursor/tools/ and configures per-user settings:
- Calendar iCal feed (for weekly notes)
- Holiday calendar iCal feed (for utilization tracking)

Run from the skill repo root: python scripts/setup.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TOOLS_SRC = SKILL_DIR / "tools"
TOOLS_DEST = Path.home() / ".cursor" / "tools"
VENV_PYTHON = TOOLS_DEST / ".venv" / "bin" / "python"


def install_tools():
    """Copy tools from repo to ~/.cursor/tools/"""
    print("Installing tools to ~/.cursor/tools/...")
    TOOLS_DEST.mkdir(parents=True, exist_ok=True)
    
    installed = []
    for tool in TOOLS_SRC.glob("*.py"):
        dest = TOOLS_DEST / tool.name
        shutil.copy2(tool, dest)
        installed.append(tool.name)
    
    if installed:
        print(f"  Installed: {', '.join(installed)}")
    else:
        print("  No tools found in repo tools/ directory.")
    
    return installed


def setup_calendar():
    """Configure the main calendar iCal feed."""
    print("\n— Calendar Setup —")
    print("Your iCal feed URL (for meetings in weekly notes).")
    
    ical_url = input("iCal feed URL (or Enter to skip): ").strip()
    if not ical_url:
        print("Skipped. Run later with:")
        print("  ~/.cursor/tools/.venv/bin/python ~/.cursor/tools/calendar_tool.py --setup \"URL\"")
        return
    
    calendar_tool = TOOLS_DEST / "calendar_tool.py"
    if not VENV_PYTHON.exists() or not calendar_tool.exists():
        print(f"Warning: calendar_tool.py not found. Run manually after installing tools.")
        return
    
    try:
        subprocess.run([str(VENV_PYTHON), str(calendar_tool), "--setup", ical_url], check=True)
        print("Calendar configured.")
    except subprocess.CalledProcessError as e:
        print(f"Calendar setup failed: {e}", file=sys.stderr)


def setup_holiday_calendar():
    """Configure the holiday/PTO calendar for utilization tracking."""
    print("\n— Holiday Calendar Setup —")
    print("Your PTO/holiday iCal feed (for utilization tracking).")
    print("This should be a separate calendar with only PTO events.")
    
    ical_url = input("Holiday iCal feed URL (or Enter to skip): ").strip()
    if not ical_url:
        print("Skipped. Run later with:")
        print("  ~/.cursor/tools/.venv/bin/python ~/.cursor/tools/utilization_tracker.py --setup-holidays \"URL\"")
        return
    
    util_tool = TOOLS_DEST / "utilization_tracker.py"
    if not VENV_PYTHON.exists() or not util_tool.exists():
        print(f"Warning: utilization_tracker.py not found. Run manually after installing tools.")
        return
    
    try:
        subprocess.run([str(VENV_PYTHON), str(util_tool), "--setup-holidays", ical_url], check=True)
        print("Holiday calendar configured.")
    except subprocess.CalledProcessError as e:
        print(f"Holiday calendar setup failed: {e}", file=sys.stderr)


def main():
    print("=" * 50)
    print("Weekly Update Skill — Setup")
    print("=" * 50)
    print()
    print("This will:")
    print("  1. Install tools to ~/.cursor/tools/")
    print("  2. Configure your calendar iCal feed")
    print("  3. Configure your holiday calendar (for utilization tracking)")
    print()
    print("GitHub username comes from `gh` (logged-in user).")
    print("Lattice URL is shared (see org-defaults.md).")
    print()
    
    # Install tools
    install_tools()
    
    # Configure calendars
    setup_calendar()
    setup_holiday_calendar()
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now run the weekly-update skill.")
    print("=" * 50)


if __name__ == "__main__":
    main()
