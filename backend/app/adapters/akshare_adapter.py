            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取沪深京 A 股实时行情失败：{e}")
            return []
    
    # ========== 创业板实时行情 ==========
    
    async def get_stock_cy_a_spot(self) -> List[StockZhASpot]:
        """获取创业板实时行情数据（东方财富）
        
        Returns:
            StockZhASpot 列表，包含所有创业板股票的实时行情数据（约 1400 只股票，23 个字段）
        """
        try:
            # 缓存检查
            cache_key = "stock_cy_a_spot"
            if self._is_cache_valid(cache_key, ttl=180):  # 3 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_cy_a_spot_em()
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockZhASpot(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    open=float(row.get('今开', 0)) if not pd.isna(row.get('今开')) else None,
                    prev_close=float(row.get('昨收', 0)) if not pd.isna(row.get('昨收')) else None,
                    volume_ratio=float(row.get('量比', 0)) if not pd.isna(row.get('量比')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                    pe_ratio_dynamic=float(row.get('市盈率 - 动态', 0)) if not pd.isna(row.get('市盈率 - 动态')) else None,
                    pb_ratio=float(row.get('市净率', 0)) if not pd.isna(row.get('市净率')) else None,
                    total_market_cap=float(row.get('总市值', 0)) if not pd.isna(row.get('总市值')) else None,
                    float_market_cap=float(row.get('流通市值', 0)) if not pd.isna(row.get('流通市值')) else None,
                    speed=float(row.get('涨速', 0)) if not pd.isna(row.get('涨速')) else None,
                    change_5min=float(row.get('5 分钟涨跌', 0)) if not pd.isna(row.get('5 分钟涨跌')) else None,
                    change_60d=float(row.get('60 日涨跌幅', 0)) if not pd.isna(row.get('60 日涨跌幅')) else None,
                    change_ytd=float(row.get('年初至今涨跌幅', 0)) if not pd.isna(row.get('年初至今涨跌幅')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取创业板实时行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取创业板实时行情失败：{e}")
            return []
    
    # ========== 科创板实时行情 ==========
    
    async def get_stock_kc_a_spot(self) -> List[StockZhASpot]:
        """获取科创板实时行情数据（东方财富）
        
        Returns:
            StockZhASpot 列表，包含所有科创板股票的实时行情数据（约 600 只股票，23 个字段）
        """
        try:
            # 缓存检查
            cache_key = "stock_kc_a_spot"
            if self._is_cache_valid(cache_key, ttl=180):  # 3 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_kc_a_spot_em()
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockZhASpot(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    open=float(row.get('今开', 0)) if not pd.isna(row.get('今开')) else None,
                    prev_close=float(row.get('昨收', 0)) if not pd.isna(row.get('昨收')) else None,
                    volume_ratio=float(row.get('量比', 0)) if not pd.isna(row.get('量比')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                    pe_ratio_dynamic=float(row.get('市盈率 - 动态', 0)) if not pd.isna(row.get('市盈率 - 动态')) else None,
                    pb_ratio=float(row.get('市净率', 0)) if not pd.isna(row.get('市净率')) else None,
                    total_market_cap=float(row.get('总市值', 0)) if not pd.isna(row.get('总市值')) else None,
                    float_market_cap=float(row.get('流通市值', 0)) if not pd.isna(row.get('流通市值')) else None,
                    speed=float(row.get('涨速', 0)) if not pd.isna(row.get('涨速')) else None,
                    change_5min=float(row.get('5 分钟涨跌', 0)) if not pd.isna(row.get('5 分钟涨跌')) else None,
                    change_60d=float(row.get('60 日涨跌幅', 0)) if not pd.isna(row.get('60 日涨跌幅')) else None,
                    change_ytd=float(row.get('年初至今涨跌幅', 0)) if not pd.isna(row.get('年初至今涨跌幅')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取科创板实时行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取科创板实时行情失败：{e}")
            return []
    
    # ========== 新浪财经 - 沪深京 A 股实时行情 ==========
    
    async def get_stock_zh_a_spot_sina(self) -> List[StockZhASpotSina]:
        """获取新浪财经 - 沪深京 A 股实时行情数据
        
        Returns:
            StockZhASpotSina 列表，包含所有沪深京 A 股股票的实时行情数据（约 5300 只股票，14 个字段）
        """
        try:
            # 缓存检查
            cache_key = "stock_zh_a_spot_sina"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存（新浪接口需要更长间隔）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_a_spot()
            
            result = []
            for _, row in data.iterrows():
                item = StockZhASpotSina(
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    buy=float(row.get('买入', 0)) if not pd.isna(row.get('买入')) else None,
                    sell=float(row.get('卖出', 0)) if not pd.isna(row.get('卖出')) else None,
                    prev_close=float(row.get('昨收', 0)) if not pd.isna(row.get('昨收')) else None,
                    open=float(row.get('今开', 0)) if not pd.isna(row.get('今开')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    timestamp=str(row.get('时间戳', '')) if not pd.isna(row.get('时间戳')) else '',
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取新浪财经沪深京 A 股实时行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取新浪财经沪深京 A 股实时行情失败：{e}")
            return []
    
    # ========== 东方财富 - 历史行情数据 ==========
    
    async def get_stock_zh_a_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAHist]:
        """获取东方财富 - 沪深京 A 股历史行情数据
        
        Args:
            symbol: 股票代码（如 '000001'）
            period: 周期，choice of {'daily', 'weekly', 'monthly'}，默认 'daily'
            start_date: 开始日期（格式 'YYYYMMDD'），默认不指定（获取全部历史数据）
            end_date: 结束日期（格式 'YYYYMMDD'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
                   - '': 不复权
                   - 'qfq': 前复权
                   - 'hfq': 后复权（量化研究推荐）
        
        Returns:
            StockZhAHist 列表，包含指定股票的历史行情数据（12 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_a_hist_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存（历史数据变化少）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "19700101",
                end_date=end_date if end_date else "20991231",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 历史行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取历史行情失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 新浪财经 - 分时数据 ==========
    
    async def get_stock_zh_a_minute_sina(
        self,
        symbol: str,
        period: str = "1",
        adjust: str = ""
    ) -> List[StockZhAMinuteSina]:
        """获取新浪财经 - 沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码（如 'sh600751'）- 需要带市场前缀
            period: 周期，choice of {'1', '5', '15', '30', '60'}，默认 '1'
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
        
        Returns:
            StockZhAMinuteSina 列表，包含指定股票最近交易日的分时数据（7 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_a_minute_sina_{symbol}_{period}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_a_minute(symbol=symbol, period=period, adjust=adjust)
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAMinuteSina(
                    day=str(row.get('day', '')) if not pd.isna(row.get('day')) else '',
                    open=float(row.get('open', 0)) if not pd.isna(row.get('open')) else None,
                    high=float(row.get('high', 0)) if not pd.isna(row.get('high')) else None,
                    low=float(row.get('low', 0)) if not pd.isna(row.get('low')) else None,
                    close=float(row.get('close', 0)) if not pd.isna(row.get('close')) else None,
                    volume=float(row.get('volume', 0)) if not pd.isna(row.get('volume')) else None,
                    amount=float(row.get('amount', 0)) if not pd.isna(row.get('amount')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 新浪财经分时数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取新浪财经分时数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 分时数据 ==========
    
    async def get_stock_zh_a_hist_min_em(
        self,
        symbol: str,
        period: str = "5",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAMinuteEM]:
        """获取东方财富 - 沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码（如 '000001'）- 不带市场前缀
            period: 周期，choice of {'1', '5', '15', '30', '60'}，默认 '5'
                   注意：1 分钟数据只返回近 5 个交易日数据且不复权
            start_date: 开始日期时间（格式 'YYYY-MM-DD HH:MM:SS'），默认不指定
            end_date: 结束日期时间（格式 'YYYY-MM-DD HH:MM:SS'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
                   注意：1 分钟数据不复权
        
        Returns:
            StockZhAMinuteEM 列表，包含指定股票的分时数据
            - 1 分钟：8 个字段（含均价）
            - 5/15/30/60 分钟：11 个字段（含涨跌幅、涨跌额、振幅、换手率）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_a_hist_min_em_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_a_hist_min_em(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "1979-09-01 09:32:00",
                end_date=end_date if end_date else "2222-01-01 09:32:00",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                # 1 分钟数据和其他数据的字段不同
                if period == "1":
                    item = StockZhAMinuteEM(
                        time=str(row.get('时间', '')) if not pd.isna(row.get('时间')) else '',
                        open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                        close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                        high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                        low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                        volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                        turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                        avg_price=float(row.get('均价', 0)) if not pd.isna(row.get('均价')) else None,
                    )
                else:
                    item = StockZhAMinuteEM(
                        time=str(row.get('时间', '')) if not pd.isna(row.get('时间')) else '',
                        open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                        close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                        high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                        low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                        volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                        turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                        change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                        change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                        amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                        turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                    )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富分时数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富分时数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 日内分时数据 ==========
    
    async def get_stock_intraday_em(self, symbol: str) -> List[StockIntradayEM]:
        """获取东方财富 - 日内分时数据（最近一个交易日，含盘前）
        
        Args:
            symbol: 股票代码（如 '000001'）- 不带市场前缀
        
        Returns:
            StockIntradayEM 列表，包含最近一个交易日的分时数据（4 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_intraday_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_intraday_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockIntradayEM(
                    time=str(row.get('时间', '')) if not pd.isna(row.get('时间')) else '',
                    price=float(row.get('成交价', 0)) if not pd.isna(row.get('成交价')) else None,
                    volume=int(row.get('手数', 0)) if not pd.isna(row.get('手数')) else 0,
                    type=str(row.get('买卖盘性质', '')) if not pd.isna(row.get('买卖盘性质')) else '',
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富日内分时数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富日内分时数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 新浪财经 - 日内分时数据 ==========
    
    async def get_stock_intraday_sina(
        self,
        symbol: str,
        date: str
    ) -> List[StockIntradaySina]:
        """获取新浪财经 - 日内分时数据（指定交易日，大单数据）
        
        Args:
            symbol: 股票代码（如 'sz000001'）- 需要带市场前缀
            date: 交易日（格式 'YYYYMMDD'）
        
        Returns:
            StockIntradaySina 列表，包含指定交易日的大单分时数据（7 个字段）
            注意：仅返回成交量≥400 手的大单数据
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_intraday_sina_{symbol}_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存（历史数据）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_intraday_sina(symbol=symbol, date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockIntradaySina(
                    symbol=str(row.get('symbol', '')) if not pd.isna(row.get('symbol')) else '',
                    name=str(row.get('name', '')) if not pd.isna(row.get('name')) else '',
                    ticktime=str(row.get('ticktime', '')) if not pd.isna(row.get('ticktime')) else '',
                    price=float(row.get('price', 0)) if not pd.isna(row.get('price')) else None,
                    volume=int(row.get('volume', 0)) if not pd.isna(row.get('volume')) else 0,
                    prev_price=float(row.get('prev_price', 0)) if not pd.isna(row.get('prev_price')) else None,
                    kind=str(row.get('kind', '')) if not pd.isna(row.get('kind')) else '',
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 新浪财经日内分时数据（{date}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取新浪财经日内分时数据失败：symbol={symbol}, date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 盘前分钟数据 ==========
    
    async def get_stock_zh_a_hist_pre_min_em(
        self,
        symbol: str,
        start_time: str = "09:00:00",
        end_time: str = "15:40:00"
    ) -> List[StockZhAHistPreMinEM]:
        """获取东方财富 - 盘前分钟数据（含盘前和盘中）
        
        Args:
            symbol: 股票代码（如 '000001'）- 不带市场前缀
            start_time: 开始时间（格式 'HH:MM:SS'），默认 '09:00:00'
            end_time: 结束时间（格式 'HH:MM:SS'），默认 '15:40:00'
        
        Returns:
            StockZhAHistPreMinEM 列表，包含最近一个交易日的分钟数据（8 个字段）
            包含盘前数据（09:15-09:25）和盘中数据（09:30-15:00）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_a_hist_pre_min_em_{symbol}_{start_time}_{end_time}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHistPreMinEM(
                    time=str(row.get('时间', '')) if not pd.isna(row.get('时间')) else '',
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富盘前分钟数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富盘前分钟数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 成长性比较（同行比较） ==========
    
    async def get_stock_zh_growth_comparison_em(self, symbol: str) -> List[StockZhGrowthComparisonEM]:
        """获取东方财富 - 成长性比较数据（同行比较）
        
        Args:
            symbol: 股票代码（如 'SZ000895'）- 需要带市场前缀
        
        Returns:
            StockZhGrowthComparisonEM 列表，包含同行业公司的成长性比较数据（21 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_growth_comparison_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_growth_comparison_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockZhGrowthComparisonEM(
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('简称', '')) if not pd.isna(row.get('简称')) else '',
                    eps_growth_3y=float(row.get('基本每股收益增长率 -3 年复合', 0)) if not pd.isna(row.get('基本每股收益增长率 -3 年复合')) else None,
                    eps_growth_24a=float(row.get('基本每股收益增长率 -24A', 0)) if not pd.isna(row.get('基本每股收益增长率 -24A')) else None,
                    eps_growth_ttm=float(row.get('基本每股收益增长率 -TTM', 0)) if not pd.isna(row.get('基本每股收益增长率 -TTM')) else None,
                    eps_growth_25e=float(row.get('基本每股收益增长率 -25E', 0)) if not pd.isna(row.get('基本每股收益增长率 -25E')) else None,
                    eps_growth_26e=float(row.get('基本每股收益增长率 -26E', 0)) if not pd.isna(row.get('基本每股收益增长率 -26E')) else None,
                    eps_growth_27e=float(row.get('基本每股收益增长率 -27E', 0)) if not pd.isna(row.get('基本每股收益增长率 -27E')) else None,
                    revenue_growth_3y=float(row.get('营业收入增长率 -3 年复合', 0)) if not pd.isna(row.get('营业收入增长率 -3 年复合')) else None,
                    revenue_growth_24a=float(row.get('营业收入增长率 -24A', 0)) if not pd.isna(row.get('营业收入增长率 -24A')) else None,
                    revenue_growth_ttm=float(row.get('营业收入增长率 -TTM', 0)) if not pd.isna(row.get('营业收入增长率 -TTM')) else None,
                    revenue_growth_25e=float(row.get('营业收入增长率 -25E', 0)) if not pd.isna(row.get('营业收入增长率 -25E')) else None,
                    revenue_growth_26e=float(row.get('营业收入增长率 -26E', 0)) if not pd.isna(row.get('营业收入增长率 -26E')) else None,
                    revenue_growth_27e=float(row.get('营业收入增长率 -27E', 0)) if not pd.isna(row.get('营业收入增长率 -27E')) else None,
                    net_profit_growth_3y=float(row.get('净利润增长率 -3 年复合', 0)) if not pd.isna(row.get('净利润增长率 -3 年复合')) else None,
                    net_profit_growth_24a=float(row.get('净利润增长率 -24A', 0)) if not pd.isna(row.get('净利润增长率 -24A')) else None,
                    net_profit_growth_ttm=float(row.get('净利润增长率 -TTM', 0)) if not pd.isna(row.get('净利润增长率 -TTM')) else None,
                    net_profit_growth_25e=float(row.get('净利润增长率 -25E', 0)) if not pd.isna(row.get('净利润增长率 -25E')) else None,
                    net_profit_growth_26e=float(row.get('净利润增长率 -26E', 0)) if not pd.isna(row.get('净利润增长率 -26E')) else None,
                    net_profit_growth_27e=float(row.get('净利润增长率 -27E', 0)) if not pd.isna(row.get('净利润增长率 -27E')) else None,
                    eps_growth_3y_rank=float(row.get('基本每股收益增长率 -3 年复合排名', 0)) if not pd.isna(row.get('基本每股收益增长率 -3 年复合排名')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富成长性比较数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富成长性比较数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 估值比较（同行比较） ==========
    
    async def get_stock_zh_valuation_comparison_em(self, symbol: str) -> List[StockZhValuationComparisonEM]:
        """获取东方财富 - 估值比较数据（同行比较）
        
        Args:
            symbol: 股票代码（如 'SZ000895'）- 需要带市场前缀
        
        Returns:
            StockZhValuationComparisonEM 列表，包含同行业公司的估值比较数据（20 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_valuation_comparison_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_valuation_comparison_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockZhValuationComparisonEM(
                    rank=float(row.get('排名', 0)) if not pd.isna(row.get('排名')) else None,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('简称', '')) if not pd.isna(row.get('简称')) else '',
                    peg=float(row.get('PEG', 0)) if not pd.isna(row.get('PEG')) else None,
                    pe_24a=float(row.get('市盈率 -24A', 0)) if not pd.isna(row.get('市盈率 -24A')) else None,
                    pe_ttm=float(row.get('市盈率 -TTM', 0)) if not pd.isna(row.get('市盈率 -TTM')) else None,
                    pe_25e=float(row.get('市盈率 -25E', 0)) if not pd.isna(row.get('市盈率 -25E')) else None,
                    pe_26e=float(row.get('市盈率 -26E', 0)) if not pd.isna(row.get('市盈率 -26E')) else None,
                    pe_27e=float(row.get('市盈率 -27E', 0)) if not pd.isna(row.get('市盈率 -27E')) else None,
                    ps_24a=float(row.get('市销率 -24A', 0)) if not pd.isna(row.get('市销率 -24A')) else None,
                    ps_ttm=float(row.get('市销率 -TTM', 0)) if not pd.isna(row.get('市销率 -TTM')) else None,
                    ps_25e=float(row.get('市销率 -25E', 0)) if not pd.isna(row.get('市销率 -25E')) else None,
                    ps_26e=float(row.get('市销率 -26E', 0)) if not pd.isna(row.get('市销率 -26E')) else None,
                    ps_27e=float(row.get('市销率 -27E', 0)) if not pd.isna(row.get('市销率 -27E')) else None,
                    pb_24a=float(row.get('市净率 -24A', 0)) if not pd.isna(row.get('市净率 -24A')) else None,
                    pb_mrq=float(row.get('市净率 -MRQ', 0)) if not pd.isna(row.get('市净率 -MRQ')) else None,
                    pcf1_24a=float(row.get('市现率 1-24A', 0)) if not pd.isna(row.get('市现率 1-24A')) else None,
                    pcf1_ttm=float(row.get('市现率 1-TTM', 0)) if not pd.isna(row.get('市现率 1-TTM')) else None,
                    pcf2_24a=float(row.get('市现率 2-24A', 0)) if not pd.isna(row.get('市现率 2-24A')) else None,
                    pcf2_ttm=float(row.get('市现率 2-TTM', 0)) if not pd.isna(row.get('市现率 2-TTM')) else None,
                    ev_ebitda_24a=float(row.get('EV/EBITDA-24A', 0)) if not pd.isna(row.get('EV/EBITDA-24A')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富估值比较数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富估值比较数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 杜邦分析比较（同行比较） ==========
    
    async def get_stock_zh_dupont_comparison_em(self, symbol: str) -> List[StockZhDupontComparisonEM]:
        """获取东方财富 - 杜邦分析比较数据（同行比较）
        
        Args:
            symbol: 股票代码（如 'SZ000895'）- 需要带市场前缀
        
        Returns:
            StockZhDupontComparisonEM 列表，包含同行业公司的杜邦分析比较数据（19 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_dupont_comparison_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_dupont_comparison_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockZhDupontComparisonEM(
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('简称', '')) if not pd.isna(row.get('简称')) else '',
                    roe_3y_avg=float(row.get('ROE-3 年平均', 0)) if not pd.isna(row.get('ROE-3 年平均')) else None,
                    roe_22a=float(row.get('ROE-22A', 0)) if not pd.isna(row.get('ROE-22A')) else None,
                    roe_23a=float(row.get('ROE-23A', 0)) if not pd.isna(row.get('ROE-23A')) else None,
                    roe_24a=float(row.get('ROE-24A', 0)) if not pd.isna(row.get('ROE-24A')) else None,
                    net_profit_margin_3y_avg=float(row.get('净利率 -3 年平均', 0)) if not pd.isna(row.get('净利率 -3 年平均')) else None,
                    net_profit_margin_22a=float(row.get('净利率 -22A', 0)) if not pd.isna(row.get('净利率 -22A')) else None,
                    net_profit_margin_23a=float(row.get('净利率 -23A', 0)) if not pd.isna(row.get('净利率 -23A')) else None,
                    net_profit_margin_24a=float(row.get('净利率 -24A', 0)) if not pd.isna(row.get('净利率 -24A')) else None,
                    asset_turnover_3y_avg=float(row.get('总资产周转率 -3 年平均', 0)) if not pd.isna(row.get('总资产周转率 -3 年平均')) else None,
                    asset_turnover_22a=float(row.get('总资产周转率 -22A', 0)) if not pd.isna(row.get('总资产周转率 -22A')) else None,
                    asset_turnover_23a=float(row.get('总资产周转率 -23A', 0)) if not pd.isna(row.get('总资产周转率 -23A')) else None,
                    asset_turnover_24a=float(row.get('总资产周转率 -24A', 0)) if not pd.isna(row.get('总资产周转率 -24A')) else None,
                    equity_multiplier_3y_avg=float(row.get('权益乘数 -3 年平均', 0)) if not pd.isna(row.get('权益乘数 -3 年平均')) else None,
                    equity_multiplier_22a=float(row.get('权益乘数 -22A', 0)) if not pd.isna(row.get('权益乘数 -22A')) else None,
                    equity_multiplier_23a=float(row.get('权益乘数 -23A', 0)) if not pd.isna(row.get('权益乘数 -23A')) else None,
                    equity_multiplier_24a=float(row.get('权益乘数 -24A', 0)) if not pd.isna(row.get('权益乘数 -24A')) else None,
                    roe_3y_avg_rank=float(row.get('ROE-3 年平均排名', 0)) if not pd.isna(row.get('ROE-3 年平均排名')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富杜邦分析比较数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富杜邦分析比较数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 公司规模比较（同行比较） ==========
    
    async def get_stock_zh_scale_comparison_em(self, symbol: str) -> List[StockZhScaleComparisonEM]:
        """获取东方财富 - 公司规模比较数据（同行比较）
        
        Args:
            symbol: 股票代码（如 'SZ000895'）- 需要带市场前缀
        
        Returns:
            StockZhScaleComparisonEM 列表，包含同行业公司的规模比较数据（10 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_zh_scale_comparison_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_zh_scale_comparison_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockZhScaleComparisonEM(
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('简称', '')) if not pd.isna(row.get('简称')) else '',
                    total_market_cap=float(row.get('总市值', 0)) if not pd.isna(row.get('总市值')) else None,
                    total_market_cap_rank=int(row.get('总市值排名', 0)) if not pd.isna(row.get('总市值排名')) else None,
                    float_market_cap=float(row.get('流通市值', 0)) if not pd.isna(row.get('流通市值')) else None,
                    float_market_cap_rank=int(row.get('流通市值排名', 0)) if not pd.isna(row.get('流通市值排名')) else None,
                    revenue=float(row.get('营业收入', 0)) if not pd.isna(row.get('营业收入')) else None,
                    revenue_rank=int(row.get('营业收入排名', 0)) if not pd.isna(row.get('营业收入排名')) else None,
                    net_profit=float(row.get('净利润', 0)) if not pd.isna(row.get('净利润')) else None,
                    net_profit_rank=int(row.get('净利润排名', 0)) if not pd.isna(row.get('净利润排名')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 东方财富公司规模比较数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取东方财富公司规模比较数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 美股历史行情 ==========
    
    async def get_stock_us_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAHist]:
        """获取东方财富 - 美股历史行情数据
        
        Args:
            symbol: 美股代码（如 '106.TTE'）
            period: 周期，choice of {'daily', 'weekly', 'monthly'}，默认 'daily'
            start_date: 开始日期（格式 'YYYYMMDD'），默认不指定
            end_date: 结束日期（格式 'YYYYMMDD'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
        
        Returns:
            StockZhAHist 列表，包含指定美股的历史行情数据（11 个字段）
            注意：成交量单位为股，货币单位为美元
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_us_hist_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_us_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "19700101",
                end_date=end_date if end_date else "20991231",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 美股历史行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取美股历史行情失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 港股历史行情 ==========
    
    async def get_stock_hk_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAHist]:
        """获取东方财富 - 港股历史行情数据
        
        Args:
            symbol: 港股代码（如 '00593'）
            period: 周期，choice of {'daily', 'weekly', 'monthly'}，默认 'daily'
            start_date: 开始日期（格式 'YYYYMMDD'），默认不指定
            end_date: 结束日期（格式 'YYYYMMDD'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
        
        Returns:
            StockZhAHist 列表，包含指定港股的历史行情数据（11 个字段）
            注意：成交量单位为股，货币单位为港元
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_hk_hist_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_hk_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "19700101",
                end_date=end_date if end_date else "20991231",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 港股历史行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取港股历史行情失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 大盘资金流 ==========
    
    async def get_stock_market_fund_flow(self) -> List[StockMarketFundFlow]:
        """获取东方财富 - 大盘资金流向历史数据
        
        Returns:
            StockMarketFundFlow 列表，包含大盘资金流向历史数据（约 121 条，15 个字段）
        """
        try:
            # 缓存检查
            cache_key = "stock_market_fund_flow"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_market_fund_flow()
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockMarketFundFlow(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    shanghai_close=float(row.get('上证 - 收盘价', 0)) if not pd.isna(row.get('上证 - 收盘价')) else None,
                    shanghai_change_pct=float(row.get('上证 - 涨跌幅', 0)) if not pd.isna(row.get('上证 - 涨跌幅')) else None,
                    shenzhen_close=float(row.get('深证 - 收盘价', 0)) if not pd.isna(row.get('深证 - 收盘价')) else None,
                    shenzhen_change_pct=float(row.get('深证 - 涨跌幅', 0)) if not pd.isna(row.get('深证 - 涨跌幅')) else None,
                    main_net_inflow=float(row.get('主力净流入 - 净额', 0)) if not pd.isna(row.get('主力净流入 - 净额')) else None,
                    main_net_inflow_ratio=float(row.get('主力净流入 - 净占比', 0)) if not pd.isna(row.get('主力净流入 - 净占比')) else None,
                    super_order_net_inflow=float(row.get('超大单净流入 - 净额', 0)) if not pd.isna(row.get('超大单净流入 - 净额')) else None,
                    super_order_net_inflow_ratio=float(row.get('超大单净流入 - 净占比', 0)) if not pd.isna(row.get('超大单净流入 - 净占比')) else None,
                    big_order_net_inflow=float(row.get('大单净流入 - 净额', 0)) if not pd.isna(row.get('大单净流入 - 净额')) else None,
                    big_order_net_inflow_ratio=float(row.get('大单净流入 - 净占比', 0)) if not pd.isna(row.get('大单净流入 - 净占比')) else None,
                    medium_order_net_inflow=float(row.get('中单净流入 - 净额', 0)) if not pd.isna(row.get('中单净流入 - 净额')) else None,
                    medium_order_net_inflow_ratio=float(row.get('中单净流入 - 净占比', 0)) if not pd.isna(row.get('中单净流入 - 净占比')) else None,
                    small_order_net_inflow=float(row.get('小单净流入 - 净额', 0)) if not pd.isna(row.get('小单净流入 - 净额')) else None,
                    small_order_net_inflow_ratio=float(row.get('小单净流入 - 净占比', 0)) if not pd.isna(row.get('小单净流入 - 净占比')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取大盘资金流，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取大盘资金流失败：{e}")
            return []
    
    # ========== 东方财富 - 板块资金流排名 ==========
    
    async def get_stock_sector_fund_flow_rank(
        self,
        indicator: str = "今日",
        sector_type: str = "行业资金流"
    ) -> List[StockSectorFundFlowRank]:
        """获取东方财富 - 板块资金流排名数据
        
        Args:
            indicator: 时间周期，choice of {"今日", "5 日", "10 日"}，默认 "今日"
            sector_type: 板块类型，choice of {"行业资金流", "概念资金流", "地域资金流"}，默认 "行业资金流"
        
        Returns:
            StockSectorFundFlowRank 列表，包含板块资金流排名数据（14 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_sector_fund_flow_rank_{indicator}_{sector_type}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_sector_fund_flow_rank(
                indicator=indicator,
                sector_type=sector_type
            )
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                # 根据 indicator 确定字段映射
                if indicator == "今日":
                    change_pct = float(row.get('今日涨跌幅', 0)) if not pd.isna(row.get('今日涨跌幅')) else None
                    main_net_inflow = float(row.get('今日主力净流入 - 净额', 0)) if not pd.isna(row.get('今日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('今日主力净流入 - 净占比', 0)) if not pd.isna(row.get('今日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('今日超大单净流入 - 净额', 0)) if not pd.isna(row.get('今日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('今日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('今日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('今日大单净流入 - 净额', 0)) if not pd.isna(row.get('今日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('今日大单净流入 - 净占比', 0)) if not pd.isna(row.get('今日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('今日中单净流入 - 净额', 0)) if not pd.isna(row.get('今日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('今日中单净流入 - 净占比', 0)) if not pd.isna(row.get('今日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('今日小单净流入 - 净额', 0)) if not pd.isna(row.get('今日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('今日小单净流入 - 净占比', 0)) if not pd.isna(row.get('今日小单净流入 - 净占比')) else None
                    main_net_inflow_max_stock = str(row.get('今日主力净流入最大股', '')) if not pd.isna(row.get('今日主力净流入最大股')) else None
                elif indicator == "5 日":
                    change_pct = float(row.get('5 日涨跌幅', 0)) if not pd.isna(row.get('5 日涨跌幅')) else None
                    main_net_inflow = float(row.get('5 日主力净流入 - 净额', 0)) if not pd.isna(row.get('5 日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('5 日主力净流入 - 净占比', 0)) if not pd.isna(row.get('5 日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('5 日超大单净流入 - 净额', 0)) if not pd.isna(row.get('5 日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('5 日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('5 日大单净流入 - 净额', 0)) if not pd.isna(row.get('5 日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('5 日大单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('5 日中单净流入 - 净额', 0)) if not pd.isna(row.get('5 日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('5 日中单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('5 日小单净流入 - 净额', 0)) if not pd.isna(row.get('5 日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('5 日小单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日小单净流入 - 净占比')) else None
                    main_net_inflow_max_stock = str(row.get('5 日主力净流入最大股', '')) if not pd.isna(row.get('5 日主力净流入最大股')) else None
                else:  # 10 日
                    change_pct = float(row.get('10 日涨跌幅', 0)) if not pd.isna(row.get('10 日涨跌幅')) else None
                    main_net_inflow = float(row.get('10 日主力净流入 - 净额', 0)) if not pd.isna(row.get('10 日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('10 日主力净流入 - 净占比', 0)) if not pd.isna(row.get('10 日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('10 日超大单净流入 - 净额', 0)) if not pd.isna(row.get('10 日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('10 日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('10 日大单净流入 - 净额', 0)) if not pd.isna(row.get('10 日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('10 日大单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('10 日中单净流入 - 净额', 0)) if not pd.isna(row.get('10 日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('10 日中单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('10 日小单净流入 - 净额', 0)) if not pd.isna(row.get('10 日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('10 日小单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日小单净流入 - 净占比')) else None
                    main_net_inflow_max_stock = str(row.get('10 日主力净流入最大股', '')) if not pd.isna(row.get('10 日主力净流入最大股')) else None
                
                item = StockSectorFundFlowRank(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    change_pct=change_pct,
                    main_net_inflow=main_net_inflow,
                    main_net_inflow_ratio=main_net_inflow_ratio,
                    super_order_net_inflow=super_order_net_inflow,
                    super_order_net_inflow_ratio=super_order_net_inflow_ratio,
                    big_order_net_inflow=big_order_net_inflow,
                    big_order_net_inflow_ratio=big_order_net_inflow_ratio,
                    medium_order_net_inflow=medium_order_net_inflow,
                    medium_order_net_inflow_ratio=medium_order_net_inflow_ratio,
                    small_order_net_inflow=small_order_net_inflow,
                    small_order_net_inflow_ratio=small_order_net_inflow_ratio,
                    main_net_inflow_max_stock=main_net_inflow_max_stock,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {sector_type}-{indicator} 板块资金流排名，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取板块资金流排名失败：indicator={indicator}, sector_type={sector_type}, error={e}")
            return []
    
    # ========== 东方财富 - 主力净流入排名 ==========
    
    async def get_stock_main_fund_flow(
        self,
        symbol: str = "全部股票"
    ) -> List[StockMainFundFlow]:
        """获取东方财富 - 主力净流入排名数据
        
        Args:
            symbol: 市场类型，choice of {"全部股票", "沪深 A 股", "沪市 A 股", "科创板", "深市 A 股", "创业板", "沪市 B 股", "深市 B 股"}，默认 "全部股票"
        
        Returns:
            StockMainFundFlow 列表，包含主力净流入排名数据（14 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_main_fund_flow_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_main_fund_flow(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockMainFundFlow(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    today_main_ratio=float(row.get('今日排行榜 - 主力净占比', 0)) if not pd.isna(row.get('今日排行榜 - 主力净占比')) else None,
                    today_rank=int(row.get('今日排行榜 - 今日排名', 0)) if not pd.isna(row.get('今日排行榜 - 今日排名')) else None,
                    today_change_pct=float(row.get('今日排行榜 - 今日涨跌', 0)) if not pd.isna(row.get('今日排行榜 - 今日涨跌')) else None,
                    day5_main_ratio=float(row.get('5 日排行榜 - 主力净占比', 0)) if not pd.isna(row.get('5 日排行榜 - 主力净占比')) else None,
                    day5_rank=int(row.get('5 日排行榜 -5 日排名', 0)) if not pd.isna(row.get('5 日排行榜 -5 日排名')) else None,
                    day5_change_pct=float(row.get('5 日排行榜 -5 日涨跌', 0)) if not pd.isna(row.get('5 日排行榜 -5 日涨跌')) else None,
                    day10_main_ratio=float(row.get('10 日排行榜 - 主力净占比', 0)) if not pd.isna(row.get('10 日排行榜 - 主力净占比')) else None,
                    day10_rank=int(row.get('10 日排行榜 -10 日排名', 0)) if not pd.isna(row.get('10 日排行榜 -10 日排名')) else None,
                    day10_change_pct=float(row.get('10 日排行榜 -10 日涨跌', 0)) if not pd.isna(row.get('10 日排行榜 -10 日涨跌')) else None,
                    sector=str(row.get('所属板块', '')) if not pd.isna(row.get('所属板块')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 主力净流入排名，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取主力净流入排名失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 行业个股资金流 ==========
    
    async def get_stock_sector_fund_flow_summary(
        self,
        symbol: str,
        indicator: str = "今日"
    ) -> List[StockSectorFundFlowSummary]:
        """获取东方财富 - 行业个股资金流数据
        
        Args:
            symbol: 行业名称（如 "电源设备"）
            indicator: 时间周期，choice of {"今日", "5 日", "10 日"}，默认 "今日"
        
        Returns:
            StockSectorFundFlowSummary 列表，包含该行业所有个股的资金流数据（15 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_sector_fund_flow_summary_{symbol}_{indicator}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_sector_fund_flow_summary(
                symbol=symbol,
                indicator=indicator
            )
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                # 根据 indicator 确定字段映射
                if indicator == "今日":
                    change_pct = float(row.get('今日涨跌幅', 0)) if not pd.isna(row.get('今日涨跌幅')) else None
                    main_net_inflow = float(row.get('今日主力净流入 - 净额', 0)) if not pd.isna(row.get('今日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('今日主力净流入 - 净占比', 0)) if not pd.isna(row.get('今日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('今日超大单净流入 - 净额', 0)) if not pd.isna(row.get('今日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('今日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('今日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('今日大单净流入 - 净额', 0)) if not pd.isna(row.get('今日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('今日大单净流入 - 净占比', 0)) if not pd.isna(row.get('今日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('今日中单净流入 - 净额', 0)) if not pd.isna(row.get('今日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('今日中单净流入 - 净占比', 0)) if not pd.isna(row.get('今日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('今日小单净流入 - 净额', 0)) if not pd.isna(row.get('今日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('今日小单净流入 - 净占比', 0)) if not pd.isna(row.get('今日小单净流入 - 净占比')) else None
                elif indicator == "5 日":
                    change_pct = float(row.get('5 日涨跌幅', 0)) if not pd.isna(row.get('5 日涨跌幅')) else None
                    main_net_inflow = float(row.get('5 日主力净流入 - 净额', 0)) if not pd.isna(row.get('5 日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('5 日主力净流入 - 净占比', 0)) if not pd.isna(row.get('5 日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('5 日超大单净流入 - 净额', 0)) if not pd.isna(row.get('5 日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('5 日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('5 日大单净流入 - 净额', 0)) if not pd.isna(row.get('5 日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('5 日大单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('5 日中单净流入 - 净额', 0)) if not pd.isna(row.get('5 日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('5 日中单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('5 日小单净流入 - 净额', 0)) if not pd.isna(row.get('5 日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('5 日小单净流入 - 净占比', 0)) if not pd.isna(row.get('5 日小单净流入 - 净占比')) else None
                else:  # 10 日
                    change_pct = float(row.get('10 日涨跌幅', 0)) if not pd.isna(row.get('10 日涨跌幅')) else None
                    main_net_inflow = float(row.get('10 日主力净流入 - 净额', 0)) if not pd.isna(row.get('10 日主力净流入 - 净额')) else None
                    main_net_inflow_ratio = float(row.get('10 日主力净流入 - 净占比', 0)) if not pd.isna(row.get('10 日主力净流入 - 净占比')) else None
                    super_order_net_inflow = float(row.get('10 日超大单净流入 - 净额', 0)) if not pd.isna(row.get('10 日超大单净流入 - 净额')) else None
                    super_order_net_inflow_ratio = float(row.get('10 日超大单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日超大单净流入 - 净占比')) else None
                    big_order_net_inflow = float(row.get('10 日大单净流入 - 净额', 0)) if not pd.isna(row.get('10 日大单净流入 - 净额')) else None
                    big_order_net_inflow_ratio = float(row.get('10 日大单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日大单净流入 - 净占比')) else None
                    medium_order_net_inflow = float(row.get('10 日中单净流入 - 净额', 0)) if not pd.isna(row.get('10 日中单净流入 - 净额')) else None
                    medium_order_net_inflow_ratio = float(row.get('10 日中单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日中单净流入 - 净占比')) else None
                    small_order_net_inflow = float(row.get('10 日小单净流入 - 净额', 0)) if not pd.isna(row.get('10 日小单净流入 - 净额')) else None
                    small_order_net_inflow_ratio = float(row.get('10 日小单净流入 - 净占比', 0)) if not pd.isna(row.get('10 日小单净流入 - 净占比')) else None
                
                item = StockSectorFundFlowSummary(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=change_pct,
                    main_net_inflow=main_net_inflow,
                    main_net_inflow_ratio=main_net_inflow_ratio,
                    super_order_net_inflow=super_order_net_inflow,
                    super_order_net_inflow_ratio=super_order_net_inflow_ratio,
                    big_order_net_inflow=big_order_net_inflow,
                    big_order_net_inflow_ratio=big_order_net_inflow_ratio,
                    medium_order_net_inflow=medium_order_net_inflow,
                    medium_order_net_inflow_ratio=medium_order_net_inflow_ratio,
                    small_order_net_inflow=small_order_net_inflow,
                    small_order_net_inflow_ratio=small_order_net_inflow_ratio,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 行业-{indicator} 个股资金流，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取行业个股资金流失败：symbol={symbol}, indicator={indicator}, error={e}")
            return []
    
    # ========== 东方财富 - 行业历史资金流 ==========
    
    async def get_stock_sector_fund_flow_hist(
        self,
        symbol: str
    ) -> List[StockSectorFundFlowHist]:
        """获取东方财富 - 行业历史资金流数据
        
        Args:
            symbol: 行业名称（如 "汽车服务"）
        
        Returns:
            StockSectorFundFlowHist 列表，包含该行业的历史资金流数据（11 个字段，约 121 条）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_sector_fund_flow_hist_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_sector_fund_flow_hist(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockSectorFundFlowHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    main_net_inflow=float(row.get('主力净流入 - 净额', 0)) if not pd.isna(row.get('主力净流入 - 净额')) else None,
                    main_net_inflow_ratio=float(row.get('主力净流入 - 净占比', 0)) if not pd.isna(row.get('主力净流入 - 净占比')) else None,
                    super_order_net_inflow=float(row.get('超大单净流入 - 净额', 0)) if not pd.isna(row.get('超大单净流入 - 净额')) else None,
                    super_order_net_inflow_ratio=float(row.get('超大单净流入 - 净占比', 0)) if not pd.isna(row.get('超大单净流入 - 净占比')) else None,
                    big_order_net_inflow=float(row.get('大单净流入 - 净额', 0)) if not pd.isna(row.get('大单净流入 - 净额')) else None,
                    big_order_net_inflow_ratio=float(row.get('大单净流入 - 净占比', 0)) if not pd.isna(row.get('大单净流入 - 净占比')) else None,
                    medium_order_net_inflow=float(row.get('中单净流入 - 净额', 0)) if not pd.isna(row.get('中单净流入 - 净额')) else None,
                    medium_order_net_inflow_ratio=float(row.get('中单净流入 - 净占比', 0)) if not pd.isna(row.get('中单净流入 - 净占比')) else None,
                    small_order_net_inflow=float(row.get('小单净流入 - 净额', 0)) if not pd.isna(row.get('小单净流入 - 净额')) else None,
                    small_order_net_inflow_ratio=float(row.get('小单净流入 - 净占比', 0)) if not pd.isna(row.get('小单净流入 - 净占比')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 行业历史资金流，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取行业历史资金流失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 概念历史资金流 ==========
    
    async def get_stock_concept_fund_flow_hist(
        self,
        symbol: str
    ) -> List[StockSectorFundFlowHist]:
        """获取东方财富 - 概念历史资金流数据
        
        Args:
            symbol: 概念名称（如 "数据要素"）
        
        Returns:
            StockSectorFundFlowHist 列表，包含该概念的历史资金流数据（11 个字段，约 121 条）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_concept_fund_flow_hist_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_concept_fund_flow_hist(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockSectorFundFlowHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    main_net_inflow=float(row.get('主力净流入 - 净额', 0)) if not pd.isna(row.get('主力净流入 - 净额')) else None,
                    main_net_inflow_ratio=float(row.get('主力净流入 - 净占比', 0)) if not pd.isna(row.get('主力净流入 - 净占比')) else None,
                    super_order_net_inflow=float(row.get('超大单净流入 - 净额', 0)) if not pd.isna(row.get('超大单净流入 - 净额')) else None,
                    super_order_net_inflow_ratio=float(row.get('超大单净流入 - 净占比', 0)) if not pd.isna(row.get('超大单净流入 - 净占比')) else None,
                    big_order_net_inflow=float(row.get('大单净流入 - 净额', 0)) if not pd.isna(row.get('大单净流入 - 净额')) else None,
                    big_order_net_inflow_ratio=float(row.get('大单净流入 - 净占比', 0)) if not pd.isna(row.get('大单净流入 - 净占比')) else None,
                    medium_order_net_inflow=float(row.get('中单净流入 - 净额', 0)) if not pd.isna(row.get('中单净流入 - 净额')) else None,
                    medium_order_net_inflow_ratio=float(row.get('中单净流入 - 净占比', 0)) if not pd.isna(row.get('中单净流入 - 净占比')) else None,
                    small_order_net_inflow=float(row.get('小单净流入 - 净额', 0)) if not pd.isna(row.get('小单净流入 - 净额')) else None,
                    small_order_net_inflow_ratio=float(row.get('小单净流入 - 净占比', 0)) if not pd.isna(row.get('小单净流入 - 净占比')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 概念历史资金流，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取概念历史资金流失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 基金持仓汇总 ==========
    
    async def get_stock_report_fund_hold(
        self,
        symbol: str = "基金持仓",
        date: str = None
    ) -> List[StockReportFundHold]:
        """获取东方财富 - 基金持仓汇总数据
        
        Args:
            symbol: 持仓类型，choice of {"基金持仓", "QFII 持仓", "社保持仓", "券商持仓", "保险持仓", "信托持仓"}，默认 "基金持仓"
            date: 财报发布日期，格式 "YYYYMMDD"，如 "20200630"
                  可选：xxxx-03-31, xxxx-06-30, xxxx-09-30, xxxx-12-31
        
        Returns:
            StockReportFundHold 列表，包含基金持仓汇总数据（9 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_report_fund_hold_{symbol}_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_report_fund_hold(symbol=symbol, date=date)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockReportFundHold(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    fund_count=int(row.get('持有基金家数', 0)) if not pd.isna(row.get('持有基金家数')) else None,
                    total_shares=int(float(row.get('持股总数', 0))) if not pd.isna(row.get('持股总数')) else None,
                    market_value=float(row.get('持股市值', 0)) if not pd.isna(row.get('持股市值')) else None,
                    change_type=str(row.get('持股变化', '')) if not pd.isna(row.get('持股变化')) else None,
                    change_shares=int(float(row.get('持股变动数值', 0))) if not pd.isna(row.get('持股变动数值')) else None,
                    change_ratio=float(row.get('持股变动比例', 0)) if not pd.isna(row.get('持股变动比例')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol}（{date}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取基金持仓汇总失败：symbol={symbol}, date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 基金持仓明细 ==========
    
    async def get_stock_report_fund_hold_detail(
        self,
        symbol: str,
        date: str = None
    ) -> List[StockReportFundHoldDetail]:
        """获取东方财富 - 基金持仓明细数据
        
        Args:
            symbol: 基金代码（如 "005827"）
            date: 财报发布日期，格式 "YYYYMMDD"，如 "20201231"
                  可选：xxxx-03-31, xxxx-06-30, xxxx-09-30, xxxx-12-31
        
        Returns:
            StockReportFundHoldDetail 列表，包含基金持仓明细数据（7 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_report_fund_hold_detail_{symbol}_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_report_fund_hold_detail(symbol=symbol, date=date)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockReportFundHoldDetail(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    shares=int(float(row.get('持股数', 0))) if not pd.isna(row.get('持股数')) else None,
                    market_value=float(row.get('持股市值', 0)) if not pd.isna(row.get('持股市值')) else None,
                    ratio_of_total_shares=float(row.get('占总股本比例', 0)) if not pd.isna(row.get('占总股本比例')) else None,
                    ratio_of_float_shares=float(row.get('占流通股本比例', 0)) if not pd.isna(row.get('占流通股本比例')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取基金 {symbol}（{date}）持仓明细，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取基金持仓明细失败：symbol={symbol}, date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 龙虎榜详情 ==========
    
    async def get_stock_lhb_detail_em(
        self,
        start_date: str,
        end_date: str
    ) -> List[StockLhbDetailEm]:
        """获取东方财富 - 龙虎榜详情数据
        
        Args:
            start_date: 开始日期，格式 "YYYYMMDD"，如 "20230403"
            end_date: 结束日期，格式 "YYYYMMDD"，如 "20230417"
        
        Returns:
            StockLhbDetailEm 列表，包含龙虎榜详情数据（21 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_lhb_detail_em_{start_date}_{end_date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockLhbDetailEm(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    list_date=str(row.get('上榜日', '')) if not pd.isna(row.get('上榜日')) else None,
                    interpretation=str(row.get('解读', '')) if not pd.isna(row.get('解读')) else None,
                    close_price=float(row.get('收盘价', 0)) if not pd.isna(row.get('收盘价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    net_buy_amount=float(row.get('龙虎榜净买额', 0)) if not pd.isna(row.get('龙虎榜净买额')) else None,
                    buy_amount=float(row.get('龙虎榜买入额', 0)) if not pd.isna(row.get('龙虎榜买入额')) else None,
                    sell_amount=float(row.get('龙虎榜卖出额', 0)) if not pd.isna(row.get('龙虎榜卖出额')) else None,
                    total_amount=float(row.get('龙虎榜成交额', 0)) if not pd.isna(row.get('龙虎榜成交额')) else None,
                    market_total_amount=int(float(row.get('市场总成交额', 0))) if not pd.isna(row.get('市场总成交额')) else None,
                    net_buy_ratio=float(row.get('净买额占总成交比', 0)) if not pd.isna(row.get('净买额占总成交比')) else None,
                    total_amount_ratio=float(row.get('成交额占总成交比', 0)) if not pd.isna(row.get('成交额占总成交比')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                    float_market_cap=float(row.get('流通市值', 0)) if not pd.isna(row.get('流通市值')) else None,
                    list_reason=str(row.get('上榜原因', '')) if not pd.isna(row.get('上榜原因')) else None,
                    after_1d_change_pct=float(row.get('上榜后 1 日', 0)) if not pd.isna(row.get('上榜后 1 日')) else None,
                    after_2d_change_pct=float(row.get('上榜后 2 日', 0)) if not pd.isna(row.get('上榜后 2 日')) else None,
                    after_5d_change_pct=float(row.get('上榜后 5 日', 0)) if not pd.isna(row.get('上榜后 5 日')) else None,
                    after_10d_change_pct=float(row.get('上榜后 10 日', 0)) if not pd.isna(row.get('上榜后 10 日')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取龙虎榜详情（{start_date}-{end_date}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取龙虎榜详情失败：start_date={start_date}, end_date={end_date}, error={e}")
            return []
    
    # ========== 东方财富 - 个股上榜统计 ==========
    
    async def get_stock_lhb_stock_statistic_em(
        self,
        symbol: str = "近一月"
    ) -> List[StockLhbStockStatisticEm]:
        """获取东方财富 - 个股上榜统计数据
        
        Args:
            symbol: 统计周期，choice of {"近一月", "近三月", "近六月", "近一年"}，默认 "近一月"
        
        Returns:
            StockLhbStockStatisticEm 列表，包含个股上榜统计数据（20 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_lhb_stock_statistic_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_lhb_stock_statistic_em(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockLhbStockStatisticEm(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else 0,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    recent_list_date=str(row.get('最近上榜日', '')) if not pd.isna(row.get('最近上榜日')) else None,
                    close_price=float(row.get('收盘价', 0)) if not pd.isna(row.get('收盘价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    list_count=int(row.get('上榜次数', 0)) if not pd.isna(row.get('上榜次数')) else None,
                    net_buy_amount=float(row.get('龙虎榜净买额', 0)) if not pd.isna(row.get('龙虎榜净买额')) else None,
                    buy_amount=float(row.get('龙虎榜买入额', 0)) if not pd.isna(row.get('龙虎榜买入额')) else None,
                    sell_amount=float(row.get('龙虎榜卖出额', 0)) if not pd.isna(row.get('龙虎榜卖出额')) else None,
                    total_amount=float(row.get('龙虎榜总成交额', 0)) if not pd.isna(row.get('龙虎榜总成交额')) else None,
                    buyer_institution_count=int(row.get('买方机构次数', 0)) if not pd.isna(row.get('买方机构次数')) else None,
                    seller_institution_count=int(row.get('卖方机构次数', 0)) if not pd.isna(row.get('卖方机构次数')) else None,
                    institution_net_buy_amount=float(row.get('机构买入净额', 0)) if not pd.isna(row.get('机构买入净额')) else None,
                    institution_buy_amount=float(row.get('机构买入总额', 0)) if not pd.isna(row.get('机构买入总额')) else None,
                    institution_sell_amount=float(row.get('机构卖出总额', 0)) if not pd.isna(row.get('机构卖出总额')) else None,
                    change_pct_1m=float(row.get('近 1 个月涨跌幅', 0)) if not pd.isna(row.get('近 1 个月涨跌幅')) else None,
                    change_pct_3m=float(row.get('近 3 个月涨跌幅', 0)) if not pd.isna(row.get('近 3 个月涨跌幅')) else None,
                    change_pct_6m=float(row.get('近 6 个月涨跌幅', 0)) if not pd.isna(row.get('近 6 个月涨跌幅')) else None,
                    change_pct_1y=float(row.get('近 1 年涨跌幅', 0)) if not pd.isna(row.get('近 1 年涨跌幅')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取个股上榜统计（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取个股上榜统计失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 新浪财经 - 机构推荐池 ==========
    
    async def get_stock_institute_recommend(
        self,
        symbol: str = "最新投资评级"
    ) -> List[StockInstituteRecommend]:
        """获取新浪财经 - 机构推荐池数据
        
        Args:
            symbol: 推荐类型，choice of {'最新投资评级', '上调评级股票', '下调评级股票', '股票综合评级', 
                     '首次评级股票', '目标涨幅排名', '机构关注度', '行业关注度', '投资评级选股'}，
                     默认 "最新投资评级"
        
        Returns:
            StockInstituteRecommend 列表，包含机构推荐池数据（7 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_institute_recommend_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_institute_recommend(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockInstituteRecommend(
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票名称', '')) if not pd.isna(row.get('股票名称')) else '',
                    rating=str(row.get('最新评级', '')) if not pd.isna(row.get('最新评级')) else None,
                    target_price=float(row.get('目标价', 0)) if not pd.isna(row.get('目标价')) else None,
                    rating_date=str(row.get('评级日期↓', '')) if not pd.isna(row.get('评级日期↓')) else None,
                    composite_rating=str(row.get('综合评级', '')) if not pd.isna(row.get('综合评级')) else None,
                    avg_change_pct=float(row.get('平均涨幅', 0)) if not pd.isna(row.get('平均涨幅')) else None,
                    industry=str(row.get('行业', '')) if not pd.isna(row.get('行业')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取机构推荐池（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取机构推荐池失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 新浪财经 - 股票评级记录 ==========
    
    async def get_stock_institute_recommend_detail(
        self,
        symbol: str
    ) -> List[StockInstituteRecommendDetail]:
        """获取新浪财经 - 股票评级记录数据
        
        Args:
            symbol: 股票代码（如 "000001"）
        
        Returns:
            StockInstituteRecommendDetail 列表，包含股票评级记录数据（8 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_institute_recommend_detail_{symbol}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_institute_recommend_detail(symbol=symbol)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockInstituteRecommendDetail(
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票名称', '')) if not pd.isna(row.get('股票名称')) else '',
                    target_price=float(row.get('目标价', 0)) if not pd.isna(row.get('目标价')) else None,
                    rating=str(row.get('最新评级', '')) if not pd.isna(row.get('最新评级')) else None,
                    institution=str(row.get('评级机构', '')) if not pd.isna(row.get('评级机构')) else None,
                    analyst=str(row.get('分析师', '')) if not pd.isna(row.get('分析师')) else None,
                    industry=str(row.get('行业', '')) if not pd.isna(row.get('行业')) else None,
                    rating_date=str(row.get('评级日期', '')) if not pd.isna(row.get('评级日期')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取股票 {symbol} 评级记录，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取股票评级记录失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 巨潮资讯 - 投资评级 ==========
    
    async def get_stock_rank_forecast_cninfo(
        self,
        date: str
    ) -> List[StockRankForecastCninfo]:
        """获取巨潮资讯 - 投资评级数据
        
        Args:
            date: 交易日，格式 "YYYYMMDD"，如 "20230817"
        
        Returns:
            StockRankForecastCninfo 列表，包含投资评级数据（11 个字段）
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_rank_forecast_cninfo_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_rank_forecast_cninfo(date=date)
            
            if data is None or len(data) == 0:
                return []
            
            # 解析数据
            result = []
            for _, row in data.iterrows():
                item = StockRankForecastCninfo(
                    sec_code=str(row.get('证券代码', '')) if not pd.isna(row.get('证券代码')) else '',
                    sec_name=str(row.get('证券简称', '')) if not pd.isna(row.get('证券简称')) else '',
                    publish_date=str(row.get('发布日期', '')) if not pd.isna(row.get('发布日期')) else None,
                    institution_name=str(row.get('研究机构简称', '')) if not pd.isna(row.get('研究机构简称')) else None,
                    researcher_name=str(row.get('研究员名称', '')) if not pd.isna(row.get('研究员名称')) else None,
                    rating=str(row.get('投资评级', '')) if not pd.isna(row.get('投资评级')) else None,
                    is_first_rating=str(row.get('是否首次评级', '')) if not pd.isna(row.get('是否首次评级')) else None,
                    rating_change=str(row.get('评级变化', '')) if not pd.isna(row.get('评级变化')) else None,
                    prev_rating=str(row.get('前一次投资评级', '')) if not pd.isna(row.get('前一次投资评级')) else None,
                    target_price_lower=float(row.get('目标价格 - 下限', 0)) if not pd.isna(row.get('目标价格 - 下限')) else None,
                    target_price_upper=float(row.get('目标价格 - 上限', 0)) if not pd.isna(row.get('目标价格 - 上限')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取投资评级（{date}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取投资评级失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 业绩报表 ==========
    
    async def get_stock_yjbb_em(self, date: str) -> List[StockYjbbEM]:
        """获取东方财富 - 业绩报表数据
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20100331 开始
        
        Returns:
            StockYjbbEM 列表，包含业绩报表数据（16 个字段）：
            - 基本信息：serial_number, code, name
            - 盈利指标：eps, net_profit, net_profit_yoy, net_profit_qoq
            - 营收指标：total_revenue, revenue_yoy, revenue_qoq
            - 财务指标：net_assets_per_share, roe, operating_cash_flow_per_share, gross_margin
            - 其他：industry, announce_date
        """
        try:
            cache_key = f"stock_yjbb_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_yjbb_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockYjbbEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    eps=float(row.get('每股收益', 0)) if not pd.isna(row.get('每股收益')) else None,
                    total_revenue=float(row.get('营业总收入 - 营业总收入', 0)) if not pd.isna(row.get('营业总收入 - 营业总收入')) else None,
                    revenue_yoy=float(row.get('营业总收入 - 同比增长', 0)) if not pd.isna(row.get('营业总收入 - 同比增长')) else None,
                    revenue_qoq=float(row.get('营业总收入 - 季度环比增长', 0)) if not pd.isna(row.get('营业总收入 - 季度环比增长')) else None,
                    net_profit=float(row.get('净利润 - 净利润', 0)) if not pd.isna(row.get('净利润 - 净利润')) else None,
                    net_profit_yoy=float(row.get('净利润 - 同比增长', 0)) if not pd.isna(row.get('净利润 - 同比增长')) else None,
                    net_profit_qoq=float(row.get('净利润 - 季度环比增长', 0)) if not pd.isna(row.get('净利润 - 季度环比增长')) else None,
                    net_assets_per_share=float(row.get('每股净资产', 0)) if not pd.isna(row.get('每股净资产')) else None,
                    roe=float(row.get('净资产收益率', 0)) if not pd.isna(row.get('净资产收益率')) else None,
                    operating_cash_flow_per_share=float(row.get('每股经营现金流量', 0)) if not pd.isna(row.get('每股经营现金流量')) else None,
                    gross_margin=float(row.get('销售毛利率', 0)) if not pd.isna(row.get('销售毛利率')) else None,
                    industry=str(row.get('所处行业', '')) if not pd.isna(row.get('所处行业')) else None,
                    announce_date=str(row.get('最新公告日期', '')) if not pd.isna(row.get('最新公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 业绩报表数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取业绩报表数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 业绩快报 ==========
    
    async def get_stock_yjkb_em(self, date: str) -> List[StockYjkbEM]:
        """获取东方财富 - 业绩快报数据
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20100331 开始
        
        Returns:
            StockYjkbEM 列表，包含业绩快报数据（18 个字段）：
            - 基本信息：serial_number, code, name
            - 盈利指标：eps, net_profit, net_profit_last_year, net_profit_yoy, net_profit_qoq
            - 营收指标：operating_revenue, revenue_last_year, revenue_yoy, revenue_qoq
            - 财务指标：net_assets_per_share, roe
            - 其他：industry, announce_date, market, security_type
        """
        try:
            cache_key = f"stock_yjkb_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_yjkb_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockYjkbEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    eps=float(row.get('每股收益', 0)) if not pd.isna(row.get('每股收益')) else None,
                    operating_revenue=float(row.get('营业收入 - 营业收入', 0)) if not pd.isna(row.get('营业收入 - 营业收入')) else None,
                    revenue_last_year=float(row.get('营业收入 - 去年同期', 0)) if not pd.isna(row.get('营业收入 - 去年同期')) else None,
                    revenue_yoy=str(row.get('营业收入 - 同比增长', '')) if not pd.isna(row.get('营业收入 - 同比增长')) else None,
                    revenue_qoq=str(row.get('营业收入 - 季度环比增长', '')) if not pd.isna(row.get('营业收入 - 季度环比增长')) else None,
                    net_profit=float(row.get('净利润 - 净利润', 0)) if not pd.isna(row.get('净利润 - 净利润')) else None,
                    net_profit_last_year=float(row.get('净利润 - 去年同期', 0)) if not pd.isna(row.get('净利润 - 去年同期')) else None,
                    net_profit_yoy=str(row.get('净利润 - 同比增长', '')) if not pd.isna(row.get('净利润 - 同比增长')) else None,
                    net_profit_qoq=str(row.get('净利润 - 季度环比增长', '')) if not pd.isna(row.get('净利润 - 季度环比增长')) else None,
                    net_assets_per_share=float(row.get('每股净资产', 0)) if not pd.isna(row.get('每股净资产')) else None,
                    roe=float(row.get('净资产收益率', 0)) if not pd.isna(row.get('净资产收益率')) else None,
                    industry=str(row.get('所处行业', '')) if not pd.isna(row.get('所处行业')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                    market=str(row.get('市场板块', '')) if not pd.isna(row.get('市场板块')) else None,
                    security_type=str(row.get('证券类型', '')) if not pd.isna(row.get('证券类型')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 业绩快报数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取业绩快报数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 业绩预告 ==========
    
    async def get_stock_yjyg_em(self, date: str) -> List[StockYjygEM]:
        """获取东方财富 - 业绩预告数据
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20081231 开始
        
        Returns:
            StockYjygEM 列表，包含业绩预告数据（11 个字段）：
            - 基本信息：serial_number, code, name
            - 预测信息：forecast_indicator, forecast_value, performance_change, performance_change_ratio
            - 预告类型：forecast_type（预增、预减、首亏、续亏等）
            - 其他：performance_change_reason, last_year_value, announce_date
        """
        try:
            cache_key = f"stock_yjyg_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_yjyg_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockYjygEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    forecast_indicator=str(row.get('预测指标', '')) if not pd.isna(row.get('预测指标')) else None,
                    performance_change=str(row.get('业绩变动', '')) if not pd.isna(row.get('业绩变动')) else None,
                    forecast_value=float(row.get('预测数值', 0)) if not pd.isna(row.get('预测数值')) else None,
                    performance_change_ratio=float(row.get('业绩变动幅度', 0)) if not pd.isna(row.get('业绩变动幅度')) else None,
                    performance_change_reason=str(row.get('业绩变动原因', '')) if not pd.isna(row.get('业绩变动原因')) else None,
                    forecast_type=str(row.get('预告类型', '')) if not pd.isna(row.get('预告类型')) else None,
                    last_year_value=float(row.get('上年同期值', 0)) if not pd.isna(row.get('上年同期值')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 业绩预告数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取业绩预告数据失败：date={date}, error={e}")
            return []
    
    # ========== 巨潮资讯 - 行业分类数据 ==========
    
    async def get_stock_industry_category_cninfo(self, symbol: str) -> List[StockIndustryCategoryCNINFO]:
        """获取巨潮资讯 - 行业分类数据
        
        Args:
            symbol: 行业分类标准，choice of {
                "证监会行业分类标准", "巨潮行业分类标准", "申银万国行业分类标准", 
                "新财富行业分类标准", "国资委行业分类标准", "巨潮产业细分标准", 
                "天相行业分类标准", "全球行业分类标准"
            }
        
        Returns:
            StockIndustryCategoryCNINFO 列表，包含行业分类数据（8 个字段）：
            - 类目信息：category_code, category_name, category_name_en
            - 行业信息：industry_type, industry_type_code
            - 层级信息：parent_code, level
            - 其他：end_date
        """
        try:
            cache_key = f"stock_industry_category_cninfo_{symbol}"
            if self._is_cache_valid(cache_key, ttl=86400):  # 24 小时缓存（行业分类数据相对稳定）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_industry_category_cninfo(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockIndustryCategoryCNINFO(
                    category_code=str(row.get('类目编码', '')) if not pd.isna(row.get('类目编码')) else None,
                    category_name=str(row.get('类目名称', '')) if not pd.isna(row.get('类目名称')) else None,
                    end_date=str(row.get('终止日期', '')) if not pd.isna(row.get('终止日期')) else None,
                    industry_type=str(row.get('行业类型', '')) if not pd.isna(row.get('行业类型')) else None,
                    industry_type_code=str(row.get('行业类型编码', '')) if not pd.isna(row.get('行业类型编码')) else None,
                    category_name_en=str(row.get('类目名称英文', '')) if not pd.isna(row.get('类目名称英文')) else None,
                    parent_code=str(row.get('父类编码', '')) if not pd.isna(row.get('父类编码')) else None,
                    level=int(row.get('分级', 0)) if not pd.isna(row.get('分级')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 行业分类数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取行业分类数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 巨潮资讯 - 上市公司行业归属变动 ==========
    
    async def get_stock_industry_change_cninfo(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[StockIndustryChangeCNINFO]:
        """获取巨潮资讯 - 上市公司行业归属的变动情况
        
        Args:
            symbol: 股票代码（如 "002594"）
            start_date: 开始日期（格式 "YYYYMMDD"）
            end_date: 结束日期（格式 "YYYYMMDD"）
        
        Returns:
            StockIndustryChangeCNINFO 列表，包含行业归属变动数据（11 个字段）：
            - 公司信息：new_stock_name, stock_code, org_name
            - 行业分类：industry_category, industry_large_class, industry_mid_class, industry_sub_class
            - 分类标准：classification_standard, classification_standard_code, industry_code
            - 变更信息：change_date
        """
        try:
            cache_key = f"stock_industry_change_cninfo_{symbol}_{start_date}_{end_date}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_industry_change_cninfo(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockIndustryChangeCNINFO(
                    new_stock_name=str(row.get('新证券简称', '')) if not pd.isna(row.get('新证券简称')) else None,
                    industry_mid_class=str(row.get('行业中类', '')) if not pd.isna(row.get('行业中类')) else None,
                    industry_large_class=str(row.get('行业大类', '')) if not pd.isna(row.get('行业大类')) else None,
                    industry_sub_class=str(row.get('行业次类', '')) if not pd.isna(row.get('行业次类')) else None,
                    industry_category=str(row.get('行业门类', '')) if not pd.isna(row.get('行业门类')) else None,
                    org_name=str(row.get('机构名称', '')) if not pd.isna(row.get('机构名称')) else None,
                    industry_code=str(row.get('行业编码', '')) if not pd.isna(row.get('行业编码')) else None,
                    classification_standard=str(row.get('分类标准', '')) if not pd.isna(row.get('分类标准')) else None,
                    classification_standard_code=str(row.get('分类标准编码', '')) if not pd.isna(row.get('分类标准编码')) else None,
                    stock_code=str(row.get('证券代码', '')) if not pd.isna(row.get('证券代码')) else None,
                    change_date=str(row.get('变更日期', '')) if not pd.isna(row.get('变更日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 行业归属变动数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取行业归属变动数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 资产负债表（沪深） ==========
    
    async def get_stock_zcfz_em(self, date: str) -> List[StockZcfzEM]:
        """获取东方财富 - 资产负债表数据（沪深 A 股）
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20081231 开始
        
        Returns:
            StockZcfzEM 列表，包含资产负债表数据（15 个字段）：
            - 基本信息：serial_number, code, name, announce_date
            - 资产：monetary_fund, accounts_receivable, inventory, total_assets, total_assets_yoy
            - 负债：accounts_payable, total_liabilities, advance_receipts, total_liabilities_yoy
            - 财务指标：asset_liability_ratio, total_equity
        """
        try:
            cache_key = f"stock_zcfz_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_zcfz_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockZcfzEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    monetary_fund=float(row.get('资产 - 货币资金', 0)) if not pd.isna(row.get('资产 - 货币资金')) else None,
                    accounts_receivable=float(row.get('资产 - 应收账款', 0)) if not pd.isna(row.get('资产 - 应收账款')) else None,
                    inventory=float(row.get('资产 - 存货', 0)) if not pd.isna(row.get('资产 - 存货')) else None,
                    total_assets=float(row.get('资产 - 总资产', 0)) if not pd.isna(row.get('资产 - 总资产')) else None,
                    total_assets_yoy=float(row.get('资产 - 总资产同比', 0)) if not pd.isna(row.get('资产 - 总资产同比')) else None,
                    accounts_payable=float(row.get('负债 - 应付账款', 0)) if not pd.isna(row.get('负债 - 应付账款')) else None,
                    total_liabilities=float(row.get('负债 - 总负债', 0)) if not pd.isna(row.get('负债 - 总负债')) else None,
                    advance_receipts=float(row.get('负债 - 预收账款', 0)) if not pd.isna(row.get('负债 - 预收账款')) else None,
                    total_liabilities_yoy=float(row.get('负债 - 总负债同比', 0)) if not pd.isna(row.get('负债 - 总负债同比')) else None,
                    asset_liability_ratio=float(row.get('资产负债率', 0)) if not pd.isna(row.get('资产负债率')) else None,
                    total_equity=float(row.get('股东权益合计', 0)) if not pd.isna(row.get('股东权益合计')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 资产负债表（沪深）数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取资产负债表（沪深）数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 资产负债表（北交所） ==========
    
    async def get_stock_zcfz_bj_em(self, date: str) -> List[StockZcfzEM]:
        """获取东方财富 - 资产负债表数据（北交所）
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20081231 开始
        
        Returns:
            StockZcfzEM 列表，包含北交所资产负债表数据（15 个字段）
        """
        try:
            cache_key = f"stock_zcfz_bj_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_zcfz_bj_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockZcfzEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    monetary_fund=float(row.get('资产 - 货币资金', 0)) if not pd.isna(row.get('资产 - 货币资金')) else None,
                    accounts_receivable=float(row.get('资产 - 应收账款', 0)) if not pd.isna(row.get('资产 - 应收账款')) else None,
                    inventory=float(row.get('资产 - 存货', 0)) if not pd.isna(row.get('资产 - 存货')) else None,
                    total_assets=float(row.get('资产 - 总资产', 0)) if not pd.isna(row.get('资产 - 总资产')) else None,
                    total_assets_yoy=float(row.get('资产 - 总资产同比', 0)) if not pd.isna(row.get('资产 - 总资产同比')) else None,
                    accounts_payable=float(row.get('负债 - 应付账款', 0)) if not pd.isna(row.get('负债 - 应付账款')) else None,
                    total_liabilities=float(row.get('负债 - 总负债', 0)) if not pd.isna(row.get('负债 - 总负债')) else None,
                    advance_receipts=float(row.get('负债 - 预收账款', 0)) if not pd.isna(row.get('负债 - 预收账款')) else None,
                    total_liabilities_yoy=float(row.get('负债 - 总负债同比', 0)) if not pd.isna(row.get('负债 - 总负债同比')) else None,
                    asset_liability_ratio=float(row.get('资产负债率', 0)) if not pd.isna(row.get('资产负债率')) else None,
                    total_equity=float(row.get('股东权益合计', 0)) if not pd.isna(row.get('股东权益合计')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 资产负债表（北交所）数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取资产负债表（北交所）数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 利润表 ==========
    
    async def get_stock_lrb_em(self, date: str) -> List[StockLrbEM]:
        """获取东方财富 - 利润表数据
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20120331 开始
        
        Returns:
            StockLrbEM 列表，包含利润表数据（15 个字段）：
            - 基本信息：serial_number, code, name, announce_date
            - 盈利：net_profit, net_profit_yoy, operating_profit, total_profit
            - 营收：total_revenue, total_revenue_yoy
            - 支出：operating_expense, selling_expense, administrative_expense, financial_expense, total_operating_expense
        """
        try:
            cache_key = f"stock_lrb_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_lrb_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockLrbEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    net_profit=float(row.get('净利润', 0)) if not pd.isna(row.get('净利润')) else None,
                    net_profit_yoy=float(row.get('净利润同比', 0)) if not pd.isna(row.get('净利润同比')) else None,
                    total_revenue=float(row.get('营业总收入', 0)) if not pd.isna(row.get('营业总收入')) else None,
                    total_revenue_yoy=float(row.get('营业总收入同比', 0)) if not pd.isna(row.get('营业总收入同比')) else None,
                    operating_expense=float(row.get('营业总支出 - 营业支出', 0)) if not pd.isna(row.get('营业总支出 - 营业支出')) else None,
                    selling_expense=float(row.get('营业总支出 - 销售费用', 0)) if not pd.isna(row.get('营业总支出 - 销售费用')) else None,
                    administrative_expense=float(row.get('营业总支出 - 管理费用', 0)) if not pd.isna(row.get('营业总支出 - 管理费用')) else None,
                    financial_expense=float(row.get('营业总支出 - 财务费用', 0)) if not pd.isna(row.get('营业总支出 - 财务费用')) else None,
                    total_operating_expense=float(row.get('营业总支出 - 营业总支出', 0)) if not pd.isna(row.get('营业总支出 - 营业总支出')) else None,
                    operating_profit=float(row.get('营业利润', 0)) if not pd.isna(row.get('营业利润')) else None,
                    total_profit=float(row.get('利润总额', 0)) if not pd.isna(row.get('利润总额')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 利润表数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取利润表数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 现金流量表 ==========
    
    async def get_stock_xjll_em(self, date: str) -> List[StockXjllEM]:
        """获取东方财富 - 现金流量表数据
        
        Args:
            date: 报告期，格式 "YYYYMMDD"，choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}
                  从 20081231 开始
        
        Returns:
            StockXjllEM 列表，包含现金流量表数据（11 个字段）：
            - 基本信息：serial_number, code, name, announce_date
            - 净现金流：net_cash_flow, net_cash_flow_yoy
            - 经营性现金流：operating_cash_flow, operating_cash_flow_ratio
            - 投资性现金流：investing_cash_flow, investing_cash_flow_ratio
            - 融资性现金流：financing_cash_flow, financing_cash_flow_ratio
        """
        try:
            cache_key = f"stock_xjll_em_{date}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_xjll_em(date=date)
            
            result = []
            for _, row in data.iterrows():
                item = StockXjllEM(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    net_cash_flow=float(row.get('净现金流 - 净现金流', 0)) if not pd.isna(row.get('净现金流 - 净现金流')) else None,
                    net_cash_flow_yoy=float(row.get('净现金流 - 同比增长', 0)) if not pd.isna(row.get('净现金流 - 同比增长')) else None,
                    operating_cash_flow=float(row.get('经营性现金流 - 现金流量净额', 0)) if not pd.isna(row.get('经营性现金流 - 现金流量净额')) else None,
                    operating_cash_flow_ratio=float(row.get('经营性现金流 - 净现金流占比', 0)) if not pd.isna(row.get('经营性现金流 - 净现金流占比')) else None,
                    investing_cash_flow=float(row.get('投资性现金流 - 现金流量净额', 0)) if not pd.isna(row.get('投资性现金流 - 现金流量净额')) else None,
                    investing_cash_flow_ratio=float(row.get('投资性现金流 - 净现金流占比', 0)) if not pd.isna(row.get('投资性现金流 - 净现金流占比')) else None,
                    financing_cash_flow=float(row.get('融资性现金流 - 现金流量净额', 0)) if not pd.isna(row.get('融资性现金流 - 现金流量净额')) else None,
                    financing_cash_flow_ratio=float(row.get('融资性现金流 - 净现金流占比', 0)) if not pd.isna(row.get('融资性现金流 - 净现金流占比')) else None,
                    announce_date=str(row.get('公告日期', '')) if not pd.isna(row.get('公告日期')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {date} 现金流量表数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取现金流量表数据失败：date={date}, error={e}")
            return []
    
    # ========== 东方财富 - 股东增减持 ==========
    
    async def get_stock_ggcg_em(self, symbol: str = "全部") -> List[StockGgcgEM]:
        """获取东方财富 - 股东增减持数据
        
        Args:
            symbol: 增减持类型，choice of {"全部", "股东增持", "股东减持"}，默认 "全部"
        
        Returns:
            StockGgcgEM 列表，包含股东增减持数据（16 个字段）：
            - 股票信息：code, name, latest_price, change_pct
            - 股东信息：shareholder_name
            - 变动信息：change_type, change_amount, change_total_ratio, change_float_ratio
            - 变动后持股：after_hold_total, after_hold_total_ratio, after_hold_float, after_hold_float_ratio
            - 日期信息：start_date, end_date, announce_date
        """
        try:
            cache_key = f"stock_ggcg_em_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存（数据量较大且频繁更新）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_ggcg_em(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                # 判断增减类型
                change_type_str = str(row.get('持股变动信息 - 增减', '')) if not pd.isna(row.get('持股变动信息 - 增减')) else ''
                change_type = 1 if '增持' in change_type_str else (-1 if '减持' in change_type_str else None)
                
                item = StockGgcgEM(
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    shareholder_name=str(row.get('股东名称', '')) if not pd.isna(row.get('股东名称')) else '',
                    change_type=change_type,
                    change_amount=float(row.get('持股变动信息 - 变动数量', 0)) if not pd.isna(row.get('持股变动信息 - 变动数量')) else None,
                    change_total_ratio=float(row.get('持股变动信息 - 占总股本比例', 0)) if not pd.isna(row.get('持股变动信息 - 占总股本比例')) else None,
                    change_float_ratio=float(row.get('持股变动信息 - 占流通股比例', 0)) if not pd.isna(row.get('持股变动信息 - 占流通股比例')) else None,
                    after_hold_total=float(row.get('变动后持股情况 - 持股总数', 0)) if not pd.isna(row.get('变动后持股情况 - 持股总数')) else None,
                    after_hold_total_ratio=float(row.get('变动后持股情况 - 占总股本比例', 0)) if not pd.isna(row.get('变动后持股情况 - 占总股本比例')) else None,
                    after_hold_float=float(row.get('变动后持股情况 - 持流通股数', 0)) if not pd.isna(row.get('变动后持股情况 - 持流通股数')) else None,
                    after_hold_float_ratio=float(row.get('变动后持股情况 - 占流通股比例', 0)) if not pd.isna(row.get('变动后持股情况 - 占流通股比例')) else None,
                    start_date=str(row.get('变动开始日', '')) if not pd.isna(row.get('变动开始日')) else None,
                    end_date=str(row.get('变动截止日', '')) if not pd.isna(row.get('变动截止日')) else None,
                    announce_date=str(row.get('公告日', '')) if not pd.isna(row.get('公告日')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取股东增减持数据（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取股东增减持数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 同花顺 - 个股资金流 ==========
    
    async def get_stock_fund_flow_individual(self, symbol: str = "即时") -> List[StockFundFlowIndividual]:
        """获取同花顺 - 个股资金流数据
        
        Args:
            symbol: 排行类型，choice of {"即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"}，默认 "即时"
        
        Returns:
            StockFundFlowIndividual 列表，包含个股资金流数据：
            - 即时模式（10 个字段）：序号、代码、名称、最新价、涨跌幅、换手率、流入资金、流出资金、净额、成交额
            - 排行模式（7 个字段）：序号、代码、名称、最新价、阶段涨跌幅、连续换手率、资金流入净额
        """
        try:
            cache_key = f"stock_fund_flow_individual_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_fund_flow_individual(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockFundFlowIndividual(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=str(row.get('涨跌幅', '')) if not pd.isna(row.get('涨跌幅')) else None,
                    turnover_rate=str(row.get('换手率', '')) if not pd.isna(row.get('换手率')) else None,
                    inflow=float(row.get('流入资金', 0)) if not pd.isna(row.get('流入资金')) else None,
                    outflow=float(row.get('流出资金', 0)) if not pd.isna(row.get('流出资金')) else None,
                    net_flow=float(row.get('净额', 0)) if not pd.isna(row.get('净额')) else None,
                    turnover_amount=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    stage_change_pct=str(row.get('阶段涨跌幅', '')) if not pd.isna(row.get('阶段涨跌幅')) else None,
                    continuous_turnover=str(row.get('连续换手率', '')) if not pd.isna(row.get('连续换手率')) else None,
                    net_inflow=float(row.get('资金流入净额', 0)) if not pd.isna(row.get('资金流入净额')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取同花顺个股资金流数据（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取同花顺个股资金流数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 同花顺 - 概念资金流 ==========
    
    async def get_stock_fund_flow_concept(self, symbol: str = "即时") -> List[StockFundFlowConcept]:
        """获取同花顺 - 概念资金流数据
        
        Args:
            symbol: 排行类型，choice of {"即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"}，默认 "即时"
        
        Returns:
            StockFundFlowConcept 列表，包含概念资金流数据：
            - 即时模式（11 个字段）：序号、行业、行业指数、行业 - 涨跌幅、流入资金、流出资金、净额、公司家数、领涨股、领涨股 - 涨跌幅、当前价
            - 排行模式（8 个字段）：序号、行业、公司家数、行业指数、阶段涨跌幅、流入资金、流出资金、净额
        """
        try:
            cache_key = f"stock_fund_flow_concept_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_fund_flow_concept(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockFundFlowConcept(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    concept_name=str(row.get('行业', '')) if not pd.isna(row.get('行业')) else '',
                    concept_index=float(row.get('行业指数', 0)) if not pd.isna(row.get('行业指数')) else None,
                    change_pct=float(row.get('行业 - 涨跌幅', 0)) if not pd.isna(row.get('行业 - 涨跌幅')) else None,
                    inflow=float(row.get('流入资金', 0)) if not pd.isna(row.get('流入资金')) else None,
                    outflow=float(row.get('流出资金', 0)) if not pd.isna(row.get('流出资金')) else None,
                    net_flow=float(row.get('净额', 0)) if not pd.isna(row.get('净额')) else None,
                    company_count=int(row.get('公司家数', 0)) if not pd.isna(row.get('公司家数')) else None,
                    leading_stock=str(row.get('领涨股', '')) if not pd.isna(row.get('领涨股')) else '',
                    leading_change_pct=float(row.get('领涨股 - 涨跌幅', 0)) if not pd.isna(row.get('领涨股 - 涨跌幅')) else None,
                    leading_price=float(row.get('当前价', 0)) if not pd.isna(row.get('当前价')) else None,
                    stage_change_pct=str(row.get('阶段涨跌幅', '')) if not pd.isna(row.get('阶段涨跌幅')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取同花顺概念资金流数据（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取同花顺概念资金流数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 同花顺 - 行业资金流 ==========
    
    async def get_stock_fund_flow_industry(self, symbol: str = "即时") -> List[StockFundFlowIndustry]:
        """获取同花顺 - 行业资金流数据
        
        Args:
            symbol: 排行类型，choice of {"即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"}，默认 "即时"
        
        Returns:
            StockFundFlowIndustry 列表，包含行业资金流数据：
            - 即时模式（11 个字段）：序号、行业、行业指数、行业 - 涨跌幅、流入资金、流出资金、净额、公司家数、领涨股、领涨股 - 涨跌幅、当前价
            - 排行模式（8 个字段）：序号、行业、公司家数、行业指数、阶段涨跌幅、流入资金、流出资金、净额
        """
        try:
            cache_key = f"stock_fund_flow_industry_{symbol}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_fund_flow_industry(symbol=symbol)
            
            result = []
            for _, row in data.iterrows():
                item = StockFundFlowIndustry(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    industry_name=str(row.get('行业', '')) if not pd.isna(row.get('行业')) else '',
                    industry_index=float(row.get('行业指数', 0)) if not pd.isna(row.get('行业指数')) else None,
                    change_pct=str(row.get('行业 - 涨跌幅', '')) if not pd.isna(row.get('行业 - 涨跌幅')) else None,
                    inflow=float(row.get('流入资金', 0)) if not pd.isna(row.get('流入资金')) else None,
                    outflow=float(row.get('流出资金', 0)) if not pd.isna(row.get('流出资金')) else None,
                    net_flow=float(row.get('净额', 0)) if not pd.isna(row.get('净额')) else None,
                    company_count=int(row.get('公司家数', 0)) if not pd.isna(row.get('公司家数')) else None,
                    leading_stock=str(row.get('领涨股', '')) if not pd.isna(row.get('领涨股')) else '',
                    leading_change_pct=str(row.get('领涨股 - 涨跌幅', '')) if not pd.isna(row.get('领涨股 - 涨跌幅')) else None,
                    leading_price=float(row.get('当前价', 0)) if not pd.isna(row.get('当前价')) else None,
                    stage_change_pct=str(row.get('阶段涨跌幅', '')) if not pd.isna(row.get('阶段涨跌幅')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取同花顺行业资金流数据（{symbol}），共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取同花顺行业资金流数据失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 同花顺 - 大单追踪 ==========
    
    async def get_stock_fund_flow_big_deal(self) -> List[StockFundFlowBigDeal]:
        """获取同花顺 - 大单追踪数据
        
        Args:
            无输入参数
        
        Returns:
            StockFundFlowBigDeal 列表，包含大单追踪数据（9 个字段）：
            - 交易信息：trade_time, code, name, trade_price, volume, amount
            - 大单性质：deal_type（买盘/卖盘）
            - 涨跌信息：change_pct, change_amount
        """
        try:
            cache_key = "stock_fund_flow_big_deal"
            if self._is_cache_valid(cache_key, ttl=60):  # 1 分钟缓存（实时数据）
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_fund_flow_big_deal()
            
            result = []
            for _, row in data.iterrows():
                item = StockFundFlowBigDeal(
                    trade_time=str(row.get('成交时间', '')) if not pd.isna(row.get('成交时间')) else None,
                    code=str(row.get('股票代码', '')) if not pd.isna(row.get('股票代码')) else '',
                    name=str(row.get('股票简称', '')) if not pd.isna(row.get('股票简称')) else '',
                    trade_price=float(row.get('成交价格', 0)) if not pd.isna(row.get('成交价格')) else None,
                    volume=int(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    amount=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    deal_type=str(row.get('大单性质', '')) if not pd.isna(row.get('大单性质')) else None,
                    change_pct=str(row.get('涨跌幅', '')) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取同花顺大单追踪数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取同花顺大单追踪数据失败：error={e}")
            return []
    
    # ========== 东方财富 - 个股资金流 ==========
    
    async def get_stock_individual_fund_flow(self, stock: str, market: str) -> List[StockIndividualFundFlow]:
        """获取东方财富 - 个股资金流数据
        
        Args:
            stock: 股票代码（如 "600094"）
            market: 市场，choice of {"sh", "sz", "bj"}
                - sh: 上海证券交易所
                - sz: 深证证券交易所
                - bj: 北京证券交易所
        
        Returns:
            StockIndividualFundFlow 列表，包含近 100 个交易日的资金流数据（13 个字段）：
            - 基本信息：date, close_price, change_pct
            - 主力流入：main_net_inflow, main_net_inflow_ratio
            - 超大单：super_order_net_inflow, super_order_net_inflow_ratio
            - 大单：big_order_net_inflow, big_order_net_inflow_ratio
            - 中单：medium_order_net_inflow, medium_order_net_inflow_ratio
            - 小单：small_order_net_inflow, small_order_net_inflow_ratio
        """
        try:
            cache_key = f"stock_individual_fund_flow_{stock}_{market}"
            if self._is_cache_valid(cache_key, ttl=3600):
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_individual_fund_flow(stock=stock, market=market)
            
            result = []
            for _, row in data.iterrows():
                item = StockIndividualFundFlow(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else None,
                    close_price=float(row.get('收盘价', 0)) if not pd.isna(row.get('收盘价')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    main_net_inflow=float(row.get('主力净流入 - 净额', 0)) if not pd.isna(row.get('主力净流入 - 净额')) else None,
                    main_net_inflow_ratio=float(row.get('主力净流入 - 净占比', 0)) if not pd.isna(row.get('主力净流入 - 净占比')) else None,
                    super_order_net_inflow=float(row.get('超大单净流入 - 净额', 0)) if not pd.isna(row.get('超大单净流入 - 净额')) else None,
                    super_order_net_inflow_ratio=float(row.get('超大单净流入 - 净占比', 0)) if not pd.isna(row.get('超大单净流入 - 净占比')) else None,
                    big_order_net_inflow=float(row.get('大单净流入 - 净额', 0)) if not pd.isna(row.get('大单净流入 - 净额')) else None,
                    big_order_net_inflow_ratio=float(row.get('大单净流入 - 净占比', 0)) if not pd.isna(row.get('大单净流入 - 净占比')) else None,
                    medium_order_net_inflow=float(row.get('中单净流入 - 净额', 0)) if not pd.isna(row.get('中单净流入 - 净额')) else None,
                    medium_order_net_inflow_ratio=float(row.get('中单净流入 - 净占比', 0)) if not pd.isna(row.get('中单净流入 - 净占比')) else None,
                    small_order_net_inflow=float(row.get('小单净流入 - 净额', 0)) if not pd.isna(row.get('小单净流入 - 净额')) else None,
                    small_order_net_inflow_ratio=float(row.get('小单净流入 - 净占比', 0)) if not pd.isna(row.get('小单净流入 - 净占比')) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {stock} 个股资金流数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取个股资金流数据失败：stock={stock}, market={market}, error={e}")
            return []
    
    # ========== 东方财富 - 个股资金流排名 ==========
    
    async def get_stock_individual_fund_flow_rank(self, indicator: str = "今日") -> List[StockIndividualFundFlowRank]:
        """获取东方财富 - 个股资金流排名数据
        
        Args:
            indicator: 排行指标，choice of {"今日", "3 日", "5 日", "10 日"}
        
        Returns:
            StockIndividualFundFlowRank 列表，包含个股资金流排名数据（15 个字段）：
            - 基本信息：serial_number, code, name, latest_price
            - 涨跌幅：change_pct（根据 indicator 不同，字段名略有差异）
            - 主力流入：main_net_inflow, main_net_inflow_ratio
            - 超大单：super_order_net_inflow, super_order_net_inflow_ratio
            - 大单：big_order_net_inflow, big_order_net_inflow_ratio
            - 中单：medium_order_net_inflow, medium_order_net_inflow_ratio
            - 小单：small_order_net_inflow, small_order_net_inflow_ratio
        """
        try:
            cache_key = f"stock_individual_fund_flow_rank_{indicator}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5 分钟缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            data = ak.stock_individual_fund_flow_rank(indicator=indicator)
            
            result = []
            for _, row in data.iterrows():
                # 根据 indicator 获取涨跌幅字段名
                if indicator == "今日":
                    change_pct_field = '今日涨跌幅'
                    main_net_field = '今日主力净流入 - 净额'
                    main_net_ratio_field = '今日主力净流入 - 净占比'
                    super_order_field = '今日超大单净流入 - 净额'
                    super_order_ratio_field = '今日超大单净流入 - 净占比'
                    big_order_field = '今日大单净流入 - 净额'
                    big_order_ratio_field = '今日大单净流入 - 净占比'
                    medium_order_field = '今日中单净流入 - 净额'
                    medium_order_ratio_field = '今日中单净流入 - 净占比'
                    small_order_field = '今日小单净流入 - 净额'
                    small_order_ratio_field = '今日小单净流入 - 净占比'
                elif indicator == "3 日":
                    change_pct_field = '3 日涨跌幅'
                    main_net_field = '3 日主力净流入 - 净额'
                    main_net_ratio_field = '3 日主力净流入 - 净占比'
                    super_order_field = '3 日超大单净流入 - 净额'
                    super_order_ratio_field = '3 日超大单净流入 - 净占比'
                    big_order_field = '3 日大单净流入 - 净额'
                    big_order_ratio_field = '3 日大单净流入 - 净占比'
                    medium_order_field = '3 日中单净流入 - 净额'
                    medium_order_ratio_field = '3 日中单净流入 - 净占比'
                    small_order_field = '3 日小单净流入 - 净额'
                    small_order_ratio_field = '3 日小单净流入 - 净占比'
                elif indicator == "5 日":
                    change_pct_field = '5 日涨跌幅'
                    main_net_field = '5 日主力净流入 - 净额'
                    main_net_ratio_field = '5 日主力净流入 - 净占比'
                    super_order_field = '5 日超大单净流入 - 净额'
                    super_order_ratio_field = '5 日超大单净流入 - 净占比'
                    big_order_field = '5 日大单净流入 - 净额'
                    big_order_ratio_field = '5 日大单净流入 - 净占比'
                    medium_order_field = '5 日中单净流入 - 净额'
                    medium_order_ratio_field = '5 日中单净流入 - 净占比'
                    small_order_field = '5 日小单净流入 - 净额'
                    small_order_ratio_field = '5 日小单净流入 - 净占比'
                else:  # 10 日
                    change_pct_field = '10 日涨跌幅'
                    main_net_field = '10 日主力净流入 - 净额'
                    main_net_ratio_field = '10 日主力净流入 - 净占比'
                    super_order_field = '10 日超大单净流入 - 净额'
                    super_order_ratio_field = '10 日超大单净流入 - 净占比'
                    big_order_field = '10 日大单净流入 - 净额'
                    big_order_ratio_field = '10 日大单净流入 - 净占比'
                    medium_order_field = '10 日中单净流入 - 净额'
                    medium_order_ratio_field = '10 日中单净流入 - 净占比'
                    small_order_field = '10 日小单净流入 - 净额'
                    small_order_ratio_field = '10 日小单净流入 - 净占比'
                
                item = StockIndividualFundFlowRank(
                    serial_number=int(row.get('序号', 0)) if not pd.isna(row.get('序号')) else None,
                    code=str(row.get('代码', '')) if not pd.isna(row.get('代码')) else '',
                    name=str(row.get('名称', '')) if not pd.isna(row.get('名称')) else '',
                    latest_price=float(row.get('最新价', 0)) if not pd.isna(row.get('最新价')) else None,
                    change_pct=float(row.get(change_pct_field, 0)) if not pd.isna(row.get(change_pct_field)) else None,
                    main_net_inflow=float(row.get(main_net_field, 0)) if not pd.isna(row.get(main_net_field)) else None,
                    main_net_inflow_ratio=float(row.get(main_net_ratio_field, 0)) if not pd.isna(row.get(main_net_ratio_field)) else None,
                    super_order_net_inflow=float(row.get(super_order_field, 0)) if not pd.isna(row.get(super_order_field)) else None,
                    super_order_net_inflow_ratio=float(row.get(super_order_ratio_field, 0)) if not pd.isna(row.get(super_order_ratio_field)) else None,
                    big_order_net_inflow=float(row.get(big_order_field, 0)) if not pd.isna(row.get(big_order_field)) else None,
                    big_order_net_inflow_ratio=float(row.get(big_order_ratio_field, 0)) if not pd.isna(row.get(big_order_ratio_field)) else None,
                    medium_order_net_inflow=float(row.get(medium_order_field, 0)) if not pd.isna(row.get(medium_order_field)) else None,
                    medium_order_net_inflow_ratio=float(row.get(medium_order_ratio_field, 0)) if not pd.isna(row.get(medium_order_ratio_field)) else None,
                    small_order_net_inflow=float(row.get(small_order_field, 0)) if not pd.isna(row.get(small_order_field)) else None,
                    small_order_net_inflow_ratio=float(row.get(small_order_ratio_field, 0)) if not pd.isna(row.get(small_order_ratio_field)) else None,
                )
                result.append(item)
            
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {indicator} 个股资金流排名数据，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取个股资金流排名数据失败：indicator={indicator}, error={e}")
            return []
    
    # ========== 东方财富 - 美股历史行情 ==========
    
    async def get_stock_us_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAHist]:
        """获取东方财富 - 美股历史行情数据
        
        Args:
            symbol: 美股代码（如 '106.TTE'）
            period: 周期，choice of {'daily', 'weekly', 'monthly'}，默认 'daily'
            start_date: 开始日期（格式 'YYYYMMDD'），默认不指定
            end_date: 结束日期（格式 'YYYYMMDD'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
        
        Returns:
            StockZhAHist 列表，包含指定美股的历史行情数据（11 个字段）
            注意：成交量单位为股，币种为美元
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_us_hist_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_us_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "19700101",
                end_date=end_date if end_date else "20991231",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    code=symbol,  # 美股代码
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 美股历史行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取美股历史行情失败：symbol={symbol}, error={e}")
            return []
    
    # ========== 东方财富 - 港股历史行情 ==========
    
    async def get_stock_hk_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[StockZhAHist]:
        """获取东方财富 - 港股历史行情数据
        
        Args:
            symbol: 港股代码（如 '00593'）
            period: 周期，choice of {'daily', 'weekly', 'monthly'}，默认 'daily'
            start_date: 开始日期（格式 'YYYYMMDD'），默认不指定
            end_date: 结束日期（格式 'YYYYMMDD'），默认不指定
            adjust: 复权类型，choice of {'', 'qfq', 'hfq'}，默认 ''（不复权）
        
        Returns:
            StockZhAHist 列表，包含指定港股的历史行情数据（11 个字段）
            注意：成交量单位为股，币种为港元
        """
        try:
            # 构建缓存 key
            cache_key = f"stock_hk_hist_{symbol}_{period}_{start_date}_{end_date}_{adjust}"
            if self._is_cache_valid(cache_key, ttl=3600):  # 1 小时缓存
                return self._cache[cache_key]
            
            await self._rate_limit()
            
            # 调用 AkShare API
            data = ak.stock_hk_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "19700101",
                end_date=end_date if end_date else "22220101",
                adjust=adjust
            )
            
            result = []
            for _, row in data.iterrows():
                item = StockZhAHist(
                    date=str(row.get('日期', '')) if not pd.isna(row.get('日期')) else '',
                    code=symbol,  # 港股代码
                    open=float(row.get('开盘', 0)) if not pd.isna(row.get('开盘')) else None,
                    close=float(row.get('收盘', 0)) if not pd.isna(row.get('收盘')) else None,
                    high=float(row.get('最高', 0)) if not pd.isna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if not pd.isna(row.get('最低')) else None,
                    volume=float(row.get('成交量', 0)) if not pd.isna(row.get('成交量')) else None,
                    turnover=float(row.get('成交额', 0)) if not pd.isna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if not pd.isna(row.get('振幅')) else None,
                    change_pct=float(row.get('涨跌幅', 0)) if not pd.isna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if not pd.isna(row.get('涨跌额')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if not pd.isna(row.get('换手率')) else None,
                )
                result.append(item)
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.info(f"成功获取 {symbol} 港股历史行情，共 {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"AkShare 获取港股历史行情失败：symbol={symbol}, error={e}")
            return []
