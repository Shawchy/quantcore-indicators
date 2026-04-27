# 优化模块 2: 智能文本过滤器

## 📊 设计概述

### 问题背景

每日获取的文本数据量巨大:
- 新闻: 8000 条
- 公告: 250 条
- 社交媒体: 50000 条
- 研报: 50 条
- **总计: 58300 条/天**

如果全部送入 LLM 分析:
- 计算成本: 58300 × 100ms = 5830 秒 ≈ 1.6 小时
- API 费用: 58300 × 0.01 元 = 583 元/天 ≈ 17500 元/月
- 实际价值: 大量重复、低质量、无关内容

### 解决方案

设计**智能文本过滤器**，实现:
- ✅ 去重过滤 (相同新闻只分析一次)
- ✅ 相关性过滤 (只分析持仓/关注列表相关)
- ✅ 质量过滤 (过滤广告、水帖)
- ✅ 重要性过滤 (优先处理高价值文本)

**预期效果**:
- 处理量: 58300 条 → 5000 条 (减少 91%)
- 计算成本: 降低 91%
- 响应延迟: 降低 95%
- API 费用: 583 元/天 → 53 元/天 (降低 91%)

---

## 🏗️ 过滤管线架构

```
┌─────────────────────────────────────────────────────────┐
│              原始文本 (58300 条/天)                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           过滤器 1: 快速去重 (规则)                       │
│                                                         │
│  方法:                                                   │
│  - MD5 Hash (标题 + 发布时间)                            │
│  - SimHash (内容相似度)                                  │
│  - 时间窗口 (24 小时内重复)                              │
│                                                         │
│  过滤率: 58300 → 35000 条 (40%)                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           过滤器 2: 相关性过滤 (规则)                     │
│                                                         │
│  方法:                                                   │
│  - 股票代码匹配 (6 位数字)                               │
│  - 股票名称匹配 (贵州茅台/600519)                        │
│  - 行业板块匹配 (白酒/新能源/芯片)                       │
│  - 关注列表匹配 (用户自选股)                             │
│                                                         │
│  过滤率: 35000 → 15000 条 (57%)                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           过滤器 3: 质量评估 (轻量模型)                   │
│                                                         │
│  方法:                                                   │
│  - 文本长度检查 (< 10 字 = 低质量)                      │
│  - 广告检测 (含"广告/推广/点击"等)                      │
│  - 垃圾内容检测 (重复字符、无意义内容)                    │
│  - 语言检测 (非中文)                                     │
│                                                         │
│  过滤率: 15000 → 10000 条 (33%)                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           过滤器 4: 重要性排序 (规则 + 统计)              │
│                                                         │
│  方法:                                                   │
│  - 关键词评分 (业绩/并购/政策 = 高)                     │
│  - 来源权重 (官方 > 媒体 > 社交)                        │
│  - 时效性评分 (新 > 旧)                                  │
│  - 情绪强度 (极端情绪 = 重要)                            │
│                                                         │
│  过滤率: 10000 → 5000 条 (50%)                          │
│  最终输出: 按重要性排序                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              高质量文本 (5000 条/天)                      │
│           ↓ 送入 LLM 分析                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. 去重过滤器

```python
# backend/app/services/text_filter/dedup_filter.py

from typing import List, Set, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib

from ...models.text_data import TextItem


class DedupFilter:
    """文本去重过滤器"""
    
    def __init__(
        self,
        cache_size: int = 100000,
        time_window_hours: int = 24
    ):
        """
        Args:
            cache_size: 缓存大小
            time_window_hours: 去重时间窗口 (小时)
        """
        self.cache_size = cache_size
        self.time_window = timedelta(hours=time_window_hours)
        
        # 缓存: {text_id: fetch_time}
        self._cache: OrderedDict[str, datetime] = OrderedDict()
        
        # 统计
        self._stats = {
            "total_input": 0,
            "duplicates_removed": 0,
        }
    
    def filter(self, texts: List[TextItem]) -> List[TextItem]:
        """
        去重过滤
        
        Args:
            texts: 原始文本列表
        
        Returns:
            List[TextItem]: 去重后的文本列表
        """
        unique_texts = []
        
        for text in texts:
            self._stats["total_input"] += 1
            
            # 生成唯一 ID
            text_id = self._generate_id(text)
            
            # 检查是否在缓存中
            if text_id in self._cache:
                # 检查是否在时间窗口内
                last_seen = self._cache[text_id]
                if datetime.now() - last_seen < self.time_window:
                    # 重复，跳过
                    self._stats["duplicates_removed"] += 1
                    continue
            
            # 新文本，加入缓存
            self._cache[text_id] = datetime.now()
            unique_texts.append(text)
            
            # 维护缓存大小
            if len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)  # 移除最老的
        
        return unique_texts
    
    def _generate_id(self, text: TextItem) -> str:
        """生成文本唯一 ID"""
        # 方法 1: 基于标题 + 发布时间
        key = f"{text.title}_{text.publish_time.strftime('%Y%m%d')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_input": self._stats["total_input"],
            "duplicates_removed": self._stats["duplicates_removed"],
            "dedup_rate": (
                self._stats["duplicates_removed"] / 
                max(1, self._stats["total_input"])
            ),
            "cache_size": len(self._cache),
        }
