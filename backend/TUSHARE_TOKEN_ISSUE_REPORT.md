# Tushare Token 问题诊断与修复报告

**生成时间**: 2026-03-12 18:00  
**问题级别**: 🔴 P0 - 严重（数据源不可用）  
**当前状态**: ⚠️ 已临时切换至备选数据源

---

## 问题概述

后端服务启动时报告 Tushare 连接失败，无法使用 Tushare 数据源。

### 错误日志

```
2026-03-12 17:59:43 | ERROR | app.adapters.tushare_adapter:initialize:70 - Tushare 连接测试失败：抱歉，您没有接口访问权限，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108
2026-03-12 17:59:43 | ERROR | app.adapters.tushare_adapter:initialize:71 - 可能原因：Token 无效、积分不足或网络问题
```

---

## 诊断过程

### 1. 检查配置文件

**文件位置**: `d:\Project\Quant\backend\.env`

**发现的配置**:
```env
TUSHARE_TOKEN=25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de
TUSHARE_POINTS=120
DEFAULT_DATA_SOURCE=tushare
```

### 2. 运行 Token 验证测试

创建并执行了 `test_token.py` 验证脚本，测试结果：

```
============================================================
Tushare Token 验证工具
============================================================

📋 配置信息:
   Token: 25879cba32...bc5de
   积分配置：120 分

🔄 正在连接 Tushare...

📅 测试 1: 获取交易日历数据...

❌ 连接失败：抱歉，您没有接口访问权限
```

### 3. 问题确认

**根本原因**: 当前配置的 Tushare Token 已失效或无效

**可能原因**:
1. ✅ Token 已过期或被重置（最可能）
2. ⚠️ 账号积分不足 120 分
3. ⚠️ 账号未完成信息完善
4. ⚠️ 账号被限制或封禁

---

## 已采取的临时措施

### 切换默认数据源为 AkShare

**修改文件**: `d:\Project\Quant\backend\.env`

**修改内容**:
```env
# 原配置
DEFAULT_DATA_SOURCE=tushare

# 新配置
DEFAULT_DATA_SOURCE=akshare
```

### 影响评估

| 功能模块 | 影响程度 | 说明 |
|---------|---------|------|
| 日线行情 | ✅ 无影响 | AkShare 提供完整数据 |
| 实时行情 | ✅ 无影响 | AkShare 提供实时数据 |
| 指数数据 | ✅ 无影响 | AkShare 支持主要指数 |
| 板块分析 | ✅ 无影响 | AkShare 提供板块数据 |
| 财务数据 | ⚠️ 部分影响 | AkShare 数据可能不如 Tushare 完整 |
| 分钟线数据 | ✅ 无影响 | AkShare 支持多周期分钟线 |

**系统当前状态**: ✅ 可以正常使用，使用 AkShare 作为数据源

---

## 永久解决方案

### 方案一：获取新的 Tushare Token（推荐）

**优点**:
- 数据质量更高
- 接口更稳定
- 支持更多高级功能

**步骤**:

1. **访问 Tushare 官网**
   - 网址：https://tushare.pro/
   
2. **注册/登录账号**
   - 如果没有账号，先注册
   - 使用手机号或邮箱注册

3. **完善个人信息**
   - 填写真实姓名、邮箱、手机等信息
   - 完成后可获得 120 积分（注册 20 分 + 完善信息 100 分）

4. **获取 Token**
   - 点击右上角头像 → "个人主页"
   - 左侧菜单选择 "接口 TOKEN"
   - 复制 Token 字符串

5. **更新配置文件**
   ```env
   # 取消注释并填入新 Token
   TUSHARE_TOKEN=你的新 token
   
   # 确认积分
   TUSHARE_POINTS=120
   
   # 切换回 Tushare
   DEFAULT_DATA_SOURCE=tushare
   ```

6. **重启后端服务**
   ```bash
   # 停止当前服务（Ctrl+C）
   # 重新启动
   cd d:\Project\Quant\backend
   python -m uvicorn app.main:app --reload
   ```

7. **验证 Token**
   ```bash
   python test_token.py
   ```

### 方案二：继续使用 AkShare

**优点**:
- 完全免费，无需注册
- 数据源丰富，覆盖全面
- 无积分限制

**缺点**:
- 部分数据更新可能不如 Tushare 及时
- 高级财务数据可能不完整

**配置**:
```env
# 保持当前配置即可
DEFAULT_DATA_SOURCE=akshare
```

