"""
将股票列表导入数据库
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("导入股票列表到数据库")
print("=" * 70)

# 读取 CSV 文件
csv_file = Path(__file__).parent / "stock_list.csv"
db_file = Path(__file__).parent / "backend" / "data" / "sqlite" / "quant.db"

print(f"\n📂 数据源：{csv_file}")
print(f"💾 数据库：{db_file}")

# 检查文件
if not csv_file.exists():
    print(f"\n❌ CSV 文件不存在：{csv_file}")
    exit(1)

if not db_file.exists():
    print(f"\n❌ 数据库文件不存在：{db_file}")
    exit(1)

# 读取 CSV
print(f"\n📖 读取 CSV 文件...")
df = pd.read_csv(csv_file)
print(f"   ✅ 读取到 {len(df)} 条记录")

# 连接数据库
print(f"\n🔗 连接数据库...")
conn = sqlite3.connect(str(db_file))
cursor = conn.cursor()

# 导入数据
print(f"\n📥 导入数据到 stock_info 表...")
try:
    inserted = 0
    updated = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            # 检查是否已存在
            cursor.execute('SELECT id FROM stock_info WHERE code = ?', (row['symbol'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                cursor.execute('''
                    UPDATE stock_info SET
                        name = ?,
                        market = ?,
                        industry = ?,
                        area = ?,
                        list_date = ?,
                        updated_at = ?
                    WHERE code = ?
                ''', (
                    row['name'],
                    row['market'],
                    row['industry'],
                    row.get('area', None),
                    str(row['list_date']) if pd.notna(row.get('list_date')) else None,
                    datetime.now(),
                    row['symbol']
                ))
                updated += 1
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO stock_info (
                        code, name, market, industry, area, list_date, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['symbol'],
                    row['name'],
                    row['market'],
                    row['industry'],
                    row.get('area', None),
                    str(row['list_date']) if pd.notna(row.get('list_date')) else None,
                    datetime.now()
                ))
                inserted += 1
            
            # 每 1000 条提交一次
            if (idx + 1) % 1000 == 0:
                conn.commit()
                print(f"   已处理 {idx + 1}/{len(df)} 条 (插入：{inserted}, 更新：{updated})")
                
        except Exception as e:
            skipped += 1
            if skipped <= 10:  # 只显示前 10 个错误
                print(f"   ⚠️  跳过 {row['symbol']}: {e}")
    
    # 最后提交
    conn.commit()
    
    print(f"\n✅ 导入完成!")
    print(f"   插入：{inserted} 条")
    print(f"   更新：{updated} 条")
    print(f"   跳过：{skipped} 条")
    
    # 验证
    cursor.execute('SELECT COUNT(*) FROM stock_info')
    total = cursor.fetchone()[0]
    print(f"\n📊 stock_info 表总记录数：{total:,} 条")
    
except Exception as e:
    print(f"\n❌ 导入失败：{e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("\n" + "=" * 70)
print("✅ 数据库导入完成")
print("=" * 70)
print(f"\n💡 下一步:")
print(f"   1. 重启后端：cd backend && python -m uvicorn app.main:app --reload")
print(f"   2. 测试 API: http://localhost:8000/api/v1/stock/search?keyword=平安")
print(f"   3. 检查前端数据展示")
