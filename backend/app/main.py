from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sys
import os
import warnings
from pathlib import Path

# 设置 pandas 环境变量以消除 pandas_ta 的警告
os.environ['PANDAS_MODE'] = 'copy_on_write'

# 过滤 pandas_ta 的弃用警告
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas_ta')
warnings.filterwarnings('ignore', category=UserWarning, message='.*copy_on_write.*')
warnings.filterwarnings('ignore', category=Warning, message='.*Pandas4Warning.*')

# 临时重定向 stderr 以过滤 pandas_ta 的警告
import io
_old_stderr = sys.stderr
sys.stderr = io.StringIO()

from app.config import settings
from app.api.v1 import api_router
from app.core.exceptions import QuantException
from app.middleware.performance import PerformanceMiddleware

# 恢复 stderr
sys.stderr = _old_stderr


def setup_logging():
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 添加过滤器以过滤 pandas_ta 的警告
    def pandas_warning_filter(record):
        # 过滤 pandas_ta 的 Pandas4Warning
        if 'Pandas4Warning' in record['message']:
            return False
        if 'copy_on_write' in record['message']:
            return False
        return True
    
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter=pandas_warning_filter
    )
    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=pandas_warning_filter
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    setup_logging()
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    
    from app.storage.sqlite import init_database
    await init_database()
    logger.info("数据库初始化完成")
    
    from app.services.trading_calendar import trading_calendar
    await trading_calendar.initialize()
    logger.info("交易日历服务初始化完成")
    
    # 初始化数据源（仅初始化，不预加载数据）
    from app.adapters import data_source_manager
    try:
        await data_source_manager.initialize()
        logger.info(f"数据源初始化完成，默认数据源：{data_source_manager._default_source}")
    except Exception as e:
        logger.error(f"数据源初始化失败：{e}")
    
    # 数据加载器已初始化为按需模式（不自动预加载）
    logger.info("数据加载模式：按需加载（用户请求时才拉取数据）")
    
    # 缓存预热（可选，提升热点数据访问速度）
    try:
        from app.storage.cache_optimizer import cache_optimizer
        
        # 定义热门股票（沪深龙头股）
        HOT_STOCKS = [
            "600000",  # 浦发银行
            "600036",  # 招商银行
            "000001",  # 平安银行
            "601318",  # 中国平安
            "600519",  # 贵州茅台
            "000858",  # 五粮液
            "601398",  # 工商银行
            "600030",  # 中信证券
            "000333",  # 美的集团
            "601888",  # 中国中免
        ]
        
        # 定义热门板块
        HOT_SECTORS = [
            "industry_银行",
            "industry_证券",
            "industry_保险",
            "industry_房地产",
            "industry_食品饮料",
            "industry_医药生物",
            "industry_电子",
            "industry_计算机",
        ]
        
        # 后台异步预热，不阻塞启动
        async def warmup_task():
            try:
                logger.info("开始缓存预热...")
                
                # 预热热门股票 K 线（最近 90 天）
                logger.info(f"预热热门股票 K 线：{len(HOT_STOCKS)}只")
                await cache_optimizer.warmup_cache("kline", HOT_STOCKS)
                
                # 预热热门板块成分股
                logger.info(f"预热热门板块：{len(HOT_SECTORS)}个")
                await cache_optimizer.warmup_cache("sector", HOT_SECTORS)
                
                logger.info("缓存预热完成")
                
            except Exception as e:
                logger.warning(f"缓存预热失败：{e}")
        
        # 启动后台预热任务
        import asyncio
        asyncio.create_task(warmup_task())
        logger.info("缓存预热任务已启动（后台运行）")
        
    except Exception as e:
        logger.warning(f"缓存预热初始化失败：{e}")
    
    # 初始化中间件（限流器、断路器）
    from app.middleware import init_middleware
    init_middleware()
    logger.info("中间件初始化完成")
    
    # 启动定期性能报告任务
    import asyncio
    from app.middleware.performance import periodic_performance_report
    asyncio.create_task(periodic_performance_report())
    logger.info("性能监控已启动")
    
    # 启动 WebSocket 推送服务
    from app.websocket import start_pusher_service
    await start_pusher_service()
    logger.info("WebSocket 推送服务已启动")
    
    # 初始化本地数据库服务
    from app.services.local_database import local_db_service
    await local_db_service.initialize()
    logger.info("本地数据库服务已启动")
    
    # 启动数据同步定时任务
    from app.services.data_sync_scheduler import data_sync_scheduler
    await data_sync_scheduler.start()
    logger.info("数据同步定时任务已启动")
    
    # 启动生命周期管理定时任务
    from app.tasks.lifecycle_tasks import start_lifecycle_tasks
    start_lifecycle_tasks()
    
    # 启动备份定时任务
    from app.tasks.backup_tasks import start_backup_tasks
    start_backup_tasks()
    
    Path(settings.SQLITE_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.PARQUET_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("数据目录初始化完成")
    
    yield  # 应用运行期间
    
    # 关闭事件
    logger.info(f"{settings.APP_NAME} 关闭中...")
    
    # 停止数据同步任务
    await data_sync_scheduler.stop()
    
    # 关闭本地数据库服务
    await local_db_service.close()
    
    # 停止 WebSocket 推送服务
    from app.websocket import stop_pusher_service
    await stop_pusher_service()
    
    # 按需加载模式无需停止数据加载器
    logger.info("数据加载器已停止（按需模式）")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
## 个人股票量化分析系统 API 文档

本系统提供完整的股票量化分析功能，包括：

### 📊 核心功能
- **技术分析**: K 线图表、技术指标 (MA/MACD/RSI/KDJ 等)
- **板块分析**: 行业板块、概念板块、板块异动
- **筹码选股**: 筹码分布、股东人数、筹码集中度
- **资金流向**: 个股资金流、市场资金流、板块资金流
- **策略回测**: 策略管理、回测系统、性能分析
- **自选股**: 自选股管理、实时监控股

### 🏗️ 数据中台架构
系统采用轻量化数据中台架构：
- **多数据源接入**: EFinance、AkShare、Baostock、TickFlow
- **智能路由**: 自动选择最优数据源，支持故障降级
- **统一数据模型**: 标准化数据清洗和验证
- **分层存储**: SQLite (热数据) + Parquet (温数据) + LRU 缓存

### 🔐 认证说明
大部分 API 需要 JWT Token 认证，请先调用 `/api/v1/auth/login` 获取 Token。

### 📈 数据源支持
- **EFinance** (主力): 东方财富数据，完全免费，速度快
- **AkShare** (主力): 开源数据源，接口丰富
- **Baostock** (主力): 证券宝数据，稳定可靠
- **TickFlow** (可选): 专业数据源，需要 API Key

---

**技术栈**:
- Backend: FastAPI + Python 3.12
- Frontend: React + TypeScript + Redux
- Database: SQLite + Parquet
- Cache: LRU Async Cache
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,  # 使用新的 lifespan 方式
        openapi_tags=[
            {"name": "认证", "description": "用户认证相关 API"},
            {"name": "个股信息", "description": "股票基本信息、财务数据、股东信息等"},
            {"name": "板块分析", "description": "行业板块、概念板块、板块异动分析"},
            {"name": "筹码选股", "description": "筹码分布、股东人数、筹码集中度分析"},
            {"name": "选股筛选", "description": "股票筛选器、条件选股"},
            {"name": "策略管理", "description": "交易策略创建、编辑、删除"},
            {"name": "回测系统", "description": "策略回测、性能分析、交易记录"},
            {"name": "自选股", "description": "自选股管理、实时监控"},
            {"name": "市场行情", "description": "市场整体行情、市场统计"},
            {"name": "实时盘口", "description": "实时报价、盘口数据"},
            {"name": "资金流向", "description": "资金流向分析、主力净流入"},
            {"name": "数据源管理", "description": "数据源健康检查、性能统计、切换配置"},
            {"name": "数据源控制", "description": "数据源优先级配置、故障转移"},
            {"name": "加载进度", "description": "数据加载进度追踪"},
            {"name": "龙虎榜", "description": "龙虎榜数据、营业部排行"},
            {"name": "资本流向", "description": "资金流向监控、大单追踪"},
            {"name": "板块信息", "description": "板块详情、成分股"},
            {"name": "指数成分", "description": "指数数据、成分股"},
            {"name": "股东信息", "description": "股东人数、十大股东"},
            {"name": "市场实时行情", "description": "市场实时报价、涨跌排行"},
            {"name": "基金信息", "description": "基金列表、净值、持仓"},
            {"name": "个股详细信息", "description": "个股详细资料、财务指标"},
            {"name": "市场情绪监控", "description": "市场情绪指标、恐慌指数"},
            {"name": "财务深度分析", "description": "财务报表、财务指标深度分析"},
            {"name": "限售解禁", "description": "限售股解禁信息"},
            {"name": "盘口异动", "description": "实时盘口异动、火箭发射"},
            {"name": "筹码分布", "description": "筹码分布图、成本分析"},
            {"name": "股票市场总貌", "description": "市场整体概况、交易统计"},
            {"name": "地区交易排序", "description": "按地区统计交易活跃度"},
            {"name": "行业成交与概况", "description": "行业成交统计、行业概况"},
            {"name": "沪深京 A 股实时行情", "description": "A 股实时报价"},
            {"name": "创业板实时行情", "description": "创业板实时报价"},
            {"name": "科创板实时行情", "description": "科创板实时报价"},
            {"name": "新浪财经实时行情", "description": "新浪财经实时数据"},
            {"name": "历史行情数据", "description": "历史 K 线数据"},
            {"name": "分时数据", "description": "分时图数据"},
            {"name": "日内分时数据", "description": "日内逐笔成交数据"},
            {"name": "盘前分钟数据", "description": "盘前集合竞价数据"},
            {"name": "同行比较", "description": "同行业股票对比"},
            {"name": "美股历史行情", "description": "美股历史数据"},
            {"name": "港股历史行情", "description": "港股历史数据"},
            {"name": "业绩报表", "description": "业绩快报、业绩预告"},
            {"name": "行业分类数据", "description": "行业分类、行业代码"},
            {"name": "财务报表", "description": "三大财务报表"},
            {"name": "股东增减持", "description": "股东增持、减持信息"},
            {"name": "资金流向", "description": "个股资金流向"},
            {"name": "大单追踪", "description": "大单成交追踪"},
            {"name": "东方财富个股资金流", "description": "东方财富个股资金流向"},
            {"name": "东方财富大盘资金流", "description": "东方财富大盘资金流向"},
            {"name": "东方财富板块资金流", "description": "东方财富板块资金流向排行"},
            {"name": "东方财富主力净流入", "description": "东方财富主力净流入数据"},
            {"name": "东方财富行业个股资金流", "description": "东方财富行业个股资金流"},
            {"name": "东方财富行业/概念历史资金流", "description": "东方财富行业/概念历史资金流"},
            {"name": "东方财富基金持股", "description": "东方财富基金持股数据"},
            {"name": "东方财富龙虎榜", "description": "东方财富龙虎榜数据"},
            {"name": "机构推荐", "description": "机构推荐股票"},
            {"name": "技术指标", "description": "技术指标计算 (MA/MACD/RSI/KDJ 等)"},
            {"name": "K 线图表", "description": "K 线数据获取和图表展示"},
            {"name": "WebSocket", "description": "WebSocket 实时推送"},
        ]
    )
    
    # 添加性能监控中间件
    app.add_middleware(PerformanceMiddleware)
    
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
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    
    return app


app = create_app()
