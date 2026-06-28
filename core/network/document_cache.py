# -*- coding: utf-8 -*-
"""
ClawRoyale ETag-based local caching system.
Handles 'If-None-Match' to minimize HTTP overhead.
"""

import os
import json
from typing import Dict, Optional

CACHE_DIR = ".cache"
MANIFEST_PATH = os.path.join(CACHE_DIR, "cache_manifest.json")
os.makedirs(CACHE_DIR, exist_ok=True)

class DocumentCacheManager:
    def __init__(self):
        self.manifest: Dict[str, Dict[str, str]] = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(MANIFEST_PATH):
            try:
                with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self) -> None:
        try:
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_etag(self, document_id: str) -> Optional[str]:
        return self.manifest.get(document_id, {}).get("etag")

    def read_cache(self, document_id: str) -> Optional[str]:
        entry = self.manifest.get(document_id)
        if not entry:
            return None
        
        file_path = os.path.join(CACHE_DIR, entry["filename"])
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def update_cache(self, document_id: str, etag: str, content: str) -> None:
        safe_filename = f"{document_id.replace('/', '_').replace(':', '_')}.txt"
        file_path = os.path.join(CACHE_DIR, safe_filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.manifest[document_id] = {
                "etag": etag,
                "filename": safe_filename
            }
            self._save_manifest()
        except Exception:
            pass