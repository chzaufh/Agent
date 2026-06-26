"""
Expert Service - 专家生成服务
Python版本
"""

import json
import os
from typing import List, Dict
import random

# 加载专家配置
EXPERTS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "experts.json")
_experts_config = None


def load_experts_config():
    """加载专家配置"""
    global _experts_config
    if _experts_config is None:
        with open(EXPERTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            _experts_config = json.load(f)
    return _experts_config


def generate_expert_personas(topic: str, participant_count: int) -> List[Dict]:
    """
    根据主题生成专家列表
    
    Args:
        topic: 讨论主题
        participant_count: 参与人数（3-5人）
    
    Returns:
        专家Persona数组
    """
    if not topic or not isinstance(topic, str) or len(topic.strip()) == 0:
        raise ValueError("讨论主题不能为空")
    
    if not isinstance(participant_count, int) or participant_count < 3 or participant_count > 5:
        raise ValueError("参与人数必须在3-5人之间")
    
    config = load_experts_config()
    selected_experts = select_experts_by_topic(topic, participant_count, config)
    
    return [
        {
            "name": expert["name"],
            "role": expert["role"],
            "expertise": expert["expertise"],
            "systemPrompt": expert["systemPrompt"],
            "avatarColor": expert["avatarColor"],
            "orderIndex": index
        }
        for index, expert in enumerate(selected_experts)
    ]


def select_experts_by_topic(topic: str, count: int, config: Dict) -> List[Dict]:
    """根据主题智能选择专家"""
    topic_lower = topic.lower()
    templates = config["templates"]
    
    # 关键词映射规则
    keyword_map = {
        '技术': ['tech-architect', 'frontend-expert', 'devops-engineer'],
        '架构': ['tech-architect', 'devops-engineer', 'security-expert'],
        '前端': ['frontend-expert', 'ux-designer', 'tech-architect'],
        '产品': ['product-manager', 'ux-designer', 'business-analyst'],
        '设计': ['ux-designer', 'frontend-expert', 'product-manager'],
        '用户': ['ux-designer', 'product-manager', 'data-scientist'],
        '体验': ['ux-designer', 'product-manager', 'frontend-expert'],
        '数据': ['data-scientist', 'tech-architect', 'business-analyst'],
        '分析': ['data-scientist', 'business-analyst', 'product-manager'],
        '安全': ['security-expert', 'tech-architect', 'devops-engineer'],
        '商业': ['business-analyst', 'product-manager', 'data-scientist'],
        '运营': ['business-analyst', 'product-manager', 'devops-engineer'],
        '性能': ['tech-architect', 'frontend-expert', 'devops-engineer'],
        '优化': ['tech-architect', 'frontend-expert', 'data-scientist'],
        '运维': ['devops-engineer', 'tech-architect', 'security-expert'],
        '部署': ['devops-engineer', 'tech-architect', 'security-expert']
    }
    
    selected_ids = set()
    
    # 根据关键词匹配
    for keyword, expert_ids in keyword_map.items():
        if keyword in topic_lower:
            selected_ids.update(expert_ids)
    
    # 如果没有匹配到，使用默认专家组合
    if len(selected_ids) == 0:
        defaults = config.get("defaultParticipants", ['tech-architect', 'product-manager', 'ux-designer'])
        selected_ids.update(defaults)
    
    # 转换为专家对象数组
    selected_experts = [t for t in templates if t["id"] in selected_ids]
    
    # 如果数量不足，补充其他专家
    if len(selected_experts) < count:
        remaining = [t for t in templates if t["id"] not in selected_ids]
        selected_experts.extend(remaining)
        selected_experts = selected_experts[:count]
    
    # 如果数量超过，随机选择
    if len(selected_experts) > count:
        random.shuffle(selected_experts)
        selected_experts = selected_experts[:count]
    
    return selected_experts


def build_system_prompt(
    participant: Dict,
    discussion_context: Dict,
    previous_messages: List[Dict],
    current_round: int
) -> str:
    """
    构建专家的完整SystemPrompt
    
    Args:
        participant: 专家信息
        discussion_context: 讨论上下文
        previous_messages: 之前的消息
        current_round: 当前轮次
    
    Returns:
        完整的SystemPrompt
    """
    base_persona = f"""你是{participant['name']}，一位专业的{participant['role']}。

【你的专业领域】
{participant['expertise']}

【你的角色定位】
作为{participant['role']}，你从专业角度分析问题，提出见解。

【发言风格】
- 保持专业但不失亲和力，用简洁的中文表达核心观点
- 结合实际案例说明问题，避免空洞理论
- 尊重其他专家意见，但勇于提出不同看法
- 每次发言聚焦2-3个核心观点，不要泛泛而谈"""

    context_info = f"""

【当前讨论主题】
{discussion_context['title']}

【讨论背景】
{discussion_context.get('description', '无额外背景说明，请根据主题展开讨论')}"""

    if previous_messages:
        message_history = '\n\n【之前的讨论内容】\n' + '\n\n'.join([
            f"{m['participant']['name']}（{m['participant']['role']}）：{m['content']}"
            for m in previous_messages[-6:]  # 只显示最近6条
        ])
    else:
        message_history = '\n\n【之前的讨论内容】\n你是第一位发言的专家，请开启这场讨论。'
    
    round_guidelines = generate_round_guidelines(current_round)
    
    return base_persona + context_info + message_history + '\n\n' + round_guidelines


def generate_round_guidelines(round_num: int) -> str:
    """生成轮次发言指引"""
    if round_num == 1:
        return """【第一轮发言指引】
这是讨论的第一轮，请：
1. 表明你对主题的初步看法和立场
2. 提出2-3个你认为最核心的观点
3. 可以提出你关注的问题或要点
4. 控制在150-300字之间
5. 语气开放友好，为后续讨论留有余地"""
    elif round_num == 2:
        return """【第二轮发言指引】
这是讨论的第二轮，请：
1. 认真回应其他专家提出的观点
2. 深化或补充你在第一轮的见解
3. 指出你与其他专家的共同点和分歧点
4. 如果有不同意见，礼貌地阐述理由和数据支持
5. 控制在200-400字之间
6. 开始尝试找寻可能的共识方向"""
    else:
        return """【第三轮（最后一轮）发言指引】
这是讨论的最后一轮，请：
1. 总结你的最终立场和核心建议
2. 尝试综合各方观点，提出折中或创新方案
3. 明确你最支持的方向并说明理由
4. 向形成团队共识的方向靠拢
5. 控制在200-350字之间
6. 语气肯定、建设性，展现专业判断力"""


def get_all_expert_templates() -> List[Dict]:
    """获取所有专家模板"""
    config = load_experts_config()
    return config["templates"]


def get_expert_template_by_id(expert_id: str) -> Dict:
    """根据ID获取专家模板"""
    config = load_experts_config()
    for template in config["templates"]:
        if template["id"] == expert_id:
            return template
    return None
