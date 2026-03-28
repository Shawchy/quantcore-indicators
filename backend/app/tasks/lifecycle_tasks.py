"""
生命周期管理定时任务

定期执行数据归档、压缩和清理任务
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from datetime import datetime

from app.storage.lifecycle_manager import lifecycle_manager
from app.adapters import data_source_manager


scheduler = AsyncIOScheduler()


async def get_all_stock_codes() -> list:
    """获取所有股票代码"""
    try:
        stocks = await data_source_manager.get_stock_list()
        return [s.code for s in stocks]
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return []


async def daily_archive_task():
    """
    每日归档任务
    
    每天凌晨 2 点执行，将 90 天前的数据从 SQLite 归档到 Parquet
    """
    logger.info("=" * 60)
    logger.info("开始每日数据归档任务")
    logger.info("=" * 60)
    
    try:
        stock_codes = await get_all_stock_codes()
        
        logger.info(f"待归档股票数量: {len(stock_codes)}")
        
        for i, code in enumerate(stock_codes, 1):
            try:
                await lifecycle_manager.auto_archive(code)
                
                if i % 100 == 0:
                    logger.info(f"归档进度: {i}/{len(stock_codes)}")
            
            except Exception as e:
                logger.error(f"归档 {code} 失败: {e}")
                continue
        
        stats = lifecycle_manager.get_stats()
        logger.info("=" * 60)
        logger.info("每日归档任务完成:")
        logger.info(f"  归档文件数: {stats['archived_files']}")
        logger.info(f"  归档记录数: {stats['archived_records']}")
        logger.info("=" * 60)
        
        lifecycle_manager.reset_stats()
    
    except Exception as e:
        logger.error(f"每日归档任务失败: {e}")


async def weekly_compress_task():
    """
    每周压缩任务
    
    每周日凌晨 3 点执行，压缩 2 年以上的数据
    """
    logger.info("=" * 60)
    logger.info("开始每周数据压缩任务")
    logger.info("=" * 60)
    
    try:
        stock_codes = await get_all_stock_codes()
        current_year = datetime.now().year
        years_to_compress = range(2015, current_year - 1)
        
        logger.info(f"待压缩年份: {list(years_to_compress)}")
        
        for year in years_to_compress:
            logger.info(f"压缩 {year} 年数据...")
            
            for i, code in enumerate(stock_codes, 1):
                try:
                    await lifecycle_manager.auto_compress_cold_data(code, year)
                    
                    if i % 100 == 0:
                        logger.info(f"  {year} 年压缩进度: {i}/{len(stock_codes)}")
                
                except Exception as e:
                    logger.error(f"压缩 {code} {year} 失败: {e}")
                    continue
        
        stats = lifecycle_manager.get_stats()
        logger.info("=" * 60)
        logger.info("每周压缩任务完成:")
        logger.info(f"  压缩文件数: {stats['compressed_files']}")
        logger.info(f"  压缩记录数: {stats['compressed_records']}")
        logger.info(f"  节省空间: {stats['space_saved_mb']} MB")
        logger.info("=" * 60)
        
        lifecycle_manager.reset_stats()
    
    except Exception as e:
        logger.error(f"每周压缩任务失败: {e}")


async def monthly_cleanup_task():
    """
    每月清理任务
    
    每月 1 号凌晨 4 点执行，清理 5 年以上的过期数据
    """
    logger.info("=" * 60)
    logger.info("开始每月数据清理任务")
    logger.info("=" * 60)
    
    try:
        stock_codes = await get_all_stock_codes()
        
        logger.info(f"待清理股票数量: {len(stock_codes)}")
        
        for i, code in enumerate(stock_codes, 1):
            try:
                await lifecycle_manager.cleanup_expired_data(code)
                
                if i % 100 == 0:
                    logger.info(f"清理进度: {i}/{len(stock_codes)}")
            
            except Exception as e:
                logger.error(f"清理 {code} 失败: {e}")
                continue
        
        stats = lifecycle_manager.get_stats()
        logger.info("=" * 60)
        logger.info("每月清理任务完成:")
        logger.info(f"  删除文件数: {stats['deleted_files']}")
        logger.info(f"  删除记录数: {stats['deleted_records']}")
        logger.info("=" * 60)
        
        lifecycle_manager.reset_stats()
    
    except Exception as e:
        logger.error(f"每月清理任务失败: {e}")


def setup_lifecycle_tasks():
    """配置生命周期管理定时任务"""
    
    # 每日归档任务 - 每天凌晨 2 点
    scheduler.add_job(
        daily_archive_task,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_archive",
        name="每日数据归档",
        replace_existing=True
    )
    logger.info("已配置: 每日归档任务 (每天 02:00)")
    
    # 每周压缩任务 - 每周日凌晨 3 点
    scheduler.add_job(
        weekly_compress_task,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id="weekly_compress",
        name="每周数据压缩",
        replace_existing=True
    )
    logger.info("已配置: 每周压缩任务 (每周日 03:00)")
    
    # 每月清理任务 - 每月 1 号凌晨 4 点
    scheduler.add_job(
        monthly_cleanup_task,
        trigger=CronTrigger(day=1, hour=4, minute=0),
        id="monthly_cleanup",
        name="每月数据清理",
        replace_existing=True
    )
    logger.info("已配置: 每月清理任务 (每月 1 号 04:00)")


def start_lifecycle_tasks():
    """启动生命周期管理定时任务"""
    setup_lifecycle_tasks()
    scheduler.start()
    logger.info("生命周期管理定时任务已启动")


def stop_lifecycle_tasks():
    """停止生命周期管理定时任务"""
    scheduler.shutdown()
    logger.info("生命周期管理定时任务已停止")
