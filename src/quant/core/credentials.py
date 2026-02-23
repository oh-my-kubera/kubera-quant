"""Credential storage utilities."""

from __future__ import annotations

import json
from pathlib import Path

from quant.core.config import quant_dir


def credentials_path() -> Path:
    return quant_dir() / "credentials.json"


def load_credentials() -> list[dict]:
    path = credentials_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_credential(credential: dict) -> None:
    credentials = load_credentials()
    provider = credential["provider"]
    credentials = [c for c in credentials if c.get("provider") != provider]
    credentials.append(credential)
    _write_credentials(credentials)


def remove_credential(provider: str) -> bool:
    credentials = load_credentials()
    remaining = [c for c in credentials if c.get("provider") != provider]
    if len(remaining) == len(credentials):
        return False
    _write_credentials(remaining)
    return True


def get_credential(provider: str) -> dict | None:
    for cred in load_credentials():
        if cred.get("provider") == provider:
            return cred
    return None


def _write_credentials(credentials: list[dict]) -> None:
    credentials_path().write_text(json.dumps(credentials, indent=2))
