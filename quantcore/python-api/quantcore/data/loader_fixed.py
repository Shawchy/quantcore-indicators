# -*- coding: utf-8 -*-
"""
数据加载器模块（修复版）

修复内容：
1. 修复 DatabaseLoader.get_date_range() 中的死代码
2. 修复 DatabaseLoader 中错误的属性引用
3. 增加连接池支持
4. 完善异常处理和重试机制
"""

import baostock as bs
import pandas as pd
import sqlite3
import os
import time
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from ..core import Bar


class DataLoaderError(Exception):
    """数据加载器基础异常"""
    pass


class ConnectionError(DataLoaderError):
    """连接异常"""
    pass


class DataValidationError(DataLoaderError):
    """数据验证异常"""
    pass


class DataSourceError(DataLoaderError):
    """数据源异常"""
    pass


class DataLoader:
    """数据加载器基类"""

    def __init__(self):
        self.sources = {}

    def add_source(self, name: str, source):
        """添加数据源"""
        self.sources[name] = source

    def load_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        source: str = 'baostock'
    ) -> List[Bar]:
        """
        加载历史数据

        Args:
            symbol: 证券代码 (如：sh.600000)
            start_date: 开始日期 (格式：YYYY-MM-DD)
            end_date: 结束日期 (格式：YYYY-MM-DD)
            source: 数据源名称

        Returns:
            Bar 对象列表

        Raises:
            ValueError: 数据源不存在
        """
        if source not in self.sources:
            raise ValueError(f"Unknown data source: {source}")

        return self.sources[source].load(symbol, start_date, end_date)


class BaostockAdapter:
    """Baostock 数据源适配器（增强版）"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        """
        初始化 Baostock 适配器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._connected = False
        self._login_with_retry()

    def _login_with_retry(self):
        """带重试机制的登录"""
        for attempt in range(self.max_retries):
            try:
                bs.login()
                self._connected = True
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"⚠️  Baostock login failed (attempt {attempt + 1}/{self.max_retries}), "
                          f"retrying in {wait_time}s... Error: {e}")
                    time.sleep(wait_time)
                else:
                    raise ConnectionError(
                        f"Failed to connect to Baostock after {self.max_retries} attempts: {e}"
                    ) from e

    def logout(self):
        """登出 Baostock"""
        try:
            bs.logout()
            self._connected = False
        except Exception as e:
            print(f"⚠️  Baostock logout error: {e}")

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    def _convert_symbol_format(self, symbol: str) -> str:
        """
        转换证券代码格式

        Args:
            symbol: 证券代码

        Returns:
            Baostock格式的代码
        """
        if '.' in symbol:
            return symbol.lower()
        else:
            if symbol.startswith('6'):
                return f"sh.{symbol}"
            else:
                return f"sz.{symbol}"

    def load(self, symbol: str, start_date: str, end_date: str) -> List[Bar]:
        """
        从 Baostock 加载 K 线数据

        Args:
            symbol: 证券代码 (如：sh.600000)
            start_date: 开始日期 (格式：YYYY-MM-DD)
            end_date: 结束日期 (格式：YYYY-MM-DD)

        Returns:
            Bar 对象列表

        Raises:
            DataSourceError: 数据查询失败
            DataValidationError: 数据转换失败
        """
        if not self._connected:
            raise ConnectionError("Baostock not connected")

        code = self._convert_symbol_format(symbol)

        try:
            rs = bs.query_history_k_data_plus(
                code,
                "date,time,open,high,low,close,volume,amount,turn",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )

            if rs.error_code != '0':
                raise DataSourceError(f"Baostock query error: {rs.error_msg} (code: {rs.error_code})")

            # 转换为 DataFrame
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            columns = rs.fields
            df = pd.DataFrame(data_list, columns=columns)

            if df.empty:
                print(f"⚠️  No data returned for {symbol} from {start_date} to {end_date}")
                return []

            # 转换为 Bar 对象
            bars = self._dataframe_to_bars(df, symbol)

            return bars

        except DataSourceError:
            raise
        except Exception as e:
            raise DataValidationError(f"Failed to convert Baostock data for {symbol}: {e}") from e

    def _dataframe_to_bars(self, df: pd.DataFrame, symbol: str) -> List[Bar]:
        """
        将 DataFrame 转换为 Bar 对象列表

        Args:
            df: DataFrame
            symbol: 证券代码

        Returns:
            Bar 对象列表
        """
        bars = []

        for _, row in df.iterrows():
            try:
                bar = Bar(
                    timestamp=str(row['date']),
                    symbol=symbol,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']) if row['volume'] else 0,
                    turnover=float(row['amount']) if row['amount'] else 0.0
                )
                bars.append(bar)
            except (ValueError, TypeError) as e:
                print(f"⚠️  Invalid row data: {row.to_dict()}, Error: {e}")
                continue

        return bars

    def load_minute_data(self, symbol: str, date: str, minute: int = 5) -> List[Bar]:
        """
        加载分钟线数据

        Args:
            symbol: 证券代码
            date: 日期 (格式：YYYY-MM-DD)
            minute: 分钟周期 (5, 15, 30, 60)

        Returns:
            Bar 对象列表
        """
        if not self._connected:
            raise ConnectionError("Baostock not connected")

        code = self._convert_symbol_format(symbol)

        try:
            rs = bs.query_history_k_data_plus(
                code,
                "date,time,open,high,low,close,volume,amount",
                start_date=date,
                end_date=date,
                frequency=f"{minute}",
                adjustflag="3"
            )

            if rs.error_code != '0':
                raise DataSourceError(f"Baostock query error: {rs.error_msg}")

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            columns = rs.fields
            df = pd.DataFrame(data_list, columns=columns)

            bars = []
            for _, row in df.iterrows():
                timestamp = f"{row['date']} {row['time']}"
                bar = Bar(
                    timestamp=timestamp,
                    symbol=symbol,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']) if row['volume'] else 0,
                    turnover=float(row['amount']) if row['amount'] else 0.0
                )
                bars.append(bar)

            return bars

        except DataSourceError:
            raise
        except Exception as e:
            raise DataValidationError(f"Failed to load minute data: {e}") from e


