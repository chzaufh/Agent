"""
AI Service - 通义千问API服务
Python版本 - 使用DashScope官方SDK（更稳定）
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入DashScope SDK
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
    logger.info("✅ DashScope SDK已加载")
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning("⚠️ DashScope SDK未安装，将使用模拟模式")


def init_dashscope():
    """初始化DashScope"""
    if not DASHSCOPE_AVAILABLE:
        return False
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("❌ 未找到DASHSCOPE_API_KEY环境变量")
        return False
    
    dashscope.api_key = api_key
    logger.info("✅ DashScope API Key已配置")
    return True


async def generate_expert_response(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """
    生成AI专家的回复 - 使用通义千问
    
    Args:
        system_prompt: 系统提示词（专家Persona）
        user_message: 用户消息
        model: 模型名称
        max_tokens: 最大token数
        temperature: 温度参数
    
    Returns:
        AI生成的回复
    """
    # 获取模型名称
    if not model:
        model = os.getenv("TONGYI_MODEL", "qwen-turbo")
    
    logger.info(f"🤖 使用模型: {model}")
    
    # 如果DashScope可用，使用官方SDK
    if DASHSCOPE_AVAILABLE and init_dashscope():
        try:
            logger.info(f"📤 调用通义千问API...")
            
            # 构造消息
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ]
            
            # 调用API（同步调用，但在async函数中）
            response = Generation.call(
                model=model,
                messages=messages,
                result_format='message',
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 检查响应
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                logger.info(f"✅ 通义千问API调用成功，返回 {len(content)} 字符")
                return content
            else:
                error_msg = f"API返回错误: {response.code} - {response.message}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"❌ 通义千问API调用失败: {str(e)}")
            raise Exception(f"AI生成失败: {str(e)}")
    
    # 如果DashScope不可用，使用模拟响应
    else:
        logger.warning("⚠️ 使用模拟AI响应")
        return generate_mock_response(user_message)


def generate_mock_response(user_message: str) -> str:
    """生成模拟响应（用于开发测试）"""
    return f"这是一个模拟响应。针对您的问题「{user_message[:50]}...」，我认为这是一个很有价值的讨论点。作为专家，我建议我们从多个角度来分析这个问题，包括技术可行性、用户体验、市场需求等方面。"


async def generate_consensus(
    discussion_title: str,
    messages: list,
    model: Optional[str] = None
) -> dict:
    """
    生成讨论共识
    
    Args:
        discussion_title: 讨论主题
        messages: 消息列表
        model: 模型名称
    
    Returns:
        包含summary和keyPoints的字典
    """
    logger.info(f"📊 开始生成讨论共识...")
    
    # 构建上下文
    context = f"讨论主题：{discussion_title}\n\n"
    context += "专家发言记录：\n"
    for msg in messages:
        context += f"- {msg.get('participant_name', '专家')}: {msg.get('content', '')}\n"
    
    # 提示词
    system_prompt = """你是一位专业的会议主持人和总结专家。请根据专家们的讨论内容，生成一份简洁的共识总结。

要求：
1. 用一段话概括整个讨论的核心内容
2. 提取3-5个关键观点
3. 语言简洁专业，避免重复

请以JSON格式返回，包含：
- summary: 总结文字（150字以内）
- keyPoints: 关键观点数组（每个30字以内）

示例格式：
{
  "summary": "本次讨论围绕XX主题展开...",
  "keyPoints": ["观点1", "观点2", "观点3"]
}"""
    
    user_prompt = f"请总结以下讨论：\n\n{context}"
    
    try:
        # 调用AI生成
        response = await generate_expert_response(
            system_prompt=system_prompt,
            user_message=user_prompt,
            model=model,
            max_tokens=1024,
            temperature=0.5
        )
        
        # 尝试解析JSON
        try:
            consensus = json.loads(response)
            logger.info(f"✅ 共识生成成功")
            return consensus
        except json.JSONDecodeError:
            # 如果不是JSON，构造一个基本的共识
            logger.warning("⚠️ AI返回非JSON格式，使用备用格式")
            return {
                "summary": response[:200] if len(response) > 200 else response,
                "keyPoints": [
                    "专家们就主题进行了深入讨论",
                    "形成了多维度的分析视角",
                    "为后续工作提供了参考方向"
                ]
            }
            
    except Exception as e:
        logger.error(f"❌ 生成共识失败: {str(e)}")
        raise Exception(f"共识生成失败: {str(e)}")


# 测试函数
async def test_api():
    """测试API连接"""
    try:
        response = await generate_expert_response(
            system_prompt="你是一位友好的AI助手。",
            user_message="你好，请做一个简短的自我介绍。",
            model="qwen-turbo"
        )
        print(f"✅ API测试成功！\n回复: {response}")
        return True
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())
