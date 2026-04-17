"""
Alpha工厂 - 集成管理层

整合所有Alpha工厂组件：
- 因子计算引擎
- 因子存储系统
- 数据源适配器
- 风险模型
- 组合优化器
- 另类数据采集

提供统一的工作流接口。
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AlphaFactoryConfig:
    """Alpha工厂配置"""
    
    # 数据源配置
    data_source: str = "backend"  # backend, mock, file
    
    # 因子计算配置
    enable_market_factors: bool = True
    enable_fundamental_factors: bool = True
    enable_alternative_factors: bool = True
    enable_structured_factors: bool = True
    
    # 风险模型配置
    risk_model: str = "barra_cne5"  # barra_cne5, barra_cne6
    
    # 优化器配置
    default_optimizer: str = "mean_variance"
    
    # 另类数据配置
    enable_fund_flow: bool = True
    enable_sentiment: bool = True
    enable_esg: bool = True
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl_hours: int = 24


@dataclass 
class FactorProductionResult:
    """因子生产结果"""
    production_time: datetime
    factors: Dict[str, pd.DataFrame]  # {factor_name: DataFrame}
    summary: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class PortfolioOptimizationResult:
    """组合优化结果"""
    optimization_time: datetime
    weights: pd.Series  # {asset: weight}
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    factor_exposures: Optional[pd.DataFrame] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    optimizer_used: str = ""


class AlphaFactory:
    """
    Alpha工厂主类
    
    功能：
    - 统一管理所有因子生产流程
    - 协调数据获取、计算、存储
    - 提供组合优化接口
    - 工作流编排和监控
    """
    
    def __init__(self, config: Optional[AlphaFactoryConfig] = None):
        self.config = config or AlphaFactoryConfig()
        
        # 初始化各组件（延迟初始化）
        self._engine = None
        self._storage = None
        self._risk_model = None
        self._optimizers = {}
        self._crawlers = {}
        
        # 运行状态
        self._is_initialized = False
        self._last_production_time: Optional[datetime] = None
        
        logger.info("Alpha工厂初始化完成")
    
    async def initialize(self):
        """初始化所有组件"""
        if self._is_initialized:
            return
        
        try:
            from quantcore.alpha.engine.calculator import FactorCalculator
            from quantcore.alpha.storage.factor_db import FactorStorage
            
            self._engine = FactorCalculator()
            self._storage = FactorStorage()
            
            # 初始化风险模型
            await self._init_risk_model()
            
            # 初始化优化器
            await self._init_optimizers()
            
            # 初始化另类数据爬虫
            await self._init_crawlers()
            
            self._is_initialized = True
            logger.info("Alpha工厂所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"Alpha工厂初始化失败: {e}")
            raise
    
    async def _init_risk_model(self):
        """初始化风险模型"""
        try:
            from quantcore.alpha.risk.barra_model import BarraRiskModel
            
            model_type = self.config.risk_model
            self._risk_model = BarraRiskModel(model_type=model_type)
            await self._risk_model.initialize()
            
            logger.info(f"风险模型初始化完成: {model_type}")
            
        except Exception as e:
            logger.warning(f"风险模型初始化失败: {e}")
            self._risk_model = None
    
    async def _init_optimizers(self):
        """初始化优化器"""
        try:
            from quantcore.alpha.optimizer.mean_variance import (
                MeanVarianceOptimizer
            )
            from quantcore.alpha.optimizer.risk_parity import RiskParityOptimizer
            from quantcore.alpha.optimizer.black_litterman import (
                BlackLittermanOptimizer
            )
            from quantcore.alpha.optimizer.max_diversification import (
                MaxDiversificationOptimizer
            )
            from quantcore.alpha.optimizer.factor_constraints import (
                FactorConstrainedOptimizer
            )
            
            self._optimizers = {
                'mean_variance': MeanVarianceOptimizer(),
                'risk_parity': RiskParityOptimizer(),
                'black_litterman': BlackLittermanOptimizer(),
                'max_diversification': MaxDiversificationOptimizer(),
                'factor_constrained': FactorConstrainedOptimizer(),
            }
            
            logger.info("优化器初始化完成")
            
        except Exception as e:
            logger.warning(f"优化器初始化失败: {e}")
    
    async def _init_crawlers(self):
        """初始化另类数据爬虫"""
        try:
            from quantcore.alpha.alternative.raw.fund_flow_crawler import (
                FundFlowCrawler
            )
            from quantcore.alpha.alternative.raw.sentiment_crawler import (
                SentimentCrawler
            )
            from quantcore.alpha.alternative.raw.esg_crawler import ESGCrawler
            
            if self.config.enable_fund_flow:
                self._crawlers['fund_flow'] = FundFlowCrawler()
            
            if self.config.enable_sentiment:
                self._crawlers['sentiment'] = SentimentCrawler()
            
            if self.config.enable_esg:
                self._crawlers['esg'] = ESGCrawler()
            
            logger.info("另类数据爬虫初始化完成")
            
        except Exception as e:
            logger.warning(f"另类数据爬虫初始化失败: {e}")
    
    async def produce_factors(
        self,
        symbols: List[str],
        end_date: Optional[date] = None,
        factor_types: Optional[List[str]] = None
    ) -> FactorProductionResult:
        """
        执行因子生产流程
        
        Args:
            symbols: 股票代码列表
            end_date: 截止日期
            factor_types: 因子类型列表 (可选: market, fundamental, alternative, structured)
            
        Returns:
            FactorProductionResult: 生产结果
        """
        await self.initialize()
        
        if end_date is None:
            end_date = date.today()
        
        start_time = datetime.now()
        all_factors = {}
        errors = []
        
        # 确定要生产的因子类型
        if factor_types is None:
            factor_types = []
            if self.config.enable_market_factors:
                factor_types.append('market')
            if self.config.enable_fundamental_factors:
                factor_types.append('fundamental')
            if self.config.enable_alternative_factors:
                factor_types.append('alternative')
            if self.config.enable_structured_factors:
                factor_types.append('structured')
        
        # 并行执行各类因子计算
        tasks = []
        
        for factor_type in factor_types:
            if factor_type == 'market':
                tasks.append(
                    self._produce_market_factors(symbols, end_date)
                )
            elif factor_type == 'fundamental':
                tasks.append(
                    self._produce_fundamental_factors(symbols, end_date)
                )
            elif factor_type == 'alternative':
                tasks.append(
                    self._produce_alternative_factors(symbols, end_date)
                )
            elif factor_type == 'structured':
                tasks.append(
                    self._produce_structured_factors(symbols, end_date)
                )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif isinstance(result, dict):
                all_factors.update(result)
        
        # 存储因子数据
        if self._storage and all_factors:
            try:
                for factor_name, factor_df in all_factors.items():
                    await self._storage.save_factor(
                        factor_name=factor_name,
                        data=factor_df,
                        date=end_date
                    )
            except Exception as e:
                errors.append(f"因子存储失败: {e}")
        
        # 更新最后生产时间
        self._last_production_time = datetime.now()
        
        # 构建结果摘要
        summary = {
            'production_time': start_time.isoformat(),
            'symbols_count': len(symbols),
            'factors_produced': list(all_factors.keys()),
            'factors_count': len(all_factors),
            'errors_count': len(errors),
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        }
        
        return FactorProductionResult(
            production_time=start_time,
            factors=all_factors,
            summary=summary,
            errors=errors
        )
    
    async def _produce_market_factors(
        self,
        symbols: List[str],
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """生产市场数据因子"""
        try:
            from quantcore.alpha.factors.market import MarketFactorLibrary
            
            library = MarketFactorLibrary()
            
            factors = {}
            
            for symbol in symbols[:10]:  # 限制数量避免超时
                try:
                    factor_data = await library.calculate_all_factors(symbol)
                    if factor_data:
                        factors[f'market_{symbol}'] = pd.DataFrame([factor_data])
                except Exception as e:
                    logger.debug(f"计算{symbol}市场因子失败: {e}")
                    continue
            
            return factors
            
        except Exception as e:
            logger.error(f"市场因子生产失败: {e}")
            return {}
    
    async def _produce_fundamental_factors(
        self,
        symbols: List[str],
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """生产基本面因子"""
        try:
            from quantcore.alpha.factors.fundamental import FundamentalFactorLibrary
            
            library = FundamentalFactorLibrary()
            
            factors = {}
            
            for symbol in symbols[:10]:
                try:
                    factor_data = await library.calculate_all_factors(symbol)
                    if factor_data:
                        factors[f'fundamental_{symbol}'] = pd.DataFrame([factor_data])
                except Exception as e:
                    logger.debug(f"计算{symbol}基本面因子失败: {e}")
                    continue
            
            return factors
            
        except Exception as e:
            logger.error(f"基本面因子生产失败: {e}")
            return {}
    
    async def _produce_alternative_factors(
        self,
        symbols: List[str],
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """生产另类数据因子"""
        factors = {}
        
        # 资金流向因子
        if 'fund_flow' in self._crawlers:
            try:
                crawler = self._crawlers['fund_flow']
                fund_factors = await crawler.calculate_fund_flow_factors(
                    symbols, end_date
                )
                
                if fund_factors:
                    df = pd.DataFrame.from_dict(fund_factors, orient='index')
                    factors['fund_flow'] = df
                    
            except Exception as e:
                logger.error(f"资金流向因子生产失败: {e}")
        
        # 舆情因子
        if 'sentiment' in self._crawlers:
            try:
                crawler = self._crawlers['sentiment']
                sentiment_factors = await crawler.calculate_sentiment_factors(
                    symbols, end_date
                )
                
                if sentiment_factors:
                    df = pd.DataFrame.from_dict(sentiment_factors, orient='index')
                    factors['sentiment'] = df
                    
            except Exception as e:
                logger.error(f"舆情因子生产失败: {e}")
        
        # ESG因子
        if 'esg' in self._crawlers:
            try:
                crawler = self._crawlers['esg']
                esg_factors = await crawler.calculate_esg_factors(
                    symbols, end_date
                )
                
                if esg_factors:
                    df = pd.DataFrame.from_dict(esg_factors, orient='index')
                    factors['esg'] = df
                    
            except Exception as e:
                logger.error(f"ESG因子生产失败: {e}")
        
        return factors
    
    async def _produce_structured_factors(
        self,
        symbols: List[str],
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """生产结构化另类因子"""
        try:
            from quantcore.alpha.factors.structured import StructuredFactorLibrary
            
            library = StructuredFactorLibrary()
            
            factors = {}
            
            for symbol in symbols[:10]:
                try:
                    factor_data = await library.calculate_all_factors(symbol)
                    if factor_data:
                        factors[f'structured_{symbol}'] = pd.DataFrame([factor_data])
                except Exception as e:
                    logger.debug(f"计算{symbol}结构化因子失败: {e}")
                    continue
            
            return factors
            
        except Exception as e:
            logger.error(f"结构化因子生产失败: {e}")
            return {}
    
    async def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        method: Optional[str] = None,
        **kwargs
    ) -> PortfolioOptimizationResult:
        """
        执行组合优化
        
        Args:
            returns: 资产收益率数据
            method: 优化方法
            **kwargs: 优化参数
            
        Returns:
            PortfolioOptimizationResult: 优化结果
        """
        await self.initialize()
        
        method = method or self.config.default_optimizer
        
        optimizer = self._optimizers.get(method)
        
        if not optimizer:
            raise ValueError(f"未知的优化方法: {method}")
        
        try:
            result = await optimizer.optimize(returns=returns, **kwargs)
            
            return PortfolioOptimizationResult(
                optimization_time=datetime.now(),
                weights=result.weights,
                expected_return=result.expected_return,
                expected_risk=result.risk,
                sharpe_ratio=result.sharpe_ratio,
                factor_exposures=getattr(result, 'factor_exposures', None),
                metrics={
                    'status': result.status,
                    'iterations': getattr(result, 'iterations', 0),
                },
                optimizer_used=method
            )
            
        except Exception as e:
            logger.error(f"组合优化失败: {e}")
            raise
    
    async def get_risk_analysis(
        self,
        positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        获取风险分析
        
        Args:
            positions: {asset: weight} 持仓
            
        Returns:
            Dict: 风险分析结果
        """
        await self.initialize()
        
        if not self._risk_model:
            return {'error': '风险模型未初始化'}
        
        try:
            risk_analysis = await self._risk_model.analyze_portfolio(positions)
            return risk_analysis
            
        except Exception as e:
            logger.error(f"风险分析失败: {e}")
            return {'error': str(e)}
    
    async def run_full_pipeline(
        self,
        symbols: List[str],
        returns: pd.DataFrame,
        optimization_method: str = "mean_variance"
    ) -> Dict[str, Any]:
        """
        运行完整流水线
        
        Args:
            symbols: 股票列表
            returns: 收益率数据
            optimization_method: 优化方法
            
        Returns:
            Dict: 完整结果
        """
        logger.info("开始运行Alpha工厂完整流水线...")
        
        results = {
            'pipeline_start': datetime.now().isoformat(),
            'status': 'running'
        }
        
        try:
            # Step 1: 因子生产
            logger.info("Step 1: 生产因子...")
            factor_result = await self.produce_factors(symbols)
            results['factor_production'] = {
                'summary': factor_result.summary,
                'factors_count': len(factor_result.factors),
                'errors': factor_result.errors
            }
            
            # Step 2: 组合优化
            logger.info("Step 2: 组合优化...")
            opt_result = await self.optimize_portfolio(
                returns, 
                method=optimization_method
            )
            results['portfolio_optimization'] = {
                'expected_return': opt_result.expected_return,
                'expected_risk': opt_result.expected_risk,
                'sharpe_ratio': opt_result.sharpe_ratio,
                'optimizer': opt_result.optimizer_used
            }
            
            # Step 3: 风险分析
            if opt_result.weights is not None:
                logger.info("Step 3: 风险分析...")
                positions = opt_result.weights.to_dict()
                risk_analysis = await self.get_risk_analysis(positions)
                results['risk_analysis'] = risk_analysis
            
            results['status'] = 'completed'
            results['pipeline_end'] = datetime.now().isoformat()
            
            duration = (
                datetime.now() - 
                datetime.fromisoformat(results['pipeline_start'])
            ).total_seconds()
            results['duration_seconds'] = duration
            
            logger.info(f"流水线执行完成，耗时: {duration:.2f}秒")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            logger.error(f"流水线执行失败: {e}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取工厂状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'initialized': self._is_initialized,
            'last_production': (
                self._last_production_time.isoformat() 
                if self._last_production_time else None
            ),
            'available_optimizers': list(self._optimizers.keys()),
            'available_crawlers': list(self._crawlers.keys()),
            'risk_model': (
                self._risk_model.model_type 
                if self._risk_model else None
            ),
            'config': {
                'data_source': self.config.data_source,
                'default_optimizer': self.config.default_optimizer,
                'risk_model': self.config.risk_model,
            }
        }


__all__ = [
    'AlphaFactory',
    'AlphaFactoryConfig',
    'FactorProductionResult',
    'PortfolioOptimizationResult',
]
