"""
数据迁移测试脚本

测试数据分类存储目录结构
"""
from pathlib import Path
from loguru import logger


def test_directory_structure():
    """测试目录结构"""
    base_dir = Path("./data")
    
    # 检查一级分类目录
    level1_dirs = ["stock", "fund", "market", "strategy"]
    
    logger.info("=" * 60)
    logger.info("检查数据分类目录结构")
    logger.info("=" * 60)
    
    for dir_name in level1_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            logger.info(f"✅ 一级目录存在: {dir_name}")
            
            # 检查二级目录
            for subdir in dir_path.iterdir():
                if subdir.is_dir():
                    logger.info(f"  ✅ 二级目录: {subdir.name}")
        else:
            logger.warning(f"❌ 一级目录不存在: {dir_name}")
    
    logger.info("=" * 60)
    
    # 检查现有 Parquet 文件
    old_parquet_dir = base_dir / "parquet"
    
    if old_parquet_dir.exists():
        logger.info("检查现有 Parquet 文件:")
        
        # 统计文件数量
        parquet_files = list(old_parquet_dir.rglob("*.parquet"))
        logger.info(f"  总文件数: {len(parquet_files)}")
        
        # 按类型分类
        kline_files = [f for f in parquet_files if "kline" in str(f)]
        fund_files = [f for f in parquet_files if "fund" in str(f)]
        index_files = [f for f in parquet_files if "index" in str(f)]
        
        logger.info(f"  K 线文件: {len(kline_files)}")
        logger.info(f"  基金文件: {len(fund_files)}")
        logger.info(f"  指数文件: {len(index_files)}")
        
        # 显示部分文件
        if parquet_files:
            logger.info("  示例文件:")
            for f in parquet_files[:5]:
                logger.info(f"    - {f.relative_to(base_dir)}")
    else:
        logger.warning("未找到现有 Parquet 目录")
    
    logger.info("=" * 60)
    logger.info("目录结构检查完成！")


if __name__ == "__main__":
    test_directory_structure()
