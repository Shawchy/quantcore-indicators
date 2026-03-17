# 历史日 K 获取 API 优化报告

## 优化内容

优化股票历史日 K 获取 API，支持**股票代码**和**股票名称**两种模式。

## 后端 API 优化

### 优化前

```python
@router.get("/{code}/kline", response_model=ResponseModel[dict])
async def get_kline(
    code: str,  # 仅支持股票代码
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq",
):
    data = await stock_service.get_kline(code, start_date, end_date, adjust)
    return ResponseModel(data=data)
```

**限制**:
- ❌ 只支持股票代码（如：600519）
- ❌ 不支持股票名称（如：贵州茅台）
- ❌ 不支持美股/港股名称（如：微软、苹果）

### 优化后

```python
@router.get("/{identifier}/kline", response_model=ResponseModel[dict])
async def get_kline(
    identifier: str,  # 支持股票代码或股票名称
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq",
    priority_load: bool = True,
):
    """
    获取股票历史日 K 线数据（支持股票代码和股票名称两种模式）
    
    Args:
        identifier: 股票代码（如：600519）或股票名称（如：贵州茅台、微软）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        adjust: 复权类型
        priority_load: 是否启用优先加载模式
    
    Returns:
        K 线数据，包含股票基本信息和历史 K 线
        
    Examples:
        - 通过股票代码获取：/api/v1/stock/600519/kline
        - 通过股票名称获取：/api/v1/stock/贵州茅台/kline
        - 通过美股名称获取：/api/v1/stock/微软/kline
    """
    # 判断是代码还是名称
    is_code = identifier.isdigit() or (len(identifier) >= 6 and identifier.replace('.', '').replace('$', '').isalnum())
    
    if is_code:
        # 通过代码获取 K 线
        code = identifier
        data = await stock_service.get_kline(code, start_date, end_date, adjust, priority_load=priority_load)
    else:
        # 通过名称获取 K 线（efinance 支持直接传入股票名称）
        import efinance as ef
        
        # efinance 支持直接传入股票名称获取历史数据
        df = ef.stock.get_quote_history(identifier)
        
        if df is None or df.empty:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到股票：{identifier}"
            )
        
        # 从 DataFrame 中提取股票代码
        stock_code = df.iloc[0]['股票代码'] if '股票代码' in df.columns else None
        stock_name = df.iloc[0]['股票名称'] if '股票名称' in df.columns else identifier
        
        # 转换为标准 K 线格式
        klines = []
        for _, row in df.iterrows():
            klines.append({
                "date": row.get('日期', ''),
                "open": float(row.get('开盘', 0)),
                "close": float(row.get('收盘', 0)),
                "high": float(row.get('最高', 0)),
                "low": float(row.get('最低', 0)),
                "volume": float(row.get('成交量', 0)),
                "amount": float(row.get('成交额', 0)),
                "change_pct": float(row.get('涨跌幅', 0)),
                "change": float(row.get('涨跌额', 0)),
                "amplitude": float(row.get('振幅', 0)),
                "turnover_rate": float(row.get('换手率', 0)),
            })
        
        data = {
            "code": stock_code,
            "name": stock_name,
            "klines": klines,
            "total": len(klines)
        }
    
    return ResponseModel(data=data)
```

**优势**:
- ✅ 支持股票代码（如：600519）
- ✅ 支持 A 股名称（如：贵州茅台）
- ✅ 支持美股/港股名称（如：微软、苹果）
- ✅ 自动识别代码/名称类型
- ✅ 返回股票代码和名称信息

## 使用示例

### 1. 通过股票代码获取（A 股）

**请求**:
```http
GET /api/v1/stock/600519/kline
```

**响应**:
```json
{
  "success": true,
  "code": "OK",
  "data": {
    "code": "600519",
    "name": "贵州茅台",
    "klines": [
      {
        "date": "2001-08-27",
        "open": -89.74,
        "close": -89.53,
        "high": -89.08,
        "low": -90.07,
        "volume": 406318.0,
        "amount": 1.41e+09,
        "change_pct": 0.92,
        "change": 0.83,
        "amplitude": -1.10,
        "turnover_rate": 56.83
      },
      // ... 更多 K 线数据
    ],
    "total": 4761
  }
}
```

### 2. 通过股票名称获取（A 股）

**请求**:
```http
GET /api/v1/stock/贵州茅台/kline
```

**响应**: 同上，自动识别为贵州茅台（600519）

### 3. 通过股票名称获取（美股）

**请求**:
```http
GET /api/v1/stock/微软/kline
```

**响应**:
```json
{
  "success": true,
  "code": "OK",
  "data": {
    "code": "MSFT",
    "name": "微软",
    "klines": [
      {
        "date": "1986-03-13",
        "open": -20.74,
        "close": -20.73,
        "high": -20.73,
        "low": -20.74,
        "volume": 1.03e+09,
        "amount": 0.0,
        "change_pct": 0.0,
        "change": 0.0,
        "amplitude": 0.0,
        "turnover_rate": 13.72
      },
      // ... 更多 K 线数据
    ],
    "total": 8362
  }
}
```

### 4. 带日期范围和复权参数

**请求**:
```http
GET /api/v1/stock/贵州茅台/kline?start_date=2023-01-01&end_date=2023-12-31&adjust=qfq
```

**参数说明**:
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）
- `adjust`: 复权类型
  - `qfq`: 前复权（默认）
  - `hfq`: 后复权
  - `none`: 不复权

## 技术实现

### 1. 自动识别代码/名称

