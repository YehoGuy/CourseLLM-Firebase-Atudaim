## Context
The current repository places multiple backends (FastAPI service and Firebase Functions)
alongside the Next.js app at the root. This obscures ownership boundaries and makes
it harder to understand how services relate.

## Goals / Non-Goals
- Goals:
  - Group backend services under a single `services/` folder.
  - Preserve runtime behavior and developer commands.
  - Keep the Next.js app in place to avoid breaking framework assumptions.
- Non-Goals:
  - Changing app behavior or APIs.
  - Introducing a new monorepo build system.

## Decisions
- Decision: Create `services/material-to-md` and `services/firebase-functions` and move the
  existing folders into them.
  - Why: Keeps backend code grouped while minimizing build/tooling changes.
- Decision: Update references in `firebase.json` and docs to new paths.
  - Why: Prevents regressions in emulator and developer workflows.

## Risks / Trade-offs
- Risk: Path changes can break scripts or documentation.
  - Mitigation: Search for references and update them in the same change.
- Risk: Developer muscle memory for paths.
  - Mitigation: Update README and add architecture.txt for quick discovery.

## Migration Plan
1. Move folders into `services/`.
2. Update configuration and docs to match the new locations.
3. Regenerate `architecture.txt`.

## Open Questions
- None.
