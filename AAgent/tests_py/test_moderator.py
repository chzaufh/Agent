"""
测试 Moderator Service - 主持人服务
TDD: 测试讨论流程管理
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from services.moderator import Moderator, run_discussion


@pytest.fixture
async def mock_db():
    """Mock数据库连接"""
    db = AsyncMock()
    
    # Mock execute返回cursor
    cursor = AsyncMock()
    cursor.lastrowid = 1
    cursor.fetchone = AsyncMock(return_value=None)
    cursor.fetchall = AsyncMock(return_value=[])
    
    db.execute = AsyncMock(return_value=cursor)
    db.commit = AsyncMock()
    
    return db


@pytest.fixture
def mock_discussion():
    """Mock讨论数据"""
    return {
        "id": 1,
        "title": "如何设计微服务架构",
        "description": "讨论微服务的最佳实践",
        "status": "pending"
    }


@pytest.fixture
def mock_participants():
    """Mock参与者列表"""
    return [
        {
            "id": 1,
            "name": "李明",
            "role": "技术架构师",
            "expertise": "系统架构",
            "system_prompt": "你是技术专家",
            "avatar_color": "#3B82F6",
            "order_index": 0
        },
        {
            "id": 2,
            "name": "王芳",
            "role": "产品经理",
            "expertise": "产品策略",
            "system_prompt": "你是产品专家",
            "avatar_color": "#10B981",
            "order_index": 1
        },
        {
            "id": 3,
            "name": "张悦",
            "role": "UX设计师",
            "expertise": "用户体验",
            "system_prompt": "你是设计专家",
            "avatar_color": "#F59E0B",
            "order_index": 2
        }
    ]


class TestModeratorInitialization:
    """测试主持人初始化"""
    
    def test_moderator_creation(self):
        """测试创建主持人实例"""
        moderator = Moderator(discussion_id=1)
        
        assert moderator.discussion_id == 1
        assert moderator.is_running == False
        assert moderator.max_rounds == 3  # 默认值
        assert moderator.current_round == 0
        assert moderator.participants == []
    
    def test_moderator_custom_rounds(self):
        """测试自定义轮次"""
        with patch.dict('os.environ', {'MAX_ROUNDS': '5'}):
            moderator = Moderator(discussion_id=1)
            assert moderator.max_rounds == 5


class TestModeratorDiscussionLoading:
    """测试讨论数据加载"""
    
    @pytest.mark.asyncio
    async def test_load_discussion_success(self, mock_db, mock_discussion):
        """测试成功加载讨论"""
        mock_db.execute.return_value.fetchone = AsyncMock(return_value=mock_discussion)
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            discussion = await moderator.load_discussion()
            
            assert discussion["id"] == 1
            assert discussion["title"] == "如何设计微服务架构"
            assert discussion["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_load_discussion_not_found(self, mock_db):
        """测试讨论不存在"""
        mock_db.execute.return_value.fetchone = AsyncMock(return_value=None)
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=999)
            
            with pytest.raises(Exception, match="讨论 #999 不存在"):
                await moderator.load_discussion()
    
    @pytest.mark.asyncio
    async def test_load_participants(self, mock_db, mock_participants):
        """测试加载参与者"""
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=mock_participants)
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            participants = await moderator.load_participants()
            
            assert len(participants) == 3
            assert participants[0]["name"] == "李明"
            assert participants[1]["name"] == "王芳"
            assert participants[2]["name"] == "张悦"


class TestModeratorMessageHandling:
    """测试消息处理"""
    
    @pytest.mark.asyncio
    async def test_save_message(self, mock_db):
        """测试保存消息"""
        mock_db.execute.return_value.lastrowid = 123
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            
            message_id = await moderator.save_message(
                participant_id=1,
                content="这是测试消息",
                round_number=1
            )
            
            assert message_id == 123
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_previous_messages(self, mock_db):
        """测试加载历史消息"""
        mock_messages = [
            {
                "content": "第一条消息",
                "participant_name": "李明",
                "participant_role": "技术架构师",
                "avatar_color": "#3B82F6"
            },
            {
                "content": "第二条消息",
                "participant_name": "王芳",
                "participant_role": "产品经理",
                "avatar_color": "#10B981"
            }
        ]
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=mock_messages)
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            messages = await moderator.load_previous_messages()
            
            assert len(messages) == 2
            assert messages[0]["participant"]["name"] == "李明"
            assert messages[0]["content"] == "第一条消息"
            assert messages[1]["participant"]["name"] == "王芳"


class TestModeratorStatusUpdates:
    """测试状态更新"""
    
    @pytest.mark.asyncio
    async def test_update_discussion_status(self, mock_db):
        """测试更新讨论状态"""
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            
            await moderator.update_discussion_status("running")
            
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_discussion(self, mock_db):
        """测试完成讨论"""
        mock_db.execute.return_value.fetchone = AsyncMock(return_value=(10,))  # 10条消息
        
        with patch('services.moderator.get_db', return_value=mock_db):
            with patch('services.moderator.broadcast_complete') as mock_broadcast:
                moderator = Moderator(discussion_id=1)
                
                await moderator.complete_discussion()
                
                # 验证状态更新
                assert mock_db.execute.called
                # 验证广播
                mock_broadcast.assert_called_once()


class TestModeratorDiscussionFlow:
    """测试完整讨论流程"""
    
    @pytest.mark.asyncio
    async def test_start_discussion_insufficient_participants(self, mock_db, mock_discussion):
        """测试参与者不足的情况"""
        # 只有2个参与者（不足3个）
        mock_db.execute.return_value.fetchone = AsyncMock(return_value=mock_discussion)
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=[
            {"id": 1, "name": "李明", "role": "技术架构师"},
            {"id": 2, "name": "王芳", "role": "产品经理"}
        ])
        
        with patch('services.moderator.get_db', return_value=mock_db):
            moderator = Moderator(discussion_id=1)
            
            with pytest.raises(Exception, match="参与专家数量不足"):
                await moderator.start_discussion()
    
    @pytest.mark.asyncio
    async def test_conduct_discussion_single_round(self, mock_db, mock_discussion, mock_participants):
        """测试单轮讨论"""
        mock_db.execute.return_value.fetchone = AsyncMock(return_value=mock_discussion)
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=[])
        mock_db.execute.return_value.lastrowid = 1
        
        with patch('services.moderator.get_db', return_value=mock_db):
            with patch('services.moderator.generate_expert_response') as mock_generate:
                with patch('services.moderator.broadcast_message') as mock_broadcast:
                    mock_generate.return_value = "这是AI生成的回复"
                    
                    moderator = Moderator(discussion_id=1)
                    moderator.participants = mock_participants
                    moderator.max_rounds = 1  # 只进行1轮
                    
                    await moderator.conduct_discussion(mock_discussion)
                    
                    # 验证每个专家都发言了
                    assert mock_generate.call_count == 3  # 3位专家
                    assert mock_broadcast.call_count == 3


class TestModeratorConsensus:
    """测试共识生成"""
    
    @pytest.mark.asyncio
    async def test_generate_fallback_consensus(self):
        """测试生成备用共识"""
        moderator = Moderator(discussion_id=1)
        
        messages = [
            {"participant_name": "李明", "content": "消息1"},
            {"participant_name": "王芳", "content": "消息2"},
            {"participant_name": "李明", "content": "消息3"}
        ]
        
        consensus = moderator.generate_fallback_consensus(messages, "测试主题")
        
        assert "summary" in consensus
        assert "keyPoints" in consensus
        assert "测试主题" in consensus["summary"]
        assert isinstance(consensus["keyPoints"], list)
        assert len(consensus["keyPoints"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_and_save_consensus_success(self, mock_db):
        """测试成功生成并保存共识"""
        mock_messages = [
            {
                "content": "技术观点",
                "participant_name": "李明",
                "participant_role": "技术架构师"
            }
        ]
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=mock_messages)
        
        mock_consensus = {
            "summary": "专家们达成了一致意见",
            "keyPoints": ["关键点1", "关键点2", "关键点3"]
        }
        
        with patch('services.moderator.get_db', return_value=mock_db):
            with patch('services.moderator.generate_consensus') as mock_gen:
                with patch('services.moderator.broadcast_consensus'):
                    mock_gen.return_value = mock_consensus
                    
                    moderator = Moderator(discussion_id=1)
                    discussion = {"title": "测试主题"}
                    
                    await moderator.generate_and_save_consensus(discussion)
                    
                    # 验证保存到数据库
                    mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_consensus_ai_failure_uses_fallback(self, mock_db):
        """测试AI失败时使用备用共识"""
        mock_messages = [
            {
                "content": "消息",
                "participant_name": "李明",
                "participant_role": "架构师"
            }
        ]
        mock_db.execute.return_value.fetchall = AsyncMock(return_value=mock_messages)
        
        with patch('services.moderator.get_db', return_value=mock_db):
            with patch('services.moderator.generate_consensus') as mock_gen:
                with patch('services.moderator.broadcast_consensus'):
                    # AI生成失败
                    mock_gen.side_effect = Exception("AI错误")
                    
                    moderator = Moderator(discussion_id=1)
                    discussion = {"title": "测试"}
                    
                    await moderator.generate_and_save_consensus(discussion)
                    
                    # 应该保存了备用共识
                    mock_db.commit.assert_called()


class TestRunDiscussion:
    """测试讨论运行函数"""
    
    @pytest.mark.asyncio
    async def test_run_discussion_function(self):
        """测试run_discussion导出函数"""
        with patch.object(Moderator, 'start_discussion') as mock_start:
            mock_start.return_value = None
            
            await run_discussion(discussion_id=1)
            
            mock_start.assert_called_once()


# 运行测试命令：
# pytest tests_py/test_moderator.py -v
# pytest tests_py/test_moderator.py -v --cov=services/moderator
# pytest tests_py/test_moderator.py::TestModeratorDiscussionFlow -v
