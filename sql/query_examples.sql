-- ============================================================================
-- 数据库查询示例 - CTP期货交易管理系统
-- ============================================================================

USE qihuo;

-- ============================================================================
-- 1. 当日委托查询
-- ============================================================================

-- 查询所有委托
SELECT * FROM daily_orders 
ORDER BY order_time DESC 
LIMIT 100;

-- 查询特定合约的委托
SELECT * FROM daily_orders 
WHERE instrument_id = 'cu2501' 
ORDER BY order_time DESC;

-- 查询特定交易日的委托
SELECT * FROM daily_orders 
WHERE trading_day = '20251229' 
ORDER BY order_time DESC;

-- 统计各合约委托量
SELECT 
    instrument_id AS '合约',
    COUNT(*) AS '委托笔数',
    SUM(order_volume) AS '总委托量',
    SUM(traded_volume) AS '总成交量'
FROM daily_orders
GROUP BY instrument_id
ORDER BY COUNT(*) DESC;

-- 查询未成交订单
SELECT * FROM daily_orders 
WHERE order_status IN ('未成交', '部分成交')
ORDER BY order_time DESC;

-- ============================================================================
-- 2. 当日持仓查询
-- ============================================================================

-- 查询所有持仓
SELECT * FROM daily_positions 
ORDER BY instrument_id;

-- 查询特定合约持仓
SELECT * FROM daily_positions 
WHERE instrument_id = 'cu2501';

-- 查询多头持仓
SELECT * FROM daily_positions 
WHERE direction = '多头'
ORDER BY position_profit DESC;

-- 查询空头持仓
SELECT * FROM daily_positions 
WHERE direction = '空头'
ORDER BY position_profit DESC;

-- 统计总持仓盈亏
SELECT 
    SUM(position_profit) AS '总浮动盈亏',
    SUM(close_profit) AS '总平仓盈亏',
    SUM(position_profit + close_profit) AS '总盈亏'
FROM daily_positions;

-- 按合约统计持仓
SELECT 
    instrument_id AS '合约',
    direction AS '方向',
    SUM(volume) AS '总持仓',
    AVG(position_price) AS '均价',
    SUM(position_profit) AS '浮动盈亏'
FROM daily_positions
GROUP BY instrument_id, direction;

-- ============================================================================
-- 3. 市场行情查询
-- ============================================================================

-- 查询最新行情
SELECT 
    instrument_id AS '合约',
    exchange_id AS '交易所',
    last_price AS '最新价',
    ROUND((last_price - pre_settlement_price) / pre_settlement_price * 100, 2) AS '涨跌幅%',
    volume AS '成交量',
    open_interest AS '持仓量',
    update_time AS '更新时间'
FROM market_data
ORDER BY update_time DESC
LIMIT 20;

-- 查询特定合约行情
SELECT * FROM market_data 
WHERE instrument_id = 'cu2501' 
ORDER BY update_time DESC 
LIMIT 10;

-- 查询涨幅前10的合约
SELECT 
    instrument_id AS '合约',
    last_price AS '最新价',
    pre_settlement_price AS '昨结算',
    ROUND((last_price - pre_settlement_price) / pre_settlement_price * 100, 2) AS '涨跌幅%'
FROM market_data
WHERE last_price > 0 AND pre_settlement_price > 0
ORDER BY (last_price - pre_settlement_price) / pre_settlement_price DESC
LIMIT 10;

-- 查询成交量前10的合约
SELECT 
    instrument_id AS '合约',
    volume AS '成交量',
    turnover AS '成交额',
    open_interest AS '持仓量',
    last_price AS '最新价'
FROM market_data
ORDER BY volume DESC
LIMIT 10;

-- 查询特定交易所的行情
SELECT * FROM market_data 
WHERE exchange_id = 'SHFE' 
ORDER BY volume DESC;

-- ============================================================================
-- 4. 合约信息查询
-- ============================================================================

-- 查询所有可交易合约
SELECT 
    instrument_id AS '合约代码',
    instrument_name AS '合约名称',
    exchange_id AS '交易所',
    volume_multiple AS '合约乘数',
    price_tick AS '最小变动价位',
    long_margin_ratio AS '保证金率'
FROM instrument_info
WHERE is_trading = 1
ORDER BY exchange_id, instrument_id;

