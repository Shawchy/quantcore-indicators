from fastapi import APIRouter, Query, Body, BackgroundTasks, Depends
from app.models.schemas import ResponseModel, PagedResponseModel, PageInfo
from app.api.deps import CurrentUser
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import uuid
import json
from datetime import datetime
from loguru import logger
from sqlalchemy import select, func

from app.storage import BacktestRecord, TradeRecord, get_session
from app.config import settings
from app.adapters import data_source_manager
from app.core.backtest import BacktestEngine

router = APIRouter()


class StrategyParams(BaseModel):
    short_period: int = Field(default=5, ge=2, le=120)
    long_period: int = Field(default=20, ge=5, le=250)
    rsi_period: int = Field(default=14, ge=2, le=100)
    oversold: float = Field(default=30, ge=5, le=50)
    overbought: float = Field(default=70, ge=50, le=95)
    fast_period: int = Field(default=12, ge=2, le=60)
    slow_period: int = Field(default=26, ge=5, le=120)
    signal_period: int = Field(default=9, ge=2, le=50)
    bollinger_period: int = Field(default=20, ge=5, le=100)
    std_dev: float = Field(default=2.0, ge=0.5, le=5.0)


class BacktestConfig(BaseModel):
    code: str = Field(default="000001", pattern=r"^\d{6}$")
    start_date: str = Field(default="", pattern=r"^\d{4}-\d{2}-\d{2}$|^$")
    end_date: str = Field(default="", pattern=r"^\d{4}-\d{2}-\d{2}$|^$")
    strategy_type: Literal["ma_cross", "macd_cross", "rsi", "bollinger"] = "ma_cross"
    strategy_params: StrategyParams = Field(default_factory=StrategyParams)
    initial_capital: float = Field(default=1000000, gt=0, le=1e9)
    strategy_id: str = Field(default="")
    
    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        if v and info.data.get("start_date"):
            start = datetime.strptime(info.data["start_date"], "%Y-%m-%d")
            end = datetime.strptime(v, "%Y-%m-%d")
            if start >= end:
                raise ValueError("开始日期必须早于结束日期")
        return v


async def run_backtest_task(
    backtest_id: str,
    code: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    strategy_type: str,
    strategy_params: dict
):
    try:
        async with get_session() as session:
            result = await session.execute(
                select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return
            
            record.status = "running"
            await session.commit()
        
        klines = await data_source_manager.get_kline(code, start_date, end_date, "qfq")
        
        if not klines:
            async with get_session() as session:
                result = await session.execute(
                    select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    record.status = "failed"
                    await session.commit()
            return
        
        import pandas as pd
        df = pd.DataFrame([{
            "date": k.date,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "code": code
        } for k in klines])
        
        engine = BacktestEngine(
            initial_capital=initial_capital,
            commission_rate=0.0003,
            slippage=0.001
        )
        
        result = engine.run(
            df=df,
            strategy_type=strategy_type,
            strategy_params=strategy_params,
            position_size=0.95,
            max_positions=1
        )
        
        async with get_session() as session:
            result_record = await session.execute(
                select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
            )
            record = result_record.scalar_one_or_none()
            
            if record:
                record.final_capital = result.final_capital
                record.total_return = result.total_return
                record.annual_return = result.annual_return
                record.max_drawdown = result.max_drawdown
                record.sharpe_ratio = result.sharpe_ratio
                record.sortino_ratio = result.sortino_ratio
                record.calmar_ratio = result.calmar_ratio
                record.win_rate = result.win_rate
                record.max_consecutive_losses = result.max_consecutive_losses
                record.status = "completed"
                await session.commit()
            
            for trade in result.trades:
                trade_record = TradeRecord(
                    backtest_id=backtest_id,
                    trade_type=trade.trade_type,
                    code=trade.code,
                    price=trade.price,
                    quantity=trade.quantity,
                    amount=trade.amount,
                    commission=trade.commission,
                    trade_date=trade.date
                )
                session.add(trade_record)
            
            await session.commit()
        
        logger.info(f"回测 {backtest_id} 完成，总收益: {result.total_return:.2f}%")
        
    except Exception as e:
        logger.error(f"回测 {backtest_id} 失败: {e}")
        async with get_session() as session:
            result = await session.execute(
                select(BacktestRecord).where(BacktestRecord.backtest_id == backtest_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.status = "failed"
                await session.commit()


@router.post("/run", response_model=ResponseModel[dict])
async def run_backtest(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    backtest_config: BacktestConfig = Body(...),
):
    try:
        strategy_type = backtest_config.strategy_type
        strategy_params = backtest_config.strategy_params.model_dump()
        code = backtest_config.code
        start_date = backtest_config.start_date
        end_date = backtest_config.end_date
        initial_capital = backtest_config.initial_capital
        
        backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
        
        async with get_session() as session:
            record = BacktestRecord(
                backtest_id=backtest_id,
                strategy_id=backtest_config.strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                status="pending"
            )
            session.add(record)
            await session.commit()
        
        background_tasks.add_task(
            run_backtest_task,
            backtest_id,
            code,
            start_date,
            end_date,
            initial_capital,
            strategy_type,
            strategy_params
        )
        
        logger.info(f"创建回测任务：{backtest_id}, 股票：{code}, 策略：{strategy_type}")
        
        return ResponseModel(data={
            "backtest_id": backtest_id,
            "status": "pending",
            "message": "回测任务已创建"
        })
    
    except Exception as e:
        logger.error(f"创建回测任务失败: {e}")
        return ResponseModel(success=False, code="INTERNAL_ERROR", message=f"创建回测任务失败: {str(e)}")


@router.get("/result/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_result(backtest_id: str, current_user: CurrentUser):
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
            "total_return": record.total_return,
            "annual_return": record.annual_return,
            "max_drawdown": record.max_drawdown,
            "sharpe_ratio": record.sharpe_ratio,
            "sortino_ratio": getattr(record, 'sortino_ratio', 0),
            "calmar_ratio": getattr(record, 'calmar_ratio', 0),
            "win_rate": getattr(record, 'win_rate', 0),
            "max_consecutive_losses": getattr(record, 'max_consecutive_losses', 0),
            "status": record.status,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })


@router.get("/performance/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_performance(backtest_id: str, current_user: CurrentUser):
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


@router.get("/trades/{backtest_id}", response_model=PagedResponseModel[dict])
async def get_backtest_trades(
    backtest_id: str,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        count_result = await session.execute(
            select(func.count()).where(TradeRecord.backtest_id == backtest_id)
        )
        total = count_result.scalar() or 0
        
        offset = (page - 1) * page_size
        result = await session.execute(
            select(TradeRecord)
            .where(TradeRecord.backtest_id == backtest_id)
            .order_by(TradeRecord.trade_date)
            .offset(offset)
            .limit(page_size)
        )
        trades = result.scalars().all()
        
        return PagedResponseModel(
            data=[{
                "id": t.id,
                "trade_type": t.trade_type,
                "code": t.code,
                "price": t.price,
                "quantity": t.quantity,
                "amount": t.amount,
                "commission": t.commission,
                "trade_date": t.trade_date
            } for t in trades],
            page_info=PageInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size
            )
        )


@router.get("/history", response_model=ResponseModel[list])
async def get_backtest_history(current_user: CurrentUser, limit: int = Query(20)):
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