```

---

### 2. 相关性过滤器

```python
# backend/app/services/text_filter/relevance_filter.py

from typing import List, Set, Optional, Dict
import re

from ...models.text_data import TextItem, TextRelevance


class RelevanceFilter:
    """文本相关性过滤器"""
    
    def __init__(
        self,
        watchlist: Optional[Set[str]] = None,
        min_relevance: TextRelevance = TextRelevance.INDIRECT
    ):
        """
        Args:
            watchlist: 关注列表 (股票代码)
            min_relevance: 最低相关性要求
        """
        self.watchlist = watchlist or set()
        self.min_relevance = min_relevance
        
        # 股票名称映射 (可扩展)
        self._symbol_name_map: Dict[str, str] = {
            "600519.SH": "贵州茅台",
            "600000.SH": "浦发银行",
            "000001.SZ": "平安银行",
            # ... 更多映射
        }
        
        # 行业板块关键词
        self._sector_keywords: Dict[str, List[str]] = {
            "白酒": ["白酒", "五粮液", "泸州老窖", "汾酒"],
            "新能源": ["新能源", "光伏", "风电", "储能", "锂电"],
            "芯片": ["芯片", "半导体", "集成电路", "晶圆"],
            "银行": ["银行", "信贷", "降息", "LPR"],
            "券商": ["券商", "证券", "经纪", "投行"],
        }
        
        # 统计
        self._stats = {
            "total_input": 0,
            "filtered_by_relevance": 0,
        }
    
    def filter(self, texts: List[TextItem]) -> List[TextItem]:
        """相关性过滤"""
        relevant_texts = []
        
        for text in texts:
            self._stats["total_input"] += 1
            
            # 检查相关性
            if self._is_relevant(text):
                relevant_texts.append(text)
            else:
                self._stats["filtered_by_relevance"] += 1
        
        return relevant_texts
    
    def _is_relevant(self, text: TextItem) -> bool:
        """判断文本是否相关"""
        # 方法 1: 检查相关股票
        if text.related_symbols:
            # 与关注列表有交集
            if set(text.related_symbols) & self.watchlist:
                return True
        
        # 方法 2: 从标题和内容中提取相关性
        full_text = f"{text.title} {text.content}"
        
        # 检查是否包含关注列表中的股票
        for symbol in self.watchlist:
            if self._text_mentions_symbol(full_text, symbol):
                return True
        
        # 方法 3: 检查行业板块
        if text.related_sectors:
            # 关注列表中的股票所属行业
            watchlist_sectors = self._get_sectors_from_symbols(
                self.watchlist
            )
            if set(text.related_sectors) & watchlist_sectors:
                return True
        
        # 方法 4: 检查行业关键词
        for sector, keywords in self._sector_keywords.items():
            if sector in watchlist_sectors:
                for keyword in keywords:
                    if keyword in full_text:
                        return True
        
        return False
    
    def _text_mentions_symbol(
        self,
        text: str,
        symbol: str
    ) -> bool:
        """检查文本是否提及某股票"""
        # 检查股票代码
        symbol_code = symbol.split(".")[0]
        if symbol_code in text:
            return True
        
        # 检查股票名称
        symbol_name = self._symbol_name_map.get(symbol, "")
        if symbol_name and symbol_name in text:
            return True
        
        return False
    
    def _get_sectors_from_symbols(
        self,
        symbols: Set[str]
    ) -> Set[str]:
        """从股票代码获取行业板块"""
        # 简化实现，实际应从数据库查询
        sectors = set()
        for symbol in symbols:
            # 根据代码前缀判断行业
            if symbol.startswith("600519"):
                sectors.add("白酒")
            elif symbol.startswith("600000"):
                sectors.add("银行")
            # ... 更多映射
        
        return sectors
    
    def update_watchlist(self, symbols: Set[str]):
        """更新关注列表"""
        self.watchlist = symbols
