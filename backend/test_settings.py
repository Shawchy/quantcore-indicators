"""检查 settings 配置"""
from app.config import settings

print("DATA_SOURCE_PRIORITY:", getattr(settings, 'DATA_SOURCE_PRIORITY', '未配置'))
print("默认数据源:", settings.DEFAULT_DATA_SOURCE)
