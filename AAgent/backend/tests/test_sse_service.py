"""
测试: SSE Service - 实时推送服务
测试SSE连接管理和事件广播
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.sse_service import (
    SSEManager,
    sse_manager,
    broadcast_message,
    broadcast_consensus,
    broadcast_complete,
    broadcast_error
)


class TestSSEManager:
    """测试SSE管理器"""
    
    def test_sse_manager_initialization(self):
        """测试：SSE管理器初始化"""
        manager = SSEManager()
        assert manager.connections == {}
    
    @pytest.mark.asyncio
    async def test_add_connection(self):
        """测试：添加连接"""
        manager = SSEManager()
        queue = asyncio.Queue()
        
        manager.add_connection(1, queue)
        
        assert 1 in manager.connections
        assert queue in manager.connections[1]
    
    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """测试：移除连接"""
        manager = SSEManager()
        queue = asyncio.Queue()
        
        manager.add_connection(1, queue)
        manager.remove_connection(1, queue)
        
        assert 1 not in manager.connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_connected_clients(self):
        """测试：向连接的客户端广播"""
        manager = SSEManager()
        queue1 = asyncio.Queue()
        queue2 = asyncio.Queue()
        
        manager.add_connection(1, queue1)
        manager.add_connection(1, queue2)
        
        await manager.broadcast(1, "test_event", {"data": "test"})
        
        # 验证两个队列都收到消息
        msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        
        assert msg1["event"] == "test_event"
        assert msg2["event"] == "test_event"
        assert msg1["data"]["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_broadcast_to_no_connections(self):
        """测试：广播到没有连接的讨论"""
        manager = SSEManager()
        
        # 不应抛出异常
        await manager.broadcast(999, "test_event", {"data": "test"})


class TestSSEBroadcastFunctions:
    """测试SSE广播函数"""
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """测试：广播消息事件"""
        # 清理全局管理器
        sse_manager.connections.clear()
        
        queue = asyncio.Queue()
        sse_manager.add_connection(1, queue)
        
        await broadcast_message(1, {
            "participant": {"name": "测试"},
            "content": "测试内容"
        })
        
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg["event"] == "message"
    
    @pytest.mark.asyncio
    async def test_broadcast_consensus(self):
        """测试：广播共识事件"""
        sse_manager.connections.clear()
        
        queue = asyncio.Queue()
        sse_manager.add_connection(2, queue)
        
        await broadcast_consensus(2, {
            "summary": "测试共识",
            "keyPoints": ["要点1"]
        })
        
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg["event"] == "consensus"
    
    @pytest.mark.asyncio
    async def test_broadcast_complete(self):
        """测试：广播完成事件"""
        sse_manager.connections.clear()
        
        queue = asyncio.Queue()
        sse_manager.add_connection(3, queue)
        
        await broadcast_complete(3, {
            "status": "completed",
            "totalMessages": 10
        })
        
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg["event"] == "complete"
    
    @pytest.mark.asyncio
    async def test_broadcast_error(self):
        """测试：广播错误事件"""
        sse_manager.connections.clear()
        
        queue = asyncio.Queue()
        sse_manager.add_connection(4, queue)
        
        await broadcast_error(4, {
            "message": "错误信息"
        })
        
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg["event"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
