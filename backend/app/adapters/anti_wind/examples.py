"""
AntiWindFacade 使用示例

演示如何在不同场景下使用反爬策略门面。
"""

import asyncio
from typing import Dict, Any
from loguru import logger

from app.adapters.anti_wind import (
    AntiWindFacade,
    BASIC_CONFIG,
    STANDARD_CONFIG,
    FULL_CONFIG,
    HEADLESS_CONFIG,
    BROWSER_CONFIG,
)


# ========== 示例 1: 基础用法 ==========

async def example_basic_usage():
    """基础用法示例"""
    logger.info("=" * 60)
    logger.info("示例 1: 基础用法")
    logger.info("=" * 60)
    
    # 使用标准配置
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    # 定义请求函数（注意：request_func 会接收 url, method, headers 参数）
    async def fetch_data(url: str, method: str, headers: dict, **kwargs) -> Dict:
        """模拟请求函数"""
        logger.info(f"请求 {url}")
        # 实际实现中，这里是 HTTP 请求逻辑
        return {"success": True, "data": "mock_data"}
    
    # 执行请求
    try:
        result = await facade.execute_with_strategies(
            request_func=fetch_data,
            url="https://www.eastmoney.com",
            method="GET"
        )
        logger.info(f"✅ 请求成功：{result}")
    except Exception as e:
        logger.error(f"❌ 请求失败：{e}")


# ========== 示例 2: 适配器中使用 ==========

class ExampleAdapter:
    """示例适配器"""
    
    def __init__(self):
        # 使用标准配置
        self.anti_wind = AntiWindFacade(STANDARD_CONFIG)
    
    async def get_stock_info(self, symbol: str) -> Dict:
        """获取股票信息"""
        async def fetch(url: str, method: str, headers: dict, **kwargs) -> Dict:
            logger.info(f"获取股票信息：{symbol}")
            # 实际请求逻辑
            return {"symbol": symbol, "name": "示例股票"}
        
        return await self.anti_wind.execute_with_strategies(
            request_func=fetch,
            url=f"https://quote.eastmoney.com/{symbol}.html",
            method="GET"
        )
    
    async def get_market_index(self, index_code: str) -> Dict:
        """获取指数数据（使用更保守的配置）"""
        # 动态调整配置
        self.anti_wind.update_config({
            'min_delay': 3.0,
            'max_delay': 6.0,
        })
        
        async def fetch(url: str, method: str, headers: dict, **kwargs) -> Dict:
            logger.info(f"获取指数数据：{index_code}")
            return {"index_code": index_code, "value": 3000}
        
        try:
            return await self.anti_wind.execute_with_strategies(
                request_func=fetch,
                url=f"https://quote.eastmoney.com/{index_code}.html",
                method="GET"
            )
        finally:
            # 恢复配置
            self.anti_wind.update_config({
                'min_delay': 1.0,
                'max_delay': 3.0,
            })


async def example_adapter_usage():
    """适配器使用示例"""
    logger.info("=" * 60)
    logger.info("示例 2: 适配器中使用")
    logger.info("=" * 60)
    
    adapter = ExampleAdapter()
    
    # 获取股票信息
    stock_info = await adapter.get_stock_info("sz000001")
    logger.info(f"股票信息：{stock_info}")
    
    # 获取指数数据
    index_data = await adapter.get_market_index("sh000001")
    logger.info(f"指数数据：{index_data}")


# ========== 示例 3: 动态策略调整 ==========

async def example_dynamic_adjustment():
    """动态策略调整示例"""
    logger.info("=" * 60)
    logger.info("示例 3: 动态策略调整")
    logger.info("=" * 60)
    
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    # 打印初始状态
    logger.info("初始策略状态:")
    facade.print_status()
    
    # 模拟触发限流
    try:
        # 禁用 UA 轮换（减少特征变化）
        facade.disable_strategy('UARotatorStrategy')
        
        # 增加延迟
        facade.update_config({
            'min_delay': 5.0,
            'max_delay': 10.0,
        })
        
        logger.info("触发限流后的策略状态:")
        facade.print_status()
        
        # 执行请求
        async def fetch(url: str, method: str, headers: dict, **kwargs):
            logger.info(f"执行限流模式下的请求：{url}")
            return {"data": "限流模式下的请求"}
        
        result = await facade.execute_with_strategies(
            request_func=fetch,
            url="https://www.eastmoney.com",
            method="GET"
        )
        logger.info(f"限流模式下请求成功：{result}")
        
    finally:
        # 恢复正常
        facade.enable_strategy('UARotatorStrategy')
        facade.update_config({
            'min_delay': 1.0,
            'max_delay': 3.0,
        })


# ========== 示例 4: 按层级管理策略 ==========

async def example_layer_management():
    """按层级管理策略示例"""
    logger.info("=" * 60)
    logger.info("示例 4: 按层级管理策略")
    logger.info("=" * 60)
    
    facade = AntiWindFacade(FULL_CONFIG)
    
    # 查看各层策略
    layer_strategies = facade.get_strategy_by_layer()
    logger.info("策略分层:")
    for layer, strategies in layer_strategies.items():
        logger.info(f"  L{layer}: {strategies}")
    
    # 获取 L2 层（伪装层）策略
    l2_strategies = facade.get_layer_strategies(2)
    logger.info(f"L2 层策略：{[s.__class__.__name__ for s in l2_strategies]}")
    
    # 禁用 L2 层（用于调试）
    for strategy in l2_strategies:
        strategy.disable()
    
    logger.info("禁用 L2 层后的状态:")
    facade.print_status()
    
    # 恢复 L2 层
    for strategy in l2_strategies:
        strategy.enable()


