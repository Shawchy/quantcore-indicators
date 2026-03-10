from fastapi import APIRouter, Query, Body, BackgroundTasks, Depends
from app.models.schemas import ResponseModel, PagedResponseModel, PageInfo
from app.api.deps import CurrentUser
from typing import Optional
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
    backtest_config: dict = Body(...),
    current_user: CurrentUser = Depends
):
    backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
    
    strategy_type = backtest_config.get("strategy_type", "ma_cross")
    strategy_params = backtest_config.get("strategy_params", {
        "short_period": 5,
        "long_period": 20
    })
    code = backtest_config.get("code", "000001")
    start_date = backtest_config.get("start_date", "")
    end_date = backtest_config.get("end_date", "")
    initial_capital = backtest_config.get("initial_capital", settings.BACKTEST_INITIAL_CAPITAL)
    
    async with get_session() as session:
        record = BacktestRecord(
            backtest_id=backtest_id,
            strategy_id=backtest_config.get("strategy_id", ""),
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
    
    return ResponseModel(data={
        "backtest_id": backtest_id,
        "status": "pending",
        "message": "回测任务已创建"
    })


@router.get("/result/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_result(backtest_id: str, current_user: CurrentUser = Depends):
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
            "status": record.status,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })


@router.get("/performance/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_performance(backtest_id: str, current_user: CurrentUser = Depends):
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
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends
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
async def get_backtest_history(limit: int = Query(20), current_user: CurrentUser = Depends):
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
