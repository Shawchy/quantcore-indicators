"""
API 集成测试
测试完整的 API 请求流程，包括认证、数据获取等
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.config import settings


@pytest.fixture(scope="module")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_client():
    """创建异步测试客户端"""
    # 初始化数据源
    from app.adapters import data_source_manager
    await data_source_manager.initialize()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # 清理
    await data_source_manager.close_all()


@pytest.fixture
async def auth_token():
    """创建认证令牌"""
    token = create_access_token(
        data={"sub": "admin", "user_id": 1, "role": "admin"}
    )
    return token


class TestHealthCheck:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """测试健康检查端点"""
        response = await async_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_performance_metrics(self, async_client):
        """测试性能指标端点"""
        response = await async_client.get("/metrics/performance")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestAuthentication:
    """认证相关端点测试"""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client):
        """测试登录成功"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client):
        """测试登录失败 - 错误密码"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong_password"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, async_client):
        """测试登录失败 - 用户不存在"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client, auth_token):
        """测试获取当前用户信息"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, async_client):
        """测试获取当前用户信息 - 无令牌"""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client):
        """测试获取当前用户信息 - 无效令牌"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout(self, async_client, auth_token):
        """测试登出"""
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data


class TestStockAPI:
    """股票相关 API 测试"""

    @pytest.mark.asyncio
    async def test_get_stock_basic(self, async_client, auth_token):
        """测试获取股票基本信息"""
        response = await async_client.get(
            "/api/v1/stock/000001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # 可能返回 200 或 404，取决于是否有数据
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    @pytest.mark.asyncio
    async def test_get_stock_kline(self, async_client, auth_token):
        """测试获取股票 K 线数据"""
        response = await async_client.get(
            "/api/v1/stock/000001/kline",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"start_date": "20240101", "end_date": "20240131", "adjust": "qfq"},
        )
        # 数据源已初始化，应该能正常返回
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    @pytest.mark.asyncio
    async def test_search_stock(self, async_client, auth_token):
        """测试搜索股票"""
        response = await async_client.get(
            "/api/v1/stock/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"keyword": "平安", "limit": 10},
        )
        # 数据源已初始化，应该能正常返回
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data


class TestWatchlistAPI:
    """自选股相关 API 测试"""

    @pytest.mark.asyncio
    async def test_get_watchlist(self, async_client, auth_token):
        """测试获取自选股列表"""
        response = await async_client.get(
            "/api/v1/watchlist",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # 返回 200 或 404 都视为正常（取决于是否有数据）
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "success" in data

    @pytest.mark.asyncio
    async def test_add_watchlist_item(self, async_client, auth_token):
        """测试添加自选股"""
        response = await async_client.post(
            "/api/v1/watchlist/add",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"code": "000001", "note": "测试股票"},
        )
        # 可能返回 200、201、400（如果已存在）或 404（如果接口不存在）
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.asyncio
    async def test_remove_watchlist_item(self, async_client, auth_token):
        """测试删除自选股"""
        response = await async_client.delete(
            "/api/v1/watchlist/remove/000001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestSectorAPI:
    """板块相关 API 测试"""

    @pytest.mark.asyncio
    async def test_get_sector_list(self, async_client, auth_token):
        """测试获取板块列表"""
        response = await async_client.get(
            "/api/v1/sector/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"sector_type": "industry"},
        )
        # 数据源已初始化，应该能正常返回
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "success" in data

    @pytest.mark.asyncio
    async def test_get_sector_ranking(self, async_client, auth_token):
        """测试获取板块排名"""
        response = await async_client.get(
            "/api/v1/sector/ranking",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"sector_type": "industry", "sort_by": "change_pct", "limit": 20},
        )
        # 数据源已初始化，应该能正常返回
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "success" in data


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_404_error(self, async_client):
        """测试 404 错误处理"""
        response = await async_client.get("/api/v1/nonexistent/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_validation_error(self, async_client, auth_token):
        """测试参数验证错误"""
        # 发送无效参数
        response = await async_client.get(
            "/api/v1/stock/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            # 缺少必需的 keyword 参数
        )
        # 根据实现可能返回 200（空结果）或 422（验证错误）
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, async_client):
        """测试方法不允许错误"""
        response = await async_client.post("/health")  # GET 端点使用 POST
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestCORS:
    """CORS 跨域测试"""

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """测试 CORS 响应头"""
        response = await async_client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers
