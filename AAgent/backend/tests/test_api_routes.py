"""
测试: API Routes - 路由接口测试
测试FastAPI路由功能 - 已修复所有问题
"""

import pytest
import sys
import os
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_database, close_database


@pytest.fixture(scope="function")
async def test_app():
    """测试应用fixture"""
    os.environ["DATABASE_PATH"] = ":memory:"
    await init_database()
    yield
    await close_database()


class TestExpertTemplatesAPI:
    """测试专家模板API"""
    
    @pytest.mark.asyncio
    async def test_get_expert_templates(self, test_app):
        """测试：获取专家模板列表"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/expert-templates/")
            
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert "maxParticipants" in data
            assert "minParticipants" in data
            assert isinstance(data["templates"], list)
    
    @pytest.mark.asyncio
    async def test_get_expert_template_by_id(self, test_app):
        """测试：获取单个专家模板"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/expert-templates/tech-architect")
            
            assert response.status_code == 200
            data = response.json()
            assert "expert" in data
            assert data["expert"]["id"] == "tech-architect"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_expert(self, test_app):
        """测试：获取不存在的专家应返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/expert-templates/invalid-id")
            
            assert response.status_code == 404


class TestDiscussionsAPI:
    """测试讨论API"""
    
    @pytest.mark.asyncio
    async def test_create_discussion(self, test_app):
        """测试：创建新讨论"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "title": "测试讨论",
                "description": "这是测试",
                "participants": [
                    {
                        "name": "李明",
                        "role": "架构师",
                        "expertise": "技术",
                        "systemPrompt": "提示词",
                        "avatarColor": "#3B82F6"
                    },
                    {
                        "name": "王芳",
                        "role": "产品经理",
                        "expertise": "产品",
                        "systemPrompt": "提示词",
                        "avatarColor": "#10B981"
                    },
                    {
                        "name": "张悦",
                        "role": "设计师",
                        "expertise": "设计",
                        "systemPrompt": "提示词",
                        "avatarColor": "#F59E0B"
                    }
                ]
            }
            
            response = await client.post("/api/discussions/", json=payload)
            
            assert response.status_code == 201
            data = response.json()
            assert "discussion" in data
            assert "participants" in data
            assert data["discussion"]["title"] == "测试讨论"
    
    @pytest.mark.asyncio
    async def test_create_discussion_too_few_participants(self, test_app):
        """测试：参与者过少应返回错误"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "title": "测试讨论",
                "description": "这是测试",
                "participants": [
                    {
                        "name": "李明",
                        "role": "架构师",
                        "expertise": "技术",
                        "systemPrompt": "提示词",
                        "avatarColor": "#3B82F6"
                    }
                ]
            }
            
            response = await client.post("/api/discussions/", json=payload)
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_discussions(self, test_app):
        """测试：获取讨论列表"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/discussions/")
            
            assert response.status_code == 200
            data = response.json()
            assert "discussions" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_discussion_by_id(self, test_app):
        """测试：获取讨论详情"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建一个讨论
            payload = {
                "title": "测试",
                "description": "描述",
                "participants": [
                    {"name": "A", "role": "R1", "expertise": "E", "systemPrompt": "P", "avatarColor": "#000"},
                    {"name": "B", "role": "R2", "expertise": "E", "systemPrompt": "P", "avatarColor": "#111"},
                    {"name": "C", "role": "R3", "expertise": "E", "systemPrompt": "P", "avatarColor": "#222"}
                ]
            }
            create_response = await client.post("/api/discussions/", json=payload)
            discussion_id = create_response.json()["discussion"]["id"]
            
            # 获取详情
            response = await client.get(f"/api/discussions/{discussion_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "discussion" in data
            assert "participants" in data
            assert "messages" in data


class TestHealthAPI:
    """测试健康检查API"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_app):
        """测试：健康检查"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_system_info(self, test_app):
        """测试：系统信息"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/info")
            
            assert response.status_code == 200
            data = response.json()
            assert "system" in data
            assert "statistics" in data
            assert "limits" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
