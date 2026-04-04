# TLS 指纹伪装部署指南

**执行日期**: 2026-04-04  
**目标**: 为所有 AkShare API 应用 TLS 指纹伪装和凭证注入

---

## 一、修改模式

### 标准修改模板

**修改前**:
```python
async def get_xxx(self, ...) -> ReturnType:
    """获取 XXX 数据（带反风控）"""
    await self._rate_limit()
    
    def fetch_sync():
        df = ak.stock_xxx()
        # ...
    
    try:
        result = await self._retry_executor.execute(...)
        return result or []
    except Exception as e:
        logger.error(f"获取 XXX 失败：{e}")
        return []
```

**修改后**:
```python
async def get_xxx(self, ...) -> ReturnType:
    """获取 XXX 数据（带 TLS 指纹伪装 + 凭证注入）"""
    # 确保凭证有效（TLS 指纹伪装）
    await self._ensure_credentials()
    
    # 限流
    await self._rate_limit()
    
    def fetch_sync():
        df = ak.stock_xxx()
        # ...
    
    try:
        result = await self._retry_executor.execute(...)
        return result or []
    except Exception as e:
        logger.error(f"获取 XXX 失败：{e}")
        return []
```

---

## 二、需要修改的 API 列表

### 已完成修改 (2 个)

1. ✅ `get_stock_list` (行号：420)
2. ✅ `get_stock_info` (行号：444)

### 待修改 API (21 个)

#### K 线相关 (4 个)
1. `get_kline` (行号：479)
2. `get_market_index_kline` (行号：541)
3. `get_weekly_kline` (行号：未找到)
4. `get_monthly_kline` (行号：未找到)

#### 行情相关 (3 个)
5. `get_realtime_quote` (行号：587)
6. `get_market_realtime_quotes` (行号：614)
7. `get_market_moneyflow_dc` (行号：898)

#### 板块相关 (4 个)
8. `get_sector_list` (行号：690) - 已有凭证注入
9. `get_sector_components` (行号：784)
10. `get_sector_ranking` (行号：807)
11. `get_board_industry_name_em` (行号：1392)
12. `get_board_industry_cons_em` (行号：1426)

#### 特色数据 (8 个)
13. `get_chip_data` (行号：853)
14. `get_stock_financial` (行号：954)
15. `get_stock_changes` (行号：1016)
16. `get_zt_pool` (行号：1064)
17. `get_zt_pool_previous` (行号：1117)
18. `get_zt_strong` (行号：1166)
19. `get_zt_sub_new` (行号：1211)
20. `get_board_changes` (行号：1262)

#### 交易所列表 (3 个)
21. `get_stock_info_sh_name_code` (行号：1302)
22. `get_stock_info_sz_name_code` (行号：1332)
23. `get_stock_info_bj_name_code` (行号：1362)

---

## 三、修改步骤

### 步骤 1: 批量添加凭证注入调用

使用文本编辑器的查找替换功能：

**查找**:
```
async def get_(xxx)\(.*?\) -> .*?:
    """获取 (.*?)"""
    await self._rate_limit\(\)
```

**替换为**:
```
async def get_\1(...) -> ...:
    """获取 \2（带 TLS 指纹伪装 + 凭证注入）"""
    # 确保凭证有效（TLS 指纹伪装）
    await self._ensure_credentials()
    
    # 限流
    await self._rate_limit()
```

### 步骤 2: 验证修改

运行以下命令验证修改是否成功：
```bash
grep -n "await self._ensure_credentials()" app/adapters/akshare_adapter.py | wc -l
```

期望输出：23（所有 API 都调用了凭证注入）

### 步骤 3: 测试

运行测试确保修改没有破坏功能：
```bash
python -m pytest tests/test_akshare_adapter.py -v
```

---

## 四、预期效果

### 修改前
- ✅ 2/23 API (9%) 使用 TLS 指纹伪装
- ⚠️ 21/23 API (91%) 仅使用基础反风控

### 修改后
- ✅ 23/23 API (100%) 使用 TLS 指纹伪装 + 凭证注入
- ✅ 所有 API 都具备完整的反风控能力

### 反风控能力提升

| 能力 | 修改前 | 修改后 |
|------|--------|--------|
| TLS 指纹伪装 | 9% | 100% ✅ |
| 凭证注入 | 9% | 100% ✅ |
| 浏览器指纹 | 9% | 100% ✅ |
| 智能降级 | 9% | 100% ✅ |

---

## 五、注意事项

1. **性能影响**: 
   - 首次请求会慢 1-2 秒（凭证获取）
   - 后续请求无影响（使用缓存凭证）

2. **资源占用**:
   - Playwright 会占用约 50MB 内存
   - 建议在生产环境使用懒加载

3. **兼容性**:
   - 需要安装 playwright: `pip install playwright`
   - 需要安装浏览器：`playwright install chromium`

4. **降级机制**:
   - 如果凭证注入失败，会自动降级到普通模式
   - 不会影响 API 的可用性

---

## 六、执行状态

- [ ] `get_kline` - 待修改
- [ ] `get_market_index_kline` - 待修改
- [ ] `get_realtime_quote` - 待修改
- [ ] `get_market_realtime_quotes` - 待修改
- [ ] `get_market_moneyflow_dc` - 待修改
- [ ] `get_sector_components` - 待修改
- [ ] `get_sector_ranking` - 待修改
- [ ] `get_chip_data` - 待修改
- [ ] `get_stock_financial` - 待修改
- [ ] `get_stock_changes` - 待修改
- [ ] `get_zt_pool` - 待修改
- [ ] `get_zt_pool_previous` - 待修改
- [ ] `get_zt_strong` - 待修改
- [ ] `get_zt_sub_new` - 待修改
- [ ] `get_board_changes` - 待修改
- [ ] `get_stock_info_sh_name_code` - 待修改
- [ ] `get_stock_info_sz_name_code` - 待修改
- [ ] `get_stock_info_bj_name_code` - 待修改
- [ ] `get_board_industry_name_em` - 待修改
- [ ] `get_board_industry_cons_em` - 待修改

---

**文档生成时间**: 2026-04-04  
**执行优先级**: 高  
**预计完成时间**: 30 分钟