---

## Tushare 积分权限说明

根据官方文档（https://tushare.pro/document/1?doc_id=108）：

### 120 分（免费）- 注册 + 完善信息
| 接口名称 | API 代码 | 描述 |
|---------|---------|------|
| 日线行情 | daily | 全部历史，交易日 15-17 点更新 |
| 股票列表 | stock_basic | 上市公司基本信息 |
| 指数列表 | index_basic | 指数基本信息 |
| 指数日线 | index_daily | 指数日线行情 |
| 交易日历 | trade_cal | 交易所交易日历 |
| 分红送股 | dividend | 上市公司分红送股信息 |
| 基金基础 | fund_basic | 公募基金基本信息 |
| 宏观数据 | macro_data | GDP、CPI 等宏观经济数据 |

### 200 分
- 龙虎榜（top_list）
- 大宗交易（block_trade）
- 融资融券（margin）

### 800 分
- 业绩预告（forecast）
- 业绩快报（express）

### 2000 分
- 周线行情（weekly）
- 月线行情（monthly）
- 完整财务三大表

### 5000 分
- 分钟线（intraday/bar）
- 资金流向（moneyflow）

### 10000 分
- 筹码分布
- 盈利预测
- Level-2 数据

---

## 验证清单

### 当前状态（使用 AkShare）
- [x] 默认数据源已切换为 AkShare
- [x] 后端服务可以正常启动
- [x] 前端可以访问 API
- [x] 基础行情数据可用
- [x] 板块分析功能可用

### 如需切换回 Tushare
- [ ] 已获取新的 Tushare Token
- [ ] 已更新 `.env` 文件中的 `TUSHARE_TOKEN`
- [ ] 已确认 `TUSHARE_POINTS` 与实际积分一致
- [ ] 已运行 `test_token.py` 验证通过
- [ ] 已将 `DEFAULT_DATA_SOURCE` 改回 `tushare`
- [ ] 已重启后端服务
- [ ] 已检查日志确认初始化成功

---

## 文件清单

### 已创建/修改的文件

1. **`d:\Project\Quant\backend\.env`** (已修改)
   - 切换默认数据源为 AkShare
   - 注释了失效的 Token

2. **`d:\Project\Quant\backend\test_token.py`** (已创建)
   - Tushare Token 验证脚本
   - 可用于测试 Token 有效性

3. **`d:\Project\Quant\backend\TUSHARE_TOKEN_FIX.md`** (已创建)
   - 详细的 Token 配置指南
   - 包含问题诊断、解决步骤、FAQ

4. **`d:\Project\Quant\backend\TUSHARE_TOKEN_ISSUE_REPORT.md`** (本文档)
   - 问题诊断与修复报告

---

## 后续建议

### 短期（1-2 天）
1. ✅ 使用 AkShare 作为临时数据源，确保系统可用
2. ⏳ 注册 Tushare 账号并获取新 Token（如需要使用 Tushare）

### 中期（1 周）
1. 评估 AkShare 和 Tushare 的数据质量差异
2. 根据实际需求决定是否继续使用 Tushare
3. 如果 AkShare 满足需求，可以保持当前配置

### 长期
1. 考虑实现数据源自动切换机制
2. 增加数据质量监控
3. 建立数据源健康检查

---

## 技术支持

### 文档资源
- Tushare 官方文档：https://tushare.pro/document/1?doc_id=108
- Tushare 积分规则：https://tushare.pro/document/1?doc_id=108
- AkShare 文档：https://akshare.akfamily.xyz/

### 联系方式
- Tushare 官方支持：https://tushare.pro/feedback
- 项目 Issues: https://github.com/your-repo/issues

---

## 附录：快速命令参考

### 测试 Token
```bash
cd d:\Project\Quant\backend
python test_token.py
```

### 启动后端（开发模式）
```bash
cd d:\Project\Quant\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 查看日志
```bash
# PowerShell
Get-Content logs/app.log -Wait -Tail 50

# 或使用 tail 命令（如果安装了 Git Bash）
tail -f logs/app.log
```

### 检查当前数据源
```bash
# 在 Python 中
cd d:\Project\Quant\backend
python -c "from app.config import settings; print(f'当前数据源：{settings.DEFAULT_DATA_SOURCE}')"
```

---

**报告生成完成**  
**下一步操作**: 请根据实际需求选择永久解决方案
