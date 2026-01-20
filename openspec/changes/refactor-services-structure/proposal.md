# Change: Refactor repository into services/ structure

## Why
The repo mixes backend services and frontend code at the root, making it harder to navigate and maintain.
Grouping backend services under a shared `services/` folder will make the project easier to understand while preserving existing behavior.

## What Changes
- Move `materialToMD/` into `services/material-to-md/`.
- Move `functions/` into `services/firebase-functions/`.
- Update configuration and documentation paths to the new locations.
- Generate `architecture.txt` showing the new hierarchy.

## Impact
- Affected specs: repo layout / project structure.
- Affected code: `firebase.json`, README, docs, scripts, and any tooling that references moved paths.
