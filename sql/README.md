# 数据库SQL脚本说明

本目录包含CTP期货交易管理系统的数据库SQL脚本文件。

## 📁 文件清单

### 1. init_database.sql - 数据库初始化脚本
**用途**: 创建数据库和所有表结构

**包含内容**:
- 创建qihuo数据库
- 创建4个数据表:
  - `daily_orders` - 当日委托表
  - `daily_positions` - 当日持仓表
  - `market_data` - 市场行情表
  - `instrument_info` - 合约信息表
- 完整的索引和约束

**使用方法**:
```bash
# 方法1: 命令行导入
mysql -u root -p < sql/init_database.sql

# 方法2: MySQL客户端执行
mysql -u root -p
mysql> SOURCE /path/to/sql/init_database.sql;
```

### 2. query_examples.sql - 查询示例脚本
**用途**: 常用SQL查询示例和数据分析

**包含内容**:
- 委托查询 (按合约、交易日、状态等)
- 持仓查询 (盈亏统计、持仓分布等)
- 行情查询 (涨跌幅、成交量排名等)
- 合约信息查询
- 综合分析查询
- 数据清理脚本
- 表维护脚本

**使用方法**:
```bash
# 在MySQL客户端中执行
mysql -u root -p qihuo
mysql> SOURCE sql/query_examples.sql;

# 或复制需要的SQL语句单独执行
```

## 🔧 快速开始

### 首次部署 - 初始化数据库

```bash
# 1. 登录MySQL
mysql -u root -p

# 2. 执行初始化脚本
mysql> SOURCE sql/init_database.sql;

# 3. 验证表创建
mysql> USE qihuo;
mysql> SHOW TABLES;
mysql> DESCRIBE daily_orders;

# 4. 退出
mysql> EXIT;
```

### 程序自动初始化

如果使用Python程序（推荐方式），无需手动执行SQL脚本：

```python
# 程序会自动创建数据库和表
python run.py
```

程序启动时会自动：
1. 连接MySQL服务器
2. 创建qihuo数据库（如果不存在）
3. 创建所有数据表（如果不存在）
4. 建立索引

## 📊 表结构说明

### daily_orders - 当日委托表
记录所有委托订单信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| order_time | VARCHAR(20) | 委托时间 |
| instrument_id | VARCHAR(31) | 合约代码 |
| direction | VARCHAR(10) | 买入/卖出 |
| offset_flag | VARCHAR(10) | 开仓/平仓 |
| order_price | DECIMAL(15,4) | 委托价格 |
| order_volume | INT | 委托数量 |
| traded_volume | INT | 成交数量 |
| order_status | VARCHAR(20) | 订单状态 |
| trading_day | VARCHAR(20) | 交易日 |

**索引**: instrument_id, trading_day, order_time

### daily_positions - 当日持仓表
记录持仓明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| instrument_id | VARCHAR(31) | 合约代码 |
| direction | VARCHAR(10) | 多头/空头 |
| position_type | VARCHAR(10) | 今仓/昨仓 |
| volume | INT | 持仓数量 |
| position_price | DECIMAL(15,4) | 持仓均价 |
| position_profit | DECIMAL(15,2) | 持仓盈亏 |
| trading_day | VARCHAR(20) | 交易日 |

**唯一约束**: (instrument_id, direction, trading_day)

### market_data - 市场行情表
记录实时行情快照

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| instrument_id | VARCHAR(31) | 合约代码 |
| exchange_id | VARCHAR(10) | 交易所 |
| last_price | DECIMAL(15,4) | 最新价 |
| volume | INT | 成交量 |
| open_interest | INT | 持仓量 |
| bid_price1 | DECIMAL(15,4) | 买一价 |
| ask_price1 | DECIMAL(15,4) | 卖一价 |
| trading_day | VARCHAR(20) | 交易日 |

**索引**: instrument_id, trading_day, update_time

### instrument_info - 合约信息表
记录合约基础信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| instrument_id | VARCHAR(31) | 合约代码 (唯一) |
| exchange_id | VARCHAR(10) | 交易所 |
| product_id | VARCHAR(31) | 品种代码 |
| volume_multiple | INT | 合约乘数 |
| price_tick | DECIMAL(15,8) | 最小变动价位 |
| long_margin_ratio | DECIMAL(10,6) | 保证金率 |

**索引**: product_id, exchange_id

## 🛠️ 常用操作

### 查看数据库状态
```sql
USE qihuo;
SHOW TABLES;
SHOW TABLE STATUS;
```

### 查看表结构
```sql
DESCRIBE daily_orders;
SHOW CREATE TABLE daily_orders;
SHOW INDEX FROM daily_orders;
```

### 数据统计
```sql
-- 各表记录数
SELECT 
    TABLE_NAME AS '表名',
    TABLE_ROWS AS '记录数'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'qihuo';
```

### 备份数据库
```bash
# 完整备份
mysqldump -u root -p qihuo > qihuo_backup_$(date +%Y%m%d).sql

# 只备份结构
mysqldump -u root -p --no-data qihuo > qihuo_structure.sql

# 只备份数据
mysqldump -u root -p --no-create-info qihuo > qihuo_data.sql
```

### 恢复数据库
```bash
mysql -u root -p qihuo < qihuo_backup_20251229.sql
```

## ⚠️ 注意事项

1. **字符集**: 所有表使用utf8mb4字符集，支持中文和emoji
2. **存储引擎**: 使用InnoDB引擎，支持事务和外键
3. **时间字段**: 使用VARCHAR存储交易日和时间，格式统一
4. **索引优化**: 已为常用查询字段建立索引
5. **数据安全**: 建议定期备份数据库

## 🔍 查询示例

详细的查询示例请参考 `query_examples.sql` 文件，包括：

- ✅ 委托查询和统计
- ✅ 持仓盈亏分析
- ✅ 行情排名查询
- ✅ 合约信息检索
- ✅ 综合数据分析
- ✅ 数据维护操作

## 📞 技术支持

如有问题，请参考:
- 主文档: ../README.md
- 快速开始: ../QUICKSTART.md
- 数据库管理器代码: ../database_manager.py
