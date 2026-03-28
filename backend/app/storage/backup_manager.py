"""
数据备份和恢复模块

提供数据备份、恢复和灾难恢复功能
"""
import os
import shutil
import gzip
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class BackupManager:
    """数据备份管理器"""
    
    def __init__(self, base_dir: str = "./data", backup_dir: str = "./backups"):
        self.base_dir = Path(base_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_config = {
            "full_backup": {
                "schedule": "weekly",
                "retention_days": 30,
                "compress": True
            },
            "incremental_backup": {
                "schedule": "daily",
                "retention_days": 7,
                "compress": False
            },
            "critical_backup": {
                "schedule": "hourly",
                "retention_days": 3,
                "compress": False
            }
        }
        
        self.stats = {
            "total_backups": 0,
            "total_size_mb": 0.0,
            "last_backup_time": None,
            "last_backup_type": None,
            "successful_backups": 0,
            "failed_backups": 0
        }
    
    async def create_full_backup(self, description: str = "") -> Dict[str, Any]:
        """
        创建完整备份
        
        备份所有数据目录和数据库
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"开始创建完整备份: {backup_name}")
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            backed_up = []
            total_size = 0
            
            dirs_to_backup = [
                ("sqlite", self.base_dir / "sqlite"),
                ("parquet", self.base_dir / "parquet"),
                ("exchanges", self.base_dir / "exchanges"),
                ("cache", self.base_dir / "cache"),
            ]
            
            for name, source_dir in dirs_to_backup:
                if source_dir.exists():
                    dest_dir = backup_path / name
                    
                    if self.backup_config["full_backup"]["compress"]:
                        await self._compress_directory(source_dir, dest_dir)
                    else:
                        shutil.copytree(source_dir, dest_dir)
                    
                    size = self._get_directory_size(dest_dir)
                    total_size += size
                    backed_up.append({
                        "name": name,
                        "path": str(dest_dir),
                        "size_mb": round(size / 1024 / 1024, 2)
                    })
                    logger.info(f"  已备份: {name} ({size / 1024 / 1024:.2f} MB)")
            
            metadata = {
                "backup_name": backup_name,
                "backup_type": "full",
                "timestamp": timestamp,
                "description": description,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "directories": backed_up,
                "compressed": self.backup_config["full_backup"]["compress"]
            }
            
            with open(backup_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.stats["total_backups"] += 1
            self.stats["total_size_mb"] += total_size / 1024 / 1024
            self.stats["last_backup_time"] = timestamp
            self.stats["last_backup_type"] = "full"
            self.stats["successful_backups"] += 1
            
            logger.info(f"完整备份创建成功: {backup_name}, 总大小: {total_size / 1024 / 1024:.2f} MB")
            
            return {
                "success": True,
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "metadata": metadata
            }
        
        except Exception as e:
            self.stats["failed_backups"] += 1
            logger.error(f"完整备份创建失败: {e}")
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_incremental_backup(self, description: str = "") -> Dict[str, Any]:
        """
        创建增量备份
        
        只备份自上次备份以来变化的文件
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"incremental_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"开始创建增量备份: {backup_name}")
        
        try:
            last_backup = await self._get_last_backup_info()
            
            if not last_backup:
                logger.info("未找到上次备份，转为完整备份")
                return await self.create_full_backup(description)
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            backed_up = []
            total_size = 0
            last_backup_time = datetime.strptime(
                last_backup["timestamp"], "%Y%m%d_%H%M%S"
            )
            
            dirs_to_check = [
                ("sqlite", self.base_dir / "sqlite"),
                ("parquet", self.base_dir / "parquet"),
            ]
            
            for name, source_dir in dirs_to_check:
                if source_dir.exists():
                    changed_files = self._get_changed_files(
                        source_dir, last_backup_time
                    )
                    
                    if changed_files:
                        dest_dir = backup_path / name
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        
                        for file_path in changed_files:
                            rel_path = file_path.relative_to(source_dir)
                            dest_file = dest_dir / rel_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_path, dest_file)
                        
                        size = self._get_directory_size(dest_dir)
                        total_size += size
                        backed_up.append({
                            "name": name,
                            "files_count": len(changed_files),
                            "size_mb": round(size / 1024 / 1024, 2)
                        })
            
            if not backed_up:
                logger.info("没有变化的文件，跳过备份")
                shutil.rmtree(backup_path)
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "no_changes"
                }
            
            metadata = {
                "backup_name": backup_name,
                "backup_type": "incremental",
                "timestamp": timestamp,
                "description": description,
                "base_backup": last_backup["backup_name"],
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "directories": backed_up
            }
            
            with open(backup_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.stats["total_backups"] += 1
            self.stats["total_size_mb"] += total_size / 1024 / 1024
            self.stats["last_backup_time"] = timestamp
            self.stats["last_backup_type"] = "incremental"
            self.stats["successful_backups"] += 1
            
            logger.info(f"增量备份创建成功: {backup_name}")
            
            return {
                "success": True,
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "metadata": metadata
            }
        
        except Exception as e:
            self.stats["failed_backups"] += 1
            logger.error(f"增量备份创建失败: {e}")
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_backup(self, backup_name: str, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        从备份恢复数据
        
        Args:
            backup_name: 备份名称
            target_dir: 目标目录（默认为原始数据目录）
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"备份不存在: {backup_name}")
            return {
                "success": False,
                "error": "backup_not_found"
            }
        
        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            logger.error(f"备份元数据不存在: {backup_name}")
            return {
                "success": False,
                "error": "metadata_not_found"
            }
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        logger.info(f"开始从备份恢复: {backup_name}")
        
        try:
            restore_dir = Path(target_dir) if target_dir else self.base_dir
            
            restored = []
            
            for dir_info in metadata.get("directories", []):
                name = dir_info["name"]
                source_dir = backup_path / name
                dest_dir = restore_dir / name
                
                if source_dir.exists():
                    if dest_dir.exists():
                        backup_dest = dest_dir.parent / f"{name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.move(str(dest_dir), str(backup_dest))
                        logger.info(f"  已备份现有目录: {name} -> {backup_dest}")
                    
                    if metadata.get("compressed"):
                        await self._decompress_directory(source_dir, dest_dir)
                    else:
                        shutil.copytree(source_dir, dest_dir)
                    
                    restored.append(name)
                    logger.info(f"  已恢复: {name}")
            
            logger.info(f"恢复完成: {backup_name}, 恢复目录: {restored}")
            
            return {
                "success": True,
                "backup_name": backup_name,
                "restored_directories": restored,
                "restore_path": str(restore_dir)
            }
        
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "metadata.json"
                
                if metadata_path.exists():
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    
                    backups.append({
                        "name": backup_dir.name,
                        "type": metadata.get("backup_type", "unknown"),
                        "timestamp": metadata.get("timestamp", ""),
                        "size_mb": metadata.get("total_size_mb", 0),
                        "description": metadata.get("description", ""),
                        "path": str(backup_dir)
                    })
        
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """清理过期备份"""
        logger.info("开始清理过期备份")
        
        backups = await self.list_backups()
        deleted = []
        
        retention_config = {
            "full": self.backup_config["full_backup"]["retention_days"],
            "incremental": self.backup_config["incremental_backup"]["retention_days"],
            "critical": self.backup_config["critical_backup"]["retention_days"]
        }
        
        for backup in backups:
            backup_type = backup["type"]
            retention_days = retention_config.get(backup_type, 30)
            
            backup_time = datetime.strptime(backup["timestamp"], "%Y%m%d_%H%M%S")
            age_days = (datetime.now() - backup_time).days
            
            if age_days > retention_days:
                backup_path = Path(backup["path"])
                shutil.rmtree(backup_path)
                deleted.append(backup["name"])
                logger.info(f"  删除过期备份: {backup['name']} ({age_days} 天)")
        
        logger.info(f"清理完成，删除 {len(deleted)} 个过期备份")
        
        return {
            "deleted_count": len(deleted),
            "deleted_backups": deleted
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        return {
            **self.stats,
            "total_size_mb": round(self.stats["total_size_mb"], 2)
        }
    
    async def _get_last_backup_info(self) -> Optional[Dict[str, Any]]:
        """获取上次备份信息"""
        backups = await self.list_backups()
        
        if backups:
            return backups[0]
        return None
    
    def _get_directory_size(self, directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    def _get_changed_files(self, directory: Path, since_time: datetime) -> List[Path]:
        """获取自指定时间以来变化的文件"""
        changed_files = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > since_time:
                    changed_files.append(file_path)
        
        return changed_files
    
    async def _compress_directory(self, source: Path, dest: Path):
        """压缩目录"""
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        with gzip.open(str(dest) + ".tar.gz", "wb") as f:
            import tarfile
            with tarfile.open(fileobj=f, mode="w") as tar:
                tar.add(source, arcname=source.name)
    
    async def _decompress_directory(self, source: Path, dest: Path):
        """解压目录"""
        import tarfile
        
        gz_file = str(source) + ".tar.gz"
        if Path(gz_file).exists():
            with gzip.open(gz_file, "rb") as f:
                with tarfile.open(fileobj=f, mode="r") as tar:
                    tar.extractall(dest.parent)


backup_manager = BackupManager()
