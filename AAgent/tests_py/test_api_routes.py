"""
测试 API Routes - FastAPI端点 (Part 1)
TDD: 测试HTTP API接口
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestHealthEndpoints:
    """测试健康检查端点"""
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestExpertTemplatesAPI:
    """测试专家模板API"""
    
    def test_get_expert_templates(self, client):
        """测试获取专家模板列表"""
        response = client.get("/api/expert-templates")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        assert "maxParticipants" in data
        assert "minParticipants" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) >= 3
        assert data["maxParticipants"] == 5
        assert data["minParticipants"] == 3
    
    def test_get_expert_template_by_id_success(self, client):
        """测试根据ID获取专家模板（成功）"""
        response = client.get("/api/expert-templates/tech-architect")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "expert" in data
        expert = data["expert"]
        assert expert["id"] == "tech-architect"
        assert expert["name"] == "李明"
        assert expert["role"] == "技术架构师"
    
    def test_get_expert_template_by_id_not_found(self, client):
        """测试根据ID获取专家模板（不存在）"""
        response = client.get("/api/expert-templates/nonexistent-expert")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


# 运行测试命令：
# pytest tests_py/test_api_routes.py -v
