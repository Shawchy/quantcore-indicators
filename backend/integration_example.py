"""
统一数据模型和存储架构 - 集成示例

演示如何将新的统一数据模型、存储路由、指标计算等功能
集成到现有的数据源适配器中
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

# 导入新模块
from app.models.unified_models import UnifiedKLine, DataSourceType, AdjustType
from app.utils.data_normalizer import DataNormalizer
from app.storage.storage_router import StorageRouter
from app.storage.parquet_manager import ParquetManager
from app.services.indicators_manager import IndicatorsManager
from app.utils.cross_source_validator import CrossSourceValidator
from app.utils.data_source_health import DataSourceHealthChecker


class IntegratedDataAdapter:
    """
    集成示例：统一数据模型适配器
    
    展示如何将新的统一数据模型和存储架构
    集成到现有数据源适配器中
    """
    
    def __init__(self, source: DataSourceType):
        """
        初始化集成适配器
        
        Args:
            source: 数据源类型
        """
        self.source = source
        self.storage_router = StorageRouter(hot_threshold_days=90)
        self.parquet_manager = ParquetManager()
        self.indicators_manager = IndicatorsManager(prefer_talib=False)
        self.validator = CrossSourceValidator(tolerance=0.01)
        self.health_checker = DataSourceHealthChecker()
        
        logger.info(f"集成适配器初始化完成：{source.value}")
    
    async def fetch_and_process_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq"
    ) -> List[UnifiedKLine]:
        """
        获取并处理 K 线数据
        
        完整流程：
        1. 从数据源获取原始数据
        2. 标准化为统一格式
        3. 数据验证
        4. 智能存储
        5. 计算技术指标
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust_type: 复权类型
            
        Returns:
            统一格式的 K 线数据列表
        """
        logger.info(f"开始处理 {code} 的 K 线数据：{start_date} - {end_date}")
        
        # 步骤 1: 模拟从数据源获取原始数据
        # 实际使用时，这里调用 ef.stock.get_kline_data() 等 API
        raw_data = await self._fetch_raw_kline(code, start_date, end_date)
        logger.info(f"获取原始数据：{len(raw_data)} 条")
        
        # 步骤 2: 数据标准化
        unified_klines = []
        for data in raw_data:
            kline = DataNormalizer.normalize_kline(data, self.source)
            unified_klines.append(kline)
        
        logger.info(f"标准化完成：{len(unified_klines)} 条")
        
        # 步骤 3: 数据验证
        if len(unified_klines) > 0:
            is_valid = DataNormalizer.validate_kline(unified_klines[0])
            if not is_valid:
                logger.warning(f"数据验证失败：{code}")
        
        # 步骤 4: 智能存储（热数据→SQLite，冷数据→Parquet）
        for kline in unified_klines:
            await self.storage_router.save_kline(
                code,
                kline.model_dump(),
                adjust_type
            )
        
        logger.info(f"存储完成：{len(unified_klines)} 条")
        
        # 步骤 5: 计算技术指标（可选）
        # 将统一格式转换为 DataFrame
        df = self._klines_to_dataframe(unified_klines)
        if len(df) > 30:  # 至少需要 30 条数据才能计算指标
            df_with_indicators = self.indicators_manager.calculate_all_indicators(df)
            logger.info(f"指标计算完成，数据形状：{df_with_indicators.shape}")
        
        return unified_klines
    
    async def fetch_and_save_batch(
        self,
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ):
        """
        批量处理并保存 K 线数据
        
        Args:
            code: 股票代码
            klines: K 线数据列表
            adjust_type: 复权类型
        """
        logger.info(f"批量处理 {code} 的 {len(klines)} 条数据")
        
        # 标准化
        unified_klines = []
        for data in klines:
            kline = DataNormalizer.normalize_kline(data, self.source)
            unified_klines.append(kline)
        
        # 批量智能存储
        await self.storage_router.save_klines_batch(
            code,
            [k.model_dump() for k in unified_klines],
            adjust_type
        )
        
        logger.info(f"批量存储完成：{len(unified_klines)} 条")
    
    async def cross_source_validation(
        self,
        code: str,
        date: str
    ) -> Dict[str, Any]:
        """
        跨数据源一致性校验
        
        Args:
            code: 股票代码
            date: 日期
            
        Returns:
            校验结果
        """
        # 模拟从多个数据源获取数据
        klines_source1 = await self._fetch_raw_kline(code, date, date)
        klines_source2 = await self._fetch_raw_kline(code, date, date)
        
        # 标准化
        klines1 = [DataNormalizer.normalize_kline(k, self.source) for k in klines_source1]
        klines2 = [DataNormalizer.normalize_kline(k, DataSourceType.AKSHARE) for k in klines_source2]
        
        # 校验
        result = await self.validator.validate(
            code,
            date,
            [klines1, klines2],
            [self.source, DataSourceType.AKSHARE]
        )
        
        return result
    
    async def check_data_source_health(self) -> Dict[str, Dict[str, Any]]:
        """
        检查数据源健康状态
        
        Returns:
            健康状态字典
        """
        result = await self.health_checker.check_all_sources()
        return result
    
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        模拟获取原始 K 线数据
        
        实际使用时替换为真实的数据源 API 调用
        """
        # 这里应该调用实际的数据源 API
        # 例如：ef.stock.get_kline_data(code, start_date, end_date)
        
        # 模拟数据
        import random
        from datetime import timedelta
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        klines = []
        current = start
        base_price = 10.0
        
        while current <= end:
            # 跳过周末
            if current.weekday() < 5:
                change = random.uniform(-0.05, 0.05)
                base_price *= (1 + change)
                
                kline = {
                    "股票代码": code,
                    "日期": current.strftime("%Y-%m-%d"),
                    "开盘": round(base_price * 0.99, 2),
                    "最高": round(base_price * 1.02, 2),
                    "最低": round(base_price * 0.98, 2),
                    "收盘": round(base_price, 2),
                    "成交量": random.randint(100000, 10000000),
                    "成交额": random.randint(1000000, 100000000),
                    "换手率": round(random.uniform(0.5, 5.0), 2)
                }
                klines.append(kline)
            
            current += timedelta(days=1)
        
        return klines
    
    def _klines_to_dataframe(self, klines: List[UnifiedKLine]) -> Any:
        """
        将统一 K 线数据转换为 DataFrame
        
        Args:
            klines: 统一 K 线数据列表
            
        Returns:
            pandas DataFrame
        """
        import pandas as pd
        
        data = []
        for k in klines:
            data.append({
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount
            })
        
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df


