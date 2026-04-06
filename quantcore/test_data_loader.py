"""数据加载器测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore.data import CSVLoader, DataCache, create_data_loader
from quantcore.core import Bar
from datetime import datetime
import tempfile
import pandas as pd


def test_csv_loader():
    """测试 CSV 加载器"""
    print("=" * 60)
    print("测试 CSV 加载器")
    print("=" * 60)
    
    # 创建临时 CSV 文件
    csv_content = """date,open,high,low,close,volume,turnover
2024-01-02,10.0,10.5,9.8,10.3,1000000,10300000.0
2024-01-03,10.3,10.8,10.2,10.6,1200000,12720000.0
2024-01-04,10.6,11.0,10.5,10.8,1100000,11880000.0
2024-01-05,10.8,11.2,10.7,11.0,1300000,14300000.0
2024-01-08,11.0,11.5,10.9,11.3,1400000,15820000.0
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file = f.name
    
    try:
        # 测试 CSV 加载
        loader = CSVLoader()
        bars = loader.load("SH.600000", file_path=temp_file)
        
        print(f"✓ 成功加载 {len(bars)} 条数据")
        assert len(bars) == 5, f"Expected 5 bars, got {len(bars)}"
        
        # 验证数据
        bar = bars[0]
        print(f"✓ 第一条数据：{bar.timestamp}, 开盘：{bar.open}, 收盘：{bar.close}")
        assert bar.open == 10.0
        assert bar.close == 10.3
        assert bar.volume == 1000000
        
        # 测试日期过滤
        bars_filtered = loader.load(
            "SH.600000", 
            start_date="2024-01-03", 
            end_date="2024-01-05",
            file_path=temp_file
        )
        print(f"✓ 过滤后数据：{len(bars_filtered)} 条")
        assert len(bars_filtered) == 3
        
        print("\n✓ CSV 加载器测试通过！")
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)


def test_csv_loader_alternative_formats():
    """测试 CSV 加载器的不同格式"""
    print("\n" + "=" * 60)
    print("测试 CSV 格式兼容性")
    print("=" * 60)
    
    # 测试不同的列名格式
    csv_content = """Date,Open,High,Low,Close,Vol,Amount
2024-01-02,10.0,10.5,9.8,10.3,1000000,10300000.0
2024-01-03,10.3,10.8,10.2,10.6,1200000,12720000.0
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file = f.name
    
    try:
        loader = CSVLoader()
        bars = loader.load("SH.600000", file_path=temp_file)
        
        print(f"✓ 成功识别不同列名格式：{len(bars)} 条数据")
        assert len(bars) == 2
        
        print("\n✓ 格式兼容性测试通过！")
        
    finally:
        os.unlink(temp_file)


def test_data_cache():
    """测试数据缓存"""
    print("\n" + "=" * 60)
    print("测试数据缓存")
    print("=" * 60)
    
    cache = DataCache(max_size=3)
    
    # 创建测试数据
    bars1 = [Bar(timestamp=datetime(2024, 1, 1), symbol="SH.600000", open=10.0, high=10.5, 
                 low=9.8, close=10.3, volume=1000000, turnover=10300000.0)]
    bars2 = [Bar(timestamp=datetime(2024, 1, 1), symbol="SH.600001", open=20.0, high=20.5,
                 low=19.8, close=20.3, volume=2000000, turnover=40600000.0)]
    bars3 = [Bar(timestamp=datetime(2024, 1, 2), symbol="SH.600000", open=10.3, high=10.8,
                 low=10.2, close=10.6, volume=1200000, turnover=12720000.0)]
    bars4 = [Bar(timestamp=datetime(2024, 1, 2), symbol="SH.600001", open=20.3, high=20.8,
                 low=20.2, close=20.6, volume=2200000, turnover=90200000.0)]
    
    # 测试缓存添加
    cache.put("key1", bars1)
    cache.put("key2", bars2)
    cache.put("key3", bars3)
    print(f"✓ 缓存大小：{len(cache.cache)}")
    assert len(cache.cache) == 3
    
    # 测试缓存获取
    cached = cache.get("key1")
    print(f"✓ 缓存命中：{len(cached)} 条数据")
    assert cached is not None
    assert len(cached) == 1
    
    # 测试缓存淘汰（LRU）
    # 访问 key2 和 key3，使它们成为最近使用的
    cache.get("key2")
    cache.get("key3")
    # 现在访问顺序是：key1, key2, key3
    cache.put("key4", bars4)  # 应该淘汰最久未使用的 key1
    print(f"✓ 缓存淘汰后大小：{len(cache.cache)}")
    assert len(cache.cache) == 3
    # key1 应该被淘汰
    assert cache.get("key1") is None
    assert cache.get("key4") is not None
    
    # 测试缓存清空
    cache.clear()
    print(f"✓ 清空后缓存大小：{len(cache.cache)}")
    assert len(cache.cache) == 0
    
    print("\n✓ 数据缓存测试通过！")


def test_create_data_loader():
    """测试数据加载器创建"""
    print("\n" + "=" * 60)
    print("测试数据加载器工厂函数")
    print("=" * 60)
    
    # 测试创建带缓存的加载器
    loader = create_data_loader(use_cache=True, cache_size=100)
    print(f"✓ 创建带缓存的加载器：{type(loader).__name__}")
    assert isinstance(loader, type(create_data_loader(use_cache=True)))
    
    # 测试创建不带缓存的加载器
    loader_no_cache = create_data_loader(use_cache=False)
    print(f"✓ 创建不带缓存的加载器：{type(loader_no_cache).__name__}")
    
    print("\n✓ 工厂函数测试通过！")


def test_batch_load():
    """测试批量加载"""
    print("\n" + "=" * 60)
    print("测试批量加载")
    print("=" * 60)
    
    # 创建多个临时 CSV 文件
    csv_content1 = """date,open,high,low,close,volume
2024-01-02,10.0,10.5,9.8,10.3,1000000
2024-01-03,10.3,10.8,10.2,10.6,1200000
"""
    csv_content2 = """date,open,high,low,close,volume
2024-01-02,20.0,20.5,19.8,20.3,2000000
2024-01-03,20.3,20.8,20.2,20.6,2200000
"""
    
    files = {}
    temp_files = []
    
    for i, content in enumerate([csv_content1, csv_content2]):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_files.append(f.name)
            files[f"SH.60000{i}"] = f.name
    
    try:
        loader = CSVLoader()
        result = loader.load_multiple(files)
        
        print(f"✓ 批量加载 {len(result)} 个证券数据")
        assert len(result) == 2
        assert len(result["SH.600000"]) == 2
        assert len(result["SH.600001"]) == 2
        
        print("\n✓ 批量加载测试通过！")
        
    finally:
        for temp_file in temp_files:
            os.unlink(temp_file)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("QuantCore 数据加载器测试")
    print("=" * 60)
    
    test_csv_loader()
    test_csv_loader_alternative_formats()
    test_data_cache()
    test_create_data_loader()
    test_batch_load()
    
    print("\n" + "=" * 60)
    print("✓✓✓ 所有数据加载器测试通过！")
    print("=" * 60)
