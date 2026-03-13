"""
创建测试用户账户脚本
"""
import asyncio
from app.storage import User, get_session, init_database
from app.core.security import get_password_hash
from loguru import logger


async def create_test_users():
    """创建测试用户"""
    # 初始化数据库
    await init_database()
    
    async with get_session() as session:
        # 检查是否已存在测试用户
        from sqlalchemy import select
        
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            # 创建管理员账户
            admin_user = User(
                user_id=1,
                username="admin",
                password=get_password_hash("admin123"),
                email="admin@example.com",
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            logger.info("创建管理员账户: admin / admin123")
        else:
            logger.info("管理员账户已存在")
        
        result = await session.execute(select(User).where(User.username == "user"))
        normal_user = result.scalar_one_or_none()
        
        if not normal_user:
            # 创建普通用户账户
            normal_user = User(
                user_id=2,
                username="user",
                password=get_password_hash("user123"),
                email="user@example.com",
                role="user",
                is_active=True
            )
            session.add(normal_user)
            logger.info("创建普通用户账户: user / user123")
        else:
            logger.info("普通用户账户已存在")
        
        await session.commit()
        logger.success("测试用户账户创建完成！")


if __name__ == "__main__":
    asyncio.run(create_test_users())
