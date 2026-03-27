#!/usr/bin/env python3
"""Setup script for weekly-update skill.

Installs tools to ~/.cursor/tools/ and configures per-user settings:
- Calendar iCal feed (for weekly notes)
- Holiday calendar iCal feed (for utilization tracking)

Run from the skill repo root: python scripts/setup.py
"""

import json
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TOOLS_SRC = SKILL_DIR / "tools"
TOOLS_DEST = Path.home() / ".cursor" / "tools"

CALENDAR_CONFIG = TOOLS_DEST / ".calendar_config.json"
UTILIZATION_CONFIG = TOOLS_DEST / ".utilization_config.json"


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
    print("Find it in Google Calendar: Settings > your calendar > 'Secret address in iCal format'")
    
    ical_url = input("\niCal feed URL (or Enter to skip): ").strip()
    if not ical_url:
        print("Skipped.")
        return
    
    config = {}
    if CALENDAR_CONFIG.exists():
        config = json.loads(CALENDAR_CONFIG.read_text())
    
    config["ical_url"] = ical_url
    CALENDAR_CONFIG.write_text(json.dumps(config, indent=2))
    print(f"Calendar configured. Saved to {CALENDAR_CONFIG}")


def setup_holiday_calendar():
    """Configure the holiday/PTO calendar for utilization tracking."""
    print("\n— Holiday Calendar Setup —")
    print("Your PTO/holiday iCal feed (for utilization tracking).")
    print("This should be a separate calendar containing only your PTO/holiday events.")
    
    ical_url = input("\nHoliday iCal feed URL (or Enter to skip): ").strip()
    if not ical_url:
        print("Skipped.")
        return
    
    config = {}
    if UTILIZATION_CONFIG.exists():
        config = json.loads(UTILIZATION_CONFIG.read_text())
    
    config["holiday_ical_url"] = ical_url
    UTILIZATION_CONFIG.write_text(json.dumps(config, indent=2))
    print(f"Holiday calendar configured. Saved to {UTILIZATION_CONFIG}")


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
    
    # Install tools
    install_tools()
    
    # Configure calendars
    setup_calendar()
    setup_holiday_calendar()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print()
    print("You can now use the weekly-update skill.")
    print("Run 'utilization check' to see your current utilization status.")


if __name__ == "__main__":
    main()
