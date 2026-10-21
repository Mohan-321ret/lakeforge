"""Prompt cache using SQLite for response caching."""

import hashlib
import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class PromptCache:
    """SQLite-backed cache for LLM responses."""

    def __init__(self, cache_path: Optional[str | Path] = None):
        """
        Initialize prompt cache.

        Args:
            cache_path: Path to SQLite cache file
                       (default: ~/.lakeforge/cache.db)
        """
        if cache_path is None:
            cache_path = Path.home() / ".lakeforge" / "cache.db"
        else:
            cache_path = Path(cache_path)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path = cache_path

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_cache (
                    key TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created ON prompt_cache(created_at)"
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """Hash prompt for cache key."""
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[dict]:
        """
        Get cached response for prompt.

        Args:
            prompt: Input prompt

        Returns:
            Cached response dict or None if not found/expired
        """
        key = self._hash_prompt(prompt)

        conn = sqlite3.connect(self.cache_path)
        try:
            cursor = conn.execute(
                """
                SELECT response, model FROM prompt_cache
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                """,
                (key, datetime.now()),
            )
            row = cursor.fetchone()

            if row:
                response_json, model = row
                try:
                    return json.loads(response_json)
                except json.JSONDecodeError:
                    return None

            return None
        finally:
            conn.close()

    def set(
        self,
        prompt: str,
        response: dict,
        model: str = "",
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Cache a response.

        Args:
            prompt: Input prompt
            response: Response dict (will be JSON serialized)
            model: Model used for this response
            ttl_seconds: Time-to-live in seconds (None = never expire)
        """
        key = self._hash_prompt(prompt)
        response_json = json.dumps(response)

        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO prompt_cache
                (key, prompt, response, model, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, prompt, response_json, model, expires_at),
            )
            conn.commit()
        finally:
            conn.close()

    def clear(self) -> None:
        """Clear all cached entries."""
        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute("DELETE FROM prompt_cache")
            conn.commit()
        finally:
            conn.close()

    def clear_expired(self) -> None:
        """Remove expired entries."""
        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute(
                "DELETE FROM prompt_cache WHERE expires_at < ?",
                (datetime.now(),),
            )
            conn.commit()
        finally:
            conn.close()

    def size(self) -> int:
        """Get number of cached entries."""
        conn = sqlite3.connect(self.cache_path)
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM prompt_cache")
            return cursor.fetchone()[0]
        finally:
            conn.close()
