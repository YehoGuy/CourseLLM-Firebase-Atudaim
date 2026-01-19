# File Normalization Service (FNS) – Developer Guide

This guide walks you through the project structure, local setup, and how to exercise the API via the interactive CLI client. It is designed for new contributors to get productive quickly.

---

## Project Structure

- `app.py` — FastAPI application wiring the REST endpoints.
- `Converter.py` — Converters for PDF/DOCX/PPTX/CSV/XLSX/HTML/TXT to Markdown with asset extraction.
- `jobs.py` — In-process job manager: queue, workers, retries/backoff, scheduler scan.
- `storage.py` — Local filesystem storage for incoming/processed/failed files.
- `models.py` — SQLAlchemy models and job statuses.
- `db.py` — Database engine/session helpers and metadata initialization.
- `settings.py` — Configuration (env-driven) for paths, concurrency, retries, polling.
- `cli.py` — Interactive CLI client to drive and verify every endpoint.
- `openapi.yaml` — OpenAPI 3.1 specification of the API surface.
- `tests/` — Pytest suites for converters and pipeline behavior.
- `storage/` — Default local storage root (created on first run):
  - `incoming/` — Source files to be processed.
  - `processed/` — Generated Markdown outputs.
  - `failed_conversions/` — Sources moved here after retries are exhausted.
- `cli_outputs/` — CLI-saved Markdown and assets from synchronous `/convert` calls.

---

## Configuration

Environment variables (defaults shown):

- `DB_URL=sqlite:///./fns.db`
- `STORAGE_ROOT=./storage`
- `INCOMING_DIR=incoming`
- `PROCESSED_DIR=processed`
- `FAILED_DIR=failed_conversions`
- `MAX_CONCURRENT_JOBS=4`
- `MAX_RETRIES=3`
- `RETRY_BACKOFF_FACTOR=2.0`
- `RETRY_INITIAL_DELAY=1.0`
- `POLLING_INTERVAL=300`
- `ENABLE_SCHEDULER=true`
- `CLI_OUTPUT_DIR=./cli_outputs`
- `FNS_BASE_URL=http://localhost:8000`

---

## Running the Service Locally

1) **Install dependencies**
```bash
pip install -r requirements.txt
```

2) **Start the FastAPI server**
```bash
uvicorn app:app --reload
```

The service will create `storage/` (incoming/processed/failed) and the SQLite DB on first run.

3) **Verify health**
Open `http://localhost:8000/docs` to view the auto-generated docs, or use the CLI client (below).

---

## Using the Interactive CLI Client

Launch the menu-driven client:
```bash
python cli_client.py   or   python3 cli_client.py
```
On startup it prints the active paths:
- Base URL (from `FNS_BASE_URL`)
- Incoming dir (where sources must live)
- Processed dir (where Markdown outputs land)
- CLI output dir (where `/convert` saves markdown + assets)

### Menu Actions

1. **Convert (sync)** — Calls `/convert` with a local file, saves Markdown and assets under `cli_outputs/<name>/`.
   - Prompt: file path.
   - Output: `cli_outputs/<stem>/<stem>.md` and `cli_outputs/<stem>/assets/...`.
2. **Ingest (async)** — Stages a local file into `storage/incoming/` and enqueues `/v1/ingest`.
   - Prompt: local path or relative path already under `incoming/`.
   - Output: Markdown under `storage/processed/<name>.md` after workers finish.
3. **Trigger scan** — Calls `/v1/trigger-scan` to enqueue anything under `incoming/` that lacks jobs or outputs.
4. **Admin stats** — Shows counts for queued/processing/completed/failed.
5. **List jobs** — Lists jobs with optional status/time filters; shows sample `processed_path`.
6. **Get job by id** — Retrieves a single job, including `processed_path` or `error_message`.
7. **Journal sync** — Fetches jobs updated since a given timestamp (for downstream sync).

### Staging Sources Automatically

For ingest, if you provide a local file path, the CLI copies it into `storage/incoming/` before calling the API. If you provide a relative path, it must already exist under `storage/incoming/`.

### Viewing Outputs

- **Synchronous convert**: Open `cli_outputs/<stem>/<stem>.md` in your editor or browser; images live in `cli_outputs/<stem>/assets/...`.
- **Async ingest/scan**: Open `storage/processed/<name>.md`; failed sources land in `storage/failed_conversions/`.

---

## Typical Workflows

**Quick one-off conversion**
1. `python cli.py` → `1` (Convert)
2. Provide local path to a document.
3. Open `cli_outputs/<stem>/<stem>.md` to review markdown and images.

**Full async pipeline**
1. Drop files into `storage/incoming/` (or use CLI option 2 with a local path).
2. `python cli.py` → `2` (Ingest) or `3` (Trigger scan).
3. `python cli.py` → `5` (List jobs) to watch statuses; `4` (Stats) for counts.
4. Open `storage/processed/<name>.md` to verify outputs; check `failed_conversions/` for exhausted retries.

**Downstream sync**
1. `python cli.py` → `7` (Journal sync) with an ISO8601 timestamp to fetch updates.
2. Use `processed_path` or `source_path` + `processed_dir` to locate markdown files; honor `is_deleted` flags.

---

## Troubleshooting

- **404 on ingest**: The CLI now stages local files automatically. If you see a 404, ensure the file exists locally or already resides under `storage/incoming/`.
- **Images not rendering**: For `/convert`, ensure you open the saved markdown alongside its `assets/` folder in `cli_outputs/<stem>/`. For async jobs, verify `storage/processed/<name>_img*.png` exists.
- **Black images from PDFs**: The converter flattens alpha and normalizes CMYK to RGB; if issues persist, re-run conversion to regenerate assets.
- **No output after trigger-scan**: Confirm the file is under `storage/incoming/` and there isn’t already a fresh `.md` in `processed/`. The scheduler re-queues missing outputs automatically.
- **Change configuration**: Override env vars (e.g., `export STORAGE_ROOT=/tmp/fns`) before starting the server/CLI.

---

## Commands Cheat Sheet

- Start server: `uvicorn app:app --reload`
- Run all tests: `pytest -q`
- Start CLI: `python cli.py`
- Open OpenAPI: `cat openapi.yaml` or browse `http://localhost:8000/docs`

---

Happy normalizing!
