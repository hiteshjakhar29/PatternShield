"""
Simple thread-safe JSON / JSONL file persistence.

Provides two store types:
  JSONStore      — single JSON file (dict/list), rewritten atomically on each save
  JSONLStore     — append-only JSONL file (one JSON object per line)
"""
import json
import os
import threading
from typing import Any, Dict, List, Optional


class JSONStore:
    """Thread-safe read/write wrapper around a single JSON file."""

    def __init__(self, path: str, default: Any = None):
        self.path = path
        self.default = default if default is not None else {}
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def read(self) -> Any:
        with self._lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return self.default

    def write(self, data: Any) -> None:
        with self._lock:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)

    def update(self, updater) -> Any:
        """Read → apply updater function → write atomically."""
        with self._lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = self.default

            data = updater(data)

            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
            return data


class JSONLStore:
    """Thread-safe append-only JSONL file store."""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def append(self, record: Dict) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_all(self) -> List[Dict]:
        with self._lock:
            try:
                records = []
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                return records
            except FileNotFoundError:
                return []

    def count(self) -> int:
        return len(self.read_all())
