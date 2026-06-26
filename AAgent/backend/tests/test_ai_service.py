"""
测试: AI Service - AI调用服务
测试AI生成和共识提取功能
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ai_service import generate_expert_response, generate_consensus


class TestAIService:
    """测试AI服务"""
    
    @pytest.mark.asyncio
    async def test_generate_expert_response_parameters(self):
        """测试：AI响应生成接受正确参数"""
        # 使用mock避免实际调用API
        with patch('services.ai_service.get_tongyi_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.content = "这是一个测试回复"
            mock_client.return_value.invoke = lambda x: mock_response
            
            result = await generate_expert_response(
                system_prompt="你是专家",
                user_message="请回答问题"
            )
            
            assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_generate_consensus_structure(self):
        """测试：共识生成返回正确结构"""
        messages = [
            {
                "participant": {"name": "李明", "role": "架构师"},
                "content": "我认为应该采用微服务架构"
            },
            {
                "participant": {"name": "王芳", "role": "产品经理"},
                "content": "从产品角度，我同意这个方案"
            }
        ]
        
        # Mock AI响应
        with patch('services.ai_service.generate_expert_response') as mock_gen:
            mock_gen.return_value = '''
            {
                "summary": "专家们就微服务架构达成共识",
                "keyPoints": ["采用微服务", "关注产品需求", "技术可行性高"]
            }
            '''
            
            result = await generate_consensus(messages, "系统架构讨论")
            
            assert "summary" in result
            assert "keyPoints" in result
            assert isinstance(result["keyPoints"], list)


class TestAIErrorHandling:
    """测试AI服务错误处理"""
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self):
        """测试：AI调用失败应抛出异常"""
        with patch('services.ai_service.get_tongyi_client') as mock_client:
            mock_client.side_effect = Exception("API调用失败")
            
            with pytest.raises(Exception, match="AI生成失败"):
                await generate_expert_response("prompt", "message")
    
    @pytest.mark.asyncio
    async def test_generate_consensus_json_parse_error(self):
        """测试：JSON解析失败时的fallback"""
        messages = [
            {
                "participant": {"name": "测试", "role": "专家"},
                "content": "测试内容"
            }
        ]
        
        with patch('services.ai_service.generate_expert_response') as mock_gen:
            # 返回非JSON格式
            mock_gen.return_value = "这不是JSON格式"
            
            result = await generate_consensus(messages, "测试")
            
            # 应该有summary字段，即使不是JSON
            assert "summary" in result
            assert "keyPoints" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
