# 优化模块 1: 文本数据源管理管线

## 📊 设计概述

### 问题背景

LLM 文本因子生产的第一步是**获取高质量文本数据**，但实际面临:
- 数据源分散 (新闻/公告/舆情/研报)
- 采集方式各异 (REST API/爬虫/WebSocket)
- 更新频率不同 (实时/分钟/日更)
- 数据格式不统一 (HTML/JSON/文本)

### 解决方案

设计**标准化文本数据管线**，实现:
- ✅ 统一数据模型
- ✅ 可插拔数据源
- ✅ 增量更新
- ✅ 去重过滤
- ✅ 质量评估

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    数据采集层                             │
│                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│  │新闻采集 │  │公告采集 │  │舆情采集 │  │研报采集 │       │
│  │(REST)  │  │(爬虫)  │  │(爬虫)  │  │(API)   │       │
│  └────────┘  └────────┘  └────────┘  └────────┘       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   数据处理层                              │
│                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│  │格式统一 │  │去重过滤 │  │相关性   │  │质量评估 │       │
│  │        │  │        │  │评分     │  │        │       │
│  └────────┘  └────────┘  └────────┘  └────────┘       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   数据存储层                              │
│                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│  │实时缓存 │  │日级存储 │  │索引构建 │  │版本管理 │       │
│  │(Redis) │  │(SQLite)│  │        │  │        │       │
│  └────────┘  └────────┘  └────────┘  └────────┘       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   数据服务层                              │
│                                                         │
│  ┌────────────────────────────────────────────┐        │
│  │  TextDataQueryService                      │        │
│  │  - 按股票查询当日文本                       │        │
│  │  - 按时间范围查询                           │        │
│  │  - 按来源/类型过滤                          │        │
│  │  - 批量导出                                 │        │
│  └────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. 统一数据模型

```python
# backend/app/models/text_data.py

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class TextSourceType(str, Enum):
    """文本数据源类型"""
    NEWS = "news"  # 新闻
    ANNOUNCEMENT = "announcement"  # 公告
    SOCIAL = "social"  # 社交媒体
    RESEARCH_REPORT = "research_report"  # 研报
    REGULATORY = "regulatory"  # 监管文件


class TextImportance(str, Enum):
    """文本重要性"""
    HIGH = "high"  # 高 (业绩、并购、政策)
    MEDIUM = "medium"  # 中 (一般新闻)
    LOW = "low"  # 低 (广告、水帖)


class TextRelevance(str, Enum):
    """文本相关性"""
    DIRECT = "direct"  # 直接相关 (提及具体股票)
    INDIRECT = "indirect"  # 间接相关 (行业/概念)
    UNRELATED = "unrelated"  # 无关


@dataclass
class TextItem:
    """文本数据项 (统一模型)"""
    # 基础信息
    text_id: str  # 唯一 ID (MD5 去重)
    source: TextSourceType  # 来源类型
    provider: str  # 数据提供商
    
    # 内容
    title: str  # 标题
    content: str  # 正文 (纯文本)
    url: Optional[str] = None  # 原文链接
    
    # 关联信息
    related_symbols: List[str] = field(default_factory=list)  # 相关股票
    related_sectors: List[str] = field(default_factory=list)  # 相关行业
    keywords: List[str] = field(default_factory=list)  # 关键词
    
    # 时间信息
    publish_time: datetime  # 发布时间
    fetch_time: datetime = field(default_factory=datetime.now)  # 抓取时间
    
    # 评估信息
    importance: TextImportance = TextImportance.MEDIUM  # 重要性
    relevance: TextRelevance = TextRelevance.DIRECT  # 相关性
    quality_score: float = 1.0  # 质量评分 (0-1)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展字段
    
    def is_duplicate(self, other: 'TextItem') -> bool:
        """判断是否重复"""
        return self.text_id == other.text_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text_id': self.text_id,
            'source': self.source.value,
            'provider': self.provider,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'related_symbols': self.related_symbols,
            'related_sectors': self.related_sectors,
            'keywords': self.keywords,
            'publish_time': self.publish_time.isoformat(),
            'fetch_time': self.fetch_time.isoformat(),
            'importance': self.importance.value,
            'relevance': self.relevance.value,
            'quality_score': self.quality_score,
            'metadata': self.metadata,
        }
```

---

### 2. 数据源接口定义

