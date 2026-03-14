# Tushare 使用指南

本指南将帮助您学习如何安装、配置和使用 Tushare 数据接口。

## 📚 目录

- [Tushare 简介](#tushare-简介)
- [安装指南](#安装指南)
- [配置 Token](#配置-token)
- [快速开始](#快速开始)
- [常用接口](#常用接口)
- [HTTP 协议方式](#http-协议方式)
- [注意事项](#注意事项)
- [故障排除](#故障排除)

## Tushare 简介

Tushare 是一个免费、开源的 Python 财经数据接口包，主要提供股票、基金、期货、债券等金融数据。

**特点:**
- 🆓 免费开源
- 📊 数据丰富
- 🚀 调用简单
- 🔄 持续更新

**官方网站:** https://tushare.pro

## 安装指南

### 方式 1: pip 安装 (推荐)

```bash
# 标准安装
pip install tushare

# 使用国内镜像源 (如果网络超时)
pip install tushare -i https://pypi.tuna.tsinghua.edu.cn/simple

# 使用阿里云镜像
pip install tushare -i https://mirrors.aliyun.com/pypi/simple/
```

### 方式 2: 从 PyPI 下载

1. 访问 https://pypi.python.org/pypi/tushare/
2. 下载压缩包
3. 解压后进入目录
4. 执行：`python setup.py install`

### 方式 3: 从 GitHub 安装

```bash
git clone https://github.com/waditu/tushare.git
cd tushare
python setup.py install
```

### 升级 Tushare

```bash
pip install tushare --upgrade
```

### 查看版本

```python
import tushare
print(tushare.__version__)
```

## 配置 Token

### 1. 获取 Token

1. 访问 https://tushare.pro
2. 注册账号
3. 登录后进入个人中心
4. 复制 Token (一串字符)

### 2. 设置 Token

**方法 1: 使用 set_token (推荐)**

```python
import tushare as ts

# 只需要在第一次调用，token 会保存在本地
ts.set_token('your_token_here')
```

**方法 2: 环境变量 (推荐用于生产环境)**

```bash
# .env 文件
TUSHARE_TOKEN=your_token_here
```

```python
import tushare as ts
import os

token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
```

**方法 3: 直接在 pro_api 中传入**

```python
import tushare as ts

pro = ts.pro_api('your_token_here')
```

## 快速开始

### 基本使用流程

```python
import tushare as ts

# 1. 设置 token
ts.set_token('your_token')

# 2. 初始化接口
pro = ts.pro_api()

# 3. 调用接口
df = pro.trade_cal(
    exchange='',
    start_date='20240101',
    end_date='20240131'
)

# 4. 查看结果
print(df)
```

### 运行测试脚本

本项目提供了测试脚本，可以快速验证配置:

```bash
cd backend
python examples/test_tushare.py
```

### 运行完整教程

```bash
python examples/tushare_tutorial.py
```

## 常用接口

### 1. 交易日历

```python
# 获取交易日历
df = pro.trade_cal(
    exchange='',  # 交易所 SSE/SZSE
    start_date='20240101',
    end_date='20240131',
    is_open='1'  # 1:开市 0:休市
)
```

### 2. 股票基本信息

```python
# 获取股票列表
df = pro.stock_basic(
    exchange='SSE',  # 交易所
    list_status='L',  # L:上市 D:退市 P:暂停
    fields='ts_code,symbol,name,area,industry'
)
```

### 3. 日线行情

```python
# 获取日线数据
df = pro.daily(
    ts_code='000001.SZ',
    start_date='20240101',
    end_date='20240131',
    fields='ts_code,trade_date,open,high,low,close,vol,amount'
)
```

### 4. 实时行情

```python
# 获取实时行情
df = pro.realtime(
    ts_code='000001.SZ',
    fields='ts_code,name,price,change,pct_chg,vol,amount'
)
```

### 5. 复权因子

```python
# 获取复权因子
df = pro.adj_factor(
    ts_code='000001.SZ',
    start_date='20240101',
    end_date='20240131'
)
```

### 6. 资金流向

```python
# 获取资金流向
df = pro.moneyflow(
    ts_code='000001.SZ',
    start_date='20240101',
    end_date='20240131'
)
```

### 7. 技术指标

```python
# MACD 指标
df = pro.macd(
    ts_code='000001.SZ',
    start_date='20240101',
    end_date='20240131'
)

# KDJ 指标
df = pro.kdj(
    ts_code='000001.SZ',
    start_date='20240101',
    end_date='20240131'
)
```

### 8. 板块信息

```python
# 行业板块分类
df = pro.index_classify(
    level='L1',  # L1:一级 L2:二级
    src='SW2021'  # 申万行业分类
)

# 板块成分
df = pro.index_member(
    index_code='801010',
    fields='ts_code,name'
)
```

## HTTP 协议方式

Tushare Pro 也支持 HTTP RESTful API，可以使用任何编程语言调用。

### 请求格式

```bash
curl -X POST -d '{
    "api_name": "trade_cal",
    "token": "your_token",
    "params": {
        "exchange":"",
        "start_date":"20240101",
        "end_date":"20240131",
        "is_open":"1"
    },
    "fields": "exchange,cal_date,is_open"
}' http://api.tushare.pro
```

### 返回格式

```json
{
    "code": 0,
    "msg": null,
    "data": {
        "fields": ["exchange", "cal_date", "is_open"],
        "items": [
            ["SSE", "20240101", 0],
            ["SSE", "20240102", 1],
            ...
        ]
    }
}
```

### Python HTTP 请求示例

```python
import requests
import json

url = 'http://api.tushare.pro'
headers = {'content-type': 'application/json'}

payload = {
    'api_name': 'trade_cal',
    'token': 'your_token',
    'params': {
        'exchange': '',
        'start_date': '20240101',
        'end_date': '20240131',
        'is_open': '1'
    },
    'fields': 'exchange,cal_date,is_open'
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()

print(result['data'])
```

## 注意事项

### 1. Token 安全

- ⚠️ **不要**将 Token 提交到版本控制系统
- ✅ 使用环境变量管理 Token
- ✅ 定期更换 Token
- ✅ 在 `.gitignore` 中添加 `.env`

### 2. 积分制度

Tushare 采用积分制度:

- 🆓 基础数据接口免费
- 💰 高级数据接口需要积分
- 📈 可以通过以下方式获取积分:
  - 注册送 100 积分
  - 每日签到
  - 社区贡献
  - 充值

### 3. 调用频率

- ⏱️ 注意 API 调用频率限制
- 💾 建议使用缓存机制
- 🔄 避免频繁重复调用
- 📊 批量获取数据

### 4. 数据格式

- 📅 日期格式：`YYYYMMDD` (如：`20240101`)
- 📝 股票代码：`000001.SZ` (平安银行)
- 📊 返回数据：pandas DataFrame 格式

### 5. 错误处理

| 错误码 | 说明 | 解决方法 |
|--------|------|----------|
| 2002 | 权限不足 | 检查积分或升级 |
| 4001 | Token 无效 | 检查 Token 是否正确 |
| 4002 | 参数错误 | 检查参数格式 |
| 5000 | 网络错误 | 检查网络连接 |

## 故障排除

### 问题 1: 安装失败

**症状:** `pip install tushare` 失败

**解决:**
```bash
# 使用国内镜像
pip install tushare -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install tushare -i https://mirrors.aliyun.com/pypi/simple/
```

### 问题 2: Token 无效

**症状:** `code: 4001, msg: token 无效`

**解决:**
1. 检查 Token 是否正确复制
2. 重新获取 Token
3. 确保 Token 未过期

### 问题 3: 权限不足

**症状:** `code: 2002, msg: 您没有权限访问该数据接口`

**解决:**
1. 检查积分是否足够
2. 升级账户
3. 使用免费接口

### 问题 4: 网络超时

**症状:** 请求超时或连接失败

**解决:**
1. 检查网络连接
2. 使用重试机制
3. 增加超时时间
4. 使用国内网络环境

### 问题 5: 数据为空

**症状:** 接口返回空数据

**解决:**
1. 检查日期范围是否正确
2. 检查股票代码是否正确
3. 检查是否为交易日
4. 查看接口文档确认参数

## 常用股票代码

### A 股市场

| 代码 | 名称 | 交易所 |
|------|------|--------|
| 000001.SZ | 平安银行 | 深交所 |
| 000002.SZ | 万科 A | 深交所 |
| 600000.SH | 浦发银行 | 上交所 |
| 600519.SH | 贵州茅台 | 上交所 |

### 主要指数

| 代码 | 名称 |
|------|------|
| 000001.SH | 上证指数 |
| 399001.SZ | 深证成指 |
| 399006.SZ | 创业板指 |

## 相关资源

- 🌐 官方网站：https://tushare.pro
- 📚 接口文档：https://tushare.pro/document/2
- 💬 社区论坛：https://tushare.pro/user/index
- 📖 GitHub: https://github.com/waditu/tushare

## 示例代码

查看以下示例文件学习如何使用 Tushare:

- `examples/tushare_tutorial.py` - 完整教程
- `examples/test_tushare.py` - 快速测试

---

**最后更新:** 2024-01
**维护者:** Quant Team
