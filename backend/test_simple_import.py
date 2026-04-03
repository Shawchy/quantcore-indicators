"""简单导入测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("开始导入测试...")

try:
    print("1. 导入 config...")
    from app.config import settings
    print(f"   DEBUG = {settings.DEBUG}")
    
    print("2. 导入 security...")
    from app.core.security import verify_access_token, authenticate_user, create_access_token
    print("   OK")
    
    print("3. 导入 websocket routes...")
    from app.websocket.routes import websocket_endpoint, list_connections
    print("   OK")
    
    print("4. 导入 unified_storage...")
    from app.storage.unified_storage import UnifiedStorage, DataCategory
    print("   OK")
    
    print("5. 导入 smart_loader...")
    from app.services.smart_loader import smart_loader
    print("   OK")
    
    print("6. 导入 billboard...")
    from app.api.v1.endpoints.billboard import get_stock_billboard
    print("   OK")
    
    print("\n✅ 所有导入成功！")
    
except Exception as e:
    print(f"\n❌ 导入失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
