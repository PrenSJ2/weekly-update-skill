---
name: weekly-update
description: >
  Generate weekly notes from MindNode, calendar, Jira MCP (HSBCPP assignments and
  worklogs), and GitHub commits; then populate Salesforce timesheet and Lattice.
  Use when the user asks for weekly notes, weekly summary, what they did this week,
  or to fill timesheet/Lattice.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Weekly Update Skill

Generates a structured weekly summary from MindNode daily notes, calendar, **Jira MCP**, and GitHub commits; then fills Salesforce timesheet and Lattice weekly update.

**Jira:** Read `~/.cursor/skills/jira-mcp-weekly/SKILL.md` and query Jira MCP during every weekly run.

## When to use

- User asks for **weekly notes**, **weekly summary**, or **what they did this week**
- User wants to **populate Salesforce timesheet** or **Lattice update** from the same workflow

## Workflow summary

1. **Step 0:** Infer or confirm client/project context (e.g. "HSBC Prep Packs").
2. **Step 1:** Read MindNode file — `mindnode_tool.py read "<file.mindnode>"` — use "Daily Notes" branch for the week.
3. **Step 2:** Read calendar — `calendar_tool.py --week <YYYY-MM-DD>`.
4. **Step 3:** **Jira MCP** — `jira-mcp-weekly` skill: worklogs, updated issues, Done in range (HSBCPP default).
5. **Step 4:** Fetch GitHub commits — `gh api user` for login, then `gh api search/commits` for `org:66degrees` and that week.
6. **Step 5:** Generate weekly notes — header, intro, daily breakdown (bullets &lt; 255 chars, no em dashes), then personal summary (four questions, first person).
7. **Step 6:** Personal summary tone from user's mood if given, else ask once.
8. **Step 7:** Run Salesforce — `salesforce_timesheet.py view` then `fill` (default unless user opts out).
9. **Step 8:** Run Lattice — `lattice_update.py` with four fields (default unless user opts out).

All tools run from `~/.cursor/tools/` using the venv:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/<script>.py [args]
```

## Mandatory reading

Before running the workflow, read:

- **Jira queries and MCP usage:** `~/.cursor/skills/jira-mcp-weekly/SKILL.md`
- **Workflow (steps, format, tone, tools):** [workflow.md](workflow.md)

Paths above are relative to this skill directory.

## Output format (summary)

- **Header:** "Weekly Notes — w/c DD Month YYYY — [Client: Project]"
- **Daily bullets:** Under 255 characters each; no em dashes; by day, not by theme.
- **Personal summary:** First person; four answers (focus, plans, challenges, anything else); 2–4 sentences each; tone matches user's feeling.

Do not submit Salesforce or Lattice automatically — tell the user to review and submit in the automation Chrome window.
