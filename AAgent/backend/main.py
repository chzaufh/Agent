from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging

from routes.discussions import router as discussions_router
from routes.experts import router as experts_router
from db.database import init_database, close_database

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("AI圆桌讨论系统启动中...")
    logger.info("=" * 60)
    try:
        await init_database()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    logger.info(f"服务地址: http://localhost:{os.getenv('PORT', '8000')}")
    logger.info(f"前端目录: {FRONTEND_DIR}  (存在={os.path.exists(FRONTEND_DIR)})")
    logger.info("系统就绪，等待请求...")
    logger.info("=" * 60)
    yield
    logger.info("正在关闭服务器...")
    await close_database()
    logger.info("服务器已完全关闭")


app = FastAPI(
    title="AI圆桌讨论系统",
    description="基于通义千问的多专家协作讨论平台",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API路由 - 必须在静态路由之前注册
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "AI圆桌讨论系统运行正常"}


app.include_router(discussions_router, prefix="/api/discussions", tags=["discussions"])
app.include_router(experts_router, prefix="/api/expert-templates", tags=["experts"])


# 静态文件路由 - 直接注册，不加 if 判断
@app.get("/")
async def serve_index():
    path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(path):
        return FileResponse(path, media_type="text/html; charset=utf-8")
    raise HTTPException(status_code=404, detail=f"index.html not found: {path}")


@app.get("/discussion.html")
async def serve_discussion():
    path = os.path.join(FRONTEND_DIR, "discussion.html")
    if os.path.isfile(path):
        return FileResponse(path, media_type="text/html; charset=utf-8")
    raise HTTPException(status_code=404, detail=f"discussion.html not found: {path}")


@app.get("/css/{file_path:path}")
async def serve_css(file_path: str):
    path = os.path.join(FRONTEND_DIR, "css", file_path)
    if os.path.isfile(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"CSS not found: {file_path}")


@app.get("/js/{file_path:path}")
async def serve_js(file_path: str):
    path = os.path.join(FRONTEND_DIR, "js", file_path)
    if os.path.isfile(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"JS not found: {file_path}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV") == "development"
    )