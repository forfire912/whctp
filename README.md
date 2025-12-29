# CTP期货交易管理系统

基于Python和Tkinter开发的期货交易数据管理系统，支持通过CTP API定期下载交易数据，并存储到MySQL数据库中进行查询和管理。

## 功能特性

- ✅ **CTP API集成**：封装期货公司提供的CTP交易和行情接口
- ✅ **数据下载**：支持下载委托、持仓、行情和合约参数等数据
- ✅ **数据存储**：自动创建MySQL数据库表结构并存储数据
- ✅ **数据查询**：提供多维度的数据查询和筛选功能
- ✅ **界面管理**：友好的图形界面，支持数据展示和导出
- ✅ **自动下载**：支持定时自动下载数据
- ✅ **配置管理**：支持保存和加载连接配置

## 系统架构

```
whctp/
├── api/                    # CTP API头文件和文档
│   ├── mdapi/             # 行情API
│   └── traderapi/         # 交易API
├── req/                    # 需求文件和示例数据
│   ├── 当日委托.csv
│   └── 当日持仓.csv
├── ctp_api_wrapper.py      # CTP API封装类
├── database_manager.py     # 数据库管理模块
├── data_importer.py        # CSV数据导入工具
├── main_gui.py             # 主界面程序
├── config.json             # 配置文件（运行后生成）
├── requirements.txt        # Python依赖
└── README.md              # 说明文档
```

## 数据库表结构

系统自动创建以下数据表：

1. **daily_orders** - 当日委托表
   - 委托时间、合约代码、买卖方向、开平标志
   - 委托价格、委托量、成交量、订单状态等

2. **daily_positions** - 当日持仓表
   - 合约代码、持仓方向、持仓类型
   - 持仓量、可用持仓、开仓均价、盈亏等

3. **market_data** - 商品行情表
   - 合约代码、最新价、涨跌幅、成交量
   - 开高低收、买卖盘口等实时行情数据

4. **instrument_info** - 商品参数表
   - 合约基本信息、交易所、品种类型
   - 合约乘数、最小变动价位、保证金率等

## 安装说明

### 1. 环境要求

- Python 3.7+
- MySQL 5.7+ 或 MariaDB 10.3+
- CTP API动态库（需要从期货公司获取）

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 安装MySQL数据库

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mysql-server
sudo mysql_secure_installation
```

**使用Docker (推荐):**
```bash
docker run -d \
  --name mysql-ctp \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=ctp_trading \
  -p 3306:3306 \
  mysql:8.0
```

### 4. 配置数据库

创建数据库和用户（如果还未创建）：

```sql
CREATE DATABASE IF NOT EXISTS ctp_trading CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ctp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ctp_trading.* TO 'ctp_user'@'localhost';
FLUSH PRIVILEGES;
```

## 使用说明

### 1. 启动程序

```bash
python main_gui.py
```

### 2. 配置连接

在界面上填写以下信息：

**CTP配置：**
- 经纪商代码（如：9999）
- 用户名和密码
- 交易前置地址（从期货公司获取）
- 行情前置地址（从期货公司获取）

**数据库配置：**
- 主机地址（localhost）
- 用户名（root 或 ctp_user）
- 密码

### 3. 连接系统

1. 填写完配置后，点击"保存配置"按钮
2. 点击"连接"按钮，系统会自动：
   - 连接MySQL数据库
   - 创建数据库表结构
   - 连接CTP交易系统
   - 登录交易账户

### 4. 下载数据

连接成功后，可以：
- 点击"下载委托数据"获取当日委托记录
- 点击"下载持仓数据"获取当前持仓情况
- 点击"下载行情数据"订阅实时行情
- 点击"下载合约参数"获取合约基本信息

### 5. 查询数据

在各个标签页中：
- 输入查询条件（交易日、合约代码等）
- 点击"查询"按钮显示数据
- 支持导出数据到CSV文件

### 6. 自动下载

- 勾选"自动下载"复选框
- 设置下载间隔（秒）
- 系统将定时自动下载委托和持仓数据

## 数据导入工具

如果已有CSV格式的历史数据，可以使用导入工具：

```bash
python data_importer.py
```

或在代码中使用：

```python
from database_manager import DatabaseManager
from data_importer import DataImporter

# 初始化
db = DatabaseManager(host="localhost", user="root", password="password")
db.connect()

importer = DataImporter(db)

# 导入委托数据
importer.import_orders_from_csv("req/当日委托.csv", trading_day="20250129")

# 导入持仓数据
importer.import_positions_from_csv("req/当日持仓.csv", trading_day="20250129")

db.close()
```

## 配置文件说明

`config.json` 示例：

```json
{
    "ctp": {
        "broker_id": "9999",
        "user_id": "123456",
        "password": "password",
        "trade_front": "tcp://180.168.146.187:10130",
        "market_front": "tcp://180.168.146.187:10131",
        "app_id": "",
        "auth_code": ""
    },
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_password",
        "database": "ctp_trading"
    },
    "auto_download": {
        "enabled": false,
        "interval": 300
    }
}
```

## 注意事项

### 1. CTP API库

本程序提供了CTP API的封装框架，实际使用时需要：

- 从期货公司获取CTP API动态库文件
- 安装Python的CTP绑定库，如：
  - `openctp-ctp` (开源CTP)
  - `ctp` (官方或第三方封装)
  
安装示例：
```bash
pip install openctp-ctp
```

然后修改 `ctp_api_wrapper.py` 中的实际API调用。

### 2. 数据安全

- 配置文件包含敏感信息，请妥善保管
- 建议使用独立的数据库用户，限制权限
- 定期备份数据库

### 3. 交易时间

- 期货交易有特定的交易时段
- 夜盘时间：21:00-次日02:30
- 日盘时间：09:00-15:00
- 建议在交易时间内使用自动下载功能

### 4. API限流

CTP API对查询频率有限制：
- 避免过于频繁的查询
- 建议自动下载间隔不少于60秒
- 遇到限流错误时需等待后重试

## 开发和扩展

### 添加新的数据表

在 `database_manager.py` 的 `_create_tables()` 方法中添加新表结构。

### 自定义查询条件

在 `database_manager.py` 中添加新的查询方法。

### 扩展UI功能

在 `main_gui.py` 中添加新的标签页和功能按钮。

### 接入实际CTP API

修改 `ctp_api_wrapper.py`，将模拟实现替换为真实的API调用。

## 常见问题

### Q1: 连接数据库失败？

检查：
- MySQL服务是否启动
- 用户名密码是否正确
- 防火墙是否开放3306端口

### Q2: CTP连接失败？

检查：
- 前置地址是否正确
- 用户名密码是否正确
- 是否在交易时间内
- 网络连接是否正常

### Q3: 数据显示为乱码？

- 确保CSV文件编码为GBK或UTF-8 with BOM
- 检查数据库字符集是否为utf8mb4

### Q4: 如何查看历史数据？

在查询条件中输入历史交易日期，点击查询即可。

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 联系方式

如有问题或建议，请提交Issue或联系开发者。

## 更新日志

### v1.0.0 (2025-01-29)
- 初始版本发布
- 实现基本的数据下载和查询功能
- 支持MySQL数据存储
- 提供Tkinter图形界面
