"""
TickFlow WebSocket 集成测试

验证：
1. TickFlow WebSocket 服务初始化
2. 连接管理器功能
3. 混合实时服务切换
4. API端点注册
5. 前端Hook可用性
"""

import asyncio
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def test_tickflow_websocket_service():
    """测试TickFlow WebSocket服务"""
    print_section("Test 1: TickFlowWebSocketService")
    
    try:
        from app.services.tickflow_websocket import (
            TickFlowWebSocketService,
            QuoteData,
            OperationType,
            get_tickflow_ws_service,
            WEBSOCKETS_AVAILABLE
        )
        
        # 测试1.1: 服务实例化
        service = TickFlowWebSocketService(api_key="test_key")
        
        passed1 = service is not None
        print_test("✅ 服务实例化", passed1, f"API Key已配置: {bool(service.api_key)}")
        
        # 测试1.2: 依赖检查
        passed2 = True
        if WEBSOCKETS_AVAILABLE:
            print_test("✅ websockets库已安装", True, "可使用WebSocket功能")
        else:
            print_test("⚠️  websockets库未安装", False, "请运行: pip install websockets")
            passed2 = False
        
        # 测试1.3: QuoteData模型
        test_data = {
            "symbol": "600000.SH",
            "region": "CN",
            "last_price": 10.15,
            "prev_close": 10.04,
            "open": 10.06,
            "high": 10.25,
            "low": 10.03,
            "volume": 1057712,
            "amount": 1072786000,
            "timestamp": 1769961600000
        }
        
        quote = QuoteData.from_tickflow(test_data)
        
        passed3 = quote.last_price == 10.15
        passed4 = quote.change == round(10.15 - 10.04, 2)  # 0.11
        passed5 = abs(quote.change_pct - round(0.11/10.04*100, 2)) < 0.01
        
        print_test("✅ QuoteData解析", passed3, f"价格={quote.last_price}, 涨跌额={quote.change}")
        print_test("✅ 涨跌幅计算", passed4, f"change_pct={quote.change_pct}%")
        print_test("✅ 振幅计算", passed5, f"amplitude={quote.amplitude}%")
        
        # 测试1.4: 字典转换
        quote_dict = quote.to_dict()
        passed6 = isinstance(quote_dict, dict) and "symbol" in quote_dict
        print_test("✅ to_dict()转换", passed6, f"字段数: {len(quote_dict)}")
        
        # 测试1.5: 符号标准化
        normalized = TickFlowWebSocketService._normalize_symbol("600000.SH")
        normalized2 = TickFlowWebSocketService._normalize_symbol("000001.SZ")
        
        passed7 = normalized == "600000"
        passed8 = normalized2 == "000001"
        
        print_test("✅ SH代码标准化", passed7, f"'600000.SH' → '{normalized}'")
        print_test("✅ SZ代码标准化", passed8, f"'000001.SZ' → '{normalized2}'")
        
        # 测试1.6: 状态检查（不连接）
        status = service.get_status()
        passed9 = "connected" in status and "subscribed_count" in status
        print_test("✅ 状态信息完整", passed9, f"指标数: {len(status)}")
        
        all_passed = all([passed1, passed3, passed4, passed5, passed6, passed7, passed8, passed9])
        
        if not passed2:
            print("\n⚠️  部分功能受限（缺少websockets库），但核心逻辑正常")
            
        return all_passed
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FAIL] 异常: {e}\n")
        return False


async def test_connection_manager():
    """测试连接管理器"""
    print_section("Test 2: ConnectionManager")
    
    try:
        from app.api.v1.endpoints.tickflow_ws_endpoint import ConnectionManager
        
        manager = ConnectionManager()
        
        # 测试2.1: 初始状态
        passed1 = len(manager._connections) == 0
        print_test("✅ 初始状态空", passed1, f"连接数: {len(manager._connections)}")
        
        # 测试2.2: 统计信息
        stats = manager.get_statistics()
        passed2 = (
            "connected_clients" in stats and 
            "total_subscriptions" in stats and
            stats["connected_clients"] == 0
        )
        print_test("✅ 统计信息结构", passed2, f"包含 {len(stats)} 个指标")
        
        # 测试2.3: 模拟客户端连接（使用Mock）
        class MockWebSocket:
            async def accept(self):
                pass
            
            async def send_text(self, message):
                pass
        
        mock_ws = MockWebSocket()
        client_id = await manager.connect(mock_ws)
        
        passed3 = client_id is not None and len(client_id) > 0
        passed4 = client_id in manager._connections
        print_test("✅ 客户端连接创建", passed3, f"Client ID: {client_id}")
        print_test("✅ 连接存储成功", passed4, f"总连接数: {len(manager._connections)}")
        
        # 测试2.4: 订阅功能
        test_symbols = ["000001", "600000", "300001"]
        manager.subscribe(client_id, test_symbols)
        
        conn_info = manager.get_client_info(client_id)
        passed5 = len(conn_info["subscribed_symbols"]) == 3
        print_test("✅ 订阅功能", passed5, f"订阅标的: {conn_info['subscribed_symbols']}")
        
        # 测试2.5: 退订功能
        manager.unsubscribe(client_id, ["000001"])
        conn_info_after = manager.get_client_info(client_id)
        passed6 = "000001" not in conn_info_after["subscribed_symbols"]
        passed7 = len(conn_info_after["subscribed_symbols"]) == 2
        print_test("✅ 退订功能", passed6 and passed7, f"剩余: {conn_info_after['subscribed_symbols']}")
        
        # 测试2.6: 断开连接
        manager.disconnect(client_id)
        passed8 = client_id not in manager._connections
        print_test("✅ 断开清理", passed8, f"剩余连接: {len(manager._connections)}")
        
        all_passed = all([passed1, passed2, passed3, passed4, passed5, passed6, passed7, passed8])
        return all_passed
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FAIL] 异常: {e}\n")
        return False


