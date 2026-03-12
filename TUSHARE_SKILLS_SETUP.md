# Tushare Skills 安装与配置指南

**项目**: D:\Project\Quant  
**更新时间**: 2026-03-12  
**状态**: ✅ 已配置

---

## 📦 **什么是 Tushare Skills？**

Tushare Skills 是专门为金融数据分析设计的"超能力包"，让 AI 助手能够：

- 📈 **实时获取股票数据** - A 股、港股、美股
- 📊 **基金期货数据** - 公募基金、期货市场
- 📉 **技术指标分析** - MA、MACD、RSI 等
- 🌍 **宏观经济数据** - GDP、CPI、利率等
- 💰 **财务数据** - 财报、业绩预告、财务指标

---

## ✅ **当前安装状态检查**

### 1. Tushare 库安装

```bash
✅ 已安装
版本：1.4.25
```

### 2. Tushare Token 配置

```bash
✅ 已配置
位置：backend/.env
Token: 54fed15e38...81c65 (已脱敏)
```

### 3. OpenClaw Skills

⚠️ **需要安装** (如果使用 OpenClaw 环境)

---

## 🔧 **安装步骤**

### 方案一：在 OpenClaw 中安装（推荐）

#### 方法 1: 使用 clawhub 命令

```bash
# 安装 Tushare Skills
clawhub install tushare-data

# 升级更新
clawhub update tushare-data
```

#### 方法 2: 对话框聊天方式

在 OpenClaw 对话框中输入：

```
请安装最新版 Tushare skills，名称为 tushare-data
```

---

### 方案二：在大模型编程环境中安装

#### 使用 npx 命令

```bash
# 安装 Tushare Skills
npx skills add https://github.com/waditu-tushare/skills --skill tushare
```

---

### 方案三：手动下载配置

#### 1. 下载源文件

```bash
# 从 GitHub 下载
git clone https://github.com/waditu-tushare/skills.git

# 或使用浏览器下载 ZIP 包
https://github.com/waditu-tushare/skills/archive/refs/heads/main.zip
```

#### 2. 查看文件结构

```
skills/
├── README.md              # 说明文档
├── tushare.md             # Tushare Skills 主文件
├── examples/              # 使用示例
└── templates/             # 模板文件
```

---

## 🔑 **Token 配置**

### 当前配置

Token 已配置在 `backend/.env` 文件中：

```env
TUSHARE_TOKEN=54fed15e389514673aea623f02a7dc1279a3f716041ffc3e71481c65
```

### 在 OpenClaw 中配置 Token

在 OpenClaw 对话框中输入：

```
请设置我的 Tushare Token：54fed15e389514673aea623f02a7dc1279a3f716041ffc3e71481c65
请帮我保密这个 Token，不要在任何输出中显示完整内容
```

### 在 Python 中配置 Token

```python
import tushare as ts

# 设置 Token
ts.set_token('54fed15e389514673aea623f02a7dc1279a3f716041ffc3e71481c65')

# 初始化 API
pro = ts.pro_api()
```

---

## 📊 **获取新的 Tushare Token**

### 步骤 1: 注册账号

访问：https://tushare.pro/

- 点击"注册"
- 填写手机号、邮箱、密码
- 完成验证

### 步骤 2: 完善信息（+100 积分）

登录后：

- 点击头像 → "个人主页"
- 填写真实姓名、职业、公司等
- 完成后可获得 120 积分（注册 20 分 + 完善信息 100 分）

### 步骤 3: 获取 Token

- 在个人主页左侧菜单选择"接口 TOKEN"
- 复制 Token 字符串（格式：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### 步骤 4: 更新配置

在 `backend/.env` 中更新：

```env
TUSHARE_TOKEN=你的新 token
```

---

## 🎯 **使用示例**

### 示例 1: 获取股票基本信息

```python
import tushare as ts

# 初始化
ts.set_token('your_token')
pro = ts.pro_api()

# 获取股票列表
df = pro.stock_basic(exchange='', list_status='L', 
                     fields='ts_code,symbol,name,area,industry')
print(df.head())
```

### 示例 2: 获取日线行情

```python
# 获取日线数据
df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240312')
print(df.head())
```

### 示例 3: 获取指数数据

```python
# 上证指数日线
df = pro.index_daily(ts_code='000001.SH', 
                     start_date='20240101', 
                     end_date='20240312')
```

### 示例 4: 获取财务数据

```python
# 利润表
df = pro.income(ts_code='000001.SZ', 
                start_date='20230101', 
                end_date='20231231')
```

---

## 📚 **Tushare Skills 功能清单**

### 股票数据

- ✅ 股票列表 (`stock_basic`)
- ✅ 日线行情 (`daily`)
- ✅ 周线行情 (`weekly`) - 需要 2000 积分
- ✅ 月线行情 (`monthly`) - 需要 2000 积分
- ✅ 实时行情 (`daily` + 最新)
- ✅ 复权行情 (`pro_bar` + `adj_factor`)
- ✅ 龙虎榜 (`top_list`) - 需要 2000 积分
- ✅ 资金流向 (`moneyflow`) - 需要 5000 积分

