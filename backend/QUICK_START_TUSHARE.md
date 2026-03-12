# 🚀 Tushare 快速配置指南

## 现状

✅ **代码已开发完成**  
✅ **Token 已配置** (`25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de`)  
⚠️ **需要获取积分** (当前 Token 没有积分，无法访问 API)

## 3 步完成配置

### 步骤 1: 注册/登录 Tushare

访问：https://tushare.pro/

- 如果没有账号，点击"注册"
- 如果已有账号，直接登录

### 步骤 2: 获取您的 Token

1. 登录后点击右上角用户名 → **个人中心**
2. 左侧菜单选择 **接口 TOKEN**
3. 复制您的 Token（40 位字母数字组合）

### 步骤 3: 替换 Token

打开文件：`backend/.env`

找到这一行：
```env
TUSHARE_TOKEN=25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de
```

替换为您的 Token：
```env
TUSHARE_TOKEN=您的 token 在这里
```

### 步骤 4: 获取积分（重要！）

**没有积分无法使用 API！**

#### 免费获取积分方法：

| 任务 | 积分 | 说明 |
|------|------|------|
| 注册账号 | +100 | 自动赠送 |
| 完善个人信息 | +50 | 个人中心 → 修改资料 |
| 关注公众号 | +50 | 关注"Tushare 社区"公众号 |
| 邀请好友 | +50/人 | 邀请码注册 |

**总计**: 最少可获得 **200 积分**（足够使用基础功能）

#### 积分用途：

- **100 积分**: 日线 K 线、分钟 K 线、股票列表（基础功能）
- **500 积分**: 实时行情、财务数据、资金流向
- **1000+ 积分**: 高级数据、Level2 数据

### 步骤 5: 验证配置

运行测试脚本：

```bash
cd backend
python test_tushare_switch.py
```

**成功输出**:
```
[INFO] 数据源 tushare 初始化成功（优先级：1)
[INFO] 数据源工厂初始化完成，可用数据源：['tushare', 'akshare', 'baostock']
✅ 获取到 726 条 K 线数据
```

**失败输出**（没有积分）:
```
[ERROR] Tushare 连接测试失败：抱歉，您没有接口访问权限
⚠️ 数据源 tushare 初始化失败，尝试下一个
✅ 可用数据源：['akshare', 'baostock']
```

## 常见问题

### Q: 我不想配置 Tushare，可以吗？

**可以！** 系统会自动使用 AkShare 作为数据源。

修改 `backend/.env`:
```env
DEFAULT_DATA_SOURCE=akshare
```

### Q: Token 安全吗？

**安全！** 
- ✅ Token 在 `.env` 文件中，不会被提交到 Git
- ✅ `.env` 已在 `.gitignore` 中排除
- ⚠️ 不要分享您的 Token 给他人

### Q: 积分不够怎么办？

**不影响使用！** 系统会自动降级到 AkShare：
- Tushare 不可用 → 自动使用 AkShare
- AkShare 限流 → 自动使用 Baostock
- 完全无感切换

### Q: 如何查看当前使用的数据源？

查看启动日志：
```
[INFO] 当前默认数据源：tushare (实际使用：tushare)
```

或者运行测试脚本查看。

## 推荐配置

### 方案 A: Tushare 优先（推荐）

适合：有 Tushare Token 且有积分的用户

```env
DEFAULT_DATA_SOURCE=tushare
TUSHARE_TOKEN=您的 token
```

**优点**: 数据质量高、稳定性好、速度快  
**缺点**: 需要获取积分

### 方案 B: AkShare 优先

适合：不想配置 Tushare 的用户

```env
DEFAULT_DATA_SOURCE=akshare
# TUSHARE_TOKEN 不需要配置
```

**优点**: 免费、无需配置  
**缺点**: 偶尔会限流、数据质量略低

### 方案 C: 混合使用

适合：有 Tushare 但不想完全依赖的用户

```env
DEFAULT_DATA_SOURCE=tushare
TUSHARE_TOKEN=您的 token
DATA_SOURCE_PRIORITY=tushare,akshare,baostock
```

**优点**: 自动降级、高可用性  
**缺点**: 需要配置 Token

## 立即开始

1. **注册 Tushare**: https://tushare.pro/
2. **获取 Token**: 个人中心 → 接口 TOKEN
3. **获取积分**: 完成任务（至少 100 积分）
4. **替换 Token**: 修改 `backend/.env`
5. **测试验证**: 运行 `python test_tushare_switch.py`

## 需要帮助？

查看详细文档：[`TUSHARE_SETUP.md`](file:///d:/Project/Quant/backend/TUSHARE_SETUP.md)

查看集成报告：[`TUSHARE_INTEGRATION_REPORT.md`](file:///d:/Project/Quant/backend/TUSHARE_INTEGRATION_REPORT.md)

---

**最后更新**: 2026-03-12  
**状态**: ✅ 等待用户配置 Token 和积分
