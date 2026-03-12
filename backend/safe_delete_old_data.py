"""
安全删除旧 data 目录的脚本
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("安全删除旧 data 目录")
print("=" * 70)

# 定义路径
old_data_dir = Path("D:/Project/Quant/data")
backend_data_dir = Path("D:/Project/Quant/backend/data")

print(f"\n1️⃣ 检查路径")
print(f"   旧 data 目录：{old_data_dir}")
print(f"   后端 data 目录：{backend_data_dir}")

# 检查后端 data 是否存在
if not backend_data_dir.exists():
    print(f"\n❌ 错误：后端 data 目录不存在！不能删除旧目录")
    exit(1)

print(f"   ✅ 后端 data 目录存在")

# 检查后端数据库文件
backend_db = backend_data_dir / "sqlite" / "quant.db"
if backend_db.exists():
    print(f"   ✅ 后端数据库正在使用：{backend_db}")
    print(f"      大小：{backend_db.stat().st_size:,} 字节")
else:
    print(f"   ⚠️  后端数据库文件不存在")

# 检查旧 data 目录
if not old_data_dir.exists():
    print(f"\nℹ️  旧 data 目录已经不存在了")
    exit(0)

print(f"\n2️⃣ 检查旧 data 目录内容")
old_db = old_data_dir / "sqlite" / "quant.db"
if old_db.exists():
    print(f"   旧数据库文件：{old_db}")
    print(f"   大小：{old_db.stat().st_size:,} 字节")
    print(f"   修改时间：{datetime.fromtimestamp(old_db.stat().st_mtime)}")
else:
    print(f"   旧数据库文件不存在")

# 创建备份
backup_dir = Path("D:/Project/Quant/data_backup")
print(f"\n3️⃣ 创建备份")
print(f"   备份到：{backup_dir}")

try:
    if backup_dir.exists():
        print(f"   ⚠️  备份目录已存在，先删除")
        shutil.rmtree(backup_dir)
    
    shutil.copytree(old_data_dir, backup_dir)
    print(f"   ✅ 备份完成")
except Exception as e:
    print(f"   ❌ 备份失败：{e}")
    exit(1)

# 删除旧目录
print(f"\n4️⃣ 删除旧 data 目录")
print(f"   目标：{old_data_dir}")
print(f"   ⚠️  此操作不可逆！")

try:
    shutil.rmtree(old_data_dir)
    print(f"   ✅ 删除成功")
except Exception as e:
    print(f"   ❌ 删除失败：{e}")
    exit(1)

# 验证
print(f"\n5️⃣ 验证")
if not old_data_dir.exists():
    print(f"   ✅ 旧 data 目录已删除")
else:
    print(f"   ❌ 旧 data 目录仍然存在")

if backend_data_dir.exists():
    print(f"   ✅ 后端 data 目录正常")
else:
    print(f"   ❌ 后端 data 目录不存在了")

print(f"\n✅ 操作完成")
print(f"\n💡 提示:")
print(f"   - 备份已保存到：{backup_dir}")
print(f"   - 如果一切正常，可以手动删除备份目录")
print(f"   - 重启后端验证：cd backend && python -m uvicorn app.main:app --reload")

print("=" * 70)