### 指数数据

- ✅ 指数列表 (`index_basic`)
- ✅ 指数日线 (`index_daily`)
- ✅ 指数成分和权重 (`index_weight`)

### 基金数据

- ✅ 基金列表 (`fund_basic`)
- ✅ 基金净值 (`fund_nav`)
- ✅ 基金持仓 (`fund_portfolio`)

### 期货数据

- ✅ 期货列表 (`fut_basic`)
- ✅ 期货行情 (`fut_daily`)

### 财务数据

- ✅ 利润表 (`income`) - 需要 2000 积分
- ✅ 资产负债表 (`balancesheet`) - 需要 2000 积分
- ✅ 现金流量表 (`cashflow`) - 需要 2000 积分
- ✅ 业绩预告 (`forecast`) - 需要 2000 积分

### 宏观经济

- ✅ GDP 数据 (`cn_gdp`)
- ✅ CPI 数据 (`cn_cpi`)
- ✅ 利率数据 (`shibor`)
- ✅ 存款准备金率 (`rrr`)

---

## 🔒 **安全建议**

### 1. Token 保密

```bash
# ✅ 正确：使用环境变量
TUSHARE_TOKEN=your_token

# ❌ 错误：硬编码在代码中
token = "your_token"  # 不要提交到 Git
```

### 2. .gitignore 配置

已在 `.gitignore` 中添加：

```gitignore
# 后端配置
backend/.env
backend/data/

# 前端配置
frontend/.env*
```

### 3. Token 脱敏显示

在日志和输出中显示脱敏后的 Token：

```python
token_preview = f"{token[:10]}...{token[-5:]}"
print(f"Token: {token_preview}")
```

---

## 🛠️ **故障排查**

### 问题 1: Token 无效

**症状**:
```
抱歉，您没有接口访问权限
```

**解决**:
1. 检查 Token 是否正确
2. 确认积分是否足够（至少 120 分）
3. 重新获取新 Token

### 问题 2: 积分不足

**症状**:
```
积分不足，无法访问该接口
```

**解决**:
1. 完善个人信息（+100 分）
2. 参与社区贡献
3. 充值积分（https://tushare.pro/user/recharge）

### 问题 3: 网络连接失败

**症状**:
```
Connection timeout
```

**解决**:
1. 检查网络连接
2. 使用代理（如果需要）
3. 稍后重试

---

## 📋 **验证清单**

- [x] Tushare 库已安装（v1.4.25）
- [x] Token 已配置在 `.env` 文件
- [ ] OpenClaw Skills 已安装（如使用 OpenClaw）
- [ ] Token 已在 OpenClaw 中配置（如使用 OpenClaw）
- [ ] 测试获取股票列表
- [ ] 测试获取日线行情
- [ ] 测试获取指数数据

---

## 🎓 **学习资源**

### 官方文档

- Tushare Pro: https://tushare.pro/
- 接口文档：https://tushare.pro/document/1?doc_id=108
- 积分规则：https://tushare.pro/document/1?doc_id=12

### GitHub 资源

- Tushare Skills: https://github.com/waditu-tushare/skills
- Tushare 源码：https://github.com/waditu/tushare

### 示例代码

- 股票分析示例：`backend/examples/stock_analysis.py`
- 指数分析示例：`backend/examples/index_analysis.py`

---

## 💡 **最佳实践**

### 1. 使用数据源降级

系统已实现自动降级机制：

```python
# 优先级：Tushare → AkShare → Baostock
DATA_SOURCE_PRIORITY = ["tushare", "akshare", "baostock"]
```

### 2. 缓存数据

使用系统内置缓存：

```python
# 内存缓存（TTL: 300 秒）
cache.set("stock_000001", data, ttl=300)

# 数据库缓存
await data_persistence.save_klines(code, klines, "qfq")
```

### 3. 批量查询

```python
# ✅ 推荐：批量查询
codes = ["000001.SZ", "000002.SZ", "000063.SZ"]
for code in codes:
    df = pro.daily(ts_code=code)

# ❌ 不推荐：单次查询过多
# df = pro.daily(ts_code="all")  # 会超时
```

---

## 📞 **获取帮助**

### 遇到问题？

1. **查看文档**: https://tushare.pro/document/1
2. **社区论坛**: https://tushare.pro/community
3. **GitHub Issues**: https://github.com/waditu/tushare/issues

### 联系方式

- Tushare 官方：support@tushare.pro
- 项目 Issues: https://github.com/your-project/issues

---

**文档更新时间**: 2026-03-12  
**维护者**: AI Assistant  
**状态**: ✅ 配置完成，可以使用
