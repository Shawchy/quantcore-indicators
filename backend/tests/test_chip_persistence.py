"""
测试筹码数据持久化
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.akshare_adapter import AkShareAdapter
from app.services.chip_service import ChipService
from app.storage.sqlite import get_session, ChipData as ChipDataDB
from sqlalchemy import select


async def test_chip_data_persistence():
    """测试筹码数据持久化"""
    
    test_code = "300981"
    
    print(f"\n{'='*60}")
    print(f"测试筹码数据持久化 - {test_code}")
    print(f"{'='*60}\n")
    
    # 1. 从数据源获取数据
    print("1️⃣  从数据源获取筹码数据...")
    adapter = AkShareAdapter()
    chip_data = await adapter.get_chip_data(test_code)
    
    if not chip_data:
        print(f"❌ 获取筹码数据失败：{test_code}")
        return
    
    print(f"✅ 获取成功：{len(chip_data)} 条")
    print(f"   第一条数据:")
    print(f"   - 代码：{chip_data[0].code}")
    print(f"   - 日期：{chip_data[0].date}")
    print(f"   - 股东户数：{chip_data[0].shareholder_count}")
    print(f"   - 户均持股：{chip_data[0].avg_shares_per_holder}\n")
    
    # 2. 保存到数据库
    print("2️⃣  保存到数据库...")
    service = ChipService()
    
    try:
        await service._save_chip_data(test_code, chip_data)
        print(f"✅ 保存成功\n")
    except Exception as e:
        print(f"❌ 保存失败：{e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 从数据库读取
    print("3️⃣  从数据库读取...")
    async with get_session() as session:
        query = select(ChipDataDB).where(ChipDataDB.code == test_code)
        result = await session.execute(query)
        db_data = result.scalars().all()
    
    if not db_data:
        print(f"❌ 数据库中没有数据")
        return
    
    print(f"✅ 读取成功：{len(db_data)} 条")
    print(f"   第一条数据:")
    print(f"   - 代码：{db_data[0].code}")
    print(f"   - 日期：{db_data[0].date}")
    print(f"   - 股东户数：{db_data[0].shareholder_count}")
    print(f"   - 户均持股：{db_data[0].avg_shares_per_holder}\n")
    
    # 4. 验证数据一致性
    print("4️⃣  验证数据一致性...")
    
    # 按日期排序
    chip_data_sorted = sorted(chip_data, key=lambda x: x.date)
    db_data_sorted = sorted(db_data, key=lambda x: x.date)
    
    # 比较第一条
    if (chip_data_sorted[0].date == db_data_sorted[0].date and
        abs(chip_data_sorted[0].shareholder_count - db_data_sorted[0].shareholder_count) < 0.01):
        print(f"✅ 数据一致\n")
    else:
        print(f"❌ 数据不一致")
        print(f"   原始数据：{chip_data_sorted[0]}")
        print(f"   数据库数据：{db_data_sorted[0]}\n")
    
    # 5. 测试重复保存（去重）
    print("5️⃣  测试重复保存（去重）...")
    await service._save_chip_data(test_code, chip_data)
    print(f"✅ 重复保存完成（应该没有新数据插入）\n")
    
    # 6. 再次从数据库读取
    print("6️⃣  再次从数据库读取...")
    async with get_session() as session:
        query = select(ChipDataDB).where(ChipDataDB.code == test_code)
        result = await session.execute(query)
        db_data2 = result.scalars().all()
    
    print(f"✅ 读取成功：{len(db_data2)} 条")
    print(f"   数据条数：{len(db_data)} -> {len(db_data2)}")
    
    if len(db_data) == len(db_data2):
        print(f"✅ 去重成功，没有重复数据\n")
    else:
        print(f"❌ 去重失败，出现重复数据\n")
    
    print(f"{'='*60}")
    print(f"测试完成！")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_chip_data_persistence())
