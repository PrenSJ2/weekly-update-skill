# Weekly Update Workflow — Full Steps

Generates a structured weekly summary by combining five sources:
1. **Client/project context** — provided by the user or inferred (e.g. "HSBC Prep Packs")
2. **MindNode daily notes** — the user's working notes captured in a mind map
3. **Calendar events** — meetings and appointments from their iCal feed
4. **Jira** — assignments, worklogs, and items completed (via **Jira MCP**; see `~/.cursor/skills/jira-mcp-weekly/SKILL.md`)
5. **GitHub commits** — commits authored by the user across the 66degrees org

## Global Tools

All automation tools live at `~/.cursor/tools/` and use the venv at `~/.cursor/tools/.venv`. Run them with:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/<script>.py [args]
```

---

## Step 0: Client/Project Context

Infer client and project from the user's message, calendar, MindNode, and Jira when possible. **Only ask** if the engagement is genuinely ambiguous.

The user may also provide additional context or colour (e.g. "this was my first week", "I was mostly pairing with X"). Weave this into the notes naturally.

---

## Step 1: Read the MindNode

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/mindnode_tool.py read "<file.mindnode>"
```

Look for the **"Daily Notes"** branch. Each child is a day's notes. Focus on entries for the current week (Monday–Friday).

---

## Step 2: Read the Calendar

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/calendar_tool.py --week <YYYY-MM-DD>
```

Replace `<YYYY-MM-DD>` with any date in the target week (e.g. today's date). If no calendar is configured yet, the tool will prompt the user to run `--setup`.

---

## Step 3: Jira MCP (assignments, work done, worklogs)

**Read and follow:** `~/.cursor/skills/jira-mcp-weekly/SKILL.md`.

Use the **Jira MCP** tools (`search_issues`, optionally `get_issue_details` with worklogs) for the target week. Default project **HSBCPP** unless the user names another. Run the JQL queries in that skill: updated issues, Done/resolved in range, and **worklogs** for day-by-day bucketing.

Merge ticket keys and outcomes into the daily breakdown (Step 5). If Jira MCP is unavailable, note it and continue.

---

## Step 4: Fetch GitHub Commits

Pull all commits authored by the user across the **66degrees** GitHub org for the target week. **Get the GitHub username automatically** from the logged-in `gh` user:

```bash
gh api user --jq '.login'
```

Use that value as `author:USERNAME` in the search. Then run:

```bash
gh api search/commits --method GET \
  -f q='org:66degrees author:USERNAME committer-date:YYYY-MM-DD..YYYY-MM-DD' \
  -f sort=committer-date \
  -f per_page=100 \
  --jq '.items[] | "\(.commit.committer.date) [\(.repository.name)] \(.commit.message | split("\n")[0])"'
```

Replace `USERNAME` in the query with the output of `gh api user --jq '.login'`. Replace the date range with the Monday and Sunday of the target week.

Use these commits to:
- **Assign each commit to the calendar day** it landed on (committer date). Include **repo** and **PR number** on merge commits.
- Supplement daily notes with concrete development work (PRs merged, features built, bugs fixed)
- Surface work that may not appear in the MindNode, calendar, or Jira
- Add technical detail to daily bullets where appropriate (e.g. "Implemented X endpoint", "Fixed Y bug in Z repo")

If the API returns no results, note this and move on (the user may not have pushed commits that week).

---

## Step 5: Generate the Weekly Notes

### Format

- **Header:** "Weekly Notes — w/c DD Month YYYY — [Client: Project]"
- **Brief intro:** 1-2 sentences of context (what the user told you, overall theme of the week)
- **Daily breakdown:** One section per day (Monday–Friday), with high-level bullet points
- **Each bullet point must be under 255 characters**
- **Never use em dashes (—).** Use commas, full stops, or restructure the sentence instead.
- Keep bullets concise, 1 line each, high-level summaries not granular details
- Phrase bullets in terms of what the user was focused on (e.g. "Reviewing X", "Coordinating Y", "Clarifying Z")
- Frame everything in terms of the client project (e.g. "Joined HSBC sync" not just "Joined sync")
- Use calendar events to fill in meetings the mindnode may not mention — list these but keep them brief
- Skip days with no activity
- Do NOT group by theme — always group by day
- **Jira:** weave ticket keys into the matching weekday (worklog date preferred)

### Tone

- Written as if reporting to a manager or for timesheets
- Professional but not overly formal
- Focus on what was achieved and contributed, not raw meeting notes
- The user is a consultant — notes should reflect their value-add to the client

---

## Step 6: Generate the Personal Weekly Summary

After the per-client daily notes, generate a **second section** that is a personal summary across all projects. This should be written in first person and answer these four questions:

1. **What did you focus on this week?**
2. **What are your plans and priorities for next week?**
3. **What challenges or roadblocks do you need help with?**
4. **Is there anything else on your mind you'd like to share?**

### Rules for personal summary

- **Mood:** If the user stated how they feel, use it. Otherwise ask once (Awful through Great) and set tone from that.
- Written in first person ("I focused on...", "Next week I plan to...")
- Spans all projects/clients. Infer from calendar, Jira, and commits; only ask if unclear.
- Keep each answer to 2-4 sentences max
- Derive "plans for next week" from the mindnode, calendar, and **open Jira** work
- Derive "challenges" from blockers, overdue items, dependencies, and **stuck Jira** issues
- "Anything else" can cover onboarding status, tooling, general observations — ask the user if unsure
- If the user provides extra colour/context, weave it in naturally

---

## Step 7: Populate Salesforce Timesheet (PSE Time Entry)

**Run by default** after weekly notes are ready (unless the user opts out). The scripts launch a second Chrome window with the user's session cookies (copied from their real profile) and connect via CDP. The user's regular Chrome stays open and untouched.

### 7a. View current schedules

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/salesforce_timesheet.py view
```

