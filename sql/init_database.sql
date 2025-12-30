-- ============================================================================
-- CTP期货交易管理系统 - 数据库初始化脚本
-- ============================================================================
-- 数据库: qihuo
-- 字符集: utf8mb4
-- 说明: 包含4个数据表的完整建表语句
-- ============================================================================

-- ============================================================================
-- 1. 当日委托表 (daily_orders)
-- 用途: 记录所有委托订单信息
-- ============================================================================
DROP TABLE IF EXISTS daily_orders;

CREATE TABLE daily_orders (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    order_time VARCHAR(20) COMMENT '委托时间 (HH:MM:SS)',
    instrument_id VARCHAR(31) COMMENT '合约代码 (如cu2501)',
    direction VARCHAR(10) COMMENT '方向 (买入/卖出)',
    offset_flag VARCHAR(10) COMMENT '开平标志 (开仓/平仓/平今/平昨)',
    order_price DECIMAL(15, 4) COMMENT '委托价格',
    order_volume INT COMMENT '委托数量',
    traded_volume INT COMMENT '已成交数量',
    order_status VARCHAR(20) COMMENT '订单状态 (全部成交/部分成交/未成交等)',
    remark TEXT COMMENT '备注信息',
    trading_day VARCHAR(20) COMMENT '交易日 (YYYYMMDD)',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引
    INDEX idx_instrument (instrument_id),
    INDEX idx_trading_day (trading_day),
    INDEX idx_order_time (order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='当日委托表';

-- ============================================================================
-- 2. 当日持仓表 (daily_positions)
-- 用途: 记录持仓明细
-- ============================================================================
DROP TABLE IF EXISTS daily_positions;

CREATE TABLE daily_positions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    instrument_id VARCHAR(31) COMMENT '合约代码',
    direction VARCHAR(10) COMMENT '持仓方向 (多头/空头)',
    position_type VARCHAR(10) COMMENT '持仓类型 (今仓/昨仓/总仓)',
    volume INT COMMENT '持仓数量',
    available_volume INT COMMENT '可用持仓数量',
    open_price DECIMAL(15, 4) COMMENT '开仓均价',
    position_price DECIMAL(15, 4) COMMENT '持仓均价',
    close_profit DECIMAL(15, 2) COMMENT '平仓盈亏',
    position_profit DECIMAL(15, 2) COMMENT '持仓盈亏 (浮动盈亏)',
    trading_day VARCHAR(20) COMMENT '交易日 (YYYYMMDD)',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引和约束
    UNIQUE KEY uk_position (instrument_id, direction, trading_day) COMMENT '防止重复持仓记录',
    INDEX idx_trading_day (trading_day)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='当日持仓表';

-- ============================================================================
-- 3. 市场行情表 (market_data)
-- 用途: 记录实时行情快照
-- ============================================================================
DROP TABLE IF EXISTS market_data;

CREATE TABLE market_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    instrument_id VARCHAR(31) COMMENT '合约代码',
    exchange_id VARCHAR(10) COMMENT '交易所代码 (SHFE/DCE/CZCE/CFFEX/INE/GFEX)',
    update_time VARCHAR(20) COMMENT '行情更新时间 (HH:MM:SS)',
    last_price DECIMAL(15, 4) COMMENT '最新价',
    pre_settlement_price DECIMAL(15, 4) COMMENT '昨结算价',
    pre_close_price DECIMAL(15, 4) COMMENT '昨收盘价',
    open_price DECIMAL(15, 4) COMMENT '今开盘价',
    highest_price DECIMAL(15, 4) COMMENT '最高价',
    lowest_price DECIMAL(15, 4) COMMENT '最低价',
    volume INT COMMENT '成交量 (手)',
    turnover DECIMAL(20, 2) COMMENT '成交额',
    open_interest INT COMMENT '持仓量 (手)',
    close_price DECIMAL(15, 4) COMMENT '今收盘价',
    settlement_price DECIMAL(15, 4) COMMENT '今结算价',
    upper_limit_price DECIMAL(15, 4) COMMENT '涨停板价',
    lower_limit_price DECIMAL(15, 4) COMMENT '跌停板价',
    bid_price1 DECIMAL(15, 4) COMMENT '买一价',
    bid_volume1 INT COMMENT '买一量',
    ask_price1 DECIMAL(15, 4) COMMENT '卖一价',
    ask_volume1 INT COMMENT '卖一量',
    trading_day VARCHAR(20) COMMENT '交易日 (YYYYMMDD)',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引
    INDEX idx_instrument (instrument_id),
    INDEX idx_trading_day (trading_day),
    INDEX idx_update_time (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场行情表';

-- ============================================================================
-- 4. 合约信息表 (instrument_info)
-- 用途: 记录交易所合约基础信息
-- ============================================================================
DROP TABLE IF EXISTS instrument_info;

CREATE TABLE instrument_info (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    instrument_id VARCHAR(31) UNIQUE COMMENT '合约代码 (唯一)',
    exchange_id VARCHAR(10) COMMENT '交易所代码',
    instrument_name VARCHAR(100) COMMENT '合约名称',
    product_id VARCHAR(31) COMMENT '品种代码',
    product_class VARCHAR(10) COMMENT '品种类型 (期货/期权/组合)',
    delivery_year INT COMMENT '交割年份',
    delivery_month INT COMMENT '交割月份',
    volume_multiple INT COMMENT '合约乘数 (每手对应数量)',
    price_tick DECIMAL(15, 8) COMMENT '最小变动价位',
    create_date VARCHAR(20) COMMENT '创建日',
    open_date VARCHAR(20) COMMENT '上市日',
    expire_date VARCHAR(20) COMMENT '到期日',
    start_delivery_date VARCHAR(20) COMMENT '开始交割日',
    end_delivery_date VARCHAR(20) COMMENT '最后交割日',
    is_trading TINYINT(1) DEFAULT 1 COMMENT '是否交易中 (1=是, 0=否)',
    long_margin_ratio DECIMAL(10, 6) COMMENT '多头保证金率',
    short_margin_ratio DECIMAL(10, 6) COMMENT '空头保证金率',
    max_market_order_volume INT COMMENT '市价单最大下单量',
    min_market_order_volume INT COMMENT '市价单最小下单量',
    max_limit_order_volume INT COMMENT '限价单最大下单量',
    min_limit_order_volume INT COMMENT '限价单最小下单量',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引
    INDEX idx_product (product_id),
    INDEX idx_exchange (exchange_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合约信息表';

-- ============================================================================
-- 初始化完成提示
-- ============================================================================
SELECT '数据库初始化完成！' AS message,
       'qihuo' AS database_name,
       '4' AS tables_created,
       'utf8mb4' AS charset;

-- 查看创建的表
SHOW TABLES;

-- ============================================================================
-- 使用说明
-- ============================================================================
-- 1. 导入脚本:
--    mysql -u root -p < init_database.sql
--
-- 2. 或在MySQL客户端中执行:
--    SOURCE /path/to/init_database.sql;
--
-- 3. 验证表结构:
--    DESCRIBE daily_orders;
--    DESCRIBE daily_positions;
--    DESCRIBE market_data;
--    DESCRIBE instrument_info;
--
-- 4. 查看索引:
--    SHOW INDEX FROM daily_orders;
-- ============================================================================
