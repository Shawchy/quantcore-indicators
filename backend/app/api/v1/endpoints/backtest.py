from fastapi import APIRouter, Query, Body
from app.models.schemas import ResponseModel
from typing import Optional
import uuid
import json
from datetime import datetime
from loguru import logger
from sqlalchemy import select

from app.storage import BacktestRecord, get_session
from app.config import settings

router = APIRouter()


@router.post("/run", response_model=ResponseModel[dict])
async def run_backtest(backtest_config: dict = Body(...)):
    backtest_id = f"backtest_{uuid.uuid4().hex[:8]}"
    
    async with get_session() as session:
        record = BacktestRecord(
            backtest_id=backtest_id,
            strategy_id=backtest_config.get("strategy_id", ""),
            start_date=backtest_config.get("start_date", ""),
            end_date=backtest_config.get("end_date", ""),
            initial_capital=backtest_config.get("initial_capital", settings.BACKTEST_INITIAL_CAPITAL),
            status="pending"
        )
        session.add(record)
        await session.commit()
        
        return ResponseModel(data={
            "backtest_id": backtest_id,
            "status": "pending",
            "message": "回测任务已创建"
        })


@router.get("/result/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_result(backtest_id: str):
    async with get_session() as session:
        result = await session.execute(
            select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return ResponseModel(success=False, code="NOT_FOUND", message="回测记录不存在")
        
        return ResponseModel(data={
            "backtest_id": record.backtest_id,
            "strategy_id": record.strategy_id,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "initial_capital": record.initial_capital,
            "final_capital": record.final_capital,
            "status": record.status,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })


@router.get("/performance/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_performance(backtest_id: str):
    async with get_session() as session:
        result = await session.execute(
            select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return ResponseModel(success=False, code="NOT_FOUND", message="回测记录不存在")
        
        return ResponseModel(data={
            "backtest_id": record.backtest_id,
            "total_return": record.total_return,
            "annual_return": record.annual_return,
            "max_drawdown": record.max_drawdown,
            "sharpe_ratio": record.sharpe_ratio
        })


@router.get("/trades/{backtest_id}", response_model=ResponseModel[list])
async def get_backtest_trades(
    backtest_id: str,
    page: int = Query(1),
    page_size: int = Query(50)
):
    return ResponseModel(data=[])


@router.get("/history", response_model=ResponseModel[list])
async def get_backtest_history(limit: int = Query(20)):
    async with get_session() as session:
        result = await session.execute(
            select(BacktestRecord).order_by(BacktestRecord.created_at.desc()).limit(limit)
        )
        records = result.scalars().all()
        
        return ResponseModel(data=[{
            "backtest_id": r.backtest_id,
            "strategy_id": r.strategy_id,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "total_return": r.total_return,
            "status": r.status,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for r in records])
