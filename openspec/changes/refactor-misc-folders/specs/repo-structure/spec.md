## ADDED Requirements
### Requirement: Misc Folder for Artifacts
The repository SHALL collect non-code artifacts (logs and generated files) under a top-level `misc/` folder.

#### Scenario: Root is decluttered
- **WHEN** a developer browses the repo root
- **THEN** transient artifacts are found under `misc/` rather than mixed with source

### Requirement: Service Docs Folder
`services/material-to-md` SHALL store documentation assets under `services/material-to-md/docs/`.

#### Scenario: Service docs are discoverable
- **WHEN** a developer looks for Material-to-MD docs
- **THEN** they are located under `services/material-to-md/docs/`
