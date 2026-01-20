## ADDED Requirements
### Requirement: Services Folder Layout
The repository SHALL organize backend services under a top-level `services/` directory, with each service in its own subfolder.

#### Scenario: Backend services are discoverable
- **WHEN** a developer browses the repo root
- **THEN** backend services are found under `services/` and not mixed with frontend source

### Requirement: Path References Updated
Configuration and documentation SHALL reference the new service paths to preserve workflows.

#### Scenario: Emulator config points to new functions source
- **WHEN** Firebase emulators start
- **THEN** the functions source path resolves under `services/firebase-functions`
