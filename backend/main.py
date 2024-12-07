"""
主应用程序入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path

from .api.routes import router as api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title="电动车充电安全监控系统",
    description="基于AI的电动车充电安全实时智能监控报警系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

# 创建数据目录
data_dir = Path("./data")
alerts_dir = data_dir / "alerts"
alerts_dir.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("Starting up the application...")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("Shutting down the application...")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式下启用热重载
    )
