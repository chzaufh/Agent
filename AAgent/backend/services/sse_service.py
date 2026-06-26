"""
SSE Service - Server-Sent Events服务
实时推送服务
Python版本
"""

import json
import logging
from typing import Dict, Set
from sse_starlette.sse import EventSourceResponse
import asyncio

logger = logging.getLogger(__name__)


class SSEManager:
    """SSE连接管理器"""
    
    def __init__(self):
        # 存储所有活跃的SSE连接 {discussion_id: Set[queue]}
        self.connections: Dict[int, Set[asyncio.Queue]] = {}
    
    def add_connection(self, discussion_id: int, queue: asyncio.Queue):
        """添加SSE连接"""
        if discussion_id not in self.connections:
            self.connections[discussion_id] = set()
        
        self.connections[discussion_id].add(queue)
        logger.info(f"[SSE] 新连接加入讨论 #{discussion_id}，当前连接数: {len(self.connections[discussion_id])}")
    
    def remove_connection(self, discussion_id: int, queue: asyncio.Queue):
        """移除SSE连接"""
        if discussion_id in self.connections:
            self.connections[discussion_id].discard(queue)
            
            if len(self.connections[discussion_id]) == 0:
                del self.connections[discussion_id]
            
            logger.info(f"[SSE] 连接断开讨论 #{discussion_id}，剩余连接数: {len(self.connections.get(discussion_id, []))}")
    
    async def broadcast(self, discussion_id: int, event: str, data: Dict):
        """向指定讨论的所有客户端发送事件"""
        if discussion_id not in self.connections or len(self.connections[discussion_id]) == 0:
            logger.debug(f"[SSE] 讨论 #{discussion_id} 没有活跃连接")
            return
        
        message = {
            "event": event,
            "data": data
        }
        
        success_count = 0
        failed_queues = []
        
        for queue in self.connections[discussion_id]:
            try:
                await queue.put(message)
                success_count += 1
            except Exception as e:
                logger.error(f"[SSE] 发送失败: {e}")
                failed_queues.append(queue)
        
        # 清理失败的连接
        for queue in failed_queues:
            self.connections[discussion_id].discard(queue)
        
        logger.info(f"[SSE] 广播到讨论 #{discussion_id}: {event}，成功: {success_count}/{len(self.connections[discussion_id]) + len(failed_queues)}")


# 创建全局SSE管理器实例
sse_manager = SSEManager()


async def event_generator(discussion_id: int):
    """SSE事件生成器"""
    queue = asyncio.Queue()
    sse_manager.add_connection(discussion_id, queue)
    
    try:
        # 发送连接成功消息
        yield {
            "event": "connected",
            "data": json.dumps({
                "discussionId": discussion_id,
                "message": "连接成功"
            })
        }
        
        # 持续发送事件
        while True:
            try:
                # 等待新事件，超时30秒发送心跳
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                yield {
                    "event": message["event"],
                    "data": json.dumps(message["data"], ensure_ascii=False)
                }
            
            except asyncio.TimeoutError:
                # 发送心跳
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": None})
                }
    
    except asyncio.CancelledError:
        logger.info(f"[SSE] 客户端主动断开连接 #{discussion_id}")
    
    finally:
        sse_manager.remove_connection(discussion_id, queue)


def get_sse_response(discussion_id: int):
    """获取SSE响应对象"""
    return EventSourceResponse(event_generator(discussion_id))


async def broadcast_message(discussion_id: int, message_data: Dict):
    """发送消息事件"""
    await sse_manager.broadcast(discussion_id, "message", message_data)


async def broadcast_consensus(discussion_id: int, consensus_data: Dict):
    """发送共识事件"""
    await sse_manager.broadcast(discussion_id, "consensus", consensus_data)


async def broadcast_complete(discussion_id: int, completion_data: Dict):
    """发送完成事件"""
    await sse_manager.broadcast(discussion_id, "complete", completion_data)


async def broadcast_error(discussion_id: int, error_data: Dict):
    """发送错误事件"""
    await sse_manager.broadcast(discussion_id, "error", error_data)

async def broadcast_status(discussion_id: int, data: Dict):
    """发送专家状态/实时共识等状态事件"""
    await sse_manager.broadcast(discussion_id, "status", data)