Read the output to understand what project assignments and hours are available. Share this with the user.

### 7b. Copy schedules and populate daily notes

Build a JSON object mapping each day to a concise note derived from the daily breakdown in Step 5. Each daily note must be **under 255 characters** (Salesforce limit). Then run the `fill` action, which will:
1. Select schedule checkboxes and click "Copy Selected Schedules"
2. Confirm the copy dialog
3. Open the notes dialog and populate daily notes for Mon–Fri
4. Click Done

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/salesforce_timesheet.py fill '{"Monday": "Reviewed API design docs, joined HSBC sync", "Tuesday": "Paired on data pipeline, fixed ingestion bug", ...}'
```

After populating, tell the user to **review the timecard in the automation Chrome window and click Save/Submit themselves.** Do NOT submit automatically.

If any step fails (selectors not found, etc.), check the screenshots saved to `/tmp/sf_step*.png` and `/tmp/sf_final.png` for debugging.

---

## Step 8: Populate Lattice Weekly Update

**Run by default** after Salesforce fill (unless the user opts out). Build a JSON object from the personal weekly summary (Step 6) with these keys:

- `focus` — answer to "What did you focus on this week?"
- `plans` — answer to "What are your plans and priorities for next week?"
- `challenges` — answer to "What challenges or roadblocks do you need help with?"
- `anything_else` — answer to "Is there anything else on your mind you'd like to share?"

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/lattice_update.py '{"focus": "...", "plans": "...", "challenges": "...", "anything_else": "..."}'
```

The **Lattice URL is the same for everyone**. Read it from **org-defaults.md** in this skill directory (section "Lattice check-in URL"), or use the script's built-in default. Pass it with `--url` if needed:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/lattice_update.py --url 'URL_FROM_org-defaults.md' '{"focus": "...", ...}'
```

After populating, tell the user to **review the update in the automation Chrome window and submit it themselves.** Do NOT submit automatically.

---

## Browser Setup

The Playwright scripts launch a **second Chrome instance** alongside the user's regular Chrome, using a copy of their session cookies so they're already logged in. No manual login or setup is required.

How it works:
1. Session files (cookies, login data, etc.) are copied from `~/Library/Application Support/Google/Chrome` to `~/.chrome-automation/`
2. A second Chrome instance launches with `--remote-debugging-port=9222` using that profile
3. Playwright connects via CDP and opens tabs for automation
4. The user's regular Chrome is completely untouched

If an automation Chrome instance is already running (from a previous step), the script reuses it without relaunching.

---

## Step 9: Utilization Check (warnings and recommendations)

**Run by default** at the end of the weekly update. This step checks the user's current utilization against bonus targets and adjusts projections based on upcoming PTO.

### What it does

1. **Scrapes Salesforce dashboard** for current utilization %
2. **Reads holiday calendar** for upcoming PTO days this quarter
3. **Calculates projections:** remaining workdays, impact of PTO, projected end-of-quarter utilization
4. **Warns** if user is above max accelerator (94%) — extra hours yield no bonus, suggest PTO
5. **Warns** if upcoming PTO puts user at risk of missing target — suggest increasing weekly hours

### Run the check

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/utilization_tracker.py check
```

### Output

The tool outputs:
- Current utilization % vs targets (80% target, 87% accel 1, 94% max)
- Remaining workdays in quarter
- Upcoming PTO days and their impact
- **Warnings** (e.g., "Above max accelerator", "PTO will reduce utilization by X%")
- **Recommendations** (e.g., "Take X days PTO before quarter end", "Increase weekly billable by Y hours")

### Present to user

After running the check, summarize the key findings:
- If **over max accelerator**: "You're at X%, above the 94% max. Consider taking Y days off before [quarter end] — extra hours won't increase your bonus."
- If **PTO upcoming + below target**: "Your upcoming PTO reduces available billable days. To hit target, increase this week's hours by X."
- If **on track**: "You're at X%, on track for accelerator tier Y."

---

## Setup (first time only)

### Calendar Setup

If the user hasn't configured their calendar yet, ask them for their iCal feed URL and run:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/calendar_tool.py --setup "https://..."
```

Common feed URL locations:
- **Google Calendar:** Settings → your calendar → "Secret address in iCal format"
- **Outlook 365:** Settings → Calendar → Shared calendars → "Publish a calendar" → ICS link
- **Apple Calendar:** Export as .ics or use CalDAV

### Holiday Calendar Setup

For utilization tracking to account for PTO, the user needs to configure their holiday calendar:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/utilization_tracker.py --setup-holidays "https://calendar.google.com/calendar/ical/..."
```

This should be a separate calendar (or filtered feed) containing only PTO/holiday events.
