# Tushare Token 配置修复指南

## 问题现象

```
2026-03-12 17:59:43 | ERROR | app.adapters.tushare_adapter:initialize:70 - Tushare 连接测试失败：抱歉，您没有接口访问权限，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108
2026-03-12 17:59:43 | ERROR | app.adapters.tushare_adapter:initialize:71 - 可能原因：Token 无效、积分不足或网络问题
```

## 当前配置状态

### 1. 检查 .env 文件

**位置**: `d:\Project\Quant\backend\.env`

**当前配置**:
```env
TUSHARE_TOKEN=25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de
TUSHARE_POINTS=120
```

### 2. 问题分析

根据 Tushare 官方文档（https://tushare.pro/document/1?doc_id=108），可能的问题：

1. **Token 已失效**: Token 可能已过期或被重置
2. **积分不足**: 虽然配置为 120 分，但实际账户积分可能不足
3. **网络问题**: 无法连接到 Tushare 服务器
4. **账号权限**: 账号未完成信息完善或被限制

## 解决步骤

### 步骤 1: 获取新的 Tushare Token

1. **访问 Tushare 官网**: https://tushare.pro/
2. **登录账号**: 如果没有账号，先注册
3. **完善个人信息**: 填写完整个人信息可获得 120 积分
4. **获取 Token**: 
   - 点击右上角头像 → "个人主页"
   - 左侧菜单选择 "接口TOKEN"
   - 复制你的 Token（格式类似：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### 步骤 2: 更新配置文件

**方法一：直接修改 .env 文件**

编辑 `d:\Project\Quant\backend\.env`:

```env
# 将 YOUR_NEW_TOKEN_HERE 替换为你从官网获取的实际 Token
TUSHARE_TOKEN=your-new-token-here

# 确认你的积分（注册 20 分 + 完善信息 100 分 = 120 分）
# 如果有更多积分，修改为实际分数
TUSHARE_POINTS=120
```

**方法二：通过命令行（推荐）**

```bash
# 进入 backend 目录
cd d:\Project\Quant\backend

# 备份当前配置
copy .env .env.backup

# 使用文本编辑器修改 .env 文件
notepad .env
```

### 步骤 3: 验证 Token 有效性

**方法一：使用测试脚本**

创建测试文件 `d:\Project\Quant\backend\test_token.py`:

```python
import tushare as ts
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
print(f"Token: {token[:10]}...{token[-5:] if token else 'None'}")

if not token:
    print("❌ Token 未配置")
    exit(1)

try:
    # 设置 Token
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 测试连接
    print("\n正在测试连接...")
    df = pro.trade_cal(exchange='', start_date='20240101', end_date='20240107')
    
    if not df.empty:
        print("✅ Token 有效，连接成功！")
        
        # 查询积分
        try:
            user_info = pro.user()
            if not user_info.empty:
                points = user_info.iloc[0].get('points', 0)
                print(f"📊 当前积分：{points} 分")
        except Exception as e:
            print(f"⚠️  无法查询积分：{e}")
    else:
        print("❌ Token 无效或积分不足")
        
except Exception as e:
    print(f"❌ 连接失败：{e}")
```

运行测试：

```bash
cd d:\Project\Quant\backend
python test_token.py
```

**方法二：使用现有测试文件**

```bash
cd d:\Project\Quant\backend
python tests\test_tushare_adapter.py
```

### 步骤 4: 重启后端服务

修改配置后，必须重启后端服务才能生效：

```bash
# 停止当前运行的服务（Ctrl+C）

# 重新启动
cd d:\Project\Quant\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 5: 检查日志

查看后端日志，确认初始化成功：

```bash
# 查看最新日志
tail -f logs/app.log

# 或者在 Windows PowerShell
Get-Content logs/app.log -Wait -Tail 50
```

成功的日志应该显示：

```
INFO | Tushare Token 已加载：xxxxxxxxxx...xxxxx
INFO | Tushare 积分：120 分
INFO | Tushare 可用接口：XX 个
INFO | Tushare 适配器初始化成功
```

## Tushare 积分规则详解

根据官方文档，各积分等级对应的权限：

### 120 分（免费）- 注册 + 完善信息
- ✅ 日线行情（daily）- 非复权
- ✅ 股票列表（stock_basic）
- ✅ 指数列表（index_basic）
- ✅ 指数日线（index_daily）
- ✅ 基金基础（fund_basic）
- ✅ 分红送股（dividend）
- ✅ 交易日历（trade_cal）
- ✅ 宏观数据（macro_data）

### 200 分
- ✅ 龙虎榜（top_list）
- ✅ 大宗交易（block_trade）
- ✅ 融资融券（margin）

### 800 分
- ✅ 业绩预告（forecast）
- ✅ 业绩快报（express）

### 2000 分
- ✅ 周线行情（weekly）
- ✅ 月线行情（monthly）
- ✅ 完整财务数据

### 5000 分
- ✅ 分钟线（intraday/bar）
- ✅ 资金流向（moneyflow）

### 10000 分
- ✅ 筹码分布
- ✅ 盈利预测
- ✅ Level-2 数据

## 备选方案

如果 Tushare 无法使用，系统会自动切换到其他数据源：

### 1. AkShare（推荐备选）
- 完全免费
- 数据源丰富
- 无需 Token

### 2. Baostock
- 完全免费
- 无需注册
- 数据质量较好

### 切换数据源

修改 `d:\Project\Quant\backend\.env`:

```env
# 默认数据源
DEFAULT_DATA_SOURCE=akshare

# 数据源优先级（从高到低）
DATA_SOURCE_PRIORITY=akshare,tushare,baostock
```

## 常见问题 FAQ

### Q1: Token 在哪里获取？
A: 登录 Tushare 官网 → 个人主页 → 接口TOKEN

### Q2: 为什么显示积分不足？
A: 
- 检查是否完成了个人信息完善
- 确认账号是否已激活
- 联系 Tushare 客服确认积分状态

### Q3: Token 会过期吗？
A: Token 本身不会过期，但如果账号违规可能被禁用

### Q4: 如何增加积分？
A:
- 完善个人信息（+100 分）
- 参与社区贡献
- 充值（https://tushare.pro/user/recharge）

### Q5: 系统会自动切换数据源吗？
A: 会的。当 Tushare 失败时，会自动尝试 AkShare 或 Baostock

## 验证清单

- [ ] 已登录 Tushare 官网获取新 Token
- [ ] 已更新 `.env` 文件中的 `TUSHARE_TOKEN`
- [ ] 已确认 `TUSHARE_POINTS` 与实际积分一致
- [ ] 已运行 `test_token.py` 验证连接
- [ ] 已重启后端服务
- [ ] 已检查日志确认初始化成功
- [ ] 前端可以正常访问 API

## 联系支持

如果以上步骤都无法解决问题：

1. **Tushare 官方支持**: https://tushare.pro/feedback
2. **项目 Issues**: https://github.com/your-repo/issues
3. **查看文档**: https://tushare.pro/document/1?doc_id=108

---

**最后更新**: 2026-03-12
**状态**: 待修复
