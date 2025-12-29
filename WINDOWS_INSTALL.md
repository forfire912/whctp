# Windows安装和部署指南

本程序专为Windows平台设计，以下是详细的安装和配置步骤。

## 系统要求

- **操作系统**: Windows 10/11 或 Windows Server 2016+
- **Python**: 3.7+ (推荐 3.9 或 3.10)
- **MySQL**: 5.7+ 或 MariaDB 10.3+
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 1GB 可用空间

## 一、安装Python

### 方法1: 从官网下载

1. 访问 https://www.python.org/downloads/
2. 下载 Windows 安装包（推荐 Python 3.10）
3. 运行安装程序
   - ✅ 勾选 "Add Python to PATH"
   - ✅ 选择 "Install for all users"（可选）
   - 点击 "Install Now"

### 方法2: 使用Chocolatey

```powershell
# 在管理员PowerShell中运行
choco install python -y
```

### 验证安装

```cmd
python --version
pip --version
```

## 二、安装MySQL数据库

### 方法1: MySQL官方版本

1. 下载 MySQL Community Server
   - 访问 https://dev.mysql.com/downloads/mysql/
   - 选择 Windows (x86, 64-bit), ZIP Archive
   
2. 安装步骤
   - 运行 MySQL Installer
   - 选择 "Developer Default" 或 "Server only"
   - 设置 root 密码（请记住此密码）
   - 配置为 Windows 服务（自动启动）
   - 完成安装

### 方法2: 使用Docker Desktop（推荐）

```cmd
# 安装Docker Desktop for Windows
# 下载地址: https://www.docker.com/products/docker-desktop

# 启动MySQL容器
docker run -d ^
  --name mysql-ctp ^
  -e MYSQL_ROOT_PASSWORD=your_password ^
  -e MYSQL_DATABASE=ctp_trading ^
  -p 3306:3306 ^
  --restart=always ^
  mysql:8.0
```

### 方法3: XAMPP集成环境

1. 下载 XAMPP
   - 访问 https://www.apachefriends.org/
   - 下载 Windows 版本
   
2. 安装并启动 MySQL 服务

### 配置MySQL

打开MySQL命令行或使用Navicat/MySQL Workbench：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ctp_trading 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户（可选，更安全）
CREATE USER 'ctp_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON ctp_trading.* TO 'ctp_user'@'localhost';
FLUSH PRIVILEGES;
```

## 三、安装项目依赖

### 1. 下载项目代码

```cmd
# 使用git克隆（如果已安装git）
git clone https://github.com/yourusername/whctp.git
cd whctp

# 或者直接下载ZIP包解压
```

### 2. 安装Python依赖

```cmd
# 在项目根目录执行
pip install -r requirements.txt

# 如果下载速度慢，使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 安装CTP API（重要）

本程序需要CTP的Python绑定库。选择以下方案之一：

**方案A: 使用OpenCTP（推荐）**
```cmd
pip install openctp-ctp
```

**方案B: 使用官方CTP**
- 从期货公司获取CTP SDK
- 安装相应的Python绑定包

## 四、配置程序

### 1. 复制配置文件

```cmd
copy config.json.example config.json
```

### 2. 编辑配置文件

使用记事本或其他文本编辑器打开 `config.json`：

```json
{
    "ctp": {
        "broker_id": "9999",          // 经纪商代码（从期货公司获取）
        "user_id": "your_username",   // 你的用户名
        "password": "your_password",  // 你的密码
        "trade_front": "tcp://180.168.146.187:10130",  // 交易前置地址
        "market_front": "tcp://180.168.146.187:10131", // 行情前置地址
        "app_id": "",                 // AppID（如需要）
        "auth_code": ""               // 认证码（如需要）
    },
    "database": {
        "host": "localhost",          // MySQL主机
        "port": 3306,                 // MySQL端口
        "user": "root",               // 数据库用户名
        "password": "your_db_password", // 数据库密码
        "database": "ctp_trading"     // 数据库名
    },
    "auto_download": {
        "enabled": false,             // 是否启用自动下载
        "interval": 300               // 自动下载间隔（秒）
    }
}
```

**重要提示：**
- `broker_id`、`user_id`、`password` 需要从你的期货公司获取
- 前置地址也需要从期货公司获取，示例中的地址仅供参考
- 请妥善保管配置文件，不要泄露密码

## 五、运行程序

### 方法1: 双击启动（最简单）

```cmd
# 双击运行
run.bat
```

### 方法2: 命令行启动

```cmd
# 在项目目录打开命令提示符
python run.py

# 或者直接运行主程序
python main_gui.py
```

### 方法3: 使用Python IDLE

1. 右键点击 `run.py`
2. 选择 "Edit with IDLE"
3. 按 F5 运行

