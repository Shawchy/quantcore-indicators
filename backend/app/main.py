from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sys
from pathlib import Path

from app.config import settings
from app.api.v1 import api_router
from app.core.exceptions import QuantException


def setup_logging():
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="个人股票量化分析系统 - 支持技术分析、板块分析、筹码选股、策略回测",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    @app.exception_handler(QuantException)
    async def quant_exception_handler(request: Request, exc: QuantException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": None
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "data": None
            }
        )
    
    @app.on_event("startup")
    async def startup_event():
        setup_logging()
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
        
        from app.storage.sqlite import init_database
        await init_database()
        logger.info("数据库初始化完成")
        
        Path(settings.SQLITE_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.PARQUET_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("数据目录初始化完成")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"{settings.APP_NAME} 关闭中...")
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
