"""
数据库模块 - SQLite异步操作
"""

import aiosqlite
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "database.sqlite")


async def _ensure_schema(db: aiosqlite.Connection):
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='discussions'"
    )
    table_exists = await cursor.fetchone()
    if not table_exists:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            await db.executescript(schema_sql)
            await db.commit()


async def init_database():
    """应用启动时建表"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await _ensure_schema(db)


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    FastAPI Depends 依赖：每个请求获得独立连接，请求结束后自动关闭。
    用法：db: aiosqlite.Connection = Depends(get_db)
    """
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()


@asynccontextmanager
async def open_db():
    """
    在非路由上下文（后台任务）中使用，支持 async with：
        async with open_db() as db:
            ...
    """
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()


async def close_database():
    """应用关闭钩子（无全局连接，无需操作）"""
    pass