## 六、使用程序

### 1. 首次启动

1. 启动程序后会看到主界面
2. 填写CTP连接信息和数据库信息
3. 点击"保存配置"按钮
4. 点击"连接"按钮

### 2. 下载数据

连接成功后：
- 点击"下载委托数据"获取当日委托
- 点击"下载持仓数据"获取当前持仓
- 点击"下载合约参数"获取合约信息

### 3. 查询数据

在各个标签页中：
- 输入查询条件
- 点击"查询"按钮
- 查看数据结果

### 4. 自动下载

- 勾选"自动下载"
- 设置时间间隔
- 程序会定时自动下载数据

## 七、导入历史数据

如果有CSV格式的历史数据：

```cmd
# 编辑 data_importer.py 设置数据库密码
# 然后运行
python data_importer.py
```

或在Python中：

```python
from database_manager import DatabaseManager
from data_importer import DataImporter

db = DatabaseManager(host="localhost", user="root", password="your_password")
db.connect()

importer = DataImporter(db)
importer.import_orders_from_csv("req/当日委托.csv", trading_day="20250129")
importer.import_positions_from_csv("req/当日持仓.csv", trading_day="20250129")

db.close()
```

## 八、常见问题

### 问题1: Python不是内部或外部命令

**解决方案：**
- 确保安装Python时勾选了 "Add Python to PATH"
- 手动添加Python到环境变量PATH中
- 重启命令提示符

### 问题2: 无法连接MySQL

**检查：**
- MySQL服务是否启动（服务管理器中查看）
- 防火墙是否阻止3306端口
- 用户名密码是否正确

```cmd
# 检查MySQL服务状态
sc query MySQL80

# 启动MySQL服务
net start MySQL80
```

### 问题3: 找不到模块 'pymysql'

**解决方案：**
```cmd
pip install pymysql
```

### 问题4: tkinter导入错误

**解决方案：**
- 重新安装Python，确保勾选 "tcl/tk and IDLE"
- 或者安装完整版Python

### 问题5: CTP连接失败

**检查：**
- 前置地址是否正确
- 用户名密码是否正确
- 是否在交易时间内（夜盘21:00-次日02:30，日盘09:00-15:00）
- 网络是否正常

### 问题6: 中文显示乱码

**解决方案：**
- 确保CSV文件编码为GBK或UTF-8 with BOM
- 使用记事本另存为时选择UTF-8编码

## 九、性能优化

### 1. 数据库优化

```sql
-- 添加索引以提高查询速度
CREATE INDEX idx_order_time ON daily_orders(order_time);
CREATE INDEX idx_instrument ON daily_orders(instrument_id);
CREATE INDEX idx_trading_day ON daily_orders(trading_day);
```

### 2. 程序优化

- 避免频繁查询（建议间隔不少于60秒）
- 定期清理历史数据
- 使用SSD硬盘存储数据库

## 十、防火墙配置

### Windows防火墙

如果需要远程访问MySQL：

1. 打开 Windows Defender 防火墙
2. 点击"高级设置"
3. 入站规则 -> 新建规则
4. 端口 -> TCP -> 3306
5. 允许连接

## 十一、创建桌面快捷方式

### 方法1: 手动创建

1. 右键桌面 -> 新建 -> 快捷方式
2. 位置填写：
   ```
   C:\Python310\pythonw.exe "D:\whctp\run.py"
   ```
   （路径根据实际情况调整）
3. 命名为 "CTP交易管理系统"
4. 完成

### 方法2: 使用批处理

创建 `start_ctp.bat`：

```batch
@echo off
cd /d "%~dp0"
start "" pythonw.exe run.py
exit
```

双击此文件即可后台运行程序（不显示命令行窗口）

## 十二、开机自启动（可选）

1. 按 `Win + R`，输入 `shell:startup`
2. 将快捷方式复制到打开的文件夹中

## 十三、备份和恢复

### 备份数据库

```cmd
# 备份
mysqldump -u root -p ctp_trading > backup_20250129.sql

# 恢复
mysql -u root -p ctp_trading < backup_20250129.sql
```

### 备份配置

定期备份 `config.json` 文件

## 十四、更新程序

```cmd
# 如果使用git
git pull

# 安装新依赖
pip install -r requirements.txt --upgrade
```

## 十五、卸载程序

1. 停止MySQL服务（如果不再需要）
2. 删除程序文件夹
3. 删除数据库（可选）：
   ```sql
   DROP DATABASE ctp_trading;
   ```

## 技术支持

如遇到问题：
1. 查看日志文件（程序界面底部日志区域）
2. 检查配置文件是否正确
3. 查看README.md获取更多信息

---

**祝使用愉快！**
