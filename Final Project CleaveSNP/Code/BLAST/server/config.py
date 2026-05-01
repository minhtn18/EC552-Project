from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).parent.parent / "server_config.json"

# Local constant — do NOT import from paths.py to avoid circular imports.
# This is the BLAST/ folder: the project's backend root.
_BLAST_ROOT = Path(__file__).parent.parent

_DEFAULTS: Dict[str, Any] = {
    "blast_bin": "",
    "db_name": "gene_db",
}

NOT_CONFIGURED_DETAIL = (
    "BLAST is not configured. "
    "Please go to Settings and provide the path to your BLAST bin folder."
)


def load_config() -> Dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {**_DEFAULTS, **data}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def save_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    # Only blast_bin is user-provided — workdir and db_name are always computed.
    allowed = {"blast_bin"}
    current = load_config()
    current.update({k: v for k, v in updates.items() if k in allowed and v is not None})
    CONFIG_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return get_settings()


def is_configured() -> bool:
    return bool(load_config().get("blast_bin", "").strip())


def get_settings() -> Dict[str, Any]:
    cfg = load_config()

    # workdir is always the BLAST root — never trust whatever is in the JSON.
    cfg["workdir"] = str(_BLAST_ROOT)

    # db_name must be absolute to avoid BLAST truncating paths that contain spaces
    # (e.g. C:\Program Files\... gets cut at the first space on Windows).
    db_raw = cfg.get("db_name", "gene_db")
    db_path = Path(db_raw)
    cfg["db_name"] = str(db_path if db_path.is_absolute() else _BLAST_ROOT / db_raw)

    cfg["configured"] = bool(cfg.get("blast_bin", "").strip())
    return cfg
