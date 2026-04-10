"""
数据版本管理

记录数据变更历史，支持版本回溯
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, select, func
from sqlalchemy.orm import relationship
from app.storage.sqlite import Base, get_session
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
from loguru import logger


class DataVersion(Base):
    """数据版本表"""
    __tablename__ = "data_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False, index=True)  # 表名
    record_id = Column(Integer, nullable=False, index=True)  # 记录 ID
    version = Column(Integer, nullable=False, index=True)  # 版本号
    operation = Column(String(20), nullable=False)  # INSERT/UPDATE/DELETE
    old_data = Column(Text)  # 旧数据（JSON）
    new_data = Column(Text)  # 新数据（JSON）
    changed_by = Column(String(50), index=True)  # 操作者（数据源）
    changed_at = Column(DateTime, default=datetime.now, index=True)  # 变更时间
    reason = Column(String(200))  # 变更原因


class DataVersionManager:
    """数据版本管理器"""
    
    @staticmethod
    async def create_version(
        table_name: str,
        record_id: int,
        operation: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        changed_by: str = "system",
        reason: str = ""
    ):
        """
        创建数据版本记录
        
        Args:
            table_name: 表名
            record_id: 记录 ID
            operation: 操作类型（INSERT/UPDATE/DELETE）
            old_data: 旧数据字典
            new_data: 新数据字典
            changed_by: 操作者
            reason: 变更原因
        """
        async with get_session() as session:
            # 获取当前最大版本号
            query = select(func.max(DataVersion.version)).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id
            )
            result = await session.execute(query)
            max_version = result.scalar() or 0
            
            # 创建新版本
            version = DataVersion(
                table_name=table_name,
                record_id=record_id,
                version=max_version + 1,
                operation=operation,
                old_data=json.dumps(old_data, ensure_ascii=False) if old_data else None,
                new_data=json.dumps(new_data, ensure_ascii=False) if new_data else None,
                changed_by=changed_by,
                reason=reason
            )
            
            session.add(version)
            await session.commit()
            
            logger.debug(f"创建版本记录：{table_name}:{record_id} v{max_version + 1} ({operation})")
    
    @staticmethod
    async def get_version_history(
        table_name: str,
        record_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取数据版本历史
        
        Args:
            table_name: 表名
            record_id: 记录 ID
            limit: 返回数量限制
        
        Returns:
            版本历史记录列表
        """
        async with get_session() as session:
            query = select(DataVersion).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id
            ).order_by(DataVersion.version.desc()).limit(limit)
            
            result = await session.execute(query)
            versions = result.scalars().all()
            
            return [DataVersionManager._version_to_dict(v) for v in versions]
    
    @staticmethod
    async def get_version_at(
        table_name: str,
        record_id: int,
        version: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定版本的数据
        
        Args:
            table_name: 表名
            record_id: 记录 ID
            version: 版本号
        
        Returns:
            指定版本的数据
        """
        async with get_session() as session:
            query = select(DataVersion).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id,
                DataVersion.version == version
            )
            
            result = await session.execute(query)
            version_record = result.scalar_one_or_none()
            
            if not version_record:
                return None
            
            return DataVersionManager._version_to_dict(version_record)
    
    @staticmethod
    async def rollback_to_version(
        table_name: str,
        record_id: int,
        target_version: int,
        changed_by: str = "system"
    ) -> bool:
        """
        回滚到指定版本
        
        Args:
            table_name: 表名
            record_id: 记录 ID
            target_version: 目标版本号
            changed_by: 操作者
        
        Returns:
            是否成功
        """
        async with get_session() as session:
            # 获取目标版本的数据
            query = select(DataVersion).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id,
                DataVersion.version == target_version
            )
            result = await session.execute(query)
            target = result.scalar_one_or_none()
            
            if not target:
                logger.error(f"版本 {target_version} 不存在")
                return False
            
            # 获取当前最新版本
            query = select(DataVersion).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id
            ).order_by(DataVersion.version.desc()).limit(1)
            result = await session.execute(query)
            latest = result.scalar_one_or_none()
            
            if not latest:
                logger.error(f"记录 {record_id} 不存在")
                return False
            
            # 创建回滚版本记录
            rollback_data = json.loads(target.new_data) if target.new_data else None
            await DataVersionManager.create_version(
                table_name=table_name,
                record_id=record_id,
                operation="ROLLBACK",
                old_data=json.loads(latest.new_data) if latest.new_data else None,
                new_data=rollback_data,
                changed_by=changed_by,
                reason=f"回滚到版本 {target_version}"
            )
            
            logger.info(f"回滚 {table_name}:{record_id} 到版本 {target_version}")
            return True
    
    @staticmethod
    async def cleanup_old_versions(
        table_name: Optional[str] = None,
        keep_versions: int = 10
    ):
        """
        清理旧版本记录
        
        Args:
            table_name: 表名（可选，None 表示所有表）
            keep_versions: 保留的版本数量
        """
        async with get_session() as session:
            # 获取所有唯一的 (table_name, record_id) 组合
            query = select(
                DataVersion.table_name,
                DataVersion.record_id,
                func.max(DataVersion.version).label('max_version')
            ).group_by(
                DataVersion.table_name,
                DataVersion.record_id
            )
            
            if table_name:
                query = query.where(DataVersion.table_name == table_name)
            
            result = await session.execute(query)
            records = result.all()
            
            deleted_count = 0
            for table_name, record_id, max_version in records:
                # 删除旧版本（保留最近的 keep_versions 个版本）
                delete_query = select(DataVersion.id).where(
                    DataVersion.table_name == table_name,
                    DataVersion.record_id == record_id,
                    DataVersion.version < (max_version - keep_versions + 1)
                )
                delete_result = await session.execute(delete_query)
                old_ids = delete_result.scalars().all()
                
                if old_ids:
                    await session.execute(
                        DataVersion.__table__.delete().where(
                            DataVersion.id.in_(old_ids)
                        )
                    )
                    deleted_count += len(old_ids)
            
            await session.commit()
            logger.info(f"清理 {deleted_count} 条旧版本记录")
    
    @staticmethod
    def _version_to_dict(version: DataVersion) -> Dict[str, Any]:
        """版本对象转字典"""
        return {
            'id': version.id,
            'table_name': version.table_name,
            'record_id': version.record_id,
            'version': version.version,
            'operation': version.operation,
            'old_data': json.loads(version.old_data) if version.old_data else None,
            'new_data': json.loads(version.new_data) if version.new_data else None,
            'changed_by': version.changed_by,
            'changed_at': version.changed_at.isoformat() if version.changed_at else None,
            'reason': version.reason
        }


# 装饰器：自动记录版本变更
def track_version(table_name: str, id_field: str = 'id'):
    """
    装饰器：自动记录数据版本变更
    
    用法:
    @track_version('kline', 'code')
    async def update_kline(code: str, data: dict):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取记录 ID
            record_id = kwargs.get(id_field) or (args[0] if args else None)
            
            if record_id is None:
                logger.warning(f"无法获取记录 ID，跳过版本追踪")
                return await func(*args, **kwargs)
            
            # 调用原函数
            result = await func(*args, **kwargs)
            
            # 记录版本（简化处理，实际应用需要获取旧数据和新数据）
            await DataVersionManager.create_version(
                table_name=table_name,
                record_id=record_id,
                operation="UPDATE",
                changed_by="system",
                reason=f"通过 {func.__name__} 更新"
            )
            
            return result
        
        return wrapper
    return decorator
