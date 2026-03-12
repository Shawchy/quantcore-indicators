"""
检查当前后端实际使用的数据路径
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings

print("=" * 70)
print("当前后端配置的数据路径")
print("=" * 70)

print(f"\n当前工作目录：{os.getcwd()}")
print(f"\n配置的路径:")
print(f"  SQLITE_DIR: {settings.SQLITE_DIR}")
print(f"  PARQUET_DIR: {settings.PARQUET_DIR}")
print(f"  DATABASE_URL: {settings.DATABASE_URL}")

print(f"\n解析后的绝对路径:")
sqlite_path = Path(settings.SQLITE_DIR).resolve()
parquet_path = Path(settings.PARQUET_DIR).resolve()

print(f"  SQLite 数据库：{sqlite_path}")
print(f"  Parquet 目录：{parquet_path}")

print(f"\n文件存在性检查:")
db_file = sqlite_path / "quant.db"
print(f"  数据库文件：{db_file}")
print(f"    存在：{db_file.exists()}")
if db_file.exists():
    print(f"    大小：{db_file.stat().st_size:,} 字节")
    print(f"    修改时间：{db_file.stat().st_mtime}")

print(f"\n⚠️  潜在问题:")
if "backend" not in str(sqlite_path):
    print(f"  ❌ 数据库路径不包含 'backend'，可能使用了错误的路径")
    print(f"     当前：{sqlite_path}")
    print(f"     期望：{Path(__file__).parent / 'data' / 'sqlite'}")
else:
    print(f"  ✅ 数据库路径正确，位于 backend 目录下")

print("\n" + "=" * 70)