# ========== 示例 5: 服务层使用 ==========

class ExampleService:
    """示例服务层"""
    
    def __init__(self):
        # 服务层使用更保守的配置
        config = {
            **STANDARD_CONFIG,
            'min_delay': 2.0,
            'max_delay': 5.0,
            'max_retries': 3,
        }
        self.anti_wind = AntiWindFacade(config)
    
    async def fetch_market_data(self, date: str) -> Dict:
        """获取市场数据"""
        async def fetch(date: str):
            logger.info(f"获取 {date} 的市场数据")
            # 实际请求逻辑
            return {
                "date": date,
                "turnover": 10000000000,
                "change_percent": 1.5
            }
        
        return await self.anti_wind.execute_with_strategies(
            request_func=lambda: fetch(date),
            url="https://data.eastmoney.com/...",
            method="GET"
        )


async def example_service_usage():
    """服务层使用示例"""
    logger.info("=" * 60)
    logger.info("示例 5: 服务层使用")
    logger.info("=" * 60)
    
    service = ExampleService()
    
    try:
        data = await service.fetch_market_data("2026-04-09")
        logger.info(f"市场数据：{data}")
    except Exception as e:
        logger.error(f"获取市场数据失败：{e}")


# ========== 示例 6: 错误处理与降级 ==========

async def example_error_handling():
    """错误处理与降级示例"""
    logger.info("=" * 60)
    logger.info("示例 6: 错误处理与降级")
    logger.info("=" * 60)
    
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        attempt += 1
        logger.info(f"第 {attempt} 次尝试")
        
        try:
            async def fetch(url: str, method: str, headers: dict, **kwargs):
                # 模拟失败
                if attempt < 2:
                    raise Exception("模拟错误")
                logger.info(f"请求成功（第 {attempt} 次尝试）: {url}")
                return {"success": True}
            
            result = await facade.execute_with_strategies(
                request_func=fetch,
                url="https://www.eastmoney.com",
                method="GET"
            )
            logger.info(f"✅ 成功：{result}")
            break
            
        except Exception as e:
            logger.warning(f"尝试 {attempt} 失败：{e}")
            
            if attempt == 1:
                # 第一次失败：禁用 TLS 指纹
                logger.info("降级：禁用 TLS 指纹")
                facade.disable_strategy('TLSFingerprintStrategy')
            elif attempt == 2:
                # 第二次失败：禁用更多策略
                logger.info("降级：禁用 UA 轮换")
                facade.disable_strategy('UARotatorStrategy')
                facade.update_config({'min_delay': 5.0})
    
    # 重置策略
    facade.reset()


# ========== 示例 7: 批量请求 ==========

async def example_batch_requests():
    """批量请求示例"""
    logger.info("=" * 60)
    logger.info("示例 7: 批量请求")
    logger.info("=" * 60)
    
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    async def fetch_stock(symbol: str) -> Dict:
        """获取单个股票数据"""
        async def request(url: str, method: str, headers: dict, **kwargs):
            logger.debug(f"获取 {symbol}")
            await asyncio.sleep(0.1)  # 模拟请求
            return {"symbol": symbol, "price": 10.0 + len(symbol)}
        
        return await facade.execute_with_strategies(
            request_func=request,
            url=f"https://quote.eastmoney.com/{symbol}.html",
            method="GET"
        )
    
    # 批量获取（注意：AntiWindFacade 会自动限流）
    symbols = ["sz000001", "sz000002", "sh600000", "sh600036"]
    
    tasks = [fetch_stock(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("批量请求结果:")
    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            logger.error(f"  {symbol}: 失败 - {result}")
        else:
            logger.info(f"  {symbol}: {result}")


# ========== 示例 8: Cookie 管理 ==========

async def example_cookie_management():
    """Cookie 管理示例"""
    logger.info("=" * 60)
    logger.info("示例 8: Cookie 管理")
    logger.info("=" * 60)
    
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    # 获取 Cookie 策略
    cookie_strategy = facade.get_strategy('CookieInjectStrategy')
    
    if cookie_strategy:
        # 设置自定义 Cookie
        cookie_strategy.set_cookie('custom_key', 'custom_value')
        logger.info("已设置自定义 Cookie")
        
        # 获取 Cookie
        value = cookie_strategy.get_cookie('custom_key')
        logger.info(f"获取 Cookie: custom_key = {value}")
        
        # 清空 Cookie
        # cookie_strategy.clear_cookies()
        # logger.info("已清空所有 Cookie")


# ========== 主函数 ==========

async def main():
    """运行所有示例"""
    logger.info("\n" + "=" * 60)
    logger.info("AntiWindFacade 使用示例合集")
    logger.info("=" * 60 + "\n")
    
    # 运行示例
    await example_basic_usage()
    await example_adapter_usage()
    await example_dynamic_adjustment()
    await example_layer_management()
    await example_service_usage()
    await example_error_handling()
    await example_batch_requests()
    await example_cookie_management()
    
    logger.info("\n" + "=" * 60)
    logger.info("所有示例运行完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
