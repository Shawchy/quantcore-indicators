import sys
import traceback

print("开始导入...")
try:
    from app.main import app
    print(f"✅ 导入成功！app 类型：{type(app)}")
    print(f"app.title: {app.title}")
except Exception as e:
    print(f"❌ 导入失败：{e}")
    traceback.print_exc()
    sys.exit(1)