```python
# backend/app/services/text_data_sources/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from ..models.text_data import TextItem


class TextDataSource(ABC):
    """文本数据源基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> TextSourceType:
        """数据源类型"""
        pass
    
    @property
    def update_frequency(self) -> timedelta:
        """更新频率 (默认 5 分钟)"""
        return timedelta(minutes=5)
    
    @abstractmethod
    async def fetch_latest(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[TextItem]:
        """
        获取最新文本数据
        
        Args:
            symbols: 股票列表 (None=全市场)
            limit: 返回数量限制
        
        Returns:
            List[TextItem]: 文本数据列表
        """
        pass
    
    @abstractmethod
    async def fetch_by_date(
        self,
        date: date,
        symbols: Optional[List[str]] = None
    ) -> List[TextItem]:
        """
        获取指定日期的文本数据
        
        Args:
            date: 日期
            symbols: 股票列表
        
        Returns:
            List[TextItem]: 文本数据列表
        """
        pass
    
    async def health_check(self) -> bool:
        """健康检查 (默认实现)"""
        try:
            items = await self.fetch_latest(limit=1)
            return len(items) > 0
        except Exception:
            return False
```

---

### 3. 具体数据源实现

```python
# backend/app/services/text_data_sources/news_source.py

class SinaNewsSource(TextDataSource):
    """新浪财经数据源"""
    
    @property
    def name(self) -> str:
        return "sina_news"
    
    @property
    def source_type(self) -> TextSourceType:
        return TextSourceType.NEWS
    
    @property
    def update_frequency(self) -> timedelta:
        return timedelta(minutes=5)
    
    async def fetch_latest(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[TextItem]:
        """从新浪财经获取最新新闻"""
        import hashlib
        from datetime import datetime
        
        # 调用新浪财经 API (示例)
        api_url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {
            "pageid": 153,
            "lid": 2516,
            "num": limit,
        }
        
        if symbols:
            # 按股票搜索
            params["keyword"] = symbols[0]
        
        # 发送请求
        response = await self._http_client.get(api_url, params=params)
        data = response.json()
        
        # 转换为统一模型
        items = []
        for article in data.get("data", []):
            text_id = hashlib.md5(
                article.get("title", "").encode()
            ).hexdigest()
            
            # 提取相关股票
            related_symbols = self._extract_symbols(
                article.get("title", "") + article.get("content", "")
            )
            
            item = TextItem(
                text_id=text_id,
                source=TextSourceType.NEWS,
                provider="sina",
                title=article.get("title", ""),
                content=article.get("content", ""),
                url=article.get("url", ""),
                related_symbols=related_symbols,
                publish_time=datetime.fromtimestamp(
                    article.get("ctime", 0)
                ),
            )
            items.append(item)
        
        return items
    
    def _extract_symbols(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        import re
        
        # 匹配 A 股代码 (6 位数字)
        pattern = r'\b(\d{6})\b'
        matches = re.findall(pattern, text)
        
        # 添加 .SH/.SZ 后缀
        symbols = []
        for code in matches:
            if code.startswith('6'):
                symbols.append(f"{code}.SH")
            else:
                symbols.append(f"{code}.SZ")
        
        return list(set(symbols))  # 去重


class JuchaoAnnouncementSource(TextDataSource):
    """巨潮资讯公告数据源"""
    
    @property
    def name(self) -> str:
        return "juchao_announcement"
    
    @property
    def source_type(self) -> TextSourceType:
        return TextSourceType.ANNOUNCEMENT
    
    @property
    def update_frequency(self) -> timedelta:
        return timedelta(hours=1)  # 公告更新较慢
    
    async def fetch_latest(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[TextItem]:
        """从巨潮资讯获取最新公告"""
        # 实现类似新浪新闻
        # 但需要处理 PDF 解析
        pass


class XueqiuSocialSource(TextDataSource):
    """雪球社交媒体数据源"""
    
    @property
    def name(self) -> str:
        return "xueqiu_social"
    
    @property
    def source_type(self) -> TextSourceType:
        return TextSourceType.SOCIAL
    
    @property
    def update_frequency(self) -> timedelta:
        return timedelta(minutes=1)  # 社交媒体更新快
    
    async def fetch_latest(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[TextItem]:
        """从雪球获取最新讨论"""
        # 实现社交媒体抓取
        pass
```

---

### 4. 数据源管理器