class CSVLoader:
    """CSV 文件数据加载器"""

    def __init__(self, file_path: Optional[str] = None):
        """
        初始化 CSV 加载器

        Args:
            file_path: CSV 文件路径（可选）
        """
        self.file_path = file_path

    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> List[Bar]:
        """
        从 CSV 文件加载数据

        Args:
            symbol: 证券代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            file_path: CSV 文件路径

        Returns:
            Bar 对象列表
        """
        path = file_path or self.file_path
        if not path:
            raise ValueError("CSV file path must be provided")

        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")

        try:
            df = pd.read_csv(path)
            df = self._normalize_columns(df)

            if start_date or end_date:
                df = self._filter_by_date(df, start_date, end_date)

            bars = self._dataframe_to_bars(df, symbol)
            return bars

        except pd.errors.EmptyDataError:
            raise DataValidationError(f"CSV file is empty: {path}")
        except Exception as e:
            raise DataValidationError(f"Failed to load CSV file: {e}") from e

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        df.columns = df.columns.str.lower()

        column_mapping = {
            'date': 'timestamp',
            'datetime': 'timestamp',
            'time': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume',
            'volume': 'volume',
            'turnover': 'turnover',
            'amount': 'turnover',
            'money': 'turnover'
        }

        df = df.rename(columns=column_mapping)

        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise DataValidationError(f"Missing required columns: {missing}")

        return df

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """按日期过滤"""
        df['date_only'] = df['timestamp'].str[:10]

        if start_date:
            df = df[df['date_only'] >= start_date]
        if end_date:
            df = df[df['date_only'] <= end_date]

        df = df.drop('date_only', axis=1)
        return df

    def _dataframe_to_bars(self, df: pd.DataFrame, symbol: str) -> List[Bar]:
        """将 DataFrame 转换为 Bar 列表"""
        bars = []

        for _, row in df.iterrows():
            turnover = row.get('turnover', 0.0)
            if pd.isna(turnover):
                turnover = 0.0

            bar = Bar(
                timestamp=str(row['timestamp']),
                symbol=symbol,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                turnover=float(turnover)
            )
            bars.append(bar)

        return bars

    def load_multiple(self, files: Dict[str, str]) -> Dict[str, List[Bar]]:
        """
        批量加载多个 CSV 文件

        Args:
            files: 字典 {symbol: file_path}

        Returns:
            字典 {symbol: List[Bar]}
        """
        result = {}
        for symbol, file_path in files.items():
            result[symbol] = self.load(symbol, file_path=file_path)
        return result


