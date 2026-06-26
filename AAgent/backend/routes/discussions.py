"""
Discussions API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import os
import aiosqlite

from db.database import get_db
from services.moderator import run_discussion
from services.sse_service import get_sse_response

logger = logging.getLogger(__name__)
router = APIRouter()


class Participant(BaseModel):
    name: str
    role: str
    expertise: Optional[str] = ""
    systemPrompt: Optional[str] = ""
    avatarColor: Optional[str] = "#3B82F6"


class CreateDiscussionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    participants: List[Participant] = Field(..., min_items=3, max_items=5)


@router.get("/")
async def get_discussions(
    status: Optional[str] = None,
    limit: int = 20,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        query = """
            SELECT d.*,
                   (SELECT COUNT(*) FROM participants WHERE discussion_id = d.id) as participantCount,
                   (SELECT COUNT(*) FROM messages WHERE discussion_id = d.id) as messageCount
            FROM discussions d
        """
        params = []
        if status:
            query += " WHERE d.status = ?"
            params.append(status)
        query += " ORDER BY d.created_at DESC LIMIT ?"
        params.append(limit)
        cursor = await db.execute(query, params)
        discussions = await cursor.fetchall()
        return {"discussions": [dict(d) for d in discussions], "total": len(discussions)}
    except Exception as e:
        logger.error(f"获取讨论列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{discussion_id}")
async def get_discussion(
    discussion_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        cursor = await db.execute("SELECT * FROM discussions WHERE id = ?", (discussion_id,))
        discussion = await cursor.fetchone()
        if not discussion:
            raise HTTPException(status_code=404, detail="讨论不存在")

        cursor = await db.execute(
            "SELECT * FROM participants WHERE discussion_id = ? ORDER BY order_index",
            (discussion_id,)
        )
        participants = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT * FROM messages WHERE discussion_id = ? ORDER BY round_number, created_at",
            (discussion_id,)
        )
        messages = await cursor.fetchall()

        cursor = await db.execute("SELECT * FROM consensus WHERE discussion_id = ?", (discussion_id,))
        consensus = await cursor.fetchone()

        import json
        consensus_data = None
        if consensus:
            cd = dict(consensus)
            cd["key_points"] = json.loads(cd.get("key_points", "[]"))
            consensus_data = cd

        return {
            "discussion": dict(discussion),
            "participants": [dict(p) for p in participants],
            "messages": [dict(m) for m in messages],
            "consensus": consensus_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取讨论详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
async def create_discussion(
    request: CreateDiscussionRequest,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        cursor = await db.execute(
            "INSERT INTO discussions (title, description, status) VALUES (?, ?, ?)",
            (request.title, request.description, "pending")
        )
        await db.commit()
        discussion_id = cursor.lastrowid

        for index, participant in enumerate(request.participants):
            await db.execute(
                """INSERT INTO participants
                   (discussion_id, name, role, expertise, system_prompt, avatar_color, order_index)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (discussion_id, participant.name, participant.role,
                 participant.expertise, participant.systemPrompt,
                 participant.avatarColor, index)
            )
        await db.commit()

        cursor = await db.execute("SELECT * FROM discussions WHERE id = ?", (discussion_id,))
        discussion = await cursor.fetchone()
        cursor = await db.execute(
            "SELECT * FROM participants WHERE discussion_id = ? ORDER BY order_index",
            (discussion_id,)
        )
        participants = await cursor.fetchall()

        logger.info(f"[API] 创建讨论成功 #{discussion_id}: {request.title}")
        return {
            "discussion": dict(discussion),
            "participants": [dict(p) for p in participants],
            "message": "讨论创建成功"
        }
    except Exception as e:
        logger.error(f"创建讨论失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{discussion_id}/start")
async def start_discussion(
    discussion_id: int,
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        cursor = await db.execute("SELECT * FROM discussions WHERE id = ?", (discussion_id,))
        discussion = await cursor.fetchone()
        if not discussion:
            raise HTTPException(status_code=404, detail="讨论不存在")
        if discussion["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"讨论状态为'{discussion['status']}'，无法启动"
            )

        if not os.getenv("DASHSCOPE_API_KEY"):
            logger.warning("[API] 未配置DASHSCOPE_API_KEY，将使用模拟AI模式")

        logger.info(f"[API] 启动讨论 #{discussion_id}")
        background_tasks.add_task(run_discussion, discussion_id)

        return {
            "status": "running",
            "message": "讨论已启动，请通过SSE接收实时消息",
            "discussionId": discussion_id,
            "sseEndpoint": f"/api/discussions/{discussion_id}/events"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动讨论失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{discussion_id}/events")
async def discussion_events(discussion_id: int):
    logger.info(f"[SSE] 客户端连接到讨论 #{discussion_id}")
    return get_sse_response(discussion_id)


@router.get("/{discussion_id}/status")
async def get_discussion_status(
    discussion_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        cursor = await db.execute(
            "SELECT status, updated_at FROM discussions WHERE id = ?", (discussion_id,)
        )
        discussion = await cursor.fetchone()
        if not discussion:
            raise HTTPException(status_code=404, detail="讨论不存在")
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM messages WHERE discussion_id = ?", (discussion_id,)
        )
        message_count = (await cursor.fetchone())[0]
        return {
            "discussionId": discussion_id,
            "status": discussion["status"],
            "messageCount": message_count,
            "updatedAt": discussion["updated_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取讨论状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{discussion_id}")
async def delete_discussion(
    discussion_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    try:
        cursor = await db.execute(
            "SELECT status FROM discussions WHERE id = ?", (discussion_id,)
        )
        discussion = await cursor.fetchone()
        if not discussion:
            raise HTTPException(status_code=404, detail="讨论不存在")
        if discussion["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"只能删除pending状态的讨论，当前: {discussion['status']}"
            )
        await db.execute("DELETE FROM discussions WHERE id = ?", (discussion_id,))
        await db.commit()
        return {"message": "讨论删除成功", "discussionId": discussion_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除讨论失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