```python
# backend/app/services/text_data_sources/manager.py

from typing import Dict, List, Optional
from datetime import date, datetime
from loguru import logger

from .base import TextDataSource
from .news_source import SinaNewsSource, EastmoneyNewsSource
from .announcement_source import JuchaoAnnouncementSource
from .social_source import XueqiuSocialSource, EastmoneySocialSource
from ..models.text_data import TextItem, TextSourceType


class TextDataSourceManager:
    """文本数据源管理器"""
    
    def __init__(self):
        # 注册所有数据源
        self._sources: Dict[str, TextDataSource] = {}
        self._source_status: Dict[str, bool] = {}  # 健康状态
        
        # 配置数据源
        self._register_sources()
    
    def _register_sources(self):
        """注册数据源"""
        sources = [
            SinaNewsSource(),
            EastmoneyNewsSource(),
            JuchaoAnnouncementSource(),
            XueqiuSocialSource(),
            EastmoneySocialSource(),
        ]
        
        for source in sources:
            self._sources[source.name] = source
            self._source_status[source.name] = False
        
        logger.info(f"注册了 {len(self._sources)} 个文本数据源")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有数据源健康状态"""
        for name, source in self._sources.items():
            try:
                is_healthy = await source.health_check()
                self._source_status[name] = is_healthy
            except Exception as e:
                logger.error(f"数据源 {name} 健康检查失败: {e}")
                self._source_status[name] = False
        
        return self._source_status.copy()
    
    async def fetch_daily_texts(
        self,
        symbols: List[str],
        date: date,
        sources: Optional[List[str]] = None
    ) -> Dict[TextSourceType, List[TextItem]]:
        """
        获取指定股票当日的文本数据
        
        Args:
            symbols: 股票代码列表
            date: 日期
            sources: 指定数据源 (None=全部)
        
        Returns:
            {TextSourceType: List[TextItem]}
        """
        results: Dict[TextSourceType, List[TextItem]] = {}
        
        # 确定要查询的数据源
        if sources is None:
            source_names = list(self._sources.keys())
        else:
            source_names = sources
        
        # 并发查询所有数据源
        tasks = []
        for name in source_names:
            if name not in self._sources:
                logger.warning(f"未知的数据源: {name}")
                continue
            
            if not self._source_status.get(name, False):
                logger.warning(f"数据源 {name} 不健康，跳过")
                continue
            
            source = self._sources[name]
            tasks.append(
                self._fetch_and_deduplicate(source, symbols, date)
            )
        
        # 等待所有任务完成
        import asyncio
        fetch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for result in fetch_results:
            if isinstance(result, Exception):
                logger.error(f"数据源查询失败: {result}")
                continue
            
            if isinstance(result, dict):
                for source_type, items in result.items():
                    if source_type in results:
                        results[source_type].extend(items)
                    else:
                        results[source_type] = items
        
        # 去重
        for source_type in results:
            results[source_type] = self._deduplicate(
                results[source_type]
            )
        
        logger.info(
            f"获取 {date} 文本数据: "
            + ", ".join(
                f"{k.value}: {len(v)}条"
                for k, v in results.items()
            )
        )
        
        return results
    
    async def _fetch_and_deduplicate(
        self,
        source: TextDataSource,
        symbols: List[str],
        date: date
    ) -> Dict[TextSourceType, List[TextItem]]:
        """查询并去重"""
        try:
            items = await source.fetch_by_date(date, symbols)
            return {source.source_type: items}
        except Exception as e:
            logger.error(f"数据源 {source.name} 查询失败: {e}")
            return {}
    
    def _deduplicate(
        self,
        items: List[TextItem]
    ) -> List[TextItem]:
        """文本去重 (基于 text_id)"""
        seen = set()
        unique_items = []
        
        for item in items:
            if item.text_id not in seen:
                seen.add(item.text_id)
                unique_items.append(item)
        
        logger.debug(f"去重: {len(items)} → {len(unique_items)}")
        return unique_items
    
    def get_source_stats(self) -> Dict[str, Dict]:
        """获取数据源统计信息"""
        return {
            name: {
                "healthy": self._source_status.get(name, False),
                "type": source.source_type.value,
                "frequency": str(source.update_frequency),
            }
            for name, source in self._sources.items()
        }
```

---

### 5. 数据存储层

