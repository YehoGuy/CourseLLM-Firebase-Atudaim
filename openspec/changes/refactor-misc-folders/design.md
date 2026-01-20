## Context
The repository currently mixes generated artifacts, logs, and documentation with primary source code in the root and service folders.
This makes navigation noisy and increases the chance of accidentally committing artifacts.

## Goals / Non-Goals
- Goals:
  - Move non-code artifacts into dedicated folders.
  - Keep runtime behavior unchanged by avoiding moves of config/runtime files.
- Non-Goals:
  - Any functional or API changes.
  - Renaming or restructuring core source code directories.

## Decisions
- Decision: Use `misc/` at the repo root for logs and generated artifacts.
- Decision: Use `services/material-to-md/docs/` for service documentation/spec files.

## Risks / Trade-offs
- Risk: Some documentation references may break.
  - Mitigation: Update README/guides in the same change.

## Migration Plan
1. Move the non-code artifacts into `misc/` and service docs into `services/material-to-md/docs/`.
2. Update any references.
3. Update `architecture.txt`.
