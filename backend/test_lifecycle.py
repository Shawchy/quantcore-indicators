"""
生命周期管理测试脚本

测试数据归档、压缩和清理功能
"""
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path


async def test_lifecycle_manager():
    """测试生命周期管理器"""
    from app.storage.lifecycle_manager import DataLifecycleManager
    
    logger.info("=" * 60)
    logger.info("测试生命周期管理器")
    logger.info("=" * 60)
    
    manager = DataLifecycleManager(base_dir="./data")
    
    # 测试数据分层
    logger.info("\n1. 测试数据分层:")
    test_dates = [
        (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),   # 30 天前
        (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),  # 180 天前
        (datetime.now() - timedelta(days=500)).strftime("%Y-%m-%d"),  # 500 天前
        (datetime.now() - timedelta(days=2000)).strftime("%Y-%m-%d"), # 2000 天前
    ]
    
    for date in test_dates:
        layer = manager.classify_data(date)
        logger.info(f"  {date} -> {layer} ({manager.lifecycle_config[layer]['description']})")
    
    # 测试归档功能
    logger.info("\n2. 测试归档功能:")
    test_code = "000001"
    
    try:
        await manager.auto_archive(test_code)
        logger.info(f"  ✅ 归档 {test_code} 成功")
    except Exception as e:
        logger.error(f"  ❌ 归档 {test_code} 失败: {e}")
    
    # 测试压缩功能
    logger.info("\n3. 测试压缩功能:")
    test_year = 2023
    
    try:
        await manager.auto_compress_cold_data(test_code, test_year)
        logger.info(f"  ✅ 压缩 {test_code} {test_year} 成功")
    except Exception as e:
        logger.error(f"  ❌ 压缩 {test_code} {test_year} 失败: {e}")
    
    # 测试清理功能
    logger.info("\n4. 测试清理功能:")
    
    try:
        await manager.cleanup_expired_data(test_code)
        logger.info(f"  ✅ 清理 {test_code} 成功")
    except Exception as e:
        logger.error(f"  ❌ 清理 {test_code} 失败: {e}")
    
    # 获取统计信息
    logger.info("\n5. 统计信息:")
    stats = manager.get_stats()
    
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("生命周期管理器测试完成")
    logger.info("=" * 60)


async def test_directory_structure():
    """测试目录结构"""
    logger.info("\n" + "=" * 60)
    logger.info("测试目录结构")
    logger.info("=" * 60)
    
    base_dir = Path("./data")
    
    # 检查归档目录
    archive_dir = base_dir / "archive"
    
    if archive_dir.exists():
        logger.info(f"✅ 归档目录存在: {archive_dir}")
        
        # 统计归档文件
        archive_files = list(archive_dir.rglob("*.parquet.gz"))
        logger.info(f"  归档文件数: {len(archive_files)}")
        
        if archive_files:
            total_size = sum(f.stat().st_size for f in archive_files) / 1024 / 1024
            logger.info(f"  归档总大小: {total_size:.2f} MB")
    else:
        logger.info(f"⚠️  归档目录不存在: {archive_dir}")
    
    # 检查热数据目录
    hot_data_dir = base_dir / "stock" / "market" / "kline" / "daily"
    
    if hot_data_dir.exists():
        logger.info(f"\n✅ 热数据目录存在: {hot_data_dir}")
        
        # 统计热数据文件
        hot_files = list(hot_data_dir.rglob("*.parquet"))
        logger.info(f"  热数据文件数: {len(hot_files)}")
        
        if hot_files:
            total_size = sum(f.stat().st_size for f in hot_files) / 1024 / 1024
            logger.info(f"  热数据总大小: {total_size:.2f} MB")
    
    logger.info("\n" + "=" * 60)


async def test_lifecycle_tasks():
    """测试定时任务配置"""
    logger.info("\n" + "=" * 60)
    logger.info("测试定时任务配置")
    logger.info("=" * 60)
    
    from app.tasks.lifecycle_tasks import setup_lifecycle_tasks, scheduler
    
    # 配置任务
    setup_lifecycle_tasks()
    
    # 获取任务列表
    jobs = scheduler.get_jobs()
    
    logger.info(f"\n已配置 {len(jobs)} 个定时任务:")
    
    for job in jobs:
        logger.info(f"  - {job.name}")
        logger.info(f"    ID: {job.id}")
        logger.info(f"    触发器: {job.trigger}")
        logger.info(f"    下次执行: {job.next_run_time}")
    
    logger.info("\n" + "=" * 60)


async def main():
    """主测试函数"""
    logger.info("开始生命周期管理测试...")
    
    # 测试生命周期管理器
    await test_lifecycle_manager()
    
    # 测试目录结构
    await test_directory_structure()
    
    # 测试定时任务配置
    await test_lifecycle_tasks()
    
    logger.info("\n所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
