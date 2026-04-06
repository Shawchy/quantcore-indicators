"""
测试东方财富接口可用性
验证哪些接口被反爬
"""
import akshare as ak
from loguru import logger
import time

def test_interface(name, func, **kwargs):
    """测试单个接口"""
    logger.info(f"\n{'='*60}")
    logger.info(f"测试接口：{name}")
    logger.info(f"{'='*60}")
    
    start = time.time()
    try:
        result = func(**kwargs)
        elapsed = time.time() - start
        if result is not None and (hasattr(result, '__len__') and len(result) > 0 or not hasattr(result, '__len__')):
            logger.success(f"✅ {name} - 成功（耗时：{elapsed:.2f}秒）")
            if hasattr(result, 'head'):
                logger.info(f"数据形状：{result.shape}")
                logger.info(f"前 3 行:\n{result.head(3)}")
            return True
        else:
            logger.warning(f"⚠️ {name} - 返回空数据（耗时：{elapsed:.2f}秒）")
            return False
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"❌ {name} - 失败（耗时：{elapsed:.2f}秒）: {e}")
        return False

if __name__ == '__main__':
    logger.info("开始测试东方财富接口可用性...")
    
    results = {}
    
    # 1. 股票列表接口（推荐）
    results['stock_info_a_code_name'] = test_interface(
        "stock_info_a_code_name (股票列表)",
        ak.stock_info_a_code_name
    )
    
    # 2. 实时行情接口（被反爬）
    results['stock_zh_a_spot_em'] = test_interface(
        "stock_zh_a_spot_em (实时行情)",
        ak.stock_zh_a_spot_em
    )
    
    # 3. 个股详细信息（应该可用）
    results['stock_individual_info_em_000001'] = test_interface(
        "stock_individual_info_em (000001)",
        ak.stock_individual_info_em,
        symbol="000001"
    )
    
    # 4. 新浪 A 股实时行情（批量）
    results['stock_zh_a_spot'] = test_interface(
        "stock_zh_a_spot (新浪批量)",
        ak.stock_zh_a_spot
    )
    
    # 5. 测试个股实时行情（新浪）
    def fetch_single_sina():
        df = ak.stock_zh_a_spot()
        return df[df['code'] == '000001']
    
    results['stock_zh_a_spot_single'] = test_interface(
        "stock_zh_a_spot 过滤单只 (000001)",
        fetch_single_sina
    )
    
    # 6. 测试新浪指数行情
    results['stock_zh_index_spot_sina'] = test_interface(
        "stock_zh_index_spot_sina (上证指数)",
        ak.stock_zh_index_spot_sina
    )
    
    # 总结
    logger.info(f"\n{'='*60}")
    logger.info("测试总结")
    logger.info(f"{'='*60}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\n总计：{success_count}/{total_count} 接口可用")
    
    if not results['stock_zh_a_spot_em']:
        logger.warning("\n⚠️ stock_zh_a_spot_em 已失效，需要替换为其他接口")
        logger.info("推荐替代方案：")
        logger.info("  1. stock_sina_a_spot (新浪行情，支持批量)")
        logger.info("  2. 使用 stock_info_a_code_name 获取列表 + stock_individual_spot_em 获取详情")
