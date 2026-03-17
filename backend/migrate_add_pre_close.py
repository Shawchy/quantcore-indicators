"""
数据库迁移脚本：添加 pre_close 字段到 kline 表
"""
from sqlalchemy import text, create_engine

def migrate():
    """添加 pre_close 字段"""
    # 直接创建同步引擎
    engine = create_engine("sqlite:///./data/sqlite/quant.db")
    
    with engine.connect() as conn:
        try:
            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(kline)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'pre_close' in columns:
                print("✅ pre_close 列已存在，无需迁移")
                return
            
            # 添加 pre_close 列
            print("🔧 正在添加 pre_close 列到 kline 表...")
            conn.execute(text(
                "ALTER TABLE kline ADD COLUMN pre_close FLOAT"
            ))
            conn.commit()
            
            print("✅ 迁移成功！pre_close 列已添加到 kline 表")
            
        except Exception as e:
            print(f"❌ 迁移失败：{e}")
            conn.rollback()
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()
