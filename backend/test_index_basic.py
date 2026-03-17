"""
测试 Tushare index_basic 接口

演示如何获取指数基础信息
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager


async def test_index_basic():
    """测试指数基础信息接口"""
    
    print("\n" + "=" * 70)
    print("Tushare index_basic 接口测试")
    print("=" * 70)
    
    # 初始化数据源
    await data_source_manager.initialize()
    
    # 测试 1：获取所有申万指数
    print("\n1️⃣ 获取所有申万指数 (market='SW')...")
    try:
        sw_indexes = await data_source_manager.get_index_basic(market='SW')
        print(f"✅ 获取到 {len(sw_indexes)} 条申万指数")
        
        if sw_indexes:
            print("\n前 5 条数据样例：")
            for i, item in enumerate(sw_indexes[:5], 1):
                print(f"\n{i}. {item['name']} ({item['ts_code']})")
                print(f"   市场：{item['market']}")
                print(f"   发布方：{item['publisher']}")
                print(f"   类别：{item['category']}")
                print(f"   基期：{item['base_date']}")
                print(f"   基点：{item['base_point']}")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 测试 2：获取中证指数
    print("\n\n2️⃣ 获取中证指数 (market='CSI')...")
    try:
        csi_indexes = await data_source_manager.get_index_basic(market='CSI')
        print(f"✅ 获取到 {len(csi_indexes)} 条中证指数")
        
        if csi_indexes:
            print("\n前 5 条数据样例：")
            for i, item in enumerate(csi_indexes[:5], 1):
                print(f"\n{i}. {item['name']} ({item['ts_code']})")
                print(f"   全称：{item['fullname']}")
                print(f"   类别：{item['category']}")
                print(f"   基期：{item['base_date']}")
                print(f"   基点：{item['base_point']}")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 测试 3：获取上证指数
    print("\n\n3️⃣ 获取上证指数 (ts_code='000001.SH')...")
    try:
        sh_index = await data_source_manager.get_index_basic(ts_code='000001.SH')
        if sh_index:
            item = sh_index[0]
            print(f"✅ 获取成功：")
            print(f"   代码：{item['ts_code']}")
            print(f"   名称：{item['name']}")
            print(f"   全称：{item['fullname']}")
            print(f"   市场：{item['market']}")
            print(f"   发布方：{item['publisher']}")
            print(f"   类别：{item['category']}")
            print(f"   基期：{item['base_date']}")
            print(f"   基点：{item['base_point']}")
            print(f"   上市日期：{item['list_date']}")
            print(f"   加权方式：{item['weight_rule']}")
            print(f"   描述：{item['desc']}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 测试 4：获取沪深 300
    print("\n\n4️⃣ 获取沪深 300 (ts_code='000300.SH')...")
    try:
        hs300 = await data_source_manager.get_index_basic(ts_code='000300.SH')
        if hs300:
            item = hs300[0]
            print(f"✅ 获取成功：")
            print(f"   代码：{item['ts_code']}")
            print(f"   名称：{item['name']}")
            print(f"   全称：{item['fullname']}")
            print(f"   市场：{item['market']}")
            print(f"   类别：{item['category']}")
            print(f"   基期：{item['base_date']}")
            print(f"   基点：{item['base_point']}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 测试 5：按名称搜索
    print("\n\n5️⃣ 按名称搜索指数 (name='医药')...")
    try:
        pharma_indexes = await data_source_manager.get_index_basic(name='医药')
        print(f"✅ 获取到 {len(pharma_indexes)} 条医药相关指数")
        
        if pharma_indexes:
            for i, item in enumerate(pharma_indexes[:5], 1):
                print(f"\n{i}. {item['name']} ({item['ts_code']})")
                print(f"   全称：{item['fullname']}")
                print(f"   市场：{item['market']}")
                print(f"   类别：{item['category']}")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 测试 6：按类别筛选
    print("\n\n6️⃣ 获取行业指数 (category='行业指数')...")
    try:
        industry_indexes = await data_source_manager.get_index_basic(category='行业指数')
        print(f"✅ 获取到 {len(industry_indexes)} 条行业指数")
        
        if industry_indexes:
            print("\n前 5 条数据样例：")
            for i, item in enumerate(industry_indexes[:5], 1):
                print(f"\n{i}. {item['name']} ({item['ts_code']})")
                print(f"   市场：{item['market']}")
                print(f"   发布方：{item['publisher']}")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
    
    # 数据字段说明
    print("\n\n" + "=" * 70)
    print("数据字段说明")
    print("=" * 70)
    print("""
返回字段：
- ts_code: TS 代码（如：000001.SH）
- name: 简称（如：上证指数）
- fullname: 指数全称（如：上证综合指数）
- market: 市场（SSE/SZSE/CSI/MSCI/SW/CICC/OTH）
- publisher: 发布方（如：上交所、中证指数）
- index_type: 指数风格
- category: 指数类别（如：行业指数、规模指数）
- base_date: 基期（如：19901219）
- base_point: 基点（如：100.0）
- list_date: 发布日期
- weight_rule: 加权方式（如：市值加权）
- desc: 描述
- exp_date: 终止日期

市场代码说明：
- MSCI: MSCI 指数
- CSI: 中证指数
- SSE: 上交所指数
- SZSE: 深交所指数
- CICC: 中金指数
- SW: 申万指数
- OTH: 其他指数
    """)
    
    await data_source_manager.close()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_index_basic())
