"""
Experts API Routes
Python FastAPI版本
"""

from fastapi import APIRouter, HTTPException
import logging
from services.expert import get_all_expert_templates, get_expert_template_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_expert_templates():
    """获取所有专家模板"""
    try:
        templates = get_all_expert_templates()
        
        return {
            "templates": templates,
            "maxParticipants": 5,
            "minParticipants": 3
        }
    
    except Exception as e:
        logger.error(f"获取专家模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{expert_id}")
async def get_expert_template(expert_id: str):
    """获取单个专家模板详情"""
    try:
        expert = get_expert_template_by_id(expert_id)
        
        if not expert:
            raise HTTPException(status_code=404, detail="专家模板不存在")
        
        return {"expert": expert}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取专家模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