```

---

### 3. 质量评估过滤器

```python
# backend/app/services/text_filter/quality_filter.py

from typing import List, Optional
import re

from ...models.text_data import TextItem


class QualityFilter:
    """文本质量评估过滤器"""
    
    # 广告关键词
    AD_KEYWORDS = [
        "广告", "推广", "点击", "链接", "购买",
        "优惠", "特价", "促销", "限时", "抢购",
    ]
    
    # 垃圾内容模式
    SPAM_PATTERNS = [
        r'(.)\1{10,}',  # 重复字符 (> 10 次)
        r'[a-zA-Z]{50,}',  # 长英文串 (> 50 字符)
        r'URL|url|http',  # URL 链接
    ]
    
    # 低质量模式
    LOW_QUALITY_PATTERNS = [
        r'^.{0,10}$',  # 太短 (< 10 字)
        r'^(.+?)\1+$',  # 完全重复
    ]
    
    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 50000,
        min_quality_score: float = 0.3
    ):
        """
        Args:
            min_length: 最小文本长度
            max_length: 最大文本长度
            min_quality_score: 最低质量评分
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_quality_score = min_quality_score
        
        # 预编译正则
        self._spam_regex = [
            re.compile(p, re.IGNORECASE)
            for p in self.SPAM_PATTERNS
        ]
        self._low_quality_regex = [
            re.compile(p, re.IGNORECASE | re.DOTALL)
            for p in self.LOW_QUALITY_PATTERNS
        ]
        
        # 统计
        self._stats = {
            "total_input": 0,
            "filtered_by_quality": 0,
        }
    
    def filter(self, texts: List[TextItem]) -> List[TextItem]:
        """质量过滤"""
        high_quality_texts = []
        
        for text in texts:
            self._stats["total_input"] += 1
            
            # 评估质量
            score = self._evaluate_quality(text)
            
            if score >= self.min_quality_score:
                text.quality_score = score
                high_quality_texts.append(text)
            else:
                self._stats["filtered_by_quality"] += 1
        
        return high_quality_texts
    
    def _evaluate_quality(self, text: TextItem) -> float:
        """评估文本质量 (0-1)"""
        content = f"{text.title} {text.content}"
        score = 1.0  # 初始满分
        
        # 检查 1: 文本长度
        if len(content) < self.min_length:
            score *= 0.1  # 太短，大幅扣分
        
        if len(content) > self.max_length:
            score *= 0.5  # 太长，适当扣分
        
        # 检查 2: 广告检测
        for keyword in self.AD_KEYWORDS:
            if keyword in content:
                score *= 0.2  # 含广告词，大幅扣分
                break
        
        # 检查 3: 垃圾内容检测
        for regex in self._spam_regex:
            if regex.search(content):
                score *= 0.3  # 垃圾内容，大幅扣分
                break
        
        # 检查 4: 低质量检测
        for regex in self._low_quality_regex:
            if regex.match(content):
                score *= 0.5  # 低质量，扣分
                break
        
        return max(0.0, min(1.0, score))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_input": self._stats["total_input"],
            "filtered_by_quality": self._stats["filtered_by_quality"],
            "filter_rate": (
                self._stats["filtered_by_quality"] /
                max(1, self._stats["total_input"])
            ),
        }
```

---

### 4. 重要性排序器

```python
# backend/app/services/text_filter/importance_ranker.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ...models.text_data import TextItem, TextImportance


class ImportanceRanker:
    """文本重要性排序器"""
    
    # 高重要性关键词
    HIGH_IMPORTANCE_KEYWORDS = [
        # 业绩类
        "净利润", "营收", "业绩", "盈利", "亏损",
        "超预期", "不及预期", "同比增长", "环比增长",
        
        # 重大事件
        "并购", "重组", "收购", "出售",
        "上市", "退市", "ST", "*ST",
        "涨停", "跌停", "异动", "停牌",
        
        # 政策类
        "央行", "降准", "降息", "加息",
        "证监会", "监管", "处罚", "调查",
        "政策", "新规", "意见征求",
        
        # 资金类
        "涨停", "放量", "北向", "南向",
        "主力", "机构", "外资", "增持",
    ]
    
    # 来源权重
    SOURCE_WEIGHTS = {
        "官方公告": 1.0,
        "证监会": 1.0,
        "央行": 1.0,
        "权威媒体": 0.9,
        "财经媒体": 0.8,
        "社交媒体": 0.6,
        "股吧论坛": 0.4,
    }
    
    def __init__(
        self,
        top_n: int = 5000
    ):
        """
        Args:
            top_n: 返回前 N 条最重要文本
        """
        self.top_n = top_n
    
    def rank(self, texts: List[TextItem]) -> List[TextItem]:
        """重要性排序"""
        # 计算每条文本的重要性评分
        scored_texts = []
        
        for text in texts:
            score = self._calculate_importance(text)
            scored_texts.append((text, score))
        
        # 按评分降序排序
        scored_texts.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 N 条
        return [text for text, score in scored_texts[:self.top_n]]
    
    def _calculate_importance(self, text: TextItem) -> float:
        """计算文本重要性评分"""
        content = f"{text.title} {text.content}"
        score = 0.0
        
        # 因素 1: 关键词评分 (0-0.4)
        keyword_score = self._keyword_score(content)
        score += keyword_score * 0.4
        
        # 因素 2: 来源权重 (0-0.3)
        source_score = self._source_score(text)
        score += source_score * 0.3
        
        # 因素 3: 时效性 (0-0.2)
        time_score = self._time_score(text)
        score += time_score * 0.2
        
        # 因素 4: 情绪强度 (0-0.1)
        sentiment_score = self._sentiment_score(content)
        score += sentiment_score * 0.1
        
        return score
    
    def _keyword_score(self, content: str) -> float:
        """关键词评分"""
        match_count = 0
        for keyword in self.HIGH_IMPORTANCE_KEYWORDS:
            if keyword in content:
                match_count += 1
        
        # 归一化到 0-1
        return min(1.0, match_count / 5)  # 最多 5 个关键词
    
    def _source_score(self, text: TextItem) -> float:
        """来源权重评分"""
        # 根据提供商判断来源类型
        provider = text.provider.lower()
        
        for source_type, weight in self.SOURCE_WEIGHTS.items():
            if source_type.lower() in provider:
                return weight
        
        # 默认权重
        return 0.5
    
    def _time_score(self, text: TextItem) -> float:
        """时效性评分"""
        now = datetime.now()
        age = now - text.publish_time
        
        # 1 小时内 = 1.0, 24 小时后 = 0.0
        if age < timedelta(hours=1):
            return 1.0
        elif age > timedelta(hours=24):
            return 0.0
        else:
            return 1.0 - age.total_seconds() / (24 * 3600)
    
    def _sentiment_score(self, content: str) -> float:
        """情绪强度评分"""
        # 简化实现：检查情绪词密度
        emotion_words = [
            "暴涨", "暴跌", "崩盘", "疯狂", "恐慌",
            "利好", "利空", "重磅", "突发",
        ]
        
        emotion_count = sum(
            1 for word in emotion_words
            if word in content
        )
        
        # 归一化到 0-1
        return min(1.0, emotion_count / 3)
```

---

### 5. 主过滤器 (组合所有过滤器)

```python
# backend/app/services/text_filter/smart_text_filter.py

from typing import List, Set, Optional
from datetime import timedelta
from loguru import logger

from ...models.text_data import TextItem, TextRelevance, TextSourceType
from .dedup_filter import DedupFilter
from .relevance_filter import RelevanceFilter
from .quality_filter import QualityFilter
from .importance_ranker import ImportanceRanker


class SmartTextFilter:
    """智能文本过滤器 (组合所有过滤器)"""
    
    def __init__(
        self,
        watchlist: Optional[Set[str]] = None,
        min_relevance: TextRelevance = TextRelevance.INDIRECT,
        top_n: int = 5000,
        enable_stats: bool = True
    ):
        """
        Args:
            watchlist: 关注列表
            min_relevance: 最低相关性
            top_n: 返回前 N 条
            enable_stats: 启用统计
        """
        # 初始化各过滤器
        self.dedup_filter = DedupFilter()
        self.relevance_filter = RelevanceFilter(
            watchlist=watchlist,
            min_relevance=min_relevance
        )
        self.quality_filter = QualityFilter()
        self.importance_ranker = ImportanceRanker(top_n=top_n)
        
        # 统计
        self._enable_stats = enable_stats
        self._stats = {
            "total_input": 0,
            "after_dedup": 0,
            "after_relevance": 0,
            "after_quality": 0,
            "final_output": 0,
        }
    
    def filter(self, texts: List[TextItem]) -> List[TextItem]:
        """
        执行完整过滤流程
        
        Args:
            texts: 原始文本列表
        
        Returns:
            List[TextItem]: 过滤后的高质量文本列表
        """
        self._stats["total_input"] = len(texts)
        
        logger.info(
            f"开始文本过滤: {len(texts)} 条原始文本"
        )
        
        # Step 1: 去重
        texts = self.dedup_filter.filter(texts)
        self._stats["after_dedup"] = len(texts)
        logger.debug(f"去重后: {len(texts)} 条")
        
        # Step 2: 相关性过滤
        texts = self.relevance_filter.filter(texts)
        self._stats["after_relevance"] = len(texts)
        logger.debug(f"相关性过滤后: {len(texts)} 条")
        
        # Step 3: 质量过滤
        texts = self.quality_filter.filter(texts)
        self._stats["after_quality"] = len(texts)
        logger.debug(f"质量过滤后: {len(texts)} 条")
        
        # Step 4: 重要性排序
        texts = self.importance_ranker.rank(texts)
        self._stats["final_output"] = len(texts)
        logger.debug(f"重要性排序后: {len(texts)} 条")
        
        if self._enable_stats:
            self._log_stats()
        
        return texts
    
    def update_watchlist(self, symbols: Set[str]):
        """更新关注列表"""
        self.relevance_filter.update_watchlist(symbols)
        logger.info(f"更新关注列表: {len(symbols)} 只股票")
    
    def get_stats(self) -> dict:
        """获取过滤统计"""
        if not self._stats["total_input"]:
            return {}
        
        return {
            "total_input": self._stats["total_input"],
            "after_dedup": self._stats["after_dedup"],
            "after_relevance": self._stats["after_relevance"],
            "after_quality": self._stats["after_quality"],
            "final_output": self._stats["final_output"],
            "dedup_rate": round(
                1 - self._stats["after_dedup"] / self._stats["total_input"],
                2
            ),
            "relevance_rate": round(
                1 - self._stats["after_relevance"] / self._stats["after_dedup"],
                2
            ),
            "quality_rate": round(
                1 - self._stats["after_quality"] / self._stats["after_relevance"],
                2
            ),
            "total_filter_rate": round(
                1 - self._stats["final_output"] / self._stats["total_input"],
                2
            ),
        }
    
    def _log_stats(self):
        """打印统计日志"""
        stats = self.get_stats()
        
        logger.info(
            f"文本过滤统计:\n"
            f"  输入: {stats['total_input']} 条\n"
            f"  去重率: {stats['dedup_rate']:.0%}\n"
            f"  相关性过滤率: {stats['relevance_rate']:.0%}\n"
            f"  质量过滤率: {stats['quality_rate']:.0%}\n"
            f"  总过滤率: {stats['total_filter_rate']:.0%}\n"
            f"  输出: {stats['final_output']} 条"
        )
```

---

## 📊 预期效果

### 过滤效果测试

| 阶段 | 输入 | 输出 | 过滤率 | 累计过滤率 |
|-----|------|------|--------|-----------|
| 原始文本 | 58300 | - | - | - |
| 去重 | 58300 | 35000 | 40% | 40% |
| 相关性 | 35000 | 15000 | 57% | 74% |
| 质量过滤 | 15000 | 10000 | 33% | 83% |
| 重要性排序 | 10000 | 5000 | 50% | 91% |

### 性能对比

| 指标 | 过滤前 | 过滤后 | 改善 |
|-----|--------|--------|------|
| 处理量 | 58300 条 | 5000 条 | -91% |
| 计算时间 | 1.6 小时 | 8 分钟 | -92% |
| API 费用 | 583 元/天 | 53 元/天 | -91% |
| LLM 调用 | 58300 次 | 5000 次 | -91% |

### 成本节约

```
月度成本对比:
- 过滤前: 583 × 30 = 17490 元/月
- 过滤后: 53 × 30 = 1590 元/月
- 节约: 15900 元/月 (91%)

年度节约: 15900 × 12 = 190800 元/年
```

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: backend/app/services/text_filter/
