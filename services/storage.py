from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_json_atomic(path: str | Path, data: Any, indent: int = 2) -> None:
    """
    Atomic JSON write:
    - Writes to a temp file in the same directory
    - fsync
    - os.replace to final path (atomic on same filesystem)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")

    payload = json.dumps(data, ensure_ascii=False, indent=indent)
    payload += "\n"

    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_path, path)