-- 查询特定品种的合约
SELECT * FROM instrument_info 
WHERE product_id = 'cu'
ORDER BY delivery_month;

-- 查询即将到期的合约
SELECT 
    instrument_id AS '合约代码',
    expire_date AS '到期日',
    DATEDIFF(expire_date, CURDATE()) AS '剩余天数'
FROM instrument_info
WHERE expire_date >= CURDATE()
ORDER BY expire_date
LIMIT 20;

-- 查询各交易所合约数量
SELECT 
    exchange_id AS '交易所',
    COUNT(*) AS '合约数量'
FROM instrument_info
WHERE is_trading = 1
GROUP BY exchange_id;

-- ============================================================================
-- 5. 综合分析查询
-- ============================================================================

-- 持仓合约的实时盈亏
SELECT 
    p.instrument_id AS '合约',
    p.direction AS '方向',
    p.volume AS '持仓量',
    p.position_price AS '持仓均价',
    m.last_price AS '最新价',
    i.volume_multiple AS '合约乘数',
    CASE 
        WHEN p.direction = '多头' THEN (m.last_price - p.position_price) * p.volume * i.volume_multiple
        WHEN p.direction = '空头' THEN (p.position_price - m.last_price) * p.volume * i.volume_multiple
        ELSE 0
    END AS '浮动盈亏'
FROM daily_positions p
LEFT JOIN market_data m ON p.instrument_id = m.instrument_id
LEFT JOIN instrument_info i ON p.instrument_id = i.instrument_id
WHERE p.volume > 0
ORDER BY p.instrument_id;

-- 今日交易活跃品种
SELECT 
    i.product_id AS '品种',
    COUNT(DISTINCT o.instrument_id) AS '合约数',
    SUM(o.order_volume) AS '总委托量',
    SUM(o.traded_volume) AS '总成交量',
    ROUND(SUM(o.traded_volume) / SUM(o.order_volume) * 100, 2) AS '成交率%'
FROM daily_orders o
LEFT JOIN instrument_info i ON o.instrument_id = i.instrument_id
WHERE o.trading_day = DATE_FORMAT(CURDATE(), '%Y%m%d')
GROUP BY i.product_id
ORDER BY SUM(o.traded_volume) DESC;

-- 各交易所持仓分布
SELECT 
    i.exchange_id AS '交易所',
    COUNT(DISTINCT p.instrument_id) AS '持仓合约数',
    SUM(p.volume) AS '总持仓量',
    SUM(p.position_profit) AS '总浮动盈亏'
FROM daily_positions p
LEFT JOIN instrument_info i ON p.instrument_id = i.instrument_id
GROUP BY i.exchange_id
ORDER BY SUM(p.volume) DESC;

-- ============================================================================
-- 6. 数据清理
-- ============================================================================

-- 删除指定交易日之前的委托记录（保留最近30天）
-- DELETE FROM daily_orders 
-- WHERE trading_day < DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 30 DAY), '%Y%m%d');

-- 删除指定交易日之前的持仓记录
-- DELETE FROM daily_positions 
-- WHERE trading_day < DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 30 DAY), '%Y%m%d');

-- 删除历史行情数据（保留最近7天）
-- DELETE FROM market_data 
-- WHERE create_time < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- ============================================================================
-- 7. 表维护
-- ============================================================================

-- 查看表状态
SHOW TABLE STATUS FROM qihuo;

-- 查看表大小
SELECT 
    table_name AS '表名',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '大小(MB)',
    table_rows AS '记录数'
FROM information_schema.tables
WHERE table_schema = 'qihuo'
ORDER BY (data_length + index_length) DESC;

-- 优化表
-- OPTIMIZE TABLE daily_orders;
-- OPTIMIZE TABLE daily_positions;
-- OPTIMIZE TABLE market_data;
-- OPTIMIZE TABLE instrument_info;

-- ============================================================================
-- 使用说明
-- ============================================================================
-- 1. 在MySQL客户端中执行查询:
--    SOURCE /path/to/query_examples.sql;
--
-- 2. 或复制需要的SQL语句单独执行
--
-- 3. 注意: 删除和优化操作已注释，使用前请去掉注释符号 --
-- ============================================================================
