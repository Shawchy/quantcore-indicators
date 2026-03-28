"""
监控系统测试脚本

测试 Prometheus 指标暴露和监控 API 端点
"""
import asyncio
import aiohttp
from loguru import logger


async def test_monitoring_endpoints():
    """测试监控 API 端点"""
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # 测试 Prometheus 指标端点
        logger.info("=" * 60)
        logger.info("测试 Prometheus 指标端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics") as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✅ Prometheus 指标端点正常")
                    logger.info(f"   指标数量: {content.count('# HELP')}")
                else:
                    logger.error(f"❌ Prometheus 指标端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ Prometheus 指标端点错误: {e}")
        
        # 测试数据源指标端点
        logger.info("\n" + "=" * 60)
        logger.info("测试数据源指标端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics/data-sources") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 数据源指标端点正常")
                    
                    for source, stats in data.get("rate_limiters", {}).items():
                        logger.info(
                            f"   {source} 限流器: "
                            f"允许 {stats['allowed']}, "
                            f"拒绝 {stats['rejected']}, "
                            f"拒绝率 {stats['rejection_rate']}"
                        )
                    
                    for source, stats in data.get("circuit_breakers", {}).items():
                        logger.info(
                            f"   {source} 断路器: "
                            f"状态 {stats['state']}, "
                            f"成功率 {stats['success_rate']}"
                        )
                else:
                    logger.error(f"❌ 数据源指标端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ 数据源指标端点错误: {e}")
        
        # 测试缓存指标端点
        logger.info("\n" + "=" * 60)
        logger.info("测试缓存指标端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics/cache") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 缓存指标端点正常")
                    
                    for cache_type, stats in data.items():
                        hits = stats.get("hits", 0)
                        misses = stats.get("misses", 0)
                        total = hits + misses
                        hit_rate = (hits / total * 100) if total > 0 else 0
                        
                        logger.info(
                            f"   {cache_type}: "
                            f"命中 {hits}, "
                            f"未命中 {misses}, "
                            f"命中率 {hit_rate:.2f}%"
                        )
                else:
                    logger.error(f"❌ 缓存指标端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ 缓存指标端点错误: {e}")
        
        # 测试存储指标端点
        logger.info("\n" + "=" * 60)
        logger.info("测试存储指标端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics/storage") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 存储指标端点正常")
                    logger.info(f"   总存储大小: {data.get('total_size_mb', 0)} MB")
                    
                    if data.get("sqlite"):
                        logger.info(
                            f"   SQLite: "
                            f"{data['sqlite']['size_mb']} MB"
                        )
                    
                    if data.get("parquet"):
                        logger.info(
                            f"   Parquet: "
                            f"{data['parquet']['file_count']} 个文件, "
                            f"{data['parquet']['total_size_mb']} MB"
                        )
                else:
                    logger.error(f"❌ 存储指标端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ 存储指标端点错误: {e}")
        
        # 测试健康检查端点
        logger.info("\n" + "=" * 60)
        logger.info("测试健康检查端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 健康检查端点正常")
                    logger.info(f"   状态: {data.get('status')}")
                    logger.info(f"   时间戳: {data.get('timestamp')}")
                    
                    for component, status in data.get("components", {}).items():
                        logger.info(
                            f"   {component}: {status.get('status')}"
                        )
                else:
                    logger.error(f"❌ 健康检查端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ 健康检查端点错误: {e}")
        
        # 测试指标摘要端点
        logger.info("\n" + "=" * 60)
        logger.info("测试指标摘要端点")
        logger.info("=" * 60)
        
        try:
            async with session.get(f"{base_url}/metrics/summary") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 指标摘要端点正常")
                    
                    for source, stats in data.get("data_sources", {}).items():
                        logger.info(
                            f"   {source}: "
                            f"限流拒绝率 {stats['rate_limiter']['rejection_rate']}, "
                            f"断路器状态 {stats['circuit_breaker']['state']}"
                        )
                else:
                    logger.error(f"❌ 指标摘要端点失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ 指标摘要端点错误: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("监控端点测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_monitoring_endpoints())
