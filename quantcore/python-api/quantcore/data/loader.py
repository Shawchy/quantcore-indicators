"""数据加载器模块

支持多种数据源：
- Baostock（在线数据）
- CSV 文件
- SQLite 数据库
- MySQL 数据库
"""
import baostock as bs
import pandas as pd
import sqlite3
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core import Bar


class DataLoader:
    """数据加载器基类"""
    
    def __init__(self):
        self.sources = {}
    
    def add_source(self, name: str, source):
        """添加数据源"""
        self.sources[name] = source
    
    def load_history(self, symbol: str, start_date: str, end_date: str, 
                     source: str = 'baostock') -> List[Bar]:
        """
        加载历史数据
        
        Args:
            symbol: 证券代码 (如：sh.600000)
            start_date: 开始日期 (格式：YYYY-MM-DD)
            end_date: 结束日期 (格式：YYYY-MM-DD)
            source: 数据源名称
            
        Returns:
            Bar 对象列表
        """
        if source not in self.sources:
            raise ValueError(f"Unknown data source: {source}")
        
        return self.sources[source].load(symbol, start_date, end_date)


class BaostockAdapter:
    """Baostock 数据源适配器"""
    
    def __init__(self):
        self.login()
    
    def login(self):
        """登录 Baostock"""
        bs.login()
    
    def logout(self):
        """登出 Baostock"""
        bs.logout()
    
    def load(self, symbol: str, start_date: str, end_date: str) -> List[Bar]:
        """
        从 Baostock 加载 K 线数据
        
        Args:
            symbol: 证券代码 (如：sh.600000)
            start_date: 开始日期 (格式：YYYY-MM-DD)
            end_date: 结束日期 (格式：YYYY-MM-DD)
            
        Returns:
            Bar 对象列表
        """
        # 转换证券代码格式
        if '.' in symbol:
            code = symbol.lower()
        else:
            if symbol.startswith('6'):
                code = f"sh.{symbol}"
            else:
                code = f"sz.{symbol}"
        
        # 查询 K 线数据
        rs = bs.query_history_k_data_plus(
            code,
            "date,time,open,high,low,close,volume,amount,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 不复权
        )
        
        if rs.error_code != '0':
            raise Exception(f"Baostock query error: {rs.error_msg}")
        
        # 转换为 DataFrame
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        columns = rs.fields
        df = pd.DataFrame(data_list, columns=columns)
        
        # 转换为 Bar 对象
        bars = []
        for _, row in df.iterrows():
            bar = Bar(
                timestamp=row['date'],
                symbol=symbol,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                turnover=float(row['amount']) if row['amount'] else 0.0
            )
            bars.append(bar)
        
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
        if '.' in symbol:
            code = symbol.lower()
        else:
            if symbol.startswith('6'):
                code = f"sh.{symbol}"
            else:
                code = f"sz.{symbol}"
        
        rs = bs.query_history_k_data_plus(
            code,
            "date,time,open,high,low,close,volume,amount",
            start_date=date,
            end_date=date,
            frequency=f"{minute}",
            adjustflag="3"
        )
        
        if rs.error_code != '0':
            raise Exception(f"Baostock query error: {rs.error_msg}")
        
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
                volume=int(row['volume']),
                turnover=float(row['amount']) if row['amount'] else 0.0
            )
            bars.append(bar)
        
        return bars


class CSVLoader:
    """CSV 文件数据加载器"""
    
    def __init__(self, file_path: Optional[str] = None):
        """
        初始化 CSV 加载器
        
        Args:
            file_path: CSV 文件路径（可选，也可在 load 方法中指定）
        """
        self.file_path = file_path
    
    def load(self, symbol: str, start_date: Optional[str] = None, 
             end_date: Optional[str] = None, file_path: Optional[str] = None) -> List[Bar]:
        """
        从 CSV 文件加载数据
        
        Args:
            symbol: 证券代码
            start_date: 开始日期（可选，用于过滤）
            end_date: 结束日期（可选，用于过滤）
            file_path: CSV 文件路径（如果初始化时未指定）
            
        Returns:
            Bar 对象列表
            
        CSV 文件格式要求:
            必须包含列：date/timestamp, open, high, low, close, volume
            可选列：turnover/amount
        """
        path = file_path or self.file_path
        if not path:
            raise ValueError("CSV file path must be provided")
        
        # 读取 CSV 文件
        df = pd.read_csv(path)
        
        # 标准化列名
        df = self._normalize_columns(df)
        
        # 日期过滤
        if start_date or end_date:
            df = self._filter_by_date(df, start_date, end_date)
        
        # 转换为 Bar 对象
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
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 先转换为小写
        df.columns = df.columns.str.lower()
        
        # 创建列名映射（小写版本）
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
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 检查必需列
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        return df
    
    def _filter_by_date(self, df: pd.DataFrame, start_date: Optional[str], 
                        end_date: Optional[str]) -> pd.DataFrame:
        """按日期过滤"""
        # 提取日期部分（假设 timestamp 格式为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
        df['date_only'] = df['timestamp'].str[:10]
        
        if start_date:
            df = df[df['date_only'] >= start_date]
        if end_date:
            df = df[df['date_only'] <= end_date]
        
        # 删除临时列
        df = df.drop('date_only', axis=1)
        
        return df
    
    def load_multiple(self, files: dict) -> dict:
        """
        批量加载多个 CSV 文件
        
        Args:
            files: 字典 {symbol: file_path}
            
        Returns:
            字典 {symbol: List[Bar]}
        """
        result = {}
        for symbol, file_path in files.items():
            bars = self.load(symbol, file_path=file_path)
            result[symbol] = bars
        return result


