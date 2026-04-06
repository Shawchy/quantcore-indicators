"""
测试 efinance 接口可用性（2026-04-05）
"""
try:
    import efinance as ef
    from loguru import logger
    import time

    def test_interface(name, func, **kwargs):
        """测试单个接口"""
        logger.info(f"\n测试：{name}")
        start = time.time()
        try:
            result = func(**kwargs)
            elapsed = time.time() - start
            if result is not None and hasattr(result, '__len__') and len(result) > 0:
                logger.success(f"✅ {name} - 成功（{elapsed:.2f}秒，{len(result)}条）")
                if hasattr(result, 'columns'):
                    logger.info(f"列名：{list(result.columns)[:10]}")
                return True
            else:
                logger.warning(f"⚠️ {name} - 空数据（{elapsed:.2f}秒）")
                return False
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"❌ {name} - 失败（{elapsed:.2f}秒）: {str(e)[:100]}")
            return False

    if __name__ == '__main__':
        logger.info("="*60)
        logger.info("2026-04-05 efinance 接口可用性测试")
        logger.info("="*60)
        
        results = {}
        
        # 实时行情
        logger.info("\n【实时行情】")
        results['ef_spot'] = test_interface(
            "stock.get_realtime_quotes",
            ef.stock.get_realtime_quotes,
            code='000001'
        )
        
        # 批量实时行情
        results['ef_spot_multi'] = test_interface(
            "stock.get_realtime_quotes(多只)",
            ef.stock.get_realtime_quotes,
            code=['000001', '000002', '600000']
        )
        
        # 股票列表
        logger.info("\n【股票列表】")
        results['ef_all'] = test_interface(
            "stock.get_all_stock_info",
            ef.stock.get_all_stock_info
        )
        
        # 个股信息
        logger.info("\n【个股信息】")
        results['ef_info'] = test_interface(
            "stock.get_stock_basic_info",
            ef.stock.get_stock_basic_info,
            code='000001'
        )
        
        # 历史行情
        logger.info("\n【历史行情】")
        results['ef_hist'] = test_interface(
            "stock.get_quote_history",
            ef.stock.get_quote_history,
            code='000001',
            start='20260101',
            end='20260405'
        )
        
        # 总结
        logger.info("\n" + "="*60)
        logger.info("测试结果总结")
        logger.info("="*60)
        
        success = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, ok in results.items():
            status = "✅" if ok else "❌"
            logger.info(f"{status} {name}")
        
        logger.info(f"\n总计：{success}/{total} 可用")
        
        if success == total:
            logger.success("\n✅ efinance 所有接口可用，建议切换到 efinance！")
        
except ImportError:
    print("efinance 未安装，请先安装：pip install efinance")
