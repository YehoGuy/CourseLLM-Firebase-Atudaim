# Change: Organize misc files into dedicated folders

## Why
The repo root and `services/material-to-md` contain a mix of docs, logs, and runtime artifacts that make navigation noisy.
Grouping non-code artifacts into dedicated folders improves clarity without breaking runtime behavior.

## What Changes
- Create `misc/` at the repo root and move only generated/log artifacts into it.
- Create `services/material-to-md/docs/` and move docs/spec files into it.
- Keep runtime and config files in place to avoid breaking paths.
- Remove the legacy `materialToMD/` folder if it is no longer in use.

## Impact
- Affected specs: repo layout / project structure.
- Affected code: documentation paths and any references to moved docs.
