from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
from loguru import logger

from app.config import settings


# JWT 配置
if not settings.SECRET_KEY:
    raise ValueError("SECRET_KEY 未设置！请在 .env 文件中设置 SECRET_KEY 环境变量")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时
REFRESH_TOKEN_EXPIRE_DAYS = 7


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    type: Optional[str] = None  # 添加 type 属性


class User(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    role: str = "user"  # user, admin
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"创建访问令牌：{data.get('username')}")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"创建刷新令牌：{data.get('username')}")
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role", "user")
        token_type: str = payload.get("type")
        
        if username is None or user_id is None:
            return None
        
        return TokenData(username=username, user_id=user_id, role=role, type=token_type)
    
    except JWTError as e:
        logger.warning(f"令牌解码失败：{e}")
        return None


def verify_access_token(token: str) -> Optional[TokenData]:
    token_data = decode_token(token)
    
    if token_data is None:
        return None
    
    if token_data.type != "access":
        logger.warning("令牌类型错误")
        return None
    
    return token_data


def verify_refresh_token(token: str) -> Optional[TokenData]:
    token_data = decode_token(token)
    
    if token_data is None:
        return None
    
    if token_data.type != "refresh":
        logger.warning("令牌类型错误")
        return None
    
    return token_data


async def verify_access_token_with_blacklist(token: str) -> Optional[TokenData]:
    token_data = verify_access_token(token)
    if token_data is None:
        return None
    
    try:
        from app.core.token_blacklist import token_blacklist
        if await token_blacklist.is_revoked(token):
            logger.warning("访问令牌已被撤销")
            return None
    except Exception as e:
        logger.warning(f"令牌黑名单检查失败，允许通过：{e}")
    
    return token_data


async def verify_refresh_token_with_blacklist(token: str) -> Optional[TokenData]:
    token_data = verify_refresh_token(token)
    if token_data is None:
        return None
    
    try:
        from app.core.token_blacklist import token_blacklist
        if await token_blacklist.is_revoked(token):
            logger.warning("刷新令牌已被撤销")
            return None
    except Exception as e:
        logger.warning(f"令牌黑名单检查失败，允许通过：{e}")
    
    return token_data


# 模拟用户数据库 (生产环境应使用数据库)
import secrets

# 使用 settings 中的默认密码配置
DEFAULT_ADMIN_PASSWORD = settings.DEFAULT_ADMIN_PASSWORD
DEFAULT_USER_PASSWORD = settings.DEFAULT_USER_PASSWORD

# 开发环境安全提示：显示默认密码已配置的警告（不显示具体密码）
if settings.DEBUG:
    logger.warning(
        "⚠️ 开发模式已启用：请确保生产环境中 DEBUG=False 且修改默认密码。\n"
        "   详细信息请查看 .env 文件中的 DEFAULT_ADMIN_PASSWORD 和 DEFAULT_USER_PASSWORD 配置"
    )


async def get_user(username: str) -> Optional[User]:
    """从数据库获取用户"""
    from app.storage import User as UserModel, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        
        if user:
            return User(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                role=user.role,
                is_active=user.is_active
            )
    
    return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """认证用户"""
    from app.storage import User as UserModel, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return User(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active
        )


async def login_for_access_token(username: str, password: str) -> Token:
    """登录获取令牌"""
    user = await authenticate_user(username, password)
    
    if not user:
        raise ValueError("用户名或密码错误")
    
    if not user.is_active:
        raise ValueError("用户已被禁用")
    
    # 创建令牌
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role
        }
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role
        }
    )
    
    logger.info(f"用户 {username} 登录成功")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


async def refresh_access_token(refresh_token: str) -> Token:
    token_data = await verify_refresh_token_with_blacklist(refresh_token)
    
    if not token_data:
        raise ValueError("刷新令牌无效或已过期")
    
    user = await get_user(token_data.username)
    
    if not user or not user.is_active:
        raise ValueError("用户不存在或已被禁用")
    
    # 创建新的访问令牌
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role
        }
    )
    
    logger.info(f"用户 {user.username} 刷新令牌成功")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,  # 刷新令牌不变
        token_type="bearer"
    )