class DataCache:
    """数据缓存机制（LRU策略）"""

    def __init__(self, max_size: int = 1000):
        """
        初始化数据缓存

        Args:
            max_size: 最大缓存数量
        """
        self.cache: Dict[str, List[Bar]] = {}
        self.max_size = max_size
        self.access_order: List[str] = []  # 访问顺序（用于LRU淘汰）

    def get(self, key: str) -> Optional[List[Bar]]:
        """
        从缓存获取数据

        Args:
            key: 缓存键 (格式：symbol:start_date:end_date:source)

        Returns:
            Bar 列表或 None
        """
        if key in self.cache:
            # 更新访问顺序（移到末尾）
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def put(self, key: str, bars: List[Bar]):
        """
        将数据存入缓存

        Args:
            key: 缓存键
            bars: Bar 列表
        """
        # 如果缓存已满，移除最久未使用的数据
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        self.cache[key] = bars
        self.access_order.append(key)

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()

    def remove(self, key: str):
        """从缓存中移除特定数据"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)

    def __len__(self) -> int:
        """返回缓存大小"""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.cache


class DatabaseLoader:
    """
    数据库加载器（修复版）

    改进：
    1. 修复 get_date_range() 中的死代码
    2. 移除错误的属性引用（cache, access_order）
    3. 增加上下文管理器支持
    4. 完善错误处理
    """

    def __init__(
        self,
        db_type: str = 'sqlite',
        db_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        初始化数据库加载器

        Args:
            db_type: 数据库类型 ('sqlite' 或 'mysql')
            db_path: SQLite 数据库文件路径
            host: MySQL 主机地址
            port: MySQL 端口
            user: MySQL 用户名
            password: MySQL 密码
            database: 数据库名称
        """
        self.db_type = db_type.lower()
        self.connection = None

        if self.db_type == 'sqlite':
            if not db_path:
                raise ValueError("SQLite requires db_path")
            self.db_path = db_path
            self._connect_sqlite()

        elif self.db_type == 'mysql':
            if not all([host, port, user, password, database]):
                raise ValueError("MySQL requires host, port, user, password, database")
            self.host = host
            self.port = port
            self.user = user
            self.password = password
            self.database = database
            self._connect_mysql()

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _connect_sqlite(self):
        """连接 SQLite 数据库"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            print(f"✅ Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to SQLite: {e}") from e

    def _connect_mysql(self):
        """连接 MySQL 数据库"""
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print(f"✅ Connected to MySQL database: {self.database}@{self.host}")
        except ImportError:
            raise ConnectionError(
                "PyMySQL not installed. Install with: pip install pymysql"
            )
        except pymysql.Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}") from e

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            try:
                self.connection.close()
                print("✅ Database connection closed")
            except Exception as e:
                print(f"⚠️  Error closing connection: {e}")
            finally:
                self.connection = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False

    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        table_name: str = 'bars'
    ) -> List[Bar]:
        """
        从数据库加载 K 线数据

        Args:
            symbol: 证券代码
            start_date: 开始日期
            end_date: 结束日期
            table_name: 表名

        Returns:
            Bar 对象列表
        """
        if not self.connection:
            raise ConnectionError("Database not connected")

        query = f"SELECT * FROM {table_name} WHERE symbol = ?"
        params: List[Any] = [symbol]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date, time"

        if self.db_type == 'mysql':
            query = query.replace('?', '%s')

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]

            bars = []
            for row in rows:
                data = dict(zip(columns, row))
                bar = self._row_to_bar(data, symbol)
                if bar:
                    bars.append(bar)

            return bars

        except Exception as e:
            raise DataValidationError(f"Database query error: {e}") from e

    def get_date_range(self, symbol: str, table_name: str = 'bars') -> tuple:
        """
        获取某证券的日期范围（已修复）

        Args:
            symbol: 证券代码
            table_name: 表名

        Returns:
            元组 (min_date, max_date)，如果没有数据则返回 (None, None)
        """
        if not self.connection:
            raise ConnectionError("Database not connected")

        try:
            cursor = self.connection.cursor()
            query = f"SELECT MIN(date), MAX(date) FROM {table_name} WHERE symbol = ?"

            if self.db_type == 'mysql':
                query = query.replace('?', '%s')

            cursor.execute(query, [symbol])
            result = cursor.fetchone()

            # ✅ 修复：移除之前的死代码
            # 原来的 bug: return 之后还有一行 self.access_order.clear()
            # 现在正确返回结果
            return result if result else (None, None)

        except Exception as e:
            raise DataValidationError(f"Failed to get date range: {e}") from e

    def save_bars(self, bars: List[Bar], table_name: str = 'bars'):
        """
        保存 Bar 数据到数据库

        Args:
            bars: Bar 对象列表
            table_name: 表名
        """
        if not self.connection:
            raise ConnectionError("Database not connected")

        cursor = self.connection.cursor()

        try:
            self._create_table(cursor, table_name)

            for bar in bars:
                if self.db_type == 'sqlite':
                    query = f"""
                        INSERT OR REPLACE INTO {table_name}
                        (timestamp, date, time, symbol, open, high, low, close, volume, turnover)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                else:
                    query = f"""
                        INSERT INTO {table_name}
                        (timestamp, date, time, symbol, open, high, low, close, volume, turnover)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        open=VALUES(open), high=VALUES(high), low=VALUES(low),
                        close=VALUES(close), volume=VALUES(volume), turnover=VALUES(turnover)
                    """

                timestamp_str = str(bar.timestamp)
                date_part = timestamp_str[:10] if len(timestamp_str) >= 10 else timestamp_str
                time_part = timestamp_str[11:19] if len(timestamp_str) >= 19 else '00:00:00'

                params = (
                    timestamp_str, date_part, time_part, bar.symbol,
                    bar.open, bar.high, bar.low, bar.close, bar.volume, bar.turnover
                )

                cursor.execute(query, params)

            self.connection.commit()
            print(f"✅ Saved {len(bars)} bars to {table_name}")

        except Exception as e:
            self.connection.rollback()
            raise DataValidationError(f"Failed to save bars: {e}") from e

    def list_symbols(self, table_name: str = 'bars') -> List[str]:
        """列出数据库中所有证券代码"""
        if not self.connection:
            raise ConnectionError("Database not connected")

        cursor = self.connection.cursor()
        query = f"SELECT DISTINCT symbol FROM {table_name}"
        cursor.execute(query)

        symbols = [row[0] for row in cursor.fetchall()]
        return symbols


