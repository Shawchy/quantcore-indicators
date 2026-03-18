"""
测试 efinance 返回的资产配置数据格式
"""
import efinance as ef

# 测试获取资产配置
print("测试 efinance.fund.get_types_percentage")
print("=" * 80)

try:
    # 不传 dates 参数
    print("\n1. 测试不传 dates 参数：")
    df = ef.fund.get_types_percentage('005827')
    print(f"   数据类型：{type(df)}")
    if df is not None:
        print(f"   是否有 empty 属性：{hasattr(df, 'empty')}")
        if hasattr(df, 'empty'):
            print(f"   df.empty: {df.empty}")
        if not getattr(df, 'empty', True):
            print(f"   行数：{len(df)}")
            print(f"   列名：{list(df.columns)}")
            print(f"   数据预览：\n{df.head()}")
    else:
        print("   返回 None")
    
    # 传 dates 参数
    print("\n2. 测试传 dates 参数：")
    df = ef.fund.get_types_percentage('005827', dates='2021-12-31')
    print(f"   数据类型：{type(df)}")
    if df is not None and not getattr(df, 'empty', True):
        print(f"   行数：{len(df)}")
        print(f"   列名：{list(df.columns)}")
        print(f"   数据预览：\n{df.head()}")
    
    # 获取公开日期
    print("\n3. 获取基金公开持仓日期：")
    try:
        public_dates = ef.fund.get_public_dates('005827')
        print(f"   公开日期列表：{public_dates}")
        if public_dates and len(public_dates) > 0:
            print(f"   前两个日期：{public_dates[:2]}")
            
            # 使用公开日期测试
            if len(public_dates) >= 2:
                print("\n4. 使用公开日期测试：")
                df = ef.fund.get_types_percentage('005827', dates=public_dates[:2])
                print(f"   数据类型：{type(df)}")
                if df is not None and not getattr(df, 'empty', True):
                    print(f"   行数：{len(df)}")
                    print(f"   列名：{list(df.columns)}")
                    print(f"   数据预览：\n{df}")
    except Exception as e:
        print(f"   获取公开日期失败：{e}")
    
except Exception as e:
    print(f"测试失败：{e}")
    import traceback
    traceback.print_exc()
