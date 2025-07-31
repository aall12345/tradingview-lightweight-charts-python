# TradingView 轻量级图表 - 带搜索功能

这是一个基于 TradingView Lightweight Charts 的 Python 图表库，专门为数据分析和交易图表显示而优化。

## 🎯 主要功能

- **智能Symbol搜索**：支持从数据库中搜索5000+个交易品种
- **实时数据显示**：连接MySQL数据库，实时显示K线数据
- **多时间周期**：支持1小时、日线、周线、月线切换
- **交互式图表**：支持缩放、拖拽、十字线等交互功能
- **自定义样式**：空心K线、自定义颜色、图例显示

## 🚀 快速开始

### 运行主程序
```bash
python3 lightweight_charts/show_view.py
```

### 基本使用
```python
from lightweight_charts import Chart

# 创建图表
chart = Chart()

# 设置数据
chart.set(your_dataframe)

# 显示图表
chart.show(block=True)
```

## 🔍 搜索功能

### 使用方法
1. **键盘搜索**：在图表界面按任意字母或数字键打开搜索框
2. **输入Symbol**：输入要搜索的交易品种名称（支持模糊搜索）
3. **确认搜索**：按回车键确认，按ESC键取消

### 搜索示例
- 输入 `btc` → 自动匹配到 `btcusdt`
- 输入 `eth` → 自动匹配到 `ethusdt`
- 输入 `000001` → 精确匹配股票代码
- 输入 `usdt` → 显示所有USDT交易对

### 快捷键
- **Ctrl+L**：显示可用Symbol列表
- **任意字母/数字**：打开搜索框

## 📊 支持的数据类型

### 加密货币（641个）
- BTC/USDT, ETH/USDT 等主流交易对
- 各种山寨币交易对

### 股票（5133个）
- A股股票代码（如：000001, 600519）
- 其他市场股票

## 🛠️ 配置要求

### 数据库配置
```python
# MySQL连接配置
driver = 'pymysql'
username = 'root'
password = 'your_password'
host = 'localhost'
port = 3390
dbname = 'analysis_system'
```

### 依赖包
- `pandas` - 数据处理
- `sqlalchemy` - 数据库ORM
- `pymysql` - MySQL驱动

## 📁 项目结构

```
lightweight_charts/
├── __init__.py          # 模块初始化
├── abstract.py          # 抽象基类
├── chart.py            # 图表核心类
├── show_view.py        # 主程序入口 ⭐
├── topbar.py           # 顶部工具栏
├── util.py             # 工具函数
└── js/                 # JavaScript文件
    ├── callback.js     # 回调处理
    ├── funcs.js        # 核心函数
    └── pkg.js          # 图表包
```

## 🎮 功能特点

### 智能搜索
- **精确匹配**：完整Symbol名称优先
- **模糊搜索**：部分字符匹配
- **自动选择**：智能选择最佳匹配
- **大小写不敏感**：支持任意大小写

### 数据处理
- **时间重采样**：自动转换不同时间周期
- **数据优化**：自动处理数据格式
- **错误处理**：完善的异常处理机制

### 用户体验
- **实时反馈**：搜索状态即时显示
- **智能提示**：显示匹配结果和建议
- **快捷操作**：键盘快捷键支持

## 📈 使用示例

### 基本图表显示
```python
import pandas as pd
from lightweight_charts import Chart

# 创建图表
chart = Chart()

# 加载数据
df = pd.read_csv('your_data.csv')
chart.set(df)

# 显示图表
chart.show(block=True)
```

### 带搜索功能的图表
```python
# 直接运行主程序
python3 lightweight_charts/show_view.py
```

## 🔧 自定义配置

### 图表样式
- 空心K线设计
- 自定义颜色方案
- 图例和价格显示
- 时间格式化

### 数据库连接
- 支持MySQL数据库
- 可配置连接参数
- 自动重连机制

## 📝 更新日志

### 最新版本
- ✅ 添加智能Symbol搜索功能
- ✅ 支持5000+交易品种
- ✅ 优化用户交互体验
- ✅ 移除不必要的依赖
- ✅ 简化项目结构

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目基于 MIT 许可证开源。