async def main():
    """集成测试示例"""
    print("=" * 60)
    print("统一数据模型和存储架构 - 集成示例")
    print("=" * 60)
    
    # 创建集成适配器
    adapter = IntegratedDataAdapter(DataSourceType.EFINANCE)
    
    # 示例 1: 获取并处理 K 线数据
    print("\n示例 1: 获取并处理 K 线数据")
    klines = await adapter.fetch_and_process_kline(
        code="600000",
        start_date="2024-01-01",
        end_date="2024-03-31",
        adjust_type="qfq"
    )
    print(f"处理完成：{len(klines)} 条")
    
    # 示例 2: 批量处理数据
    print("\n示例 2: 批量处理数据")
    sample_klines = [
        {
            "股票代码": "600000",
            "日期": "2024-04-01",
            "开盘": 11.0,
            "最高": 11.3,
            "最低": 10.9,
            "收盘": 11.2,
            "成交量": 5000000,
            "成交额": 56000000,
            "换手率": 2.5
        },
        {
            "股票代码": "600000",
            "日期": "2024-04-02",
            "开盘": 11.2,
            "最高": 11.5,
            "最低": 11.1,
            "收盘": 11.4,
            "成交量": 5500000,
            "成交额": 62700000,
            "换手率": 2.8
        }
    ]
    await adapter.fetch_and_save_batch("600000", sample_klines)
    
    # 示例 3: 检查数据源健康状态
    print("\n示例 3: 检查数据源健康状态")
    health_status = await adapter.check_data_source_health()
    for source, status in health_status.items():
        print(f"{source}: {status.get('status', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("集成示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
