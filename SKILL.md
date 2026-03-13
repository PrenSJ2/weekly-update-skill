---
name: weekly-update
description: >
  Generate weekly notes by combining MindNode daily notes and calendar events,
  then populate Salesforce timesheet and Lattice update. Use when the user asks
  for weekly notes, weekly summary, what they did this week, or to fill
  timesheet/Lattice.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Weekly Update Skill

Generates a structured weekly summary from MindNode daily notes, calendar, and GitHub commits; then fills Salesforce timesheet and Lattice weekly update.

## When to use

- User asks for **weekly notes**, **weekly summary**, or **what they did this week**
- User wants to **populate Salesforce timesheet** or **Lattice update** from the same workflow

## Workflow summary

1. **Step 0:** Ask for client/project context (e.g. "HSBC Prep Packs").
2. **Step 1:** Read MindNode file — `mindnode_tool.py read "<file.mindnode>"` — use "Daily Notes" branch for the week.
3. **Step 2:** Read calendar — `calendar_tool.py --week <YYYY-MM-DD>`.
4. **Step 3:** Fetch GitHub commits for the week (66degrees org, author PrenSJ2) via `gh api search/commits`.
5. **Step 4:** Generate weekly notes — header, intro, daily breakdown (bullets &lt; 255 chars, no em dashes), then personal summary (four questions, first person).
6. **Step 5:** Ask how user is feeling (Awful / Poor / Neutral / Good / Great) and generate personal weekly summary.
7. **Step 6:** Optionally populate Salesforce timesheet — confirm with user, then `salesforce_timesheet.py view` then `fill '{"Monday": "...", ...}'`.
8. **Step 7:** Optionally populate Lattice — confirm with user, then `lattice_update.py '{"focus": "...", "plans": "...", "challenges": "...", "anything_else": "..."}'`.

All tools run from `~/.cursor/tools/` using the venv:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/<script>.py [args]
```

## Mandatory reading

Before running the workflow, read the full step-by-step instructions:

- **Workflow (steps, format, tone, tools):** [workflow.md](workflow.md)

Paths above are relative to this skill directory.

## Output format (summary)

- **Header:** "Weekly Notes — w/c DD Month YYYY — [Client: Project]"
- **Daily bullets:** Under 255 characters each; no em dashes; by day, not by theme.
- **Personal summary:** First person; four answers (focus, plans, challenges, anything else); 2–4 sentences each; tone matches user's feeling.

Do not submit Salesforce or Lattice automatically — ask the user to review and submit in the automation Chrome window.
