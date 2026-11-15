# Updating projects built from TeamKit

**Status:** decided by the owner on 2026-10-31; not built yet. Build it with the first real update (methodology v2).

## Rule
- `docs/team/` (common rules and role briefs) is never edited per project, so an update replaces it whole.
- `docs/delivery/` and `CLAUDE.md` belong to the project. An update never overwrites them; it lists what to add by hand.

## Mechanism
1. **Version stamp.** Each project keeps `.teamkit-version`: the TeamKit version it was built from or last updated to. TeamKit's own version is `TEMPLATE_VERSION`.
2. **TeamKit changelog.** Each version says what changed and what a project must do: rows to add to an addendum, renamed roles, new rule numbers.
3. **`tools/update_project.py <project>`**:
   - compares the two versions;
   - replaces `docs/team/` whole;
   - prints the manual steps for `docs/delivery/` and `CLAUDE.md` from the changelog;
   - when a project has edited `docs/team/` anyway, shows the diff and stops without overwriting anything;
   - makes one commit, "chore: update TeamKit A → B".
4. **Who runs it:** the project's CTO, on the owner's word, as a backlog item.

## Not chosen
- **A git submodule or subtree for `docs/team/`.** It confuses agents, and the project stops being self-contained.
- **Agents reading rules straight from the TeamKit folder.** The project breaks on another machine, and every TeamKit edit hits all projects unchecked.