```python
# backend/app/storage/text_data_storage.py

from typing import List, Optional, Dict
from datetime import date, datetime
from pathlib import Path
import sqlite3
import json
import pandas as pd

from ..models.text_data import TextItem, TextSourceType


class TextDataStorage:
    """文本数据存储"""
    
    def __init__(self, db_path: str = "data/text_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS text_items (
                text_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                provider TEXT NOT NULL,
                title TEXT,
                content TEXT,
                url TEXT,
                related_symbols TEXT,  -- JSON array
                related_sectors TEXT,  -- JSON array
                keywords TEXT,  -- JSON array
                publish_time TEXT,
                fetch_time TEXT,
                importance TEXT,
                relevance TEXT,
                quality_score REAL,
                metadata TEXT  -- JSON
            )
        """)
        
        # 创建索引
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_publish_time 
            ON text_items(publish_time)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_related_symbols 
            ON text_items(related_symbols)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source 
            ON text_items(source)
        """)
        
        conn.commit()
        conn.close()
    
    def save_texts(self, texts: List[TextItem]) -> int:
        """
        保存文本数据
        
        Returns:
            int: 成功保存的数量
        """
        conn = sqlite3.connect(self.db_path)
        
        saved_count = 0
        for text in texts:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO text_items
                    (text_id, source, provider, title, content, url,
                     related_symbols, related_sectors, keywords,
                     publish_time, fetch_time, importance, relevance,
                     quality_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    text.text_id,
                    text.source.value,
                    text.provider,
                    text.title,
                    text.content,
                    text.url,
                    json.dumps(text.related_symbols),
                    json.dumps(text.related_sectors),
                    json.dumps(text.keywords),
                    text.publish_time.isoformat(),
                    text.fetch_time.isoformat(),
                    text.importance.value,
                    text.relevance.value,
                    text.quality_score,
                    json.dumps(text.metadata),
                ))
                saved_count += 1
            except Exception as e:
                # 忽略重复插入
                pass
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def query_texts(
        self,
        date: date,
        symbols: Optional[List[str]] = None,
        source_type: Optional[TextSourceType] = None,
        limit: int = 1000
    ) -> List[TextItem]:
        """查询文本数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM text_items WHERE DATE(publish_time) = ?"
        params = [date.isoformat()]
        
        if symbols:
            # 查询包含任一股票的文本
            symbol_conditions = " OR ".join(
                f"related_symbols LIKE ?" for _ in symbols
            )
            query += f" AND ({symbol_conditions})"
            params.extend(f"%{s}%" for s in symbols)
        
        if source_type:
            query += " AND source = ?"
            params.append(source_type.value)
        
        query += " ORDER BY publish_time DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        texts = []
        for row in rows:
            text = TextItem(
                text_id=row['text_id'],
                source=TextSourceType(row['source']),
                provider=row['provider'],
                title=row['title'],
                content=row['content'],
                url=row['url'],
                related_symbols=json.loads(row['related_symbols'] or '[]'),
                related_sectors=json.loads(row['related_sectors'] or '[]'),
                keywords=json.loads(row['keywords'] or '[]'),
                publish_time=datetime.fromisoformat(row['publish_time']),
                fetch_time=datetime.fromisoformat(row['fetch_time']),
                importance=TextSourceType(row['importance']),
                relevance=TextSourceType(row['relevance']),
                quality_score=row['quality_score'],
                metadata=json.loads(row['metadata'] or '{}'),
            )
            texts.append(text)
        
        conn.close()
        return texts
    
    def get_daily_stats(self, date: date) -> Dict[str, int]:
        """获取每日统计"""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute("""
            SELECT source, COUNT(*) as count
            FROM text_items
            WHERE DATE(publish_time) = ?
            GROUP BY source
        """, (date.isoformat(),))
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
        
        conn.close()
        return stats
```

---

## 📋 数据源配置

```yaml
# config/text_data_sources.yaml

sources:
  news:
    - name: sina_news
      provider: "新浪财经"
      enabled: true
      update_interval: 300  # 5 分钟
      daily_volume: 5000
      api_type: "REST"
      
    - name: eastmoney_news
      provider: "东方财富"
      enabled: true
      update_interval: 300
      daily_volume: 3000
      api_type: "REST"

  announcement:
    - name: juchao_announcement
      provider: "巨潮资讯"
      enabled: true
      update_interval: 3600  # 1 小时
      daily_volume: 200
      api_type: "爬虫"
      
    - name: sse_announcement
      provider: "上交所"
      enabled: true
      update_interval: 3600
      daily_volume: 50
      api_type: "爬虫"

  social:
    - name: xueqiu_social
      provider: "雪球"
      enabled: true
      update_interval: 60  # 1 分钟
      daily_volume: 30000
      api_type: "爬虫"
      
    - name: eastmoney_social
      provider: "东方财富股吧"
      enabled: true
      update_interval: 60
      daily_volume: 20000
      api_type: "爬虫"

storage:
  db_path: "data/text_data.db"
  retention_days: 90  # 保留 90 天
  max_size_mb: 1000  # 最大 1GB

filter:
  min_quality_score: 0.3  # 最低质量评分
  deduplicate: true  # 启用去重
  relevance_threshold: "indirect"  # 最低相关性
```

---

## 🎯 预期效果

### 数据覆盖

| 来源类型 | 日处理量 | 更新频率 | 覆盖率 |
|---------|---------|---------|--------|
| 新闻 | 8000 条 | 5 分钟 | 90%+ |
| 公告 | 250 条 | 1 小时 | 95%+ |
| 社交媒体 | 50000 条 | 1 分钟 | 80%+ |
| 研报 | 50 条 | 日更 | 70%+ |
| **总计** | **58300 条** | - | - |

### 性能指标

| 指标 | 目标值 | 说明 |
|-----|--------|------|
| 采集延迟 | < 5 分钟 | 从发布到入库 |
| 去重率 | > 20% | 减少重复数据 |
| 存储效率 | < 100MB/天 | SQLite 压缩 |
| 查询延迟 | < 100ms | 按股票查询 |
| 可用性 | > 99% | 健康监控 |

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: backend/app/services/text_data_sources/
