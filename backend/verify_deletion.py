"""
验证旧 data 目录已删除
"""
from pathlib import Path

print("=" * 70)
print("验证旧 data 目录已删除")
print("=" * 70)

# 检查路径
old_data = Path("D:/Project/Quant/data")
old_data_backup = Path("D:/Project/Quant/data_backup")
backend_data = Path("D:/Project/Quant/backend/data")

print(f"\n1️⃣ 检查旧 data 目录")
if old_data.exists():
    print(f"   ❌ 旧 data 目录仍然存在：{old_data}")
else:
    print(f"   ✅ 旧 data 目录已删除")

print(f"\n2️⃣ 检查备份目录")
if old_data_backup.exists():
    print(f"   ⚠️  备份目录存在：{old_data_backup}")
    print(f"      可以手动删除：Remove-Item '{old_data_backup}' -Recurse -Force")
else:
    print(f"   ℹ️  备份目录不存在")

print(f"\n3️⃣ 检查后端 data 目录")
if backend_data.exists():
    print(f"   ✅ 后端 data 目录正常：{backend_data}")
    
    db_file = backend_data / "sqlite" / "quant.db"
    if db_file.exists():
        print(f"   ✅ 数据库文件存在：{db_file}")
        print(f"      大小：{db_file.stat().st_size:,} 字节")
    else:
        print(f"   ❌ 数据库文件不存在")
else:
    print(f"   ❌ 后端 data 目录不存在")

print(f"\n4️⃣ 检查项目目录结构")
project_root = Path("D:/Project/Quant")
dirs = [d.name for d in project_root.iterdir() if d.is_dir()]
print(f"   目录列表：{', '.join(sorted(dirs))}")

if 'data' in dirs:
    print(f"   ❌ 发现 data 目录")
elif 'data_backup' in dirs:
    print(f"   ⚠️  发现 data_backup 目录（备份）")
else:
    print(f"   ✅ 没有 data 目录")

print(f"\n✅ 验证完成")
print(f"\n💡 下一步:")
print(f"   1. 重启后端：cd backend && python -m uvicorn app.main:app --reload")
print(f"   2. 测试 API 是否正常")
print(f"   3. 如果一切正常，可以删除备份目录")
print(f"   4. 更新 README 说明数据路径")

print("=" * 70)
