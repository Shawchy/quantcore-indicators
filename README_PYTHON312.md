# 量化分析系统 - Python 3.12.10 环境配置

## 📋 系统信息

- **Python版本**: 3.12.10
- **虚拟环境**: venv312
- **安装日期**: 2025-03-10
- **依赖包**: 已全部安装完成

## 🚀 快速启动

### 启动后端服务

双击运行 `start_backend.bat` 或在命令行中执行：

```bash
# Windows
start_backend.bat

# 或手动启动
venv312\Scripts\activate
cd backend
python main.py
```

服务启动后访问：
- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📦 已安装的核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.135.1 | Web框架 |
| Pandas | 3.0.1 | 数据处理 |
| NumPy | 2.2.6 | 数值计算 |
| Pydantic | 2.12.5 | 数据验证 |
| SQLAlchemy | 2.0.48 | ORM |
| PyArrow | 23.0.1 | 数据存储 |
| Polars | 1.38.1 | 高性能数据处理 |
| AkShare | 1.18.37 | 中国股市数据 |
| Baostock | 0.8.9 | 免费证券数据 |
| yFinance | 1.2.0 | 美股数据 |

## 🔧 环境管理

### 激活虚拟环境

```bash
# Windows PowerShell
.\venv312\Scripts\Activate.ps1

# Windows CMD
venv312\Scripts\activate.bat
```

### 退出虚拟环境

```bash
deactivate
```

### 安装新的依赖包

```bash
# 激活虚拟环境后
pip install package_name

# 或使用国内镜像
pip install package_name -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 更新依赖包

```bash
# 更新所有包
pip list --outdated

# 更新特定包
pip install --upgrade package_name
```

## 📝 项目结构

```
quantitative-analyst/
├── backend/              # 后端服务
│   ├── app/             # 应用代码
│   ├── main.py          # 启动文件
│   └── requirements.txt # 依赖列表
├── frontend/            # 前端应用
├── venv312/            # Python 3.12.10 虚拟环境
├── start_backend.bat    # 后端启动脚本
└── README_PYTHON312.md  # 本文件
```

## 🧪 验证安装

运行验证脚本检查环境：

```bash
.\venv312\Scripts\python.exe verify_install.py
```

预期输出：
```
Python版本: 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
Python路径: M:\Project\Quant\quantitative-analyst\venv312\Scripts\python.exe
FastAPI版本: 0.135.1
Pandas版本: 3.0.1
NumPy版本: 2.2.6
Pydantic版本: 2.12.5

✅ 所有核心依赖包验证完成！
```

## 🌐 常用命令

```bash
# 查看Python版本
python --version

# 查看已安装的包
pip list

# 查看包的详细信息
pip show package_name

# 导出依赖列表
pip freeze > requirements.txt

# 从requirements.txt安装
pip install -r requirements.txt
```

## 📚 Python 3.12.10 新特性

- 更好的错误提示
- 性能优化（相比3.11提升5-10%）
- f-string改进
- 类型系统增强
- 更好的并发性能

## ⚠️ 注意事项

1. **虚拟环境**: 始终在虚拟环境中工作，避免污染系统Python
2. **依赖管理**: 使用requirements.txt管理依赖
3. **版本控制**: 不要将venv312目录提交到Git
4. **安全更新**: 定期更新依赖包以获取安全修复

## 🔍 故障排除

### 虚拟环境激活失败

如果PowerShell提示执行策略错误，运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 依赖包安装失败

使用国内镜像源：

```bash
pip install package_name -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 端口被占用

修改 `backend/app/config.py` 中的端口配置：

```python
# 默认端口: 8000
# 如果被占用，可以改为其他端口
```

## 📞 技术支持

如有问题，请检查：
1. Python版本是否为3.12.10
2. 虚拟环境是否正确激活
3. 所有依赖包是否已安装
4. 端口是否被占用

---

**配置完成时间**: 2025-03-10  
**Python版本**: 3.12.10  
**状态**: ✅ 环境配置完成，可以开始使用