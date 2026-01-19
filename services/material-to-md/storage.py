import base64
import shutil
from pathlib import Path
from typing import Iterable, List

from settings import Settings


class LocalStorageBackend:
    """
    Simple local filesystem storage backend that stores incoming, processed,
    and failed files under a common root.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = Path(settings.storage_root)
        self.incoming = self.root / settings.incoming_dir
        self.processed = self.root / settings.processed_dir
        self.failed = self.root / settings.failed_dir

    def ensure_dirs(self) -> None:
        for path in (self.incoming, self.processed, self.failed):
            path.mkdir(parents=True, exist_ok=True)

    def read_source(self, source_path: str) -> bytes:
        path = self.incoming / source_path
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        return path.read_bytes()

    def list_incoming_files(self) -> Iterable[str]:
        for path in self.incoming.rglob("*"):
            if path.is_file():
                yield str(path.relative_to(self.incoming))

    def write_processed(self, source_path: str, markdown: str, assets: List) -> str:
        dest_relative = Path(source_path).with_suffix(".md")
        dest_path = self.processed / dest_relative
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(markdown, encoding="utf-8")

        for asset in assets:
            asset_path = dest_path.parent / asset.path
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_bytes = base64.b64decode(asset.data_base64)
            asset_path.write_bytes(asset_bytes)

        return str(dest_path)

    def move_to_failed(self, source_path: str) -> str:
        src = self.incoming / source_path
        dest = self.failed / source_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.move(src, dest)
        return str(dest)

    def source_exists(self, source_path: str) -> bool:
        return (self.incoming / source_path).exists()

    def processed_exists(self, source_path: str) -> bool:
        dest_relative = Path(source_path).with_suffix(".md")
        return (self.processed / dest_relative).exists()