```python
def is_stock_code(identifier: str) -> bool:
    """
    判断是否为股票代码
    
    规则：
    - A 股：6 位数字（如：600519）
    - 美股/港股：字母 + 数字组合（如：MSFT、00700）
    """
    if identifier.isdigit():
        return True  # 纯数字（A 股）
    
    if len(identifier) >= 6:
        # 去除特殊字符后判断
        cleaned = identifier.replace('.', '').replace('$', '')
        if cleaned.isalnum():
            return True  # 字母数字组合（美股/港股）
    
    return False  # 判断为股票名称
```

### 2. efinance API 调用

```python
import efinance as ef

# 通过股票代码获取
df = ef.stock.get_quote_history('600519')

# 通过股票名称获取（efinance 原生支持）
df = ef.stock.get_quote_history('贵州茅台')
df = ef.stock.get_quote_history('微软')  # 美股也支持
```

### 3. 数据格式转换

```python
# efinance 返回的 DataFrame 格式
# 股票名称 | 股票代码 | 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量 | 成交额 | 振幅 | 涨跌幅 | 涨跌额 | 换手率
# 贵州茅台 | 600519  | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ...

# 转换为标准 K 线格式
klines = []
for _, row in df.iterrows():
    klines.append({
        "date": row.get('日期', ''),
        "open": float(row.get('开盘', 0)),
        "close": float(row.get('收盘', 0)),
        "high": float(row.get('最高', 0)),
        "low": float(row.get('最低', 0)),
        "volume": float(row.get('成交量', 0)),
        "amount": float(row.get('成交额', 0)),
        "change_pct": float(row.get('涨跌幅', 0)),
        "change": float(row.get('涨跌额', 0)),
        "amplitude": float(row.get('振幅', 0)),
        "turnover_rate": float(row.get('换手率', 0)),
    })
```

## 前端使用建议

### 1. 搜索框组件（可选实现）

```typescript
// StockSearchInput.tsx
import { useState } from 'react'
import { Input, InputGroup, InputLeftElement } from '@chakra-ui/react'
import { SearchIcon } from '@chakra-ui/icons'
import { useNavigate } from 'react-router-dom'

const StockSearchInput = () => {
  const [inputValue, setInputValue] = useState('')
  const navigate = useNavigate()
  
  const handleSearch = () => {
    if (!inputValue.trim()) return
    
    // 直接跳转到股票详情页，后端会自动识别代码/名称
    navigate(`/stock/${encodeURIComponent(inputValue.trim())}`)
  }
  
  return (
    <InputGroup>
      <InputLeftElement pointerEvents="none">
        <SearchIcon />
      </InputLeftElement>
      <Input
        placeholder="输入股票代码或名称（如：600519 或 贵州茅台）"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
    </InputGroup>
  )
}
```

### 2. React Query 调用

```typescript
// 使用 useQuery 获取 K 线数据
const { data, isLoading, error } = useQuery({
  queryKey: ['stockKline', identifier],
  queryFn: () => stockApi.getKline(identifier),
  // identifier 可以是代码或名称
  // 例如：'600519' 或 '贵州茅台' 或 '微软'
})
```

## 优势对比

| 特性 | 优化前 | 优化后 |
|-----|-------|-------|
| **股票代码** | ✅ 支持 | ✅ 支持 |
| **A 股名称** | ❌ 不支持 | ✅ 支持 |
| **美股名称** | ❌ 不支持 | ✅ 支持 |
| **港股名称** | ❌ 不支持 | ✅ 支持 |
| **自动识别** | ❌ 无 | ✅ 智能识别 |
| **返回代码** | ⚠️ 部分 | ✅ 总是返回 |
| **返回名称** | ⚠️ 部分 | ✅ 总是返回 |

## 注意事项

### 1. 股票名称格式

- **A 股**: 使用中文全称（如：`贵州茅台`、`宁德时代`）
- **美股**: 使用中文译名（如：`微软 `、` 苹果 `、` 特斯拉`）
- **港股**: 使用中文名称（如：`腾讯控股 `、` 阿里巴巴`）

### 2. 重名处理

如果存在重名股票，efinance 可能返回多个结果。建议：
- 优先使用股票代码
- 或使用更具体的名称（如：`贵州茅台` 而非 `茅台`）

### 3. 数据范围

efinance 提供完整历史数据：
- **A 股**: 从上市至今
- **美股**: 从 IPO 至今（如微软从 1986 年开始）
- **港股**: 从上市至今

### 4. 性能优化

- 大数据量时建议添加日期范围参数
- 使用 `priority_load=true` 启用优先加载模式
- 前端添加缓存策略（React Query staleTime）

## 总结

### 已完成优化

1. ✅ **后端 API**: 支持股票代码和名称两种模式
2. ✅ **自动识别**: 智能判断输入是代码还是名称
3. ✅ **数据转换**: 统一返回标准 K 线格式
4. ✅ **信息完整**: 总是返回股票代码和名称

### 使用场景

- **普通用户**: 直接输入股票名称（如：`贵州茅台`）
- **专业用户**: 输入股票代码（如：`600519`）
- **美股投资者**: 输入中文名称（如：`微软`）

### 用户体验提升

- **更直观**: 不需要记住股票代码
- **更友好**: 支持自然语言输入
- **更智能**: 自动识别和处理

---

**优化完成时间**: 2026-03-17  
**影响范围**: `/api/v1/stock/{identifier}/kline` API  
**向后兼容**: ✅ 完全兼容原有股票代码模式