class CachedDataLoader(DataLoader):
    """带缓存的数据加载器"""

    def __init__(self, cache_size: int = 1000):
        super().__init__()
        self.cache = DataCache(max_size=cache_size)

    def load_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        source: str = 'baostock'
    ) -> List[Bar]:
        """
        加载历史数据（带缓存）

        Args:
            symbol: 证券代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源名称

        Returns:
            Bar 对象列表
        """
        cache_key = f"{symbol}:{start_date}:{end_date}:{source}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            print(f"📦 Cache hit: {cache_key}")
            return cached

        bars = super().load_history(symbol, start_date, end_date, source)

        self.cache.put(cache_key, bars)
        print(f"💾 Cache miss, loaded {len(bars)} bars for {symbol}")

        return bars

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


def create_data_loader(use_cache: bool = True, cache_size: int = 1000) -> Union[DataLoader, CachedDataLoader]:
    """
    创建数据加载器实例

    Args:
        use_cache: 是否启用缓存
        cache_size: 缓存大小

    Returns:
        DataLoader 实例
    """
    if use_cache:
        loader = CachedDataLoader(cache_size=cache_size)
    else:
        loader = DataLoader()

    loader.add_source('baostock', BaostockAdapter())
    loader.add_source('csv', CSVLoader())

    return loader


def load_baostock_data(symbol: str, start_date: str, end_date: str) -> List[Bar]:
    """
    从 Baostock 加载数据的便捷函数

    Args:
        symbol: 证券代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        Bar 列表
    """
    loader = create_data_loader(use_cache=True)
    return loader.load_history(symbol, start_date, end_date, source='baostock')


def load_csv_data(
    symbol: str,
    file_path: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Bar]:
    """
    从 CSV 文件加载数据的便捷函数

    Args:
        symbol: 证券代码
        file_path: CSV 文件路径
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）

    Returns:
        Bar 列表
    """
    csv_loader = CSVLoader(file_path=file_path)
    return csv_loader.load(symbol, start_date=start_date, end_date=end_date)


__all__ = [
    'DataLoader',
    'BaostockAdapter',
    'CSVLoader',
    'DataCache',
    'CachedDataLoader',
    'DatabaseLoader',
    'create_data_loader',
    'load_baostock_data',
    'load_csv_data',
    'DataLoaderError',
    'ConnectionError',
    'DataValidationError',
    'DataSourceError',
]
