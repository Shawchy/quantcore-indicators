"""
优化 monitoring.py 端点

修复内容：
1. 添加依赖注入函数
2. 完善异常处理
3. 移除硬编码导入
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def optimize_monitoring():
    """优化 monitoring.py 文件"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/monitoring.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 1. 在文件开头添加依赖注入函数
    import_section_end = content.find('\n\nrouter = APIRouter')
    
    if import_section_end == -1:
        print("❌ 未找到 router 定义")
        return False
    
    # 添加依赖注入函数和必要的导入
    dependency_injection_code = """
from fastapi import Depends, HTTPException
from loguru import logger


# ==================== 依赖注入 ====================

def get_rate_limiters():
    \"\"\"获取限流器实例（依赖注入）\"\"\"
    try:
        from app.middleware.rate_limiter import rate_limiters
        if rate_limiters is None:
            logger.error("限流器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return rate_limiters
    except ImportError as e:
        logger.error(f"限流器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_circuit_breakers():
    \"\"\"获取断路器实例（依赖注入）\"\"\"
    try:
        from app.middleware.circuit_breaker import circuit_breakers
        if circuit_breakers is None:
            logger.error("断路器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return circuit_breakers
    except ImportError as e:
        logger.error(f"断路器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_cache_manager():
    \"\"\"获取缓存管理器实例（依赖注入）\"\"\"
    try:
        from app.storage.cache import cache_manager
        if cache_manager is None:
            logger.error("缓存管理器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return cache_manager
    except ImportError as e:
        logger.error(f"缓存管理器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_trading_calendar():
    \"\"\"获取交易日历服务实例（依赖注入）\"\"\"
    try:
        from app.services.trading_calendar import trading_calendar
        if trading_calendar is None:
            logger.error("交易日历服务实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return trading_calendar
    except ImportError as e:
        logger.error(f"交易日历服务导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")

"""
    
    # 插入依赖注入代码
    new_content = content[:import_section_end] + dependency_injection_code + content[import_section_end:]
    
    # 2. 修复 get_data_source_metrics 函数
    old_func1 = '''@router.get("/data-sources")
async def get_data_source_metrics():
    """获取数据源详细指标"""
    metrics = {
        "rate_limiters": {},
        "circuit_breakers": {},
        "requests": {}
    }
    
    # 限流器统计
    for source, limiter in rate_limiters.items():'''
    
    new_func1 = '''@router.get("/data-sources")
async def get_data_source_metrics(
    rate_limiters=Depends(get_rate_limiters),
    circuit_breakers=Depends(get_circuit_breakers)
):
    """获取数据源详细指标"""
    try:
        metrics = {
            "rate_limiters": {},
            "circuit_breakers": {},
            "requests": {}
        }
        
        # 限流器统计
        for source, limiter in rate_limiters.items():'''
    
    new_content = new_content.replace(old_func1, new_func1)
    
    # 继续完成函数体的异常处理
    old_end1 = '''    return metrics'''
    new_end1 = '''        return metrics
    except Exception as e:
        logger.error(f"获取数据源指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取指标失败")'''
    
    new_content = new_content.replace(old_end1, new_end1, 1)
    
    # 3. 修复 get_cache_metrics 函数
    old_func2 = '''@router.get("/cache")
async def get_cache_metrics():
    """获取缓存详细指标"""
    cache_stats = cache_manager.get_all_stats()'''
    
    new_func2 = '''@router.get("/cache")
async def get_cache_metrics(
    cache_manager=Depends(get_cache_manager)
):
    """获取缓存详细指标"""
    try:
        cache_stats = cache_manager.get_all_stats()'''
    
    new_content = new_content.replace(old_func2, new_func2)
    
    # 修复 get_cache_metrics 函数结尾
    old_end2 = '''    return cache_stats'''
    new_end2 = '''        return cache_stats
    except Exception as e:
        logger.error(f"获取缓存指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取缓存指标失败")'''
    
    new_content = new_content.replace(old_end2, new_end2, 1)
    
    # 4. 修复 get_storage_metrics 函数
    old_func3 = '''@router.get("/storage")
async def get_storage_metrics():
    """获取存储详细指标"""
    from pathlib import Path
    import os'''
    
    new_func3 = '''@router.get("/storage")
async def get_storage_metrics():
    """获取存储详细指标"""
    try:
        from pathlib import Path
        import os'''
    
    new_content = new_content.replace(old_func3, new_func3)
    
    # 修复 get_storage_metrics 函数结尾
    old_end3 = '''    return storage_info'''
    new_end3 = '''        return storage_info
    except Exception as e:
        logger.error(f"获取存储指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取存储指标失败")'''
    
    new_content = new_content.replace(old_end3, new_end3, 1)
    
    # 5. 修复 get_metrics_summary 函数
    old_func4 = '''@router.get("/summary")
async def get_metrics_summary():
    """获取指标摘要"""
    summary = {
        "data_sources": {},
        "cache": cache_manager.get_all_stats(),
        "storage": await get_storage_metrics()
    }'''
    
    new_func4 = '''@router.get("/summary")
async def get_metrics_summary(
    cache_manager=Depends(get_cache_manager)
):
    """获取指标摘要"""
    try:
        summary = {
            "data_sources": {},
            "cache": cache_manager.get_all_stats(),
            "storage": await get_storage_metrics()
        }'''
    
    new_content = new_content.replace(old_func4, new_func4)
    
    # 修复 get_metrics_summary 函数结尾
    old_end4 = '''    return summary'''
    new_end4 = '''        return summary
    except Exception as e:
        logger.error(f"获取指标摘要失败：{e}")
        raise HTTPException(status_code=500, detail="获取指标摘要失败")'''
    
    new_content = new_content.replace(old_end4, new_end4, 1)
    
    # 6. 修复 get_trading_calendar_status 函数
    old_func5 = '''@router.get("/trading-calendar")
async def get_trading_calendar_status():
    """获取交易日历状态"""
    from app.services.trading_calendar import trading_calendar
    
    status = trading_calendar.get_cache_status()'''
    
    new_func5 = '''@router.get("/trading-calendar")
async def get_trading_calendar_status(
    trading_calendar=Depends(get_trading_calendar)
):
    """获取交易日历状态"""
    try:
        status = trading_calendar.get_cache_status()'''
    
    new_content = new_content.replace(old_func5, new_func5)
    
    # 修复 get_trading_calendar_status 函数结尾
    old_end5 = '''    }'''
    new_end5 = '''        }
    except Exception as e:
        logger.error(f"获取交易日历状态失败：{e}")
        raise HTTPException(status_code=500, detail="获取交易日历状态失败")'''
    
    # 只替换第一次出现的 } （即函数的结尾）
    new_content = new_content.replace(old_end5, new_end5, 1)
    
    # 7. 修复 refresh_trading_calendar 函数
    old_func6 = '''@router.post("/trading-calendar/refresh")
async def refresh_trading_calendar():
    """强制刷新交易日历数据"""
    from app.services.trading_calendar import trading_calendar
    
    success = await trading_calendar.force_refresh()'''
    
    new_func6 = '''@router.post("/trading-calendar/refresh")
async def refresh_trading_calendar(
    trading_calendar=Depends(get_trading_calendar)
):
    """强制刷新交易日历数据"""
    try:
        success = await trading_calendar.force_refresh()'''
    
    new_content = new_content.replace(old_func6, new_func6)
    
    # 保存
    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ {file_path} 优化完成")
    return True


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("=" * 60)
    print("🔧 优化 monitoring.py")
    print("=" * 60)
    print()
    
    success = optimize_monitoring()
    
    print()
    if success:
        print("🎉 monitoring.py 优化成功！")
    else:
        print("⚠️  optimization 失败")
