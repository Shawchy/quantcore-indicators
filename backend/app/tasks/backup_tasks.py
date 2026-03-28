"""
备份定时任务

定期执行数据备份任务
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.storage.backup_manager import backup_manager


scheduler = AsyncIOScheduler()


async def daily_backup_task():
    """
    每日增量备份任务
    
    每天凌晨 1 点执行
    """
    logger.info("=" * 60)
    logger.info("开始每日增量备份任务")
    logger.info("=" * 60)
    
    try:
        result = await backup_manager.create_incremental_backup(
            description="每日自动增量备份"
        )
        
        if result.get("success"):
            if result.get("skipped"):
                logger.info("每日备份跳过: 无变化文件")
            else:
                logger.info(f"每日备份完成: {result.get('backup_name')}")
        else:
            logger.error(f"每日备份失败: {result.get('error')}")
        
        await backup_manager.cleanup_old_backups()
    
    except Exception as e:
        logger.error(f"每日备份任务失败: {e}")


async def weekly_backup_task():
    """
    每周完整备份任务
    
    每周日凌晨 0 点执行
    """
    logger.info("=" * 60)
    logger.info("开始每周完整备份任务")
    logger.info("=" * 60)
    
    try:
        result = await backup_manager.create_full_backup(
            description="每周自动完整备份"
        )
        
        if result.get("success"):
            logger.info(f"每周备份完成: {result.get('backup_name')}")
        else:
            logger.error(f"每周备份失败: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"每周备份任务失败: {e}")


def setup_backup_tasks():
    """配置备份定时任务"""
    
    scheduler.add_job(
        daily_backup_task,
        trigger=CronTrigger(hour=1, minute=0),
        id="daily_backup",
        name="每日增量备份",
        replace_existing=True
    )
    logger.info("已配置: 每日增量备份任务 (每天 01:00)")
    
    scheduler.add_job(
        weekly_backup_task,
        trigger=CronTrigger(day_of_week='sun', hour=0, minute=0),
        id="weekly_backup",
        name="每周完整备份",
        replace_existing=True
    )
    logger.info("已配置: 每周完整备份任务 (每周日 00:00)")


def start_backup_tasks():
    """启动备份定时任务"""
    setup_backup_tasks()
    scheduler.start()
    logger.info("备份定时任务已启动")


def stop_backup_tasks():
    """停止备份定时任务"""
    scheduler.shutdown()
    logger.info("备份定时任务已停止")
