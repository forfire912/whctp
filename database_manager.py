#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL数据库管理模块
用于管理CTP交易数据的存储和查询
"""

import pymysql
from pymysql import Error
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, host: str = "localhost", port: int = 3306,
                 user: str = "root", password: str = "",
                 database: str = "ctp_trading"):
        """
        初始化数据库连接
        
        Args:
            host: 数据库主机
            port: 数据库端口
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self) -> bool:
        """连接到MySQL数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"成功连接到MySQL服务器 {self.host}:{self.port}")
            
            # 创建数据库（如果不存在）
            self._create_database()
            
            # 切换到目标数据库
            self.connection.select_db(self.database)
            
            # 创建表结构
            self._create_tables()
            
            return True
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def _create_database(self):
        """创建数据库"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                self.connection.commit()
                logger.info(f"数据库 {self.database} 已准备就绪")
        except Error as e:
            logger.error(f"创建数据库失败: {e}")
    
    def _create_tables(self):
        """创建数据表结构"""
        try:
            with self.connection.cursor() as cursor:
                # 当日委托表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_orders (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_time VARCHAR(20) COMMENT '委托时间',
                        instrument_id VARCHAR(31) COMMENT '合约代码',
                        direction VARCHAR(10) COMMENT '方向(买入/卖出)',
                        offset_flag VARCHAR(10) COMMENT '开平(开仓/平仓)',
                        order_price DECIMAL(15, 4) COMMENT '委托价格',
                        order_volume INT COMMENT '委托量',
                        traded_volume INT COMMENT '成交量',
                        order_status VARCHAR(20) COMMENT '状态',
                        remark TEXT COMMENT '备注',
                        trading_day VARCHAR(20) COMMENT '交易日',
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_instrument (instrument_id),
                        INDEX idx_trading_day (trading_day),
                        INDEX idx_order_time (order_time)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='当日委托表'
                """)
                
                # 当日持仓表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_positions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        instrument_id VARCHAR(31) COMMENT '合约代码',
                        direction VARCHAR(10) COMMENT '方向(多/空)',
                        position_type VARCHAR(10) COMMENT '持仓类型(今仓/总仓)',
                        volume INT COMMENT '持仓量',
                        available_volume INT COMMENT '可用持仓',
                        open_price DECIMAL(15, 4) COMMENT '开仓均价',
                        position_price DECIMAL(15, 4) COMMENT '持仓均价',
                        close_profit DECIMAL(15, 2) COMMENT '平仓盈亏',
                        position_profit DECIMAL(15, 2) COMMENT '持仓盈亏',
                        trading_day VARCHAR(20) COMMENT '交易日',
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY uk_position (instrument_id, direction, trading_day),
                        INDEX idx_trading_day (trading_day)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='当日持仓表'
                """)
                
                # 商品行情表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        instrument_id VARCHAR(31) COMMENT '合约代码',
                        exchange_id VARCHAR(10) COMMENT '交易所代码',
                        update_time VARCHAR(20) COMMENT '更新时间',
                        last_price DECIMAL(15, 4) COMMENT '最新价',
                        pre_settlement_price DECIMAL(15, 4) COMMENT '昨结算',
                        pre_close_price DECIMAL(15, 4) COMMENT '昨收盘',
                        open_price DECIMAL(15, 4) COMMENT '今开盘',
                        highest_price DECIMAL(15, 4) COMMENT '最高价',
                        lowest_price DECIMAL(15, 4) COMMENT '最低价',
                        volume INT COMMENT '成交量',
                        turnover DECIMAL(20, 2) COMMENT '成交额',
                        open_interest INT COMMENT '持仓量',
                        close_price DECIMAL(15, 4) COMMENT '今收盘',
                        settlement_price DECIMAL(15, 4) COMMENT '今结算',
                        upper_limit_price DECIMAL(15, 4) COMMENT '涨停价',
                        lower_limit_price DECIMAL(15, 4) COMMENT '跌停价',
                        bid_price1 DECIMAL(15, 4) COMMENT '买一价',
                        bid_volume1 INT COMMENT '买一量',
                        ask_price1 DECIMAL(15, 4) COMMENT '卖一价',
                        ask_volume1 INT COMMENT '卖一量',
                        trading_day VARCHAR(20) COMMENT '交易日',
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_instrument (instrument_id),
                        INDEX idx_trading_day (trading_day),
                        INDEX idx_update_time (update_time)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品行情表'
                """)
                
                # 商品参数表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS instrument_info (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        instrument_id VARCHAR(31) UNIQUE COMMENT '合约代码',
                        exchange_id VARCHAR(10) COMMENT '交易所代码',
                        instrument_name VARCHAR(100) COMMENT '合约名称',
                        product_id VARCHAR(31) COMMENT '品种代码',
                        product_class VARCHAR(10) COMMENT '品种类型',
                        delivery_year INT COMMENT '交割年份',
                        delivery_month INT COMMENT '交割月',
                        volume_multiple INT COMMENT '合约乘数',
                        price_tick DECIMAL(15, 8) COMMENT '最小变动价位',
                        create_date VARCHAR(20) COMMENT '创建日',
                        open_date VARCHAR(20) COMMENT '上市日',
                        expire_date VARCHAR(20) COMMENT '到期日',
                        start_delivery_date VARCHAR(20) COMMENT '开始交割日',
                        end_delivery_date VARCHAR(20) COMMENT '结束交割日',
                        is_trading TINYINT(1) DEFAULT 1 COMMENT '是否交易中',
                        long_margin_ratio DECIMAL(10, 6) COMMENT '多头保证金率',
                        short_margin_ratio DECIMAL(10, 6) COMMENT '空头保证金率',
                        max_market_order_volume INT COMMENT '市价单最大量',
                        min_market_order_volume INT COMMENT '市价单最小量',
                        max_limit_order_volume INT COMMENT '限价单最大量',
                        min_limit_order_volume INT COMMENT '限价单最小量',
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_product (product_id),
                        INDEX idx_exchange (exchange_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品参数表'
                """)
                
                self.connection.commit()
                logger.info("数据表结构已创建")
        except Error as e:
            logger.error(f"创建表失败: {e}")
            self.connection.rollback()
    
    def insert_orders(self, orders: List[Dict[str, Any]]) -> int:
        """
        批量插入委托数据
        
        Args:
            orders: 委托数据列表
            
        Returns:
            插入的记录数
        """
        if not orders:
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO daily_orders 
                    (order_time, instrument_id, direction, offset_flag, order_price, 
                     order_volume, traded_volume, order_status, remark, trading_day)
                    VALUES (%(order_time)s, %(instrument_id)s, %(direction)s, %(offset_flag)s,
                            %(order_price)s, %(order_volume)s, %(traded_volume)s, 
                            %(order_status)s, %(remark)s, %(trading_day)s)
                """
                count = cursor.executemany(sql, orders)
                self.connection.commit()
                logger.info(f"成功插入 {count} 条委托记录")
                return count
        except Error as e:
            logger.error(f"插入委托数据失败: {e}")
            self.connection.rollback()
            return 0
    
    def insert_positions(self, positions: List[Dict[str, Any]]) -> int:
        """
        批量插入持仓数据（使用REPLACE INTO避免重复）
        
        Args:
            positions: 持仓数据列表
            
        Returns:
            插入的记录数
        """
        if not positions:
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    REPLACE INTO daily_positions 
                    (instrument_id, direction, position_type, volume, available_volume,
                     open_price, position_price, close_profit, position_profit, trading_day)
                    VALUES (%(instrument_id)s, %(direction)s, %(position_type)s, %(volume)s,
                            %(available_volume)s, %(open_price)s, %(position_price)s,
                            %(close_profit)s, %(position_profit)s, %(trading_day)s)
                """
                count = cursor.executemany(sql, positions)
                self.connection.commit()
                logger.info(f"成功更新 {count} 条持仓记录")
                return count
        except Error as e:
            logger.error(f"插入持仓数据失败: {e}")
            self.connection.rollback()
            return 0
    
    def insert_market_data(self, market_data: List[Dict[str, Any]]) -> int:
        """
        批量插入行情数据
        
        Args:
            market_data: 行情数据列表
            
        Returns:
            插入的记录数
        """
        if not market_data:
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO market_data 
                    (instrument_id, exchange_id, update_time, last_price, pre_settlement_price,
                     pre_close_price, open_price, highest_price, lowest_price, volume, turnover,
                     open_interest, close_price, settlement_price, upper_limit_price, 
                     lower_limit_price, bid_price1, bid_volume1, ask_price1, ask_volume1, trading_day)
                    VALUES (%(instrument_id)s, %(exchange_id)s, %(update_time)s, %(last_price)s,
                            %(pre_settlement_price)s, %(pre_close_price)s, %(open_price)s,
                            %(highest_price)s, %(lowest_price)s, %(volume)s, %(turnover)s,
                            %(open_interest)s, %(close_price)s, %(settlement_price)s,
                            %(upper_limit_price)s, %(lower_limit_price)s, %(bid_price1)s,
                            %(bid_volume1)s, %(ask_price1)s, %(ask_volume1)s, %(trading_day)s)
                """
                count = cursor.executemany(sql, market_data)
                self.connection.commit()
                logger.info(f"成功插入 {count} 条行情记录")
                return count
        except Error as e:
            logger.error(f"插入行情数据失败: {e}")
            self.connection.rollback()
            return 0
    
    def insert_instrument_info(self, instruments: List[Dict[str, Any]]) -> int:
        """
        批量插入合约参数数据
        
        Args:
            instruments: 合约参数列表
            
        Returns:
            插入的记录数
        """
        if not instruments:
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO instrument_info 
                    (instrument_id, exchange_id, instrument_name, product_id, product_class,
                     delivery_year, delivery_month, volume_multiple, price_tick, create_date,
                     open_date, expire_date, start_delivery_date, end_delivery_date, is_trading,
                     long_margin_ratio, short_margin_ratio, max_market_order_volume,
                     min_market_order_volume, max_limit_order_volume, min_limit_order_volume)
                    VALUES (%(instrument_id)s, %(exchange_id)s, %(instrument_name)s, %(product_id)s,
                            %(product_class)s, %(delivery_year)s, %(delivery_month)s,
                            %(volume_multiple)s, %(price_tick)s, %(create_date)s, %(open_date)s,
                            %(expire_date)s, %(start_delivery_date)s, %(end_delivery_date)s,
                            %(is_trading)s, %(long_margin_ratio)s, %(short_margin_ratio)s,
                            %(max_market_order_volume)s, %(min_market_order_volume)s,
                            %(max_limit_order_volume)s, %(min_limit_order_volume)s)
                    ON DUPLICATE KEY UPDATE
                        instrument_name=VALUES(instrument_name),
                        is_trading=VALUES(is_trading),
                        long_margin_ratio=VALUES(long_margin_ratio),
                        short_margin_ratio=VALUES(short_margin_ratio)
                """
                count = cursor.executemany(sql, instruments)
                self.connection.commit()
                logger.info(f"成功更新 {count} 条合约参数记录")
                return count
        except Error as e:
            logger.error(f"插入合约参数失败: {e}")
            self.connection.rollback()
            return 0
    
    def query_orders(self, trading_day: Optional[str] = None, 
                    instrument_id: Optional[str] = None,
                    limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询委托数据
        
        Args:
            trading_day: 交易日
            instrument_id: 合约代码
            limit: 返回记录数限制
            
        Returns:
            委托数据列表
        """
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM daily_orders WHERE 1=1"
                params = []
                
                if trading_day:
                    sql += " AND trading_day = %s"
                    params.append(trading_day)
                
                if instrument_id:
                    sql += " AND instrument_id = %s"
                    params.append(instrument_id)
                
                sql += " ORDER BY order_time DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Error as e:
            logger.error(f"查询委托数据失败: {e}")
            return []
    
    def query_positions(self, trading_day: Optional[str] = None,
                       instrument_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询持仓数据
        
        Args:
            trading_day: 交易日
            instrument_id: 合约代码
            
        Returns:
            持仓数据列表
        """
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM daily_positions WHERE 1=1"
                params = []
                
                if trading_day:
                    sql += " AND trading_day = %s"
                    params.append(trading_day)
                
                if instrument_id:
                    sql += " AND instrument_id = %s"
                    params.append(instrument_id)
                
                sql += " ORDER BY instrument_id, direction"
                
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Error as e:
            logger.error(f"查询持仓数据失败: {e}")
            return []
    
    def query_market_data(self, trading_day: Optional[str] = None,
                         instrument_id: Optional[str] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询行情数据
        
        Args:
            trading_day: 交易日
            instrument_id: 合约代码
            limit: 返回记录数限制
            
        Returns:
            行情数据列表
        """
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM market_data WHERE 1=1"
                params = []
                
                if trading_day:
                    sql += " AND trading_day = %s"
                    params.append(trading_day)
                
                if instrument_id:
                    sql += " AND instrument_id = %s"
                    params.append(instrument_id)
                
                sql += " ORDER BY update_time DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Error as e:
            logger.error(f"查询行情数据失败: {e}")
            return []
    
    def query_instrument_info(self, instrument_id: Optional[str] = None,
                             exchange_id: Optional[str] = None,
                             is_trading: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        查询合约参数
        
        Args:
            instrument_id: 合约代码
            exchange_id: 交易所代码
            is_trading: 是否交易中
            
        Returns:
            合约参数列表
        """
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM instrument_info WHERE 1=1"
                params = []
                
                if instrument_id:
                    sql += " AND instrument_id = %s"
                    params.append(instrument_id)
                
                if exchange_id:
                    sql += " AND exchange_id = %s"
                    params.append(exchange_id)
                
                if is_trading is not None:
                    sql += " AND is_trading = %s"
                    params.append(1 if is_trading else 0)
                
                sql += " ORDER BY instrument_id"
                
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Error as e:
            logger.error(f"查询合约参数失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


if __name__ == "__main__":
    # 测试代码
    db = DatabaseManager(
        host="localhost",
        user="root",
        password="your_password",
        database="ctp_trading"
    )
    
    if db.connect():
        # 测试查询
        orders = db.query_orders(limit=10)
        print(f"查询到 {len(orders)} 条委托记录")
        
        positions = db.query_positions()
        print(f"查询到 {len(positions)} 条持仓记录")
        
        db.close()
