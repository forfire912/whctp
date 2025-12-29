# CTP期货交易管理系统 - Windows安装前准备

## 快速安装步骤

### 1. 安装Python依赖

```cmd
pip install pymysql openctp-ctp pandas
```

### 2. 配置MySQL数据库

**使用XAMPP（推荐新手）：**
- 下载安装XAMPP: https://www.apachefriends.org/
- 启动MySQL服务
- 打开phpMyAdmin创建数据库 `ctp_trading`

**或使用MySQL直接安装：**
```cmd
# 下载MySQL Community Server并安装
# 创建数据库
mysql -u root -p
CREATE DATABASE ctp_trading CHARACTER SET utf8mb4;
```

### 3. 配置连接信息

复制 `config.json.example` 为 `config.json`，编辑：

```json
{
    "ctp": {
        "broker_id": "9999",
        "user_id": "你的用户名",
        "password": "你的密码",
        "trade_front": "tcp://...",
        "market_front": "tcp://...",
        "app_id": "",
        "auth_code": ""
    },
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "你的MySQL密码",
        "database": "ctp_trading"
    }
}
```

### 4. 启动程序

```cmd
# 方式1: 双击运行
run.bat

# 方式2: 命令行
python run.py
```

## 重要说明

### CTP API版本

本程序使用 **SFIT CTP Mini API V1.7.3-P2**，支持：
- ✅ 上期所 (SHFE)
- ✅ 大商所 (DCE)  
- ✅ 郑商所 (CZCE)
- ✅ 中金所 (CFFEX)
- ✅ 上海能源 (INE)
- ✅ 广期所 (GFEX)

### 获取CTP账户

您需要从期货公司获取：
1. **经纪商代码** (BrokerID)
2. **用户名和密码**
3. **交易前置地址** (TraderFront)
4. **行情前置地址** (MarketFront)
5. **AppID和认证码**（部分期货公司需要）

### openctp-ctp库说明

**openctp-ctp** 是开源的CTP API Python绑定库：
- GitHub: https://github.com/openctp/openctp-ctp-python
- 支持Windows x64平台
- 基于官方CTP API封装
- 兼容Python 3.7+

如果安装失败，可能原因：
1. Python版本过旧（需要3.7+）
2. 缺少Visual C++运行库
3. 网络问题

**解决方案：**
```cmd
# 安装Visual C++ Redistributable
# 从微软官网下载并安装

# 使用国内镜像源
pip install openctp-ctp -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 模拟模式

如果无法安装 `openctp-ctp`，程序会自动切换到**模拟模式**：
- 界面正常运行
- 数据库功能正常
- API调用仅输出日志
- 适合测试界面和数据库功能

## 交易时间

**夜盘**：21:00 - 次日02:30  
**日盘**：09:00 - 15:00  
**小节休息**：10:15-10:30, 11:30-13:30

非交易时间连接CTP会失败！

## 常见问题

### Q: pip安装很慢？
A: 使用清华镜像源
```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 提示"无法导入CTP模块"？
A: 程序会自动使用模拟模式，不影响界面和数据库测试

### Q: CTP连接失败？
A: 检查：
- 是否在交易时间内
- 前置地址是否正确
- 用户名密码是否正确
- 网络是否正常

### Q: 数据库连接失败？
A: 检查：
- MySQL服务是否启动
- 用户名密码是否正确
- 端口3306是否开放

## 技术支持

详细文档：
- [README.md](README.md) - 完整功能说明
- [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) - 详细安装指南
- [api/doc/SFIT_CTP_Mini_API_V1.7.3-P2.pdf](api/doc/SFIT_CTP_Mini_API_V1.7.3-P2.pdf) - 官方API文档

---

**准备好了吗？双击 run.bat 开始使用！** 🚀
