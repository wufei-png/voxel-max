# Agent documentation rules

Before changing this repository, read [`docs/README.md`](docs/README.md).

- Treat `docs/current/` as the source of truth for cross-project decisions.
- For subject-specific work, read only that subject's `projects/<subject>/README.md` and the owning identity or pack document it routes to.
- Read `docs/guides/` only for the operation being performed.
- Do not treat any `archive/` directory as current truth. Open archived material only for history, discarded alternatives, or provenance.
- A concept reference is not an approved master. Do not begin pack production until the subject README points to an approved identity spec and master.
- Sticker IDs such as `S01` are local to a pack. Use the subject and pack path when referring to them outside that pack.
- Put subject-specific assets and scripts under the owning project. Put pack-specific scripts under the owning pack. Do not move one-off production logic into the generic Skill.
- If implementation and a current document disagree, report and reconcile the mismatch; do not silently choose archived text.
- When a project decision or phase status changes, update `docs/README.md` and the owning project document in the same change.

The repository Skill at `.agents/skills/animated-sticker-maker/` is manual-only. Do not invoke it from an ordinary image or animation request unless the user explicitly names `$animated-sticker-maker`.
