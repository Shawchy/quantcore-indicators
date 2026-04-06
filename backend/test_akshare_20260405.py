"""
测试 akshare 各接口可用性（2026-04-05）
"""
import akshare as ak
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
    logger.info("2026-04-05 akshare 接口可用性测试")
    logger.info("="*60)
    
    results = {}
    
    # 东方财富接口（预期失效）
    logger.info("\n【东方财富接口】")
    results['em_stock_list'] = test_interface(
        "stock_info_a_code_name",
        ak.stock_info_a_code_name
    )
    results['em_spot'] = test_interface(
        "stock_zh_a_spot_em",
        ak.stock_zh_a_spot_em
    )
    results['em_info'] = test_interface(
        "stock_individual_info_em(000001)",
        ak.stock_individual_info_em,
        symbol="000001"
    )
    
    # 新浪接口
    logger.info("\n【新浪接口】")
    results['sina_spot'] = test_interface(
        "stock_zh_a_spot",
        ak.stock_zh_a_spot
    )
    
    # 历史行情（应该可用）
    logger.info("\n【历史行情接口】")
    results['hist_000001'] = test_interface(
        "stock_zh_a_hist(000001)",
        ak.stock_zh_a_hist,
        symbol="000001",
        period="daily",
        start_date="20260101",
        end_date="20260405",
        adjust="qfq"
    )
    
    # 指数行情
    logger.info("\n【指数接口】")
    results['index_sina'] = test_interface(
        "stock_zh_index_spot_sina",
        ak.stock_zh_index_spot_sina
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
    
    if success < total / 2:
        logger.warning("\n⚠️ 大量接口失效，建议：")
        logger.warning("  1. 检查网络连接")
        logger.warning("  2. 检查 akshare 版本")
        logger.warning("  3. 考虑使用其他数据源（如 efinance）")
