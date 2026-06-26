"""
测试: Moderator Service - 主持人服务
测试讨论流程控制和管理功能 - 已修复所有问题
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.moderator import Moderator
from db.database import init_database, close_database, get_db


@pytest.fixture(scope="function")
async def test_db():
    """测试数据库fixture"""
    os.environ["DATABASE_PATH"] = ":memory:"
    await init_database()
    yield
    await close_database()


@pytest.fixture
async def sample_discussion(test_db):
    """创建示例讨论 - 返回discussion_id"""
    db = await get_db()
    
    # 创建讨论
    cursor = await db.execute(
        "INSERT INTO discussions (title, description, status) VALUES (?, ?, ?)",
        ("测试讨论", "这是一个测试讨论", "pending")
    )
    await db.commit()
    discussion_id = cursor.lastrowid
    
    # 添加参与者
    participants = [
        ("李明", "技术架构师", "技术专长", "系统提示词", "#3B82F6", 0),
        ("王芳", "产品经理", "产品专长", "系统提示词", "#10B981", 1),
        ("张悦", "UX设计师", "设计专长", "系统提示词", "#F59E0B", 2),
    ]
    
    for name, role, expertise, prompt, color, order in participants:
        await db.execute(
            """INSERT INTO participants 
            (discussion_id, name, role, expertise, system_prompt, avatar_color, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (discussion_id, name, role, expertise, prompt, color, order)
        )
    
    await db.commit()
    
    # 返回ID，不是coroutine
    return discussion_id


class TestModeratorInitialization:
    """测试主持人初始化"""
    
    @pytest.mark.asyncio
    async def test_moderator_creation(self, test_db):
        """测试：创建主持人实例"""
        moderator = Moderator(1)
        
        assert moderator.discussion_id == 1
        assert moderator.is_running is False
        assert moderator.max_rounds == 3
        assert moderator.current_round == 0
    
    @pytest.mark.asyncio
    async def test_moderator_custom_rounds(self, test_db):
        """测试：自定义轮次数"""
        os.environ["MAX_ROUNDS"] = "5"
        moderator = Moderator(1)
        
        assert moderator.max_rounds == 5
        # 恢复默认值
        os.environ["MAX_ROUNDS"] = "3"


class TestModeratorDiscussionFlow:
    """测试主持人讨论流程"""
    
    @pytest.mark.asyncio
    async def test_load_discussion(self, sample_discussion, test_db):
        """测试：加载讨论信息"""
        discussion_id = sample_discussion  # 已经是int，不需要await
        moderator = Moderator(discussion_id)
        discussion = await moderator.load_discussion()
        
        assert discussion["id"] == discussion_id
        assert discussion["title"] == "测试讨论"
        assert discussion["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_load_participants(self, sample_discussion, test_db):
        """测试：加载参与专家"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        participants = await moderator.load_participants()
        
        assert len(participants) == 3
        assert participants[0]["name"] == "李明"
        assert participants[1]["name"] == "王芳"
        assert participants[2]["name"] == "张悦"
    
    @pytest.mark.asyncio
    async def test_update_discussion_status(self, sample_discussion, test_db):
        """测试：更新讨论状态"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        await moderator.update_discussion_status("running")
        
        db = await get_db()
        cursor = await db.execute(
            "SELECT status FROM discussions WHERE id = ?",
            (discussion_id,)
        )
        row = await cursor.fetchone()
        
        assert row["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_save_message(self, sample_discussion, test_db):
        """测试：保存消息"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        participants = await moderator.load_participants()
        
        message_id = await moderator.save_message(
            participants[0]["id"],
            "这是一条测试消息",
            1
        )
        
        assert message_id > 0
        
        # 验证消息已保存
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        )
        message = await cursor.fetchone()
        
        assert message["content"] == "这是一条测试消息"
        assert message["round_number"] == 1
    
    @pytest.mark.asyncio
    async def test_load_previous_messages(self, sample_discussion, test_db):
        """测试：加载历史消息"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        participants = await moderator.load_participants()
        
        # 添加几条消息
        await moderator.save_message(participants[0]["id"], "消息1", 1)
        await moderator.save_message(participants[1]["id"], "消息2", 1)
        
        # 加载消息
        messages = await moderator.load_previous_messages()
        
        assert len(messages) == 2
        assert messages[0]["content"] == "消息1"
        assert messages[1]["content"] == "消息2"


class TestModeratorErrorHandling:
    """测试主持人错误处理"""
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_discussion(self, test_db):
        """测试：加载不存在的讨论应抛出异常"""
        moderator = Moderator(9999)
        
        with pytest.raises(Exception, match="讨论.*不存在"):
            await moderator.load_discussion()
    
    @pytest.mark.asyncio
    async def test_fail_discussion(self, sample_discussion, test_db):
        """测试：标记讨论失败"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        await moderator.fail_discussion("测试失败原因")
        
        db = await get_db()
        cursor = await db.execute(
            "SELECT status FROM discussions WHERE id = ?",
            (discussion_id,)
        )
        row = await cursor.fetchone()
        
        assert row["status"] == "failed"


class TestModeratorConsensus:
    """测试共识生成"""
    
    @pytest.mark.asyncio
    async def test_generate_fallback_consensus(self, sample_discussion, test_db):
        """测试：生成备用共识"""
        discussion_id = sample_discussion
        moderator = Moderator(discussion_id)
        
        messages = [
            {"participant_name": "李明", "content": "观点1"},
            {"participant_name": "王芳", "content": "观点2"},
        ]
        
        consensus = moderator.generate_fallback_consensus(messages, "测试主题")
        
        assert "summary" in consensus
        assert "keyPoints" in consensus
        assert isinstance(consensus["keyPoints"], list)
        assert len(consensus["keyPoints"]) > 0
        assert "测试主题" in consensus["summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
