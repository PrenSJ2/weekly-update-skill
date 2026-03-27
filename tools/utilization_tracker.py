#!/usr/bin/env python3
"""Utilization tracker with holiday calendar integration.

Tracks utilization against bonus targets, warns on over-acceleration,
and adjusts projections based on upcoming PTO.

Usage:
    # Set up holiday calendar (one-time)
    python utilization_tracker.py --setup-holidays "https://calendar.google.com/calendar/ical/..."

    # Check current utilization and get recommendations
    python utilization_tracker.py check

    # View upcoming holidays only
    python utilization_tracker.py holidays
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from icalendar import Calendar

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_helper import cleanup, connect_to_chrome

CONFIG_PATH = Path.home() / ".cursor" / "tools" / ".utilization_config.json"

UTIL_TARGET = 0.80
ACCEL_1 = 0.87
ACCEL_2 = 0.94

SF_DASHBOARD_URL = (
    "https://66degrees.lightning.force.com/lightning/r/Dashboard/01ZUV000003QOjJ2AW/view?queryScope=userFolders"
)

QUARTERS = [
    (1, 1, 3, 31),   # Q1: Jan 1 - Mar 31
    (4, 1, 6, 30),   # Q2: Apr 1 - Jun 30
    (7, 1, 9, 30),   # Q3: Jul 1 - Sep 30
    (10, 1, 12, 31), # Q4: Oct 1 - Dec 31
]


def setup_holidays(url: str):
    """Save the holiday calendar iCal URL."""
    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
    config["holiday_ical_url"] = url
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"Holiday calendar configured. URL saved to {CONFIG_PATH}")


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text())


def _get_quarter_bounds(ref_date: date) -> tuple[date, date]:
    """Return (start, end) dates for the quarter containing ref_date."""
    year = ref_date.year
    for start_m, start_d, end_m, end_d in QUARTERS:
        start = date(year, start_m, start_d)
        end = date(year, end_m, end_d)
        if start <= ref_date <= end:
            return start, end
    return date(year, 1, 1), date(year, 3, 31)


def _count_workdays(start: date, end: date) -> int:
    """Count weekdays (Mon-Fri) between start and end inclusive."""
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def _to_date(dt_val) -> date:
    """Convert an icalendar date/datetime to a Python date."""
    if isinstance(dt_val, datetime):
        return dt_val.date()
    if isinstance(dt_val, date):
        return dt_val
    return date.fromisoformat(str(dt_val))


def get_upcoming_holidays(until_date: date) -> list[dict]:
    """Fetch holidays/PTO from the configured iCal feed up to until_date."""
    config = _load_config()
    url = config.get("holiday_ical_url")
    if not url:
        return []

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Warning: Could not fetch holiday calendar: {e}", file=sys.stderr)
        return []

    cal = Calendar.from_ical(resp.text)
    today = date.today()
    holidays = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        start_date = _to_date(dtstart.dt)

        dtend = component.get("dtend")
        end_date = _to_date(dtend.dt) - timedelta(days=1) if dtend else start_date

        if end_date < today or start_date > until_date:
            continue

        summary = str(component.get("summary", "PTO"))
        
        current = max(start_date, today)
        while current <= min(end_date, until_date):
            if current.weekday() < 5:
                holidays.append({
                    "date": current,
                    "summary": summary,
                })
            current += timedelta(days=1)

    holidays.sort(key=lambda h: h["date"])
    return holidays


def _kill_automation_chrome():
    """Kill any existing automation Chrome."""
    subprocess.run(["pkill", "-f", "chrome-automation"], capture_output=True)
    time.sleep(2)


def scrape_utilization() -> dict | None:
    """Scrape current utilization from Salesforce dashboard.
    
    Returns dict with utilization data or None if scraping fails.
    Looks for "Quarter to Date" utilization specifically.
    Dashboard content is inside an iframe.
    """
    _kill_automation_chrome()
    
    try:
        pw, browser, page = connect_to_chrome()
    except Exception as e:
        print(f"Warning: Could not connect to Chrome: {e}", file=sys.stderr)
        return None

    try:
        page.goto(SF_DASHBOARD_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(15)
        
        # Click the Refresh button to ensure data is up to date
        # The button is inside the dashboard iframe
        refresh_clicked = False
        try:
            iframes = page.query_selector_all("iframe")
            for iframe in iframes:
                frame = iframe.content_frame()
                if frame:
                    for selector in [
                        "button:has-text('Refresh')",
                        "[title='Refresh']",
                        "a:has-text('Refresh')",
                        "span:text-is('Refresh')",
                    ]:
                        try:
                            btn = frame.locator(selector).first
                            if btn.is_visible(timeout=2000):
                                btn.click(timeout=5000)
                                print("Clicked Refresh button in dashboard.", file=sys.stderr)
                                refresh_clicked = True
                                time.sleep(15)
                                break
                        except Exception:
                            pass
                    if refresh_clicked:
                        break
            if not refresh_clicked:
                print("Refresh button not found (continuing with cached data).", file=sys.stderr)
        except Exception as e:
            print(f"Could not click Refresh (continuing): {e}", file=sys.stderr)
        
        page.screenshot(path="/tmp/util_dashboard.png")
        print("Dashboard screenshot saved to /tmp/util_dashboard.png", file=sys.stderr)
        
        text = ""
        iframes = page.query_selector_all("iframe")
        for iframe in iframes:
            try:
                frame = iframe.content_frame()
                if frame:
                    frame_text = frame.evaluate("() => document.body.innerText")
                    if "Utilization" in frame_text:
                        text = frame_text
                        break
            except Exception:
                pass
        
        if not text:
            text = page.inner_text("body", timeout=10000)
        
        import re
        
        result = {
            "utilization": None,
            "utilization_qtd": None,
            "utilization_mtd": None,
            "utilization_week": None,
            "raw_text": text[:3000],
        }
        
        qtd_match = re.search(r'Quarter\s+to\s+Date.*?(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE | re.DOTALL)
        if qtd_match:
            result["utilization_qtd"] = float(qtd_match.group(1)) / 100
            result["utilization"] = result["utilization_qtd"]
        
        mtd_match = re.search(r'Month\s+to\s+Date.*?(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE | re.DOTALL)
        if mtd_match:
            result["utilization_mtd"] = float(mtd_match.group(1)) / 100
        
        week_match = re.search(r'Last\s+Week.*?(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE | re.DOTALL)
        if week_match:
            result["utilization_week"] = float(week_match.group(1)) / 100
        
        if result["utilization"] is None:
            all_pcts = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
            if all_pcts:
                result["all_percentages"] = [float(p) for p in all_pcts[:10]]
        
        return result
        
    except Exception as e:
        print(f"Warning: Dashboard scrape failed: {e}", file=sys.stderr)
        return None
    finally:
        cleanup(pw, browser)


def calculate_projections(
    current_util: float | None,
    holidays: list[dict],
    ref_date: date | None = None,
) -> dict:
    """Calculate utilization projections and recommendations."""
    today = ref_date or date.today()
    q_start, q_end = _get_quarter_bounds(today)
    
    total_workdays = _count_workdays(q_start, q_end)
    elapsed_workdays = _count_workdays(q_start, today - timedelta(days=1))
    remaining_workdays = _count_workdays(today, q_end)
    
    holiday_dates = {h["date"] for h in holidays}
    remaining_workdays_after_pto = remaining_workdays - len(holiday_dates)
    
    result = {
        "quarter": f"Q{(q_start.month - 1) // 3 + 1} {q_start.year}",
        "quarter_end": q_end.isoformat(),
        "total_workdays": total_workdays,
        "elapsed_workdays": elapsed_workdays,
        "remaining_workdays": remaining_workdays,
        "upcoming_pto_days": len(holiday_dates),
        "remaining_workdays_after_pto": remaining_workdays_after_pto,
        "holidays": [{"date": h["date"].isoformat(), "summary": h["summary"]} for h in holidays],
        "warnings": [],
        "recommendations": [],
    }
    
    if current_util is not None:
        result["current_utilization"] = current_util
        result["current_utilization_pct"] = f"{current_util * 100:.1f}%"
        
        if current_util > ACCEL_2:
            excess = current_util - ACCEL_2
            excess_hours = excess * total_workdays * 8
            result["warnings"].append(
                f"You're at {current_util*100:.1f}%, above max accelerator ({ACCEL_2*100:.0f}%). "
                f"~{excess_hours:.0f} hours this quarter yield no additional bonus."
            )
            result["recommendations"].append(
                f"Consider taking {excess_hours / 8:.1f} days PTO before {q_end.strftime('%b %d')} "
                "instead of over-working for no extra bonus."
            )
        elif current_util > ACCEL_1:
            headroom = ACCEL_2 - current_util
            headroom_hours = headroom * total_workdays * 8
            result["recommendations"].append(
                f"You're in accelerator tier 1 ({current_util*100:.1f}%). "
                f"~{headroom_hours:.0f} hours headroom before max accelerator."
            )
        elif current_util > UTIL_TARGET:
            result["recommendations"].append(
                f"You're above target ({current_util*100:.1f}% > {UTIL_TARGET*100:.0f}%). On track for bonus."
            )
        else:
            gap = UTIL_TARGET - current_util
            hours_needed = gap * total_workdays * 8
            days_needed = hours_needed / 8
            if remaining_workdays_after_pto > 0:
                extra_per_day = hours_needed / remaining_workdays_after_pto
                result["warnings"].append(
                    f"Below target: {current_util*100:.1f}% vs {UTIL_TARGET*100:.0f}% target. "
                    f"Need ~{hours_needed:.0f} more billable hours ({days_needed:.1f} days)."
                )
                result["recommendations"].append(
                    f"To hit target, average {8 + extra_per_day:.1f} billable hrs/day "
                    f"for remaining {remaining_workdays_after_pto} workdays."
                )
    
    if holidays and current_util is not None:
        pto_days = len(holiday_dates)
        if remaining_workdays > 0:
            lost_util_pct = (pto_days / total_workdays) * 100
            result["warnings"].append(
                f"Upcoming PTO ({pto_days} days) reduces potential utilization by ~{lost_util_pct:.1f}%."
            )
            
            if current_util < UTIL_TARGET:
                extra_hours_needed = (UTIL_TARGET - current_util) * total_workdays * 8
                if remaining_workdays_after_pto > 0:
                    weekly_increase = extra_hours_needed / (remaining_workdays_after_pto / 5)
                    result["recommendations"].append(
                        f"To compensate for PTO and hit target, increase weekly billable by ~{weekly_increase:.1f} hrs."
                    )
    
    return result


def action_check():
    """Full check: scrape utilization, check holidays, calculate projections."""
    print("Fetching utilization from Salesforce dashboard...", file=sys.stderr)
    util_data = scrape_utilization()
    
    current_util = util_data.get("utilization") if util_data else None
    
    today = date.today()
    _, q_end = _get_quarter_bounds(today)
    
    print("Fetching upcoming holidays...", file=sys.stderr)
    holidays = get_upcoming_holidays(q_end)
    
    projections = calculate_projections(current_util, holidays, today)
    
    if util_data:
        projections["utilization_mtd"] = util_data.get("utilization_mtd")
        projections["utilization_week"] = util_data.get("utilization_week")
    
    print("\n" + "=" * 60)
    print(f"UTILIZATION CHECK — {projections['quarter']}")
    print("=" * 60)
    
    if current_util is not None:
        print(f"\nQuarter to Date: {current_util * 100:.1f}%")
        if util_data and util_data.get("utilization_mtd"):
            print(f"Month to Date:   {util_data['utilization_mtd'] * 100:.1f}%")
        if util_data and util_data.get("utilization_week"):
            print(f"Last Week:       {util_data['utilization_week'] * 100:.1f}%")
        print(f"\nTargets: {UTIL_TARGET*100:.0f}% base | {ACCEL_1*100:.0f}% accel 1 | {ACCEL_2*100:.0f}% max")
    else:
        print("\nCurrent Utilization: Could not scrape (check /tmp/util_dashboard.png)")
    
    print(f"\nQuarter ends: {projections['quarter_end']}")
    print(f"Workdays: {projections['elapsed_workdays']} elapsed, {projections['remaining_workdays']} remaining")
    
    if projections["upcoming_pto_days"] > 0:
        print(f"\nUpcoming PTO ({projections['upcoming_pto_days']} days):")
        for h in projections["holidays"][:10]:
            print(f"  - {h['date']}: {h['summary']}")
        print(f"  Effective remaining workdays: {projections['remaining_workdays_after_pto']}")
    
    if projections["warnings"]:
        print("\n⚠️  WARNINGS:")
        for w in projections["warnings"]:
            print(f"  • {w}")
    
    if projections["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for r in projections["recommendations"]:
            print(f"  • {r}")
    
    print()
    
    print(json.dumps(projections, indent=2, default=str))


def action_holidays():
    """Show upcoming holidays only."""
    today = date.today()
    _, q_end = _get_quarter_bounds(today)
    
    holidays = get_upcoming_holidays(q_end)
    
    if not holidays:
        print("No upcoming holidays/PTO found in calendar.")
        print("Set up with: utilization_tracker.py --setup-holidays <URL>")
        return
    
    print(f"Upcoming PTO through {q_end.strftime('%b %d, %Y')}:")
    print("-" * 40)
    for h in holidays:
        print(f"  {h['date'].strftime('%a %b %d')}: {h['summary']}")
    print(f"\nTotal: {len(holidays)} PTO day(s)")


def main():
    parser = argparse.ArgumentParser(description="Utilization tracker with holiday integration")
    parser.add_argument(
        "action",
        nargs="?",
        choices=["check", "holidays"],
        help="'check' for full utilization check, 'holidays' to view upcoming PTO",
    )
    parser.add_argument(
        "--setup-holidays",
        metavar="URL",
        help="Configure holiday calendar iCal URL",
    )
    args = parser.parse_args()

    if args.setup_holidays:
        setup_holidays(args.setup_holidays)
        return

    if args.action == "check":
        action_check()
    elif args.action == "holidays":
        action_holidays()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
