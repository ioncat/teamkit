# Quickstart: a new project with a team of agents in 15 minutes

For the owner (the human). Everything else in the template is written for the agents.

## Ways to install

| Way | Choose it when |
|---|---|
| 1. Plugin from GitHub | The normal way: you want the `/teamkit:` commands (init, adopt, update, help) and updates. |
| 2. Plugin from a local folder | You want to try a version before it is published, or you work on TeamKit itself. |
| 3. The generator directly | You do not use the plugin (scripts, CI, no Claude Code): the same safety, but no product interview; you answer questions or give an answers file. |
| 4. Manual copy | The fallback: copy the folder and fill in the blanks by hand. |

**1. Plugin from GitHub** (in a terminal, once):

```
claude plugin marketplace add ioncat/teamkit
claude plugin install teamkit@teamkit
```

Check: `claude plugin list`. Update to a newer version: `claude plugin marketplace update teamkit`, then `claude plugin update teamkit@teamkit`, then restart Claude Code (the update applies after a restart). Uninstall: `claude plugin uninstall teamkit@teamkit`, and, if you no longer want the source either, `claude plugin marketplace remove teamkit`.

**2. Plugin from a local folder:**

```
claude plugin marketplace add "<path to the teamkit folder>"
claude plugin install teamkit@teamkit
```

Two marketplaces with the same name `teamkit` conflict: if the GitHub one is added, remove it first (`claude plugin marketplace remove teamkit`). To go back to the GitHub version, remove the local one the same way and add the GitHub one again.

**3. The generator directly** (Python 3.10 or newer, nothing else to install). Always give the full path, because you run it in your own project folder:

```
python "<path to teamkit>/tools/new_project.py" --out "<project folder>"
```

| Flag | Meaning |
|---|---|
| `--out <folder>` | The project folder: new (empty or absent); with `--adopt`, an existing project (the root of a git repository). |
| `--adopt` | Existing project: add TeamKit without changing anything that exists (clean git tree; new files only; a manifest and an undo). |
| `--answers <file.json>` | Take the answers from a JSON file instead of asking questions. |
| `--dry-run` | Print the plan and write nothing. Use it first. |
| `--undo-adopt` | Remove exactly the files a previous `--adopt` created (from `.teamkit-adopt-manifest.txt`). |

Examples: a new project, plan only: `python "<path to teamkit>/tools/new_project.py" --out "<new folder>" --dry-run`. An existing project, plan only: `python "<path to teamkit>/tools/new_project.py" --out "<project folder>" --adopt --dry-run`. Undo an adoption: `python "<path to teamkit>/tools/new_project.py" --out "<project folder>" --undo-adopt`.

**4. Manual copy:** copy the `teamkit` folder into the project folder and follow "1. Prepare the folder" below.

## Create a project with the generator

```
python tools/new_project.py --out <new folder>            # interview
python tools/new_project.py --out <new folder> --answers answers.json   # no questions
python tools/new_project.py --out <new folder> --dry-run  # plan only, writes nothing
```

Questions: kind (web, mobile, service, data-ml, research); stack (for mobile: flutter, react-native, native-ios, native-android, native-both, other; otherwise any text); depth (research, mvp, product); project name; repository public or private; tracker (linear, github, backlog); chat language; documentation level (light, standard, full; defaults from the depth); will users connect their own agents (MCP; default yes for product depth with web or service); does it push messages, spend tokens or write live data (then it gets a stage and the QA role; default yes for product depth, never for research).

Answers file: JSON with the keys `name`, `kind`, `stack`, `depth`, `visibility`, `tracker`, `language`, `docs`, `mcp`, `stage`.

What you get: a new folder with only the roles of the preset, the rules cut to the depth, the blanks the answers can fill already filled, `project.yaml` (answers and template version), `.claude/work_mode` set to `manual`, `git init` and a first commit. What remains: the `<<...>>` blanks only the project can answer (the generator lists them): stack commands, folders per role, tracker key, what counts as personal data. Then open the Product Manager session with its start message (the Product row of `docs/team/START_PROMPTS.md`).

The manual way below stays valid as a fallback.

## Existing project

Bring TeamKit into a project that already exists. It must be a git repository. **Adopting breaks nothing that exists**: nothing is overwritten or deleted, only files that do not exist yet are written (and only in `docs/team/`, `docs/delivery/`, `docs/discovery/README.md`, `.claude/work_mode`, `project.yaml`); `CLAUDE.md`, `README.md`, `.gitignore`, build files and CI are never touched; there is no `git init`, no branch and no commit; before and after the run every file of the repository is hashed, and if any file that existed has changed the run removes what it wrote and fails.

