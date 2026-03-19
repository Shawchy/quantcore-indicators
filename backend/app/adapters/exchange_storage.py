"""
交易所数据持久化服务

提供交易所数据的文件存储和加载功能
支持 JSON 格式存储、自动过期检测、数据验证等功能
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger


class ExchangeStorage:
    """交易所数据存储服务"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化存储服务
        
        Args:
            data_dir: 数据存储目录，默认为项目根目录的 data/exchanges 文件夹
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 默认存储在项目根目录的 data/exchanges 文件夹
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / "data" / "exchanges"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.exchanges_file = self.data_dir / "exchanges.json"
        self.metadata_file = self.data_dir / "exchanges_metadata.json"
        
        logger.info(f"交易所数据存储服务已初始化：{self.data_dir}")
    
    def save_exchanges(
        self, 
        exchanges: List[Dict[str, Any]], 
        source: str = "tickflow",
        expiry_days: int = 7
    ) -> bool:
        """
        保存交易所列表到文件
        
        Args:
            exchanges: 交易所列表数据
            source: 数据来源（tickflow, akshare, tushare 等）
            expiry_days: 数据过期天数，默认 7 天
        
        Returns:
            是否保存成功
        """
        try:
            if not exchanges:
                logger.warning("交易所列表为空，跳过保存")
                return False
            
            # 准备数据
            data = {
                "exchanges": exchanges,
                "metadata": {
                    "source": source,
                    "update_time": datetime.now().isoformat(),
                    "expiry_time": (datetime.now() + timedelta(days=expiry_days)).isoformat(),
                    "expiry_days": expiry_days,
                    "count": len(exchanges),
                    "total_instruments": sum(exc.get('count', 0) for exc in exchanges)
                }
            }
            
            # 保存交易所数据
            with open(self.exchanges_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存简化版元数据（方便快速读取）
            metadata = {
                "update_time": data["metadata"]["update_time"],
                "expiry_time": data["metadata"]["expiry_time"],
                "source": source,
                "count": len(exchanges)
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(
                f"✅ 交易所数据已保存到 {self.exchanges_file}\n"
                f"   来源：{source}\n"
                f"   交易所数量：{len(exchanges)}\n"
                f"   总标的数：{data['metadata']['total_instruments']}\n"
                f"   过期时间：{data['metadata']['expiry_time']}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存交易所数据失败：{e}")
            return False
    
    def load_exchanges(self) -> Optional[Dict[str, Any]]:
        """
        从文件加载交易所列表
        
        Returns:
            包含 exchanges 和 metadata 的字典，如果文件不存在或已过期则返回 None
        """
        try:
            # 检查文件是否存在
            if not self.exchanges_file.exists():
                logger.debug("交易所数据文件不存在")
                return None
            
            if not self.metadata_file.exists():
                logger.warning("元数据文件不存在，将重新加载完整数据")
                # 尝试从主文件加载
                return self._load_from_file()
            
            # 先检查元数据
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 检查是否过期
            expiry_time = datetime.fromisoformat(metadata.get('expiry_time', ''))
            if datetime.now() > expiry_time:
                logger.warning(f"交易所数据已过期（过期时间：{expiry_time}）")
                return None
            
            # 检查来源
            logger.debug(
                f"从缓存加载交易所数据:\n"
                f"   来源：{metadata.get('source', 'unknown')}\n"
                f"   更新时间：{metadata.get('update_time', 'unknown')}\n"
                f"   交易所数量：{metadata.get('count', 0)}"
            )
            
            # 加载完整数据
            return self._load_from_file()
            
        except Exception as e:
            logger.error(f"❌ 加载交易所数据失败：{e}")
            return None
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """从主文件加载数据"""
        try:
            with open(self.exchanges_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据结构
            if 'exchanges' not in data or 'metadata' not in data:
                logger.warning("数据文件格式不正确")
                return None
            
            # 再次检查过期时间
            expiry_time = datetime.fromisoformat(data['metadata'].get('expiry_time', ''))
            if datetime.now() > expiry_time:
                logger.warning("数据已过期")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"加载文件失败：{e}")
            return None
    
    def is_data_valid(self) -> bool:
        """
        检查数据是否有效（存在且未过期）
        
        Returns:
            数据是否有效
        """
        try:
            if not self.metadata_file.exists():
                return False
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            expiry_time = datetime.fromisoformat(metadata.get('expiry_time', ''))
            return datetime.now() <= expiry_time
            
        except Exception:
            return False
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        获取元数据（不加载完整数据）
        
        Returns:
            元数据字典
        """
        try:
            if not self.metadata_file.exists():
                return None
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 添加是否过期的信息
            expiry_time = datetime.fromisoformat(metadata.get('expiry_time', ''))
            metadata['is_valid'] = datetime.now() <= expiry_time
            metadata['is_expired'] = not metadata['is_valid']
            
            return metadata
            
        except Exception as e:
            logger.error(f"获取元数据失败：{e}")
            return None
    
    def clear(self) -> bool:
        """
        清除存储的数据
        
        Returns:
            是否清除成功
        """
        try:
            if self.exchanges_file.exists():
                self.exchanges_file.unlink()
                logger.debug(f"已删除：{self.exchanges_file}")
            
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                logger.debug(f"已删除：{self.metadata_file}")
            
            logger.info("交易所数据已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除数据失败：{e}")
            return False
    
    def export_to_csv(self, output_file: Optional[str] = None) -> Optional[str]:
        """
        导出交易所数据为 CSV 格式
        
        Args:
            output_file: 输出文件路径，默认在 data/exchanges/exports 目录下
        
        Returns:
            输出文件路径，如果失败返回 None
        """
        try:
            data = self.load_exchanges()
            if not data:
                logger.warning("没有可导出的数据")
                return None
            
            # 准备导出目录
            export_dir = self.data_dir / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if output_file:
                output_path = Path(output_file)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = export_dir / f"exchanges_{timestamp}.csv"
            
            # 写入 CSV
            import csv
            exchanges = data['exchanges']
            
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(['交易所代码', '地区', '标的数量', '数据类型'])
                
                # 写入数据
                for exc in exchanges:
                    exchange_code = exc.get('exchange', '')
                    # 根据交易所代码判断数据类型
                    if exchange_code in ['SH', 'SZ', 'BJ']:
                        data_type = '股票'
                    elif exchange_code in ['SHFE', 'DCE', 'CZCE', 'CFFEX', 'INE', 'GFEX']:
                        data_type = '期货'
                    else:
                        data_type = '未知'
                    
                    writer.writerow([
                        exchange_code,
                        exc.get('region', ''),
                        exc.get('count', 0),
                        data_type
                    ])
            
            logger.info(f"✅ 已导出 CSV 文件：{output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"导出 CSV 失败：{e}")
            return None
    
    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        获取统计数据
        
        Returns:
            统计数据字典
        """
        try:
            data = self.load_exchanges()
            if not data:
                return None
            
            exchanges = data['exchanges']
            metadata = data['metadata']
            
            # 分类统计
            stock_exchanges = [e for e in exchanges if e.get('exchange') in ['SH', 'SZ', 'BJ']]
            futures_exchanges = [e for e in exchanges if e.get('exchange') in ['SHFE', 'DCE', 'CZCE', 'CFFEX', 'INE', 'GFEX']]
            
            stats = {
                'total_exchanges': len(exchanges),
                'total_instruments': sum(e.get('count', 0) for e in exchanges),
                'stock_exchanges': {
                    'count': len(stock_exchanges),
                    'instruments': sum(e.get('count', 0) for e in stock_exchanges)
                },
                'futures_exchanges': {
                    'count': len(futures_exchanges),
                    'instruments': sum(e.get('count', 0) for e in futures_exchanges)
                },
                'by_exchange': [
                    {
                        'exchange': e.get('exchange'),
                        'region': e.get('region'),
                        'count': e.get('count', 0)
                    }
                    for e in exchanges
                ],
                'metadata': metadata
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计数据失败：{e}")
            return None
    
    def save_exchange_instruments(
        self,
        exchange: str,
        instruments: List[Dict[str, Any]],
        source: str = "tickflow",
        expiry_days: int = 7
    ) -> bool:
        """
        保存交易所标的列表到文件
        
        Args:
            exchange: 交易所代码（如：SH, SZ）
            instruments: 标的列表数据
            source: 数据来源
            expiry_days: 数据过期天数
        
        Returns:
            是否保存成功
        """
        try:
            if not instruments:
                logger.warning(f"交易所 {exchange} 标的列表为空，跳过保存")
                return False
            
            # 准备数据
            data = {
                "instruments": instruments,
                "metadata": {
                    "exchange": exchange,
                    "source": source,
                    "update_time": datetime.now().isoformat(),
                    "expiry_time": (datetime.now() + timedelta(days=expiry_days)).isoformat(),
                    "expiry_days": expiry_days,
                    "count": len(instruments)
                }
            }
            
            # 保存数据到文件
            instruments_file = self.data_dir / f"instruments_{exchange}.json"
            with open(instruments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(
                f"✅ {exchange} 标的数据已保存到 {instruments_file}\n"
                f"   来源：{source}\n"
                f"   标的数量：{len(instruments)}\n"
                f"   过期时间：{data['metadata']['expiry_time']}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"保存 {exchange} 标的数据失败：{e}")
            return False
    
    def load_exchange_instruments(self, exchange: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载交易所标的列表
        
        Args:
            exchange: 交易所代码
        
        Returns:
            包含 instruments 和 metadata 的字典，如果文件不存在或已过期则返回 None
        """
        try:
            instruments_file = self.data_dir / f"instruments_{exchange}.json"
            
            # 检查文件是否存在
            if not instruments_file.exists():
                logger.debug(f"{exchange} 标的数据文件不存在")
                return None
            
            # 加载数据
            with open(instruments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据结构
            if 'instruments' not in data or 'metadata' not in data:
                logger.warning(f"{exchange} 标的数据文件格式不正确")
                return None
            
            # 检查过期时间
            expiry_time = datetime.fromisoformat(data['metadata'].get('expiry_time', ''))
            if datetime.now() > expiry_time:
                logger.warning(f"{exchange} 标的数据已过期（过期时间：{expiry_time}）")
                return None
            
            metadata = data['metadata']
            logger.debug(
                f"从缓存加载 {exchange} 标的数据:\n"
                f"   来源：{metadata.get('source', 'unknown')}\n"
                f"   更新时间：{metadata.get('update_time', 'unknown')}\n"
                f"   标的数量：{metadata.get('count', 0)}"
            )
            
            return data
            
        except Exception as e:
            logger.error(f"加载 {exchange} 标的数据失败：{e}")
            return None
    
    def is_instruments_valid(self, exchange: str) -> bool:
        """
        检查交易所标的数据是否有效
        
        Args:
            exchange: 交易所代码
        
        Returns:
            数据是否有效
        """
        try:
            instruments_file = self.data_dir / f"instruments_{exchange}.json"
            
            if not instruments_file.exists():
                return False
            
            with open(instruments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            expiry_time = datetime.fromisoformat(data['metadata'].get('expiry_time', ''))
            return datetime.now() <= expiry_time
            
        except Exception:
            return False
    
    def clear_instruments(self, exchange: Optional[str] = None) -> bool:
        """
        清除交易所标的数据
        
        Args:
            exchange: 交易所代码，如果为 None 则清除所有
        
        Returns:
            是否清除成功
        """
        try:
            if exchange:
                # 清除特定交易所
                instruments_file = self.data_dir / f"instruments_{exchange}.json"
                if instruments_file.exists():
                    instruments_file.unlink()
                    logger.debug(f"已删除：{instruments_file}")
                logger.info(f"{exchange} 标的数据已清除")
            else:
                # 清除所有
                for file in self.data_dir.glob("instruments_*.json"):
                    file.unlink()
                    logger.debug(f"已删除：{file}")
                logger.info("所有交易所标的数据已清除")
            
            return True
            
        except Exception as e:
            logger.error(f"清除标的数据失败：{e}")
            return False


# 创建全局单例
exchange_storage = ExchangeStorage()
