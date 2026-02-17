"""Database management for usage tracking and conversation storage."""

import aiosqlite
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class Database:
    """SQLite database for storing usage stats and conversations."""

    def __init__(self, db_path: str = "./data/models.db"):
        self.db_path = db_path

    async def initialize(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Usage statistics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # API keys table (encrypted in production)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    provider TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Model preferences table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    preferred_model TEXT NOT NULL,
                    fallback_models TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            await db.commit()

    async def log_usage(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost: float,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log usage statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO usage_stats 
                (model, provider, input_tokens, output_tokens, total_tokens, cost, latency_ms, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model,
                    provider,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cost,
                    latency_ms,
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            await db.commit()

    async def get_usage_stats(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get usage statistics with optional filters."""
        query = "SELECT * FROM usage_stats WHERE 1=1"
        params = []

        if model:
            query += " AND model = ?"
            params.append(model)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_aggregated_stats(
        self, group_by: str = "model"
    ) -> List[Dict[str, Any]]:
        """Get aggregated usage statistics."""
        query = f"""
            SELECT 
                {group_by},
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(cost) as total_cost,
                AVG(latency_ms) as avg_latency_ms,
                MAX(timestamp) as last_used
            FROM usage_stats
            GROUP BY {group_by}
            ORDER BY total_requests DESC
        """

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def save_conversation(
        self,
        conversation_id: str,
        title: str,
        model: str,
        provider: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save or update a conversation."""
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Check if conversation exists
            async with db.execute(
                "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute(
                    """
                    UPDATE conversations 
                    SET title = ?, model = ?, provider = ?, messages = ?, updated_at = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (
                        title,
                        model,
                        provider,
                        json.dumps(messages),
                        now,
                        json.dumps(metadata) if metadata else None,
                        conversation_id,
                    ),
                )
            else:
                await db.execute(
                    """
                    INSERT INTO conversations 
                    (id, title, model, provider, messages, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        title,
                        model,
                        provider,
                        json.dumps(messages),
                        now,
                        now,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
            await db.commit()

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    conv = dict(row)
                    conv["messages"] = json.loads(conv["messages"])
                    if conv["metadata"]:
                        conv["metadata"] = json.loads(conv["metadata"])
                    return conv
                return None

    async def list_conversations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, title, model, provider, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
            return True

    async def store_api_key(self, provider: str, api_key: str) -> None:
        """Store an API key (should be encrypted in production)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO api_keys (provider, api_key, updated_at)
                VALUES (?, ?, ?)
                """,
                (provider, api_key, datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get an API key for a provider."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT api_key FROM api_keys WHERE provider = ?", (provider,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

# Made with Bob
