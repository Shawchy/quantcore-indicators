from fastapi import APIRouter, Query, Body
from app.models.schemas import ResponseModel
from typing import Optional
import uuid
import json
from datetime import datetime
from loguru import logger
from sqlalchemy import select

from app.storage import Strategy, get_session

router = APIRouter()


@router.get("/list", response_model=ResponseModel[list])
async def get_strategy_list():
    async with get_session() as session:
        result = await session.execute(select(Strategy))
        strategies = result.scalars().all()
        
        return ResponseModel(data=[{
            "strategy_id": s.strategy_id,
            "name": s.name,
            "strategy_type": s.strategy_type,
            "is_active": s.is_active,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for s in strategies])


@router.get("/{strategy_id}", response_model=ResponseModel[dict])
async def get_strategy(strategy_id: str):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        return ResponseModel(data={
            "strategy_id": strategy.strategy_id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": json.loads(strategy.config) if strategy.config else {},
            "is_active": strategy.is_active,
            "created_at": strategy.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })


@router.post("/create", response_model=ResponseModel[dict])
async def create_strategy(strategy_config: dict = Body(...)):
    strategy_id = f"strategy_{uuid.uuid4().hex[:8]}"
    
    async with get_session() as session:
        strategy = Strategy(
            strategy_id=strategy_id,
            name=strategy_config.get("name", "未命名策略"),
            strategy_type=strategy_config.get("type", "custom"),
            config=json.dumps(strategy_config.get("config", {})),
            is_active=True
        )
        session.add(strategy)
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略创建成功"
        })


@router.put("/{strategy_id}", response_model=ResponseModel[dict])
async def update_strategy(strategy_id: str, strategy_config: dict = Body(...)):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        if "name" in strategy_config:
            strategy.name = strategy_config["name"]
        if "config" in strategy_config:
            strategy.config = json.dumps(strategy_config["config"])
        if "is_active" in strategy_config:
            strategy.is_active = strategy_config["is_active"]
        
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略更新成功"
        })


@router.delete("/{strategy_id}", response_model=ResponseModel[dict])
async def delete_strategy(strategy_id: str):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        await session.delete(strategy)
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略删除成功"
        })


@router.post("/{strategy_id}/optimize", response_model=ResponseModel[dict])
async def optimize_strategy_params(
    strategy_id: str,
    param_ranges: dict = Body(..., description="参数优化范围"),
    method: str = Query("bayesian", description="优化方法: bayesian, grid")
):
    return ResponseModel(data={
        "strategy_id": strategy_id,
        "status": "optimizing",
        "message": "参数优化任务已提交"
    })
