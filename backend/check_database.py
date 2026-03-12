import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'sqlite', 'quant.db')
print(f"数据库路径：{db_path}")
print(f"数据库文件存在：{os.path.exists(db_path)}\n")

if not os.path.exists(db_path):
    print("❌ 数据库文件不存在！")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print("📊 数据库表列表:")
for table in tables:
    print(f"  - {table[0]}")

print()

# 检查每个表的数据量
for table_name in ['stock_info', 'kline', 'technical_indicators', 'sector_info', 'watchlist']:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f"📋 {table_name} 表记录数：{count}")
    except Exception as e:
        print(f"❌ {table_name} 表检查失败：{e}")

print()

# 查看 stock_info 前 5 条
print("📋 stock_info 表前 5 条记录:")
try:
    cursor.execute('SELECT code, name, market, industry FROM stock_info LIMIT 5')
    stocks = cursor.fetchall()
    for stock in stocks:
        print(f"  {stock[0]} | {stock[1]} | {stock[2]} | {stock[3]}")
except Exception as e:
    print(f"  ❌ 查询失败：{e}")

print()

# 查看 kline 前 5 条
print("📋 kline 表前 5 条记录:")
try:
    cursor.execute('SELECT code, date, open, high, low, close FROM kline LIMIT 5')
    klines = cursor.fetchall()
    for kline in klines:
        print(f"  {kline[0]} | {kline[1]} | {kline[2]:.2f} | {kline[3]:.2f} | {kline[4]:.2f} | {kline[5]:.2f}")
except Exception as e:
    print(f"  ❌ 查询失败：{e}")

print()

# 查看 sector_info
print("📋 sector_info 表前 5 条记录:")
try:
    cursor.execute('SELECT code, name, sector_type FROM sector_info LIMIT 5')
    sectors = cursor.fetchall()
    for sector in sectors:
        print(f"  {sector[0]} | {sector[1]} | {sector[2]}")
except Exception as e:
    print(f"  ❌ 查询失败：{e}")

conn.close()

print("\n✅ 数据库检查完成")
