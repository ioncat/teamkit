---
name: update
description: Compare this project's TeamKit version with the installed TeamKit and list what must change. Read-only.
disable-model-invocation: true
---

# TeamKit: what does this project need to be brought up to date? (read-only)

You change no file. Talk to the owner in his language.

1. Read `project.yaml` in the current folder: its `template_version` is the TeamKit version the project was built from. If the file is missing, say that this project was not built by TeamKit and stop.
2. Read `${CLAUDE_PLUGIN_ROOT}/TEMPLATE_VERSION`: the installed TeamKit version. If both are equal, say the project is up to date and stop.
3. Read `${CLAUDE_PLUGIN_ROOT}/TEAMKIT_CHANGELOG.md`: the sections of every version newer than the project's. Read `${CLAUDE_PLUGIN_ROOT}/docs/update-mechanism.md` for the rule: `docs/team/` is replaced whole, `docs/delivery/` and `CLAUDE.md` belong to the project and are changed by hand.
4. Report in a short list: what changed in `docs/team/`; the manual steps for `docs/delivery/` and `CLAUDE.md`; anything that needs an answer from the owner.
5. Say that the automatic updater (`tools/update_project.py`) is not built yet, so the steps are done by hand on the owner's word, as one commit "chore: update TeamKit A to B".