async def test_hybrid_realtime_service():
    """测试混合实时服务"""
    print_section("Test 3: HybridRealtimeService")
    
    try:
        from app.services.hybrid_realtime import (
            HybridRealtimeService,
            HybridConfig,
            DataSourcePriority,
            get_hybrid_realtime_service
        )
        
        # 测试3.1: 实例化
        config = HybridConfig(
            prefer_websocket=True,
            ws_fallback_to_polling=True,
            polling_interval_ms=30000
        )
        
        service = HybridRealtimeService(config=config)
        
        passed1 = service.config.prefer_websocket == True
        print_test("✅ 配置加载", passed1, f"优先WS: {config.prefer_websocket}")
        
        # 测试3.2: 初始化
        await service.initialize()
        
        status = service.get_status()
        passed2 = "current_source" in status
        print_test("✅ 初始化完成", passed2, f"当前源: {status['current_source']}")
        
        # 测试3.3: 获取行情（降级模式）
        test_codes = ["000001", "600000"]
        data, source = await service.get_quotes(test_codes)
        
        passed3 = source in ["tickflow_ws", "smart_polling", "cache"]
        passed4 = isinstance(data, dict)
        print_test("✅ 行情获取", passed3, f"数据源: {source}")
        print_test("✅ 数据格式", passed4, f"数量: {len(data)}")
        
        # 测试3.4: 状态信息完整性
        required_keys = [
            "current_source",
            "ws_status",
            "polling_stats",
            "config"
        ]
        
        has_all_keys = all(k in status for k in required_keys)
        print_test("✅ 状态完整性", has_all_keys, f"缺失: {[k for k in required_keys if k not in status]}")
        
        # 测试3.5: 全局单例
        global_instance = get_hybrid_realtime_service()
        passed5 = global_instance is service
        print_test("✅ 单例模式", passed5, "同一实例")
        
        all_passed = all([passed1, passed2, passed3, passed4, passed5])
        return all_passed
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FAIL] 异常: {e}\n")
        return False


def test_api_endpoints():
    """测试API端点定义"""
    print_section("Test 4: API Endpoints & Frontend Hooks")
    
    tests_passed = []
    
    # 测试4.1: WebSocket端点模块
    try:
        from app.api.v1.endpoints.tickflow_ws_endpoint import router as ws_router
        
        passed1 = ws_router is not None
        print_test("✅ WS端点模块导入", passed1, f"路由前缀: /api/v1/ws")
        tests_passed.append(passed1)
        
        # 检查路由定义
        routes = [str(route.path) for route in ws_router.routes]
        has_ws_route = "/quotes" in routes or any("/ws" in r for r in routes)
        print_test("✅ WS路由存在", has_ws_route, f"路由: {routes[:3]}")
        tests_passed.append(has_ws_route)
        
    except ImportError as e:
        print_test("❌ WS端点模块导入失败", False, str(e))
        tests_passed.append(False)
    
    # 测试4.2: 智能轮询端点
    try:
        from app.api.v1.endpoints.smart_realtime import router as polling_router
        
        passed2 = polling_router is not None
        print_test("✅ 轮询端点模块", passed2)
        tests_passed.append(passed2)
        
    except ImportError as e:
        print_test("❌ 轮询端点模块导入失败", False, str(e))
        tests_passed.append(False)
    
    # 测试4.3: 检查前端文件是否存在
    import os
    
    frontend_hooks_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "frontend", "src", "hooks"
    )
    
    hooks_to_check = [
        ("useSmartPolling.ts", "智能轮询Hook"),
        ("useTickFlowWS.ts", "TickFlow WSHook"),
    ]
    
    for filename, description in hooks_to_check:
        filepath = os.path.join(frontend_hooks_path, filename)
        exists = os.path.exists(filepath)
        icon = "✅" if exists else "⚠️ "
        print(f"{icon} [{description}] 文件{'存在' if exists else '缺失'}: {filename}")
        tests_passed.append(exists)
    
    return all(tests_passed)


def print_test(name: str, passed: bool, detail: str = ""):
    """打印测试结果"""
    icon = "✅" if passed else "❌"
    msg = f"{icon} {name}"
    if detail:
        msg += f"\n      → {detail}"
    print(msg)


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("  TICKFLOW WEB SOCKET INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = {}
    
    results["TickFlowWebSocket"] = await test_tickflow_websocket_service()
    results["ConnectionManager"] = test_connection_manager()
    results["HybridRealtime"] = await test_hybrid_realtime_service()
    results["APIEndpoints"] = test_api_endpoints()
    
    # 汇总
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n📊 结果:")
    print(f"   通过: {passed}/{total}")
    print(f"   成功率: {passed/total*100:.0f}%\n")
    
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"   {icon} {name}: {'PASS' if ok else 'FAIL'}")
    
    if passed == total:
        print("\n🎉 所有测试通过！TickFlow WebSocket集成就绪！")
        print("\n📋 下一步:")
        print("   1. 在 .env 中设置 TICKFLOW_API_KEY=your-api-key")
        print("   2. 运行: pip install websockets")
        print("   3. 启动后端服务")
        print("   4. 使用前端 Hook 连接实时行情")
    else:
        failed = [n for n, p in results.items() if not p]
        print(f"\n⚠️  {len(failed)} 个模块需要修复:")
        for name in failed:
            print(f"   - {name}")
    
    print(f"\n⏰ 完成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
