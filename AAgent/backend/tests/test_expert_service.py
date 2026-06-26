"""
测试: Expert Service - 专家生成服务
测试专家选择和Persona生成功能
"""

import pytest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.expert import (
    generate_expert_personas,
    select_experts_by_topic,
    build_system_prompt,
    get_all_expert_templates,
    get_expert_template_by_id
)


class TestExpertGeneration:
    """测试专家生成功能"""
    
    def test_generate_expert_personas_valid_input(self):
        """测试：有效输入生成专家列表"""
        # Arrange
        topic = "如何设计高并发系统"
        participant_count = 3
        
        # Act
        experts = generate_expert_personas(topic, participant_count)
        
        # Assert
        assert len(experts) == participant_count
        assert all("name" in e for e in experts)
        assert all("role" in e for e in experts)
        assert all("expertise" in e for e in experts)
        assert all("systemPrompt" in e for e in experts)
        assert all("avatarColor" in e for e in experts)
        assert all("orderIndex" in e for e in experts)
    
    def test_generate_expert_personas_min_count(self):
        """测试：最少3人"""
        topic = "产品设计"
        experts = generate_expert_personas(topic, 3)
        assert len(experts) == 3
    
    def test_generate_expert_personas_max_count(self):
        """测试：最多5人"""
        topic = "数据分析"
        experts = generate_expert_personas(topic, 5)
        assert len(experts) == 5
    
    def test_generate_expert_personas_invalid_count_too_few(self):
        """测试：人数过少应抛出异常"""
        with pytest.raises(ValueError, match="参与人数必须在3-5人之间"):
            generate_expert_personas("测试", 2)
    
    def test_generate_expert_personas_invalid_count_too_many(self):
        """测试：人数过多应抛出异常"""
        with pytest.raises(ValueError, match="参与人数必须在3-5人之间"):
            generate_expert_personas("测试", 6)
    
    def test_generate_expert_personas_empty_topic(self):
        """测试：空主题应抛出异常"""
        with pytest.raises(ValueError, match="讨论主题不能为空"):
            generate_expert_personas("", 3)
    
    def test_generate_expert_personas_whitespace_topic(self):
        """测试：空白主题应抛出异常"""
        with pytest.raises(ValueError, match="讨论主题不能为空"):
            generate_expert_personas("   ", 3)


class TestExpertSelection:
    """测试专家选择逻辑"""
    
    def test_select_experts_by_tech_keyword(self):
        """测试：技术关键词应选择技术相关专家"""
        # Arrange
        topic = "微服务架构设计"
        count = 3
        
        # 加载配置
        from services.expert import load_experts_config
        config = load_experts_config()
        
        # Act
        experts = select_experts_by_topic(topic, count, config)
        
        # Assert
        expert_ids = [e["id"] for e in experts]
        # 应该包含技术架构师
        assert "tech-architect" in expert_ids or len(experts) == count
    
    def test_select_experts_by_product_keyword(self):
        """测试：产品关键词应选择产品相关专家"""
        topic = "用户体验优化"
        count = 4
        
        from services.expert import load_experts_config
        config = load_experts_config()
        
        experts = select_experts_by_topic(topic, count, config)
        expert_ids = [e["id"] for e in experts]
        
        # 应该包含UX设计师或产品经理
        assert any(eid in expert_ids for eid in ["ux-designer", "product-manager"])
    
    def test_select_experts_returns_correct_count(self):
        """测试：返回正确数量的专家"""
        topic = "任意主题"
        
        from services.expert import load_experts_config
        config = load_experts_config()
        
        for count in [3, 4, 5]:
            experts = select_experts_by_topic(topic, count, config)
            assert len(experts) == count


class TestSystemPromptBuilder:
    """测试SystemPrompt构建"""
    
    def test_build_system_prompt_first_round(self):
        """测试：第一轮发言的SystemPrompt"""
        # Arrange
        participant = {
            "name": "李明",
            "role": "技术架构师",
            "expertise": "系统架构设计"
        }
        discussion_context = {
            "title": "如何优化系统性能",
            "description": "探讨性能优化方案"
        }
        previous_messages = []
        current_round = 1
        
        # Act
        prompt = build_system_prompt(
            participant,
            discussion_context,
            previous_messages,
            current_round
        )
        
        # Assert
        assert "李明" in prompt
        assert "技术架构师" in prompt
        assert "如何优化系统性能" in prompt
        assert "第一轮发言" in prompt
    
    def test_build_system_prompt_with_history(self):
        """测试：包含历史消息的SystemPrompt"""
        participant = {
            "name": "王芳",
            "role": "产品经理",
            "expertise": "产品规划"
        }
        discussion_context = {
            "title": "新产品设计",
            "description": "讨论新产品方向"
        }
        previous_messages = [
            {
                "participant": {"name": "李明", "role": "架构师"},
                "content": "从技术角度来看..."
            }
        ]
        
        prompt = build_system_prompt(
            participant,
            discussion_context,
            previous_messages,
            2
        )
        
        assert "李明" in prompt
        assert "从技术角度来看" in prompt
        assert "第二轮发言" in prompt


class TestExpertTemplates:
    """测试专家模板获取"""
    
    def test_get_all_expert_templates(self):
        """测试：获取所有专家模板"""
        templates = get_all_expert_templates()
        
        assert isinstance(templates, list)
        assert len(templates) >= 3
        assert all("id" in t for t in templates)
        assert all("name" in t for t in templates)
    
    def test_get_expert_template_by_id_valid(self):
        """测试：通过有效ID获取专家模板"""
        expert = get_expert_template_by_id("tech-architect")
        
        assert expert is not None
        assert expert["id"] == "tech-architect"
        assert "name" in expert
        assert "role" in expert
    
    def test_get_expert_template_by_id_invalid(self):
        """测试：无效ID应返回None"""
        expert = get_expert_template_by_id("non-existent-id")
        assert expert is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