class DataCache:
    """数据缓存机制"""
    
    def __init__(self, max_size: int = 1000):
        """
        初始化数据缓存
        
        Args:
            max_size: 最大缓存数量
        """
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[List[Bar]]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键 (格式：symbol:start_date:end_date:source)
            
        Returns:
            Bar 列表或 None
        """
        if key in self.cache:
            # 更新访问顺序
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


class DatabaseLoader:
    """数据库加载器（支持 SQLite 和 MySQL）"""
    
    def __init__(self, db_type: str = 'sqlite', db_path: Optional[str] = None,
                 host: Optional[str] = None, port: Optional[int] = None,
                 user: Optional[str] = None, password: Optional[str] = None,
                 database: Optional[str] = None):
        """
        初始化数据库加载器
        
        Args:
            db_type: 数据库类型 ('sqlite' 或 'mysql')
            db_path: SQLite 数据库文件路径（仅 SQLite 需要）
            host: MySQL 主机地址（仅 MySQL 需要）
            port: MySQL 端口（仅 MySQL 需要）
            user: MySQL 用户名（仅 MySQL 需要）
            password: MySQL 密码（仅 MySQL 需要）
            database: 数据库名称
            
        Example:
        ```python
        # SQLite
        loader = DatabaseLoader(db_type='sqlite', db_path='data/stocks.db')
        
        # MySQL
        loader = DatabaseLoader(
            db_type='mysql',
            host='localhost',
            port=3306,
            user='root',
            password='password',
            database='quant'
        )
        ```
        """
        self.db_type = db_type
        self.connection = None
        
        if db_type == 'sqlite':
            if not db_path:
                raise ValueError("SQLite requires db_path")
            self.db_path = db_path
            self._connect_sqlite()
        
        elif db_type == 'mysql':
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
            print(f"Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to SQLite: {e}")
    
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
            print(f"Connected to MySQL database: {self.database}@{self.host}")
        except ImportError:
            raise Exception("PyMySQL not installed. Install with: pip install pymysql")
        except pymysql.Error as e:
            raise Exception(f"Failed to connect to MySQL: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def load(self, symbol: str, start_date: Optional[str] = None,
             end_date: Optional[str] = None, table_name: str = 'bars') -> List[Bar]:
        """
        从数据库加载 K 线数据
        
        Args:
            symbol: 证券代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            table_name: 表名
            
        Returns:
            Bar 对象列表
        """
        if not self.connection:
            raise Exception("Database not connected")
        
        # 构建 SQL 查询
        query = f"SELECT * FROM {table_name} WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date, time"
        
        if self.db_type == 'mysql':
            query = query.replace('?', '%s')  # MySQL 使用 %s 作为占位符
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            bars = []
            for row in rows:
                data = dict(zip(columns, row))
                bar = self._row_to_bar(data, symbol)
                if bar:
                    bars.append(bar)
            
            return bars
        
        except Exception as e:
            raise Exception(f"Database query error: {e}")
    
    def _row_to_bar(self, data: Dict[str, Any], symbol: str) -> Optional[Bar]:
        """将数据库行转换为 Bar 对象"""
        try:
            # 支持多种列名映射
            timestamp = data.get('timestamp') or data.get('date') or data.get('datetime')
            if not timestamp:
                return None
            
            # 如果有 time 列，合并到 timestamp
            if 'time' in data and data['time']:
                timestamp = f"{timestamp} {data['time']}"
            
            bar = Bar(
                timestamp=timestamp,
                symbol=symbol,
                open=float(data.get('open', 0)),
                high=float(data.get('high', 0)),
                low=float(data.get('low', 0)),
                close=float(data.get('close', 0)),
                volume=int(data.get('volume', 0)) or int(data.get('vol', 0)),
                turnover=float(data.get('turnover', 0)) or float(data.get('amount', 0)) or 0.0
            )
            return bar
        
        except Exception as e:
            print(f"Error converting row to Bar: {e}")
            return None
    
    def save_bars(self, bars: List[Bar], table_name: str = 'bars'):
        """
        保存 Bar 数据到数据库
        
        Args:
            bars: Bar 对象列表
            table_name: 表名
        """
        if not self.connection:
            raise Exception("Database not connected")
        
        cursor = self.connection.cursor()
        
        # 创建表（如果不存在）
        self._create_table(cursor, table_name)
        
        # 插入数据
        for bar in bars:
            if self.db_type == 'sqlite':
                query = f"""
                    INSERT OR REPLACE INTO {table_name} 
                    (timestamp, date, time, symbol, open, high, low, close, volume, turnover)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            else:  # MySQL
                query = f"""
                    INSERT INTO {table_name} 
                    (timestamp, date, time, symbol, open, high, low, close, volume, turnover)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    open=VALUES(open), high=VALUES(high), low=VALUES(low), 
                    close=VALUES(close), volume=VALUES(volume), turnover=VALUES(turnover)
                """
            
            # 提取日期和时间
            timestamp_str = str(bar.timestamp)
            date_part = timestamp_str[:10] if len(timestamp_str) >= 10 else timestamp_str
            time_part = timestamp_str[11:19] if len(timestamp_str) >= 19 else '00:00:00'
            
            params = (
                timestamp_str, date_part, time_part, bar.symbol,
                bar.open, bar.high, bar.low, bar.close, bar.volume, bar.turnover
            )
            
            cursor.execute(query, params)
        
        self.connection.commit()
        print(f"Saved {len(bars)} bars to {table_name}")
    
    def _create_table(self, cursor, table_name: str):
        """创建数据表"""
        if self.db_type == 'sqlite':
            query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT,
                    symbol TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER,
                    turnover REAL,
                    UNIQUE(timestamp, symbol)
                )
            """
        else:  # MySQL
            query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    date DATE NOT NULL,
                    time TIME,
                    symbol VARCHAR(20) NOT NULL,
                    open DECIMAL(10,4) NOT NULL,
                    high DECIMAL(10,4) NOT NULL,
                    low DECIMAL(10,4) NOT NULL,
                    close DECIMAL(10,4) NOT NULL,
                    volume BIGINT,
                    turnover DECIMAL(20,4),
                    UNIQUE KEY unique_ts_symbol (timestamp, symbol)
                )
            """
        
        cursor.execute(query)
    
    def list_symbols(self, table_name: str = 'bars') -> List[str]:
        """列出数据库中所有证券代码"""
        if not self.connection:
            raise Exception("Database not connected")
        
        cursor = self.connection.cursor()
        query = f"SELECT DISTINCT symbol FROM {table_name}"
        cursor.execute(query)
        
        symbols = [row[0] for row in cursor.fetchall()]
        return symbols
    
    def get_date_range(self, symbol: str, table_name: str = 'bars') -> tuple:
        """获取某证券的日期范围"""
        if not self.connection:
            raise Exception("Database not connected")
        
        cursor = self.connection.cursor()
        query = f"SELECT MIN(date), MAX(date) FROM {table_name} WHERE symbol = ?"
        
        if self.db_type == 'mysql':
            query = query.replace('?', '%s')
        
        cursor.execute(query, [symbol])
        result = cursor.fetchone()
        
        return result if result else (None, None)
        self.access_order.clear()
    
    def remove(self, key: str):
        """从缓存中移除特定数据"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)


class CachedDataLoader(DataLoader):
    """带缓存的数据加载器"""
    
    def __init__(self, cache_size: int = 1000):
        super().__init__()
        self.cache = DataCache(max_size=cache_size)
    
    def load_history(self, symbol: str, start_date: str, end_date: str, 
                     source: str = 'baostock') -> List[Bar]:
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
        # 生成缓存键
        cache_key = f"{symbol}:{start_date}:{end_date}:{source}"
        
        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached is not None:
            print(f"Cache hit: {cache_key}")
            return cached
        
        # 从数据源加载
        bars = super().load_history(symbol, start_date, end_date, source)
        
        # 存入缓存
        self.cache.put(cache_key, bars)
        print(f"Cache miss, loaded {len(bars)} bars for {symbol}")
        
        return bars


def create_data_loader(use_cache: bool = True, cache_size: int = 1000) -> DataLoader:
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
    
    # 添加 Baostock 数据源
    loader.add_source('baostock', BaostockAdapter())
    loader.add_source('csv', CSVLoader())
    
    return loader


# 便捷函数
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


def load_csv_data(symbol: str, file_path: str, 
                  start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> List[Bar]:
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
