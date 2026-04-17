"""
ESG (环境、社会、治理) 数据爬虫

采集和计算ESG相关因子：
- E (Environment): 环境指标
- S (Social): 社会责任指标
- G (Governance): 公司治理指标
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ESGScore:
    """ESG评分结构"""
    symbol: str
    date: str
    
    # 综合评分 (0-100)
    total_score: float = 50.0
    
    # 分项评分
    e_score: float = 50.0  # 环境
    s_score: float = 50.0  # 社会
    g_score: float = 50.0  # 治理
    
    # 环境子维度
    carbon_emission: float = 50.0  # 碳排放
    energy_efficiency: float = 50.0  # 能源效率
    waste_management: float = 50.0  # 废物管理
    water_usage: float = 50.0  # 水资源使用
    
    # 社会子维度
    employee_satisfaction: float = 50.0  # 员工满意度
    product_safety: float = 50.0  # 产品安全
    community_involvement: float = 50.0  # 社区参与
    supply_chain_ethics: float = 50.0  # 供应链伦理
    
    # 治理子维度
    board_diversity: float = 50.0  # 董事会多样性
    executive_compensation: float = 50.0  # 高管薪酬
    shareholder_rights: float = 50.0  # 股东权利
    transparency: float = 50.0  # 信息透明度
    
    # 评级
    rating: str = "C"  # AAA, AA, A, BBB, BB, B, CCC, CC, C
    
    # 变化趋势
    score_change_1y: float = 0.0  # 年度变化
    industry_rank: Optional[int] = None  # 行业排名
    
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ESGEvent:
    """ESG事件"""
    event_type: str  # environmental, social, governance
    severity: str  # high, medium, low
    title: str
    description: str
    event_date: date
    impact_score: float  # -10 to 10
    source: str


class ESGCrawler:
    """
    ESG数据爬虫
    
    功能：
    - 多源ESG数据采集
    - ESG评分整合
    - ESG因子计算
    - ESG事件监测
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # ESG评分权重
        self.esg_weights = self.config.get('esg_weights', {
            'e': 0.33,
            's': 0.33,
            'g': 0.34
        })
        
        # 子维度权重
        self.dimension_weights = {
            'environment': {
                'carbon_emission': 0.3,
                'energy_efficiency': 0.25,
                'waste_management': 0.25,
                'water_usage': 0.2
            },
            'social': {
                'employee_satisfaction': 0.25,
                'product_safety': 0.25,
                'community_involvement': 0.25,
                'supply_chain_ethics': 0.25
            },
            'governance': {
                'board_diversity': 0.25,
                'executive_compensation': 0.25,
                'shareholder_rights': 0.25,
                'transparency': 0.25
            }
        }
        
        logger.info("ESG数据爬虫初始化完成")
    
    async def get_esg_scores(
        self,
        symbols: List[str],
        end_date: Optional[date] = None
    ) -> Dict[str, ESGScore]:
        """
        获取ESG评分
        
        Args:
            symbols: 股票代码列表
            end_date: 截止日期
            
        Returns:
            {symbol: ESGScore}
        """
        if end_date is None:
            end_date = date.today()
        
        results = {}
        
        for symbol in symbols:
            try:
                esg_score = await self._fetch_single_esg(symbol, end_date)
                if esg_score:
                    results[symbol] = esg_score
                    
            except Exception as e:
                logger.debug(f"获取{symbol}ESG数据失败: {e}")
                continue
        
        return results
    
    async def _fetch_single_esg(
        self,
        symbol: str,
        end_date: date
    ) -> Optional[ESGScore]:
        """获取单个股票的ESG数据"""
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            
            esg_data = await adapter.get_esg_data(symbol=symbol)
            
            if esg_data:
                return self._parse_esg_response(esg_data, symbol, end_date)
            
            logger.debug(f"Backend无{symbol}ESG数据，使用模拟数据")
            return await self._generate_mock_esg(symbol, end_date)
            
        except Exception as e:
            logger.warning(f"获取{symbol}ESG失败: {e}")
            return await self._generate_mock_esg(symbol, end_date)
    
    def _parse_esg_response(
        self,
        data: Dict[str, Any],
        symbol: str,
        end_date: date
    ) -> ESGScore:
        """解析ESG响应数据"""
        return ESGScore(
            symbol=symbol,
            date=str(end_date),
            total_score=data.get('total_score', 50.0),
            e_score=data.get('e_score', 50.0),
            s_score=data.get('s_score', 50.0),
            g_score=data.get('g_score', 50.0),
            rating=data.get('rating', 'C'),
            raw_data=data
        )
    
    async def _generate_mock_esg(
        self,
        symbol: str,
        end_date: date
    ) -> ESGScore:
        """生成模拟ESG数据（用于开发和测试）"""
        np.random.seed(hash(f"esg_{symbol}") % (2**32))
        
        base_score = np.random.uniform(30, 80)
        
        e_score = np.clip(base_score + np.random.randn() * 15, 0, 100)
        s_score = np.clip(base_score + np.random.randn() * 12, 0, 100)
        g_score = np.clip(base_score + np.random.randn() * 10, 0, 100)
        
        total_score = (
            e_score * self.esg_weights['e'] +
            s_score * self.esg_weights['s'] +
            g_score * self.esg_weights['g']
        )
        
        rating = self._score_to_rating(total_score)
        
        return ESGScore(
            symbol=symbol,
            date=str(end_date),
            total_score=total_score,
            e_score=e_score,
            s_score=s_score,
            g_score=g_score,
            
            # 环境子维度
            carbon_emission=np.clip(e_score + np.random.randn() * 10, 0, 100),
            energy_efficiency=np.clip(e_score + np.random.randn() * 8, 0, 100),
            waste_management=np.clip(e_score + np.random.randn() * 12, 0, 100),
            water_usage=np.clip(e_score + np.random.randn() * 9, 0, 100),
            
            # 社会子维度
            employee_satisfaction=np.clip(s_score + np.random.randn() * 11, 0, 100),
            product_safety=np.clip(s_score + np.random.randn() * 9, 0, 100),
            community_involvement=np.clip(s_score + np.random.randn() * 13, 0, 100),
            supply_chain_ethics=np.clip(s_score + np.random.randn() * 10, 0, 100),
            
            # 治理子维度
            board_diversity=np.clip(g_score + np.random.randn() * 8, 0, 100),
            executive_compensation=np.clip(g_score + np.random.randn() * 12, 0, 100),
            shareholder_rights=np.clip(g_score + np.random.randn() * 7, 0, 100),
            transparency=np.clip(g_score + np.random.randn() * 9, 0, 100),
            
            rating=rating,
            score_change_1y=np.random.uniform(-10, 15),
            industry_rank=np.random.randint(1, 100)
        )
    
    def _score_to_rating(self, score: float) -> str:
        """将分数转换为评级"""
        if score >= 90:
            return "AAA"
        elif score >= 80:
            return "AA"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "BBB"
        elif score >= 50:
            return "BB"
        elif score >= 40:
            return "B"
        elif score >= 30:
            return "CCC"
        elif score >= 20:
            return "CC"
        else:
            return "C"
    
    async def get_esg_events(
        self,
        symbol: str,
        days_back: int = 90
    ) -> List[ESGEvent]:
        """
        获取ESG事件
        
        Args:
            symbol: 股票代码
            days_back: 回溯天数
            
        Returns:
            List[ESGEvent]: ESG事件列表
        """
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            
            events = await adapter.get_esg_events(
                symbol=symbol,
                days_back=days_back
            )
            
            if events:
                return [self._parse_event(e) for e in events]
            
            return await self._generate_mock_events(symbol, days_back)
            
        except Exception as e:
            logger.warning(f"获取{symbol}ESG事件失败: {e}")
            return await self._generate_mock_events(symbol, days_back)
    
    def _parse_event(self, data: Dict[str, Any]) -> ESGEvent:
        """解析ESG事件数据"""
        return ESGEvent(
            event_type=data.get('event_type', 'governance'),
            severity=data.get('severity', 'medium'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            event_date=datetime.strptime(
                data.get('event_date', ''), '%Y-%m-%d'
            ).date() if data.get('event_date') else date.today(),
            impact_score=data.get('impact_score', 0),
            source=data.get('source', '')
        )
    
    async def _generate_mock_events(
        self,
        symbol: str,
        days_back: int = 90
    ) -> List[ESGEvent]:
        """生成模拟ESG事件"""
        mock_events = [
            ESGEvent(
                event_type="environmental",
                severity="low",
                title=f"{symbol}发布可持续发展报告",
                description="公司发布年度ESG报告",
                event_date=date.today() - timedelta(days=10),
                impact_score=3.0,
                source="公司公告"
            ),
            ESGEvent(
                event_type="governance",
                severity="medium",
                title=f"{symbol}董事会成员变动",
                description="独立董事增加",
                event_date=date.today() - timedelta(days=30),
                impact_score=2.0,
                source="监管文件"
            ),
            ESGEvent(
                event_type="social",
                severity="low",
                title=f"{symbol}员工培训计划",
                description="启动员工技能提升项目",
                event_date=date.today() - timedelta(days=45),
                impact_score=2.5,
                source="公司新闻"
            )
        ]
        
        return mock_events
    
    async def calculate_esg_factors(
        self,
        symbols: List[str],
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        批量计算ESG因子
        
        Args:
            symbols: 股票代码列表
            end_date: 截止日期
            
        Returns:
            {symbol: {factor_name: factor_value}}
        """
        from datetime import timedelta
        
        if end_date is None:
            end_date = date.today()
        
        all_factors = {}
        
        esg_scores = await self.get_esg_scores(symbols, end_date)
        
        for symbol, esg_data in esg_scores.items():
            try:
                factors = {
                    "symbol": symbol,
                    "date": str(end_date),
                    
                    # ESG综合得分（标准化到0-1）
                    "esg_total_score": esg_data.total_score / 100.0,
                    
                    # E/S/G分项得分
                    "esg_environment_score": esg_data.e_score / 100.0,
                    "esg_social_score": esg_data.s_score / 100.0,
                    "esg_governance_score": esg_data.g_score / 100.0,
                    
                    # 环境子因子
                    "esg_carbon_performance": esg_data.carbon_emission / 100.0,
                    "esg_energy_efficiency": esg_data.energy_efficiency / 100.0,
                    "esg_waste_management": esg_data.waste_management / 100.0,
                    
                    # 社会子因子
                    "esg_employee_welfare": esg_data.employee_satisfaction / 100.0,
                    "esg_product_responsibility": esg_data.product_safety / 100.0,
                    
                    # 治理子因子
                    "esg_board_quality": esg_data.board_diversity / 100.0,
                    "esg_transparency": esg_data.transparency / 100.0,
                    
                    # ESG动量（年度改善）
                    "esg_momentum_1y": esg_data.score_change_1y / 100.0,
                    
                    # 行业相对排名（倒数，值越小越好）
                    "esg_industry_rank_pct": (
                        1.0 - esg_data.industry_rank / 100.0
                    ) if esg_data.industry_rank else 0.5,
                    
                    # ESG评级编码（数值越高越好）
                    "esg_rating_code": self._rating_to_code(esg_data.rating),
                }
                
                # 获取ESG事件影响
                events = await self.get_esg_events(symbol, days_back=90)
                
                if events:
                    recent_impact = sum(
                        e.impact_score for e in events 
                        if (end_date - e.event_date).days <= 30
                    )
                    
                    negative_events = len([
                        e for e in events 
                        if e.impact_score < -3 and e.severity == 'high'
                    ])
                    
                    factors.update({
                        "esg_recent_event_impact": recent_impact / 10.0,
                        "esg_negative_event_count": float(negative_events),
                    })
                else:
                    factors.update({
                        "esg_recent_event_impact": 0.0,
                        "esg_negative_event_count": 0.0,
                    })
                
                all_factors[symbol] = factors
                
            except Exception as e:
                logger.debug(f"计算{symbol}ESG因子失败: {e}")
                continue
        
        return all_factors
    
    def _rating_to_code(self, rating: str) -> float:
        """将评级转换为数值"""
        rating_map = {
            'AAA': 9.0,
            'AA': 8.0,
            'A': 7.0,
            'BBB': 6.0,
            'BB': 5.0,
            'B': 4.0,
            'CCC': 3.0,
            'CC': 2.0,
            'C': 1.0
        }
        return rating_map.get(rating, 0.0) / 9.0
    
    async def get_industry_esg_comparison(
        self,
        symbols: List[str],
        industry_map: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        获取行业内ESG对比
        
        Args:
            symbols: 股票列表
            industry_map: {symbol: industry} 映射
            
        Returns:
            DataFrame: 行业对比数据
        """
        esg_scores = await self.get_esg_scores(symbols)
        
        records = []
        for symbol, esg in esg_scores.items():
            record = {
                'symbol': symbol,
                'industry': industry_map.get(symbol, 'unknown') if industry_map else 'unknown',
                'total_score': esg.total_score,
                'e_score': esg.e_score,
                's_score': esg.s_score,
                'g_score': esg.g_score,
                'rating': esg.rating,
                'rank_in_industry': esg.industry_rank
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        if not df.empty and 'industry' in df.columns:
            df['industry_avg'] = df.groupby('industry')['total_score'].transform('mean')
            df['industry_diff'] = df['total_score'] - df['industry_avg']
            df['percentile_in_industry'] = df.groupby('industry')['total_score'].rank(pct=True)
        
        return df


from datetime import timedelta