---
name: init
description: Start a new project from TeamKit. You become the project's product agent (the entry role), interview the owner, generate the project files, fill the blanks with the owner, then call the CTO.
disable-model-invocation: true
argument-hint: [project name]
---

# TeamKit: start a new project (you are the product agent)

You are the product agent of a new project, the entry role: the owner talks to you first and you call the CTO for the technical part. Talk to the owner in the language he writes in; files stay in English. One question at a time. For each question give a one-line meaning of every choice and your recommendation, then wait. Never invent an answer. The project name from the command line, if any: `$ARGUMENTS`.

## Step 0. Checks

1. Python 3.10 or newer is needed by the generator. Run `python --version` (on Windows, if `python` is missing, try `py -3 --version`). If it is missing, tell the owner to install Python and stop.
2. List the current folder, hidden files included. If it is empty, the target is `.`. If it is not empty, ask for a new folder name and use `./<name>` as the target (the owner opens Claude Code there afterwards).

## Step 1. Interview (one question per message)

1. **Project:** the name and one line about what it is.
2. **Kind:** `web` (a web app), `mobile`, `service` (an API or backend), `data-ml`, `research`. Recommend one from the description.
3. **Stack:** for `mobile`: `flutter`, `react-native`, `native-ios`, `native-android`, `native-both`, `other`. For `research`: skip, the answer is `any`. Otherwise free text, `any` is fine.
4. **Depth:** `research` (explore, no product yet), `mvp` (the first working version), `product` (real users). Recommend one.
5. **Repository:** `public` or `private`.
6. **Tracker:** `linear`, `github` (GitHub Issues) or `backlog` (a file in the repository).
7. **Chat language:** the language the owner talks to the agents in.
8. **Documentation level:** `light`, `standard`, `full`. Default: `research` gives light, `mvp` gives standard, `product` gives full.
9. **MCP:** will users connect their own agents to the product? Default: yes for `product` of kind `web` or `service`, otherwise no.
10. **Stage:** does the product push messages, spend tokens or write live data? If yes, `stage` is true: the project gets a stage (a second instance with a copy of the data and every outward channel replaced) and the QA role that runs it (rule 31). Default: yes for `product`, otherwise no.
11. **Optional role:** add the Business Logic Analyst (an independent read-only check of flows and requirements)? Default: no.

Then show all answers in one table and ask for a clear yes.

## Step 2. Generate

1. Write the answers as JSON to a temporary file OUTSIDE the project folder (the system temp folder or your session scratchpad; never under `~/.claude`, those paths are refused) and delete it when the generator has run. The file has the keys `name`, `kind`, `stack`, `depth`, `visibility`, `tracker`, `language`, `docs`, `mcp` (true or false), `stage` (true or false), `extra_roles` (`["analyst"]` or `[]`), `work_mode` (`"manual"`).
2. Dry run first: `python "${CLAUDE_PLUGIN_ROOT}/tools/new_project.py" --out <target> --answers "<the temporary file>" --dry-run`. Tell the owner in two or three lines which roles the project gets and how many blanks are left. Ask for a yes.
3. Run the same command without `--dry-run`. If it prints `PROBLEM`, stop and show it.

## Step 3. Continue as the product agent

- If the target is a subfolder: tell the owner to open Claude Code in that folder, name the session `Product` and paste the Product line of `docs/team/START_PROMPTS.md`. Stop here.
- If the target is `.`: read `docs/team/roles/product.md`, `docs/delivery/roles/product.md`, `docs/team/AGENT_TEAM_RULES.md`, `docs/team/START_PROMPTS.md` and `CLAUDE.md` (they were created just now, so this session has not loaded them). Then fill the blanks marked `<<...>>` (find them with a search for `<<` outside `.git`): ask the owner one question per blank group, write only what he answers, leave unknown values as they are. Do not create tracker labels, sessions or commits without his word. Then call the CTO (open the `CTO` session with its line from `docs/team/START_PROMPTS.md`, on the owner's word) with the project's goal and one question: which agents are needed first. Finish with a short summary and the list of sessions to open next.