1. Commit or stash your work, so that `git status` is empty, and **work on a new branch**: `git switch -c chore/adopt-teamkit`. If something goes wrong you throw the branch away.
2. Dry run: `python tools/new_project.py --out <your project> --adopt --dry-run` (add `--answers answers.json` to skip the questions). It lists the **new** files, the files **kept** as they are (a TeamKit file you already have), what is **not written** by design, and where the section for your own `CLAUDE.md` goes. Nothing is written. A `REFUSED` line (for example a file where a folder is needed) means nothing would be written; fix it first.
3. Adopt: the same command without `--dry-run`. It writes `.teamkit-adopt-manifest.txt` first (so that even a run that is killed can be undone), then the new files, and prints the one command that undoes exactly this run. It refuses to write through a symlink or a Windows junction, and Ctrl-C removes what it had written. Every file of the repository is hashed twice (before and after), so on a very large repository the run takes a while.
4. **Look at the result before you commit:** `git status` must show only new files (all marked `??`) and `git diff` must be empty. Then commit the adoption yourself, on the branch.
5. Undo, if you want it back: `python tools/new_project.py --out <your project> --undo-adopt` removes exactly the files in the manifest (a file you changed since is left alone) and the folders it made.
6. Merge by hand: your `CLAUDE.md` is untouched, its TeamKit section is `docs/team/CLAUDE_TEAMKIT_SECTION.md` (copy what you want into `CLAUDE.md`, or start one from it, then delete the file); the lines the plan named for `.gitignore`; any other kept file.
7. Fill the "File ownership" table in `docs/delivery/AGENT_RULES.md` from the real folders of the project, and the other `<<...>>` blanks the generator listed.
8. Start in `manual` mode (`.claude/work_mode`, written only if it did not exist) with the minimal roles: Product Manager, Business Analyst, CTO, Backend, Reviewer. Then open the Product Manager session as in section 2.

In Claude Code, run `/teamkit:adopt` in the project folder. It goes product first: the Product Manager reads the project and proposes its maturity stage, the user, the North Star, the success signal and the current milestone, and summarises the backlog (each item as "we see, we propose, accept or your variant"; **no agreed goal, no adoption**); then the CTO reads the technology in the light of that goal (risks, team, rule conflicts side by side, a health report and starter tasks, the team for the stage, how much documentation); only then does it run the dry run and steps 2 to 8 with you, one edit at a time on your word, and it fills `docs/delivery/PRODUCT_BRIEF.md` with what you agreed. `/teamkit:help` lists all commands.

## 0. What to know

- The agents work as separate Claude Code sessions. You open the Product Manager; the Product Manager opens the Business Analyst and the CTO; the CTO opens the delivery roles. Without a `start_session` tool you open each session yourself and paste its start message. The CTO can write to sessions that already exist, wake sleeping ones and start short-lived subagents.
- The CTO does not write code and is the only one who pushes (after the checks). The others commit locally.
- Minimal team: **Product Manager + Business Analyst + CTO + Backend + Reviewer**. Add the others (Frontend, Mobile, MCP, Web QA) when there is work for them; add QA and a stage as soon as the product sends, spends or writes live data.

## 1. Prepare the folder (5 minutes)

1. Copy `teamkit` into a new project folder, for example `<projects folder>\<name>`.
2. In the new folder run `git init`, then make the first commit `chore: start from TeamKit`.
3. Find every place to fill in: search the text for `<<` (in VS Code: Ctrl+Shift+F). Required:
   - `CLAUDE.md`: what the project does, the stack, the run and test commands, the critical rules;
   - `docs/delivery/AGENT_RULES.md`: row 20 (the tracker and the issue key), row 12 (is the repository public or private, what counts as personal data), and the "File ownership" table (who owns which folders).
4. The other `<<...>>` in the role addenda (`docs/delivery/roles/`) are filled in by the agents on their first task; you may skip them.
5. Pick a work mode: the file `.claude/work_mode` with one word, `manual` (the default: you work yourself) or `auto` (the agents work almost without you). Start with `manual`.

## 2. Open the Product Manager (3 minutes)

1. Open Claude Code (desktop) in the new folder and name the session `Product`.
2. Paste the first message from `docs/team/START_PROMPTS.md` (the Product row).
3. The Product Manager reads the rules and the roadmap, talks to you about the goal, and calls the CTO when a question is technical. The CTO proposes the tracker and the labels (`by-backend`, `reviewed`, `needs-owner` and so on) and says which agents to open first.

## 3. Open the others (one at a time, 1 minute each)

A new session in the same folder, named as in the table of `START_PROMPTS.md`, with its message pasted in. Each agent tells the CTO "ready" and waits for a task.

Order: Product Manager → Business Analyst → CTO → Backend → Reviewer (when the first risky change appears) → QA (when the first change with an effect needs the stage) → the rest as needed.

## 4. The first task

Tell the Product Manager in plain words what you want first. The Business Analyst does the discovery and writes the task (`Origin:` as the first line, user story, acceptance criteria); the CTO adds the technical part, hands it to the right agent and accepts the result. You get only: a finished result, a problem, or a decision that belongs to you.

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
