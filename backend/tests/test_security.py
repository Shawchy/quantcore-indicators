"""
安全模块单元测试
测试 JWT 认证、密码加密等核心安全功能
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
    authenticate_user,
    SECRET_KEY,
    ALGORITHM,
)


class TestPasswordHashing:
    """密码哈希测试"""

    def test_password_hashing(self):
        """测试密码哈希生成和验证"""
        password = "test_password123"
        hashed = get_password_hash(password)

        # 验证哈希值不同于原始密码
        assert hashed != password
        # 验证密码验证成功
        assert verify_password(password, hashed) is True
        # 验证错误密码验证失败
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """测试不同密码生成不同哈希"""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """测试相同密码生成不同哈希（加盐）"""
        password = "same_password"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 由于加盐，相同密码的哈希值应该不同
        assert hash1 != hash2
        # 但都能验证通过
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "testuser", "user_id": 1, "role": "user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # 解码验证
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 1
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        data = {"sub": "testuser", "user_id": 1, "role": "user"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        # 解码验证
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_token_expiration(self):
        """测试令牌过期时间"""
        data = {"sub": "testuser", "user_id": 1}

        # 创建短期令牌
        short_token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # 立即验证应该通过
        token_data = verify_access_token(short_token)
        assert token_data is not None

        # 等待令牌过期
        import time
        time.sleep(2)

        # 过期后验证应该失败
        token_data = verify_access_token(short_token)
        assert token_data is None

    def test_decode_token(self):
        """测试令牌解码"""
        data = {"sub": "testuser", "user_id": 1, "role": "admin"}
        token = create_access_token(data)

        token_data = decode_token(token)

        assert token_data is not None
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
        assert token_data.role == "admin"
        assert token_data.type == "access"

    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        token_data = decode_token("invalid_token")
        assert token_data is None

    def test_verify_access_token_type(self):
        """测试访问令牌类型验证"""
        # 创建访问令牌
        access_data = {"sub": "testuser", "user_id": 1}
        access_token = create_access_token(access_data)

        # 创建刷新令牌
        refresh_data = {"sub": "testuser", "user_id": 1}
        refresh_token = create_refresh_token(refresh_data)

        # 访问令牌验证
        assert verify_access_token(access_token) is not None
        # 刷新令牌作为访问令牌验证应该失败
        assert verify_access_token(refresh_token) is None

    def test_verify_refresh_token_type(self):
        """测试刷新令牌类型验证"""
        # 创建访问令牌
        access_data = {"sub": "testuser", "user_id": 1}
        access_token = create_access_token(access_data)

        # 创建刷新令牌
        refresh_data = {"sub": "testuser", "user_id": 1}
        refresh_token = create_refresh_token(refresh_data)

        # 刷新令牌验证
        assert verify_refresh_token(refresh_token) is not None
        # 访问令牌作为刷新令牌验证应该失败
        assert verify_refresh_token(access_token) is None


class TestAuthentication:
    """用户认证测试"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """测试用户认证成功"""
        # 使用测试用户
        user = await authenticate_user("admin", "admin123")

        assert user is not None
        assert user.username == "admin"
        assert user.role == "admin"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """测试用户认证失败 - 错误密码"""
        user = await authenticate_user("admin", "wrong_password")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """测试用户认证失败 - 用户不存在"""
        user = await authenticate_user("nonexistent_user", "password")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self):
        """测试用户认证失败 - 用户被禁用"""
        # 注意：当前测试环境没有禁用用户，需要手动创建
        # 这里仅作为测试框架示例
        pass


class TestTokenEdgeCases:
    """令牌边界情况测试"""

    def test_token_with_special_characters(self):
        """测试包含特殊字符的用户名"""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        token_data = verify_access_token(token)
        assert token_data is not None
        assert token_data.username == "user@example.com"

    def test_token_with_unicode(self):
        """测试包含 Unicode 字符的用户名"""
        data = {"sub": "用户_123", "user_id": 1}
        token = create_access_token(data)

        token_data = verify_access_token(token)
        assert token_data is not None
        assert token_data.username == "用户_123"

    def test_malformed_token(self):
        """测试格式错误的令牌"""
        assert decode_token("not.a.valid.token") is None
        assert decode_token("") is None
        assert decode_token("Bearer token") is None
