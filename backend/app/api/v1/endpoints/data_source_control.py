"""
数据源管理工具
提供数据源开关控制功能，可以在不拉取外部数据的情况下使用本地/测试数据
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from loguru import logger
from enum import Enum

from app.models.schemas import ResponseModel
from app.api.deps import CurrentAdminUser

router = APIRouter()


class DataSourceMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class DataSourceStatus:
    _instance = None
    _mode: DataSourceMode = DataSourceMode.ONLINE
    _disabled_sources: set = set()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def mode(self) -> DataSourceMode:
        return self._mode
    
    @mode.setter
    def mode(self, value: DataSourceMode):
        self._mode = value
        logger.info(f"数据源模式已切换为：{value.value}")
    
    @property
    def disabled_sources(self) -> set:
        return self._disabled_sources
    
    def disable_source(self, source: str):
        self._disabled_sources.add(source)
        logger.info(f"已禁用数据源：{source}")
    
    def enable_source(self, source: str):
        self._disabled_sources.discard(source)
        logger.info(f"已启用数据源：{source}")
    
    def is_source_disabled(self, source: str) -> bool:
        return source in self._disabled_sources


data_source_status = DataSourceStatus()


@router.get("/status", response_model=ResponseModel[Dict[str, Any]])
async def get_data_source_status(
    current_user: CurrentAdminUser = None
):
    """
    获取当前数据源状态
    
    返回：
    - mode: 当前模式（online/offline）
    - disabled_sources: 已禁用的数据源列表
    """
    return ResponseModel(data={
        "mode": data_source_status.mode.value,
        "disabled_sources": list(data_source_status.disabled_sources),
        "available_modes": [m.value for m in DataSourceMode]
    })


@router.post("/mode", response_model=ResponseModel[Dict[str, Any]])
async def set_data_source_mode(
    mode: str = Query(..., description="模式：online-在线，offline-离线"),
    current_user: CurrentAdminUser = None
):
    """
    设置数据源模式
    
    模式说明：
    - online: 正常从外部数据源拉取数据
    - offline: 禁用所有外部数据源，只使用本地缓存/数据库
    """
    try:
        new_mode = DataSourceMode(mode)
        data_source_status.mode = new_mode
        
        if new_mode == DataSourceMode.OFFLINE:
            for source in ["tushare", "akshare", "baostock", "yfinance"]:
                data_source_status.disable_source(source)
        else:
            data_source_status.disabled_sources.clear()
        
        return ResponseModel(data={
            "mode": data_source_status.mode.value,
            "disabled_sources": list(data_source_status.disabled_sources),
            "message": f"数据源模式已切换为：{new_mode.value}"
        })
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的模式：{mode}")


@router.post("/toggle", response_model=ResponseModel[Dict[str, Any]])
async def toggle_data_source(
    source: str = Query(..., description="数据源名称：tushare, akshare, baostock, yfinance"),
    enabled: bool = Query(..., description="是否启用"),
    current_user: CurrentAdminUser = None
):
    """
    单独启用/禁用某个数据源
    """
    valid_sources = {"tushare", "akshare", "baostock", "yfinance"}
    
    if source not in valid_sources:
        raise HTTPException(status_code=400, detail=f"无效的数据源：{source}")
    
    if enabled:
        data_source_status.enable_source(source)
    else:
        data_source_status.disable_source(source)
    
    return ResponseModel(data={
        "source": source,
        "enabled": enabled,
        "disabled_sources": list(data_source_status.disabled_sources),
        "message": f"数据源 {source} 已{'启用' if enabled else '禁用'}"
    })


@router.post("/reset", response_model=ResponseModel[Dict[str, Any]])
async def reset_data_source(
    current_user: CurrentAdminUser = None
):
    """
    重置数据源状态（恢复默认）
    """
    data_source_status.mode = DataSourceMode.ONLINE
    data_source_status.disabled_sources.clear()
    
    return ResponseModel(data={
        "mode": data_source_status.mode.value,
        "disabled_sources": list(data_source_status.disabled_sources),
        "message": "数据源状态已重置为默认"
    })


def is_data_fetch_disabled() -> bool:
    """检查是否禁用数据拉取"""
    return data_source_status.mode == DataSourceMode.OFFLINE


def is_source_available(source: str) -> bool:
    """检查数据源是否可用"""
    return not data_source_status.is_source_disabled(source)
