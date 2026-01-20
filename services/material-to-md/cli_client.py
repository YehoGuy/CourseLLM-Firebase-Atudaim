"""Interactive CLI client to exercise all File Normalization Service endpoints."""

import base64
import json
import mimetypes
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import shutil

DEFAULT_BASE_URL = os.environ.get("FNS_BASE_URL", "http://localhost:8000")
PROCESSED_ROOT = Path(os.environ.get("STORAGE_ROOT", "./storage")) / os.environ.get("PROCESSED_DIR", "processed")
INCOMING_ROOT = Path(os.environ.get("STORAGE_ROOT", "./storage")) / os.environ.get("INCOMING_DIR", "incoming")
OUTPUT_DIR = Path(os.environ.get("CLI_OUTPUT_DIR", "./cli_outputs"))


def _processed_target(rel: str) -> str:
    return str((PROCESSED_ROOT / Path(rel)).with_suffix(".md"))


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _client() -> httpx.Client:
    return httpx.Client(timeout=30)


def _base_url() -> str:
    return os.environ.get("FNS_BASE_URL", DEFAULT_BASE_URL)


def _prompt(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def _verify_hint(title: str, steps: list[str], output_path: Optional[str] = None) -> None:
    print(f"\nVerification steps for {title}:")
    for idx, step in enumerate(steps, start=1):
        print(f"  {idx}. {step}")
    if output_path:
        print(f"  → Output path: {output_path}")
    print("")


def _summarize_job(job: Dict[str, Any]) -> str:
    return (
        f"id={job.get('id')} status={job.get('status')} retries={job.get('retry_count')} "
        f"source={job.get('source_path')} updated_at={job.get('updated_at')}"
    )


def _summarize_jobs(jobs: list[Dict[str, Any]]) -> None:
    for job in jobs:
        print(" - " + _summarize_job(job))


def _write_markdown_with_assets(basename: str, markdown: str, assets: list[Dict[str, Any]]) -> tuple[Path, Path]:
    """
    Save markdown plus any assets to a dedicated folder inside OUTPUT_DIR.

    Returns (markdown_path, asset_root).
    """
    run_root = OUTPUT_DIR / Path(basename).stem
    run_root.mkdir(parents=True, exist_ok=True)
    md_path = run_root / basename
    md_path.write_text(markdown, encoding="utf-8")
    asset_root = run_root
    if assets:
        for asset in assets:
            rel_path = Path(asset.get("path", "assets/unnamed"))
            target = run_root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            data_b64 = asset.get("data_base64", "")
            try:
                target.write_bytes(base64.b64decode(data_b64))
            except Exception:
                continue
            # keep relative paths in markdown as-is; they point to assets/...
    return md_path, asset_root


def _stage_source_into_incoming(path_input: str) -> str:
    """
    Ensure the provided file is placed under incoming/. Returns the relative path.
    If the path already looks relative (and not present locally), we just pass it through.
    """
    INCOMING_ROOT.mkdir(parents=True, exist_ok=True)
    candidate = Path(path_input)
    if candidate.is_file():
        dest = INCOMING_ROOT / candidate.name
        shutil.copyfile(candidate, dest)
        return str(dest.relative_to(INCOMING_ROOT))
    # If it already exists under incoming, use it; otherwise fail fast with guidance.
    rel = path_input.lstrip("./")
    if (INCOMING_ROOT / rel).is_file():
        return rel
    sys.exit(f"Source file not found locally or under incoming: {path_input}\n"
             f"Place the file in {INCOMING_ROOT} or provide a local path to stage.")


def do_convert() -> None:
    base = _base_url()
    path = _prompt("Path to file for /convert")
    if not os.path.isfile(path):
        sys.exit(f"File not found: {path}")
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    with open(path, "rb") as fh, _client() as client:
        resp = client.post(f"{base}/convert", files={"file": (filename, fh, content_type)})
        resp.raise_for_status()
        data = resp.json()
        markdown = data.get("markdown", "")
        assets = data.get("assets", [])
        preview = markdown[:400].replace("\n", " ") + ("..." if len(markdown) > 400 else "")
        saved_path, asset_root = _write_markdown_with_assets(Path(filename).with_suffix(".md").name, markdown, assets)
        print("\n[convert] Success")
        print(f" - Markdown length: {len(markdown)} chars")
        print(f" - Assets: {len(assets)} file(s)")
        print(f" - Preview: {preview}")
        print(f" - Saved markdown: {saved_path}")
        if assets:
            print(f" - Saved assets under: {asset_root}")
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(data)
        _verify_hint(
            "/convert",
            [
                "Confirm status 200 and that markdown text includes expected structure.",
                "If there are assets, base64-decode one to confirm image rendering.",
                "Open the saved markdown file to visually inspect headings, lists, RTL text, and images.",
            ],
            output_path=f"{saved_path} (assets under {asset_root})",
        )


def do_ingest() -> None:
    base = _base_url()
    user_path = _prompt("Relative source_path in incoming/ (or local file path to stage)")
    rel = _stage_source_into_incoming(user_path)
    staged_path = INCOMING_ROOT / rel
    with _client() as client:
        resp = client.post(f"{base}/v1/ingest", json={"source_path": rel})
        resp.raise_for_status()
        data = resp.json()
        target_path = _processed_target(rel)
        print("\n[ingest] Accepted")
        print(f" - Job: {_summarize_job(data)}")
        print(f" - Staged source: {staged_path}")
        print(f" - Expected output: {target_path}")
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(data)
        _verify_hint(
            "/v1/ingest",
            [
                "Check returned job id and status=QUEUED.",
                "Call 'jobs' menu option to watch it reach COMPLETED.",
                f"Inspect processed markdown at {target_path}.",
            ],
            output_path=f"Processed: {target_path} | Staged source: {staged_path}",
        )


def do_trigger_scan() -> None:
    base = _base_url()
    with _client() as client:
        resp = client.post(f"{base}/v1/trigger-scan")
        resp.raise_for_status()
        queued = resp.json().get("queued")
        print("\n[trigger-scan] Completed")
        print(f" - Files enqueued: {queued}")
        print(f" - Scanned folder: {INCOMING_ROOT}")
        _verify_hint(
            "/v1/trigger-scan",
            [
                "Ensure incoming/ has at least one file before triggering.",
                "After call, run 'jobs' to confirm new items appear.",
                "Wait for completion and verify processed markdown output exists.",
            ],
            output_path=f"{PROCESSED_ROOT}/<source>.md for each processed file",
        )


def do_stats() -> None:
    base = _base_url()
    with _client() as client:
        resp = client.get(f"{base}/v1/admin/stats")
        resp.raise_for_status()
        stats = resp.json()
        print("\n[stats]")
        for key in ["queued", "processing", "completed", "failed"]:
            print(f" - {key}: {stats.get(key, 0)}")
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(stats)
        _verify_hint(
            "/v1/admin/stats",
            [
                "Counts should reflect expected totals (queued/processing/completed/failed).",
                "Submit a new ingest and re-run stats to observe queued increment.",
                "Force a failure (bad file) and ensure failed count increments.",
            ],
            output_path=f"{PROCESSED_ROOT}/<source>.md (COMPLETED) or <storage_root>/failed_conversions/ (FAILED)",
        )


def do_jobs() -> None:
    base = _base_url()
    status = _prompt("Filter by status (QUEUED/PROCESSING/COMPLETED/FAILED, empty for all)", "")
    start = _prompt("Start timestamp (ISO8601, optional)", "")
    end = _prompt("End timestamp (ISO8601, optional)", "")
    params: Dict[str, str] = {}
    if status:
        params["status"] = status
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    with _client() as client:
        resp = client.get(f"{base}/v1/admin/jobs", params=params)
        resp.raise_for_status()
        jobs = resp.json()
        print(f"\n[jobs] count={len(jobs)}")
        if jobs:
            _summarize_jobs(jobs)
            sample = jobs[0]
            if sample.get("processed_path"):
                print(f" - sample processed_path: {sample.get('processed_path')}")
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(jobs)
        _verify_hint(
            "/v1/admin/jobs",
            [
                "Verify jobs reflect expected states after ingests/scans.",
                "Check retry_count/error_message for failed jobs.",
                "Cross-check processed_path points to generated markdown files.",
            ],
            output_path="See processed_path field (typically under processed/)",
        )


def do_job() -> None:
    base = _base_url()
    job_id = _prompt("Job id")
    with _client() as client:
        resp = client.get(f"{base}/v1/admin/jobs/{job_id}")
        resp.raise_for_status()
        job = resp.json()
        print(f"\n[job] id={job_id}")
        print(" - " + _summarize_job(job))
        if job.get("processed_path"):
            print(f" - processed_path: {job.get('processed_path')}")
        if job.get("error_message"):
            print(f" - error: {job.get('error_message')}")
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(job)
        _verify_hint(
            "/v1/admin/jobs/{id}",
            [
                "Ensure job status matches expectations (COMPLETED/FAILED/etc.).",
                "If failed, read error_message and inspect failed_conversions/ directory.",
                "If completed, open processed markdown referenced by processed_path.",
            ],
            output_path="processed_path from response (typically under processed/)",
        )


def do_journal() -> None:
    base = _base_url()
    since = _prompt("Since timestamp (ISO8601, e.g., 2024-01-01T00:00:00Z)")
    try:
        datetime.fromisoformat(since.replace("Z", "+00:00"))
    except ValueError:
        sys.exit("Invalid ISO8601 timestamp for --since")
    with _client() as client:
        resp = client.get(f"{base}/v1/journal/sync", params={"since": since})
        resp.raise_for_status()
        entries = resp.json()
        print(f"\n[journal] count={len(entries)}")
        if entries:
            _summarize_jobs(entries)
        if _prompt("Show full JSON? (y/N)", "N").lower() == "y":
            _print_json(entries)
        _verify_hint(
            "/v1/journal/sync",
            [
                "Confirm entries include updates after the provided timestamp.",
                "Check is_deleted flags to align with removed sources.",
                "Download referenced processed files to confirm availability for downstream sync.",
            ],
            output_path=f"{PROCESSED_ROOT}/<source>.md (and is_deleted flags)",
        )


MENU_OPTIONS = {
    "1": ("Convert (sync)", do_convert),
    "2": ("Ingest (async)", do_ingest),
    "3": ("Trigger scan", do_trigger_scan),
    "4": ("Admin stats", do_stats),
    "5": ("List jobs", do_jobs),
    "6": ("Get job by id", do_job),
    "7": ("Journal sync", do_journal),
    "q": ("Quit", None),
}


def main(argv: Optional[list[str]] = None) -> None:
    print("File Normalization Service CLI")
    print(f"Base URL: {_base_url()}")
    print(f"Incoming dir: {INCOMING_ROOT}")
    print(f"Processed dir: {PROCESSED_ROOT}")
    print(f"CLI output dir: {OUTPUT_DIR}")
    while True:
        print("\nSelect an action:")
        for key, (label, _) in MENU_OPTIONS.items():
            print(f"  {key}) {label}")
        choice = input("> ").strip().lower()
        if choice == "q":
            print("Bye.")
            return
        action = MENU_OPTIONS.get(choice)
        if not action:
            print("Invalid choice, try again.")
            continue
        _, func = action
        try:
            func()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error {exc.response.status_code}: {exc.response.text}")
        except httpx.HTTPError as exc:
            print(f"Request failed: {exc}")
        except SystemExit as exc:
            print(str(exc))


if __name__ == "__main__":
    main()
