# Quickstart: a new project with a team of agents in 15 minutes

For the owner (the human). Everything else in the template is written for the agents.

## Create a project with the generator

```
python tools/new_project.py --out <new folder>            # interview
python tools/new_project.py --out <new folder> --answers answers.json   # no questions
python tools/new_project.py --out <new folder> --dry-run  # plan only, writes nothing
```

Questions: kind (web, mobile, service, data-ml, research); stack (for mobile: flutter, react-native, native-ios, native-android, native-both, other; otherwise any text); depth (research, mvp, product); project name; repository public or private; tracker (linear, github, backlog); chat language; documentation level (light, standard, full; defaults from the depth); will users connect their own agents (MCP; default yes for product depth with web or service).

Answers file: JSON with the keys `name`, `kind`, `stack`, `depth`, `visibility`, `tracker`, `language`, `docs`, `mcp`.

What you get: a new folder with only the roles of the preset, the rules cut to the depth, the blanks the answers can fill already filled, `project.yaml` (answers and template version), `.claude/work_mode` set to `manual`, `git init` and a first commit. What remains: the `<<...>>` blanks only the project can answer (the generator lists them): stack commands, folders per role, tracker key, what counts as personal data. Then open the CTO session with its start message.

The manual way below stays valid as a fallback.

## 0. What to know

- The agents work as separate Claude Code sessions. **The CTO does not create permanent agents**: you open the sessions and paste each one's start message. The CTO can write to sessions that already exist, wake sleeping ones and start short-lived subagents.
- The CTO does not write code and is the only one who pushes (after the checks). The others commit locally.
- Minimal team: **Product + business analyst + CTO + backend + reviewer**. Add the others (frontend, mobile, mcp, product, qa, qa-web) when there is work for them; add `qa` and a stage as soon as the product sends, spends or writes live data.

## 1. Prepare the folder (5 minutes)

1. Copy `teamkit` into a new project folder, for example `<projects folder>\<name>`.
2. In the new folder run `git init`, then make the first commit `chore: start from TeamKit`.
3. Find every place to fill in: search the text for `<<` (in VS Code: Ctrl+Shift+F). Required:
   - `CLAUDE.md`: what the project does, the stack, the run and test commands, the critical rules;
   - `docs/delivery/AGENT_RULES.md`: row 20 (the tracker and the issue key), row 12 (is the repository public or private, what counts as personal data), and the "File ownership" table (who owns which folders).
4. The other `<<...>>` in the role addenda (`docs/delivery/roles/`) are filled in by the agents on their first task; you may skip them.
5. Pick a work mode: the file `.claude/work_mode` with one word, `manual` (the default: you work yourself) or `auto` (the agents work almost without you). Start with `manual`.

## 2. Open the Product agent (3 minutes)

1. Open Claude Code (desktop) in the new folder and name the session `Product`.
2. Paste the first message from `docs/team/START_PROMPTS.md` (the Product row).
3. The Product agent reads the rules and the roadmap, talks to you about the goal, and calls the CTO when a question is technical. The CTO proposes the tracker and the labels (`by-backend`, `reviewed`, `needs-owner` and so on) and says which agents to open first.

## 3. Open the others (one at a time, 1 minute each)

A new session in the same folder, named as in the table of `START_PROMPTS.md`, with its message pasted in. Each agent tells the CTO "ready" and waits for a task.

Order: backend → reviewer (when the first risky change appears) → the rest as needed.

## 4. The first task

Tell the Product agent in plain words what you want first. The business analyst does the discovery and writes the task (`Origin:` as the first line, user story, acceptance criteria); the CTO adds the technical part, hands it to the right agent and accepts the result. You get only: a finished result, a problem, or a decision that belongs to you.

## 5. What you decide

Pushes in `manual` mode; live data (database writes, restarts); changes to the team's rules; switching between `auto` and `manual`; spending of tokens and money; anything the agents mark as "owner's decision".

## 6. When a session loses its context

Paste the same start message and add: "Read the latest file in `.claude/sessions/` and continue."

## 7. End of the day

Ask the CTO to write the session log (`.claude/sessions/`) and to give one line per task.

## Frequently asked questions

| Question | Answer |
|---|---|
| Do I need all the roles? | No. Start with three and add the others later |
| How do I add a new role? | Copy `docs/team/roles/backend.md`, change "who you are" and the first action, add a row to the ownership table and to `START_PROMPTS.md` |
| Is the repository public? | Then add a guard test for personal data right away (rule 12) |
| What about mobile? | The `mobile` role: a copy of frontend with phone checks; mobile QA needs its own role (an emulator, golden snapshots) |
