#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTP API封装类
用于与期货交易接口进行交互
"""

import ctypes
import os
import time
from datetime import datetime
from typing import Callable, Dict, Any


class CTPTraderAPI:
    """CTP交易API封装类"""
    
    def __init__(self, broker_id: str, user_id: str, password: str, 
                 front_addr: str, app_id: str = "", auth_code: str = ""):
        """
        初始化CTP交易API
        
        Args:
            broker_id: 经纪公司代码
            user_id: 用户代码
            password: 密码
            front_addr: 前置机地址
            app_id: 应用标识
            auth_code: 认证码
        """
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.front_addr = front_addr
        self.app_id = app_id
        self.auth_code = auth_code
        
        self.is_connected = False
        self.is_logged_in = False
        self.request_id = 0
        self.front_id = 0
        self.session_id = 0
        
        # 回调函数
        self.callbacks = {
            'on_connected': None,
            'on_disconnected': None,
            'on_login': None,
            'on_logout': None,
            'on_error': None,
            'on_order_rsp': None,
            'on_position_rsp': None,
            'on_trade_rsp': None,
            'on_instrument_rsp': None
        }
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def connect(self) -> bool:
        """连接到CTP服务器"""
        try:
            # 注意：这里需要实际的CTP动态库支持
            # 在实际部署时需要安装CTP的Python绑定（如openctp-ctp或其他封装）
            print(f"正在连接到CTP服务器: {self.front_addr}")
            time.sleep(1)  # 模拟连接过程
            
            self.is_connected = True
            if self.callbacks['on_connected']:
                self.callbacks['on_connected']({'status': 'connected', 'front_addr': self.front_addr})
            
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"连接失败: {e}")
            return False
    
    def login(self) -> bool:
        """登录CTP系统"""
        if not self.is_connected:
            print("请先连接到服务器")
            return False
        
        try:
            print(f"用户 {self.user_id} 正在登录...")
            time.sleep(1)  # 模拟登录过程
            
            self.is_logged_in = True
            self.request_id += 1
            
            if self.callbacks['on_login']:
                # 兼容 lambda d, *_: ...
                self.callbacks['on_login']({
                    'broker_id': self.broker_id,
                    'user_id': self.user_id,
                    'login_time': datetime.now().strftime('%H:%M:%S'),
                    'trading_day': datetime.now().strftime('%Y%m%d')
                }, None)
            
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"登录失败: {e}")
            return False
    
    def logout(self) -> bool:
        """登出CTP系统"""
        try:
            print(f"用户 {self.user_id} 正在登出...")
            time.sleep(0.5)
            
            self.is_logged_in = False
            if self.callbacks['on_logout']:
                self.callbacks['on_logout']()
            
            return True
        except Exception as e:
            print(f"登出失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.is_logged_in:
            self.logout()
        
        self.is_connected = False
        if self.callbacks['on_disconnected']:
            self.callbacks['on_disconnected']()
    
    def query_orders(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """
        查询当日委托（模拟返回与账号/合约相关的示例数据）
        
        Args:
            instrument_id: 合约代码
            exchange_id: 交易所代码
            
        Returns:
            委托列表
        """
        if not self.is_logged_in:
            print("请先登录")
            return []
        
        print("查询委托信息...")
        self.request_id += 1
        # 简单生成2条示例委托
        trading_day = datetime.now().strftime('%Y%m%d')
        base_instr = instrument_id or 'cu2501'
        orders = [
            {
                'order_time': '09:30:01',
                'instrument_id': base_instr,
                'direction': '买入',
                'offset_flag': '开仓',
                'order_price': 72000.0,
                'order_volume': 1,
                'traded_volume': 1,
                'order_status': '全部成交',
                'remark': f'模拟委托1({self.user_id})',
                'trading_day': trading_day
            },
            {
                'order_time': '10:15:20',
                'instrument_id': base_instr,
                'direction': '卖出',
                'offset_flag': '平仓',
                'order_price': 72150.0,
                'order_volume': 2,
                'traded_volume': 1,
                'order_status': '部分成交还在队列中',
                'remark': f'模拟委托2({self.user_id})',
                'trading_day': trading_day
            },
        ]
        
        if self.callbacks['on_order_rsp']:
            self.callbacks['on_order_rsp'](orders)
        return orders
    
    def query_positions(self, instrument_id: str = "") -> list:
        """
        查询持仓（模拟返回与账号/合约相关的示例数据）
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            持仓列表
        """
        if not self.is_logged_in:
            print("请先登录")
            return []
        
        print("查询持仓信息...")
        self.request_id += 1
        trading_day = datetime.now().strftime('%Y%m%d')
        base_instr = instrument_id or 'cu2501'
        positions = [
            {
                'instrument_id': base_instr,
                'direction': '多头',
                'position_type': '总仓',
                'volume': 3,
                'available_volume': 2,
                'open_price': 71500.0,
                'position_price': 71800.0,
                'close_profit': 500.0,
                'position_profit': 900.0,
                'trading_day': trading_day
            }
        ]
        if self.callbacks['on_position_rsp']:
            self.callbacks['on_position_rsp'](positions)
        return positions
    
    def query_trades(self, instrument_id: str = "") -> list:
        """
        查询成交（模拟返回与账号/合约相关的示例数据）
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            成交列表
        """
        if not self.is_logged_in:
            print("请先登录")
            return []
        
        print("查询成交信息...")
        self.request_id += 1
        trading_day = datetime.now().strftime('%Y%m%d')
        base_instr = instrument_id or 'cu2501'
        trades = [
            {
                'trade_time': '09:30:02',
                'instrument_id': base_instr,
                'direction': '买入',
                'offset_flag': '开仓',
                'price': 72000.0,
                'volume': 1,
                'trade_id': 'T001',
                'trading_day': trading_day
            }
        ]
        if self.callbacks['on_trade_rsp']:
            self.callbacks['on_trade_rsp'](trades)
        return trades
    
    def query_instruments(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """
        查询合约（模拟返回几个常见品种）
        
        Args:
            instrument_id: 合约代码
            exchange_id: 交易所代码
            
        Returns:
            合约列表
        """
        if not self.is_logged_in:
            print("请先登录")
            return []
        
        print("查询合约信息...")
        self.request_id += 1
        insts = [
            {
                'instrument_id': 'cu2501',
                'exchange_id': 'SHFE',
                'instrument_name': '铜2501',
                'product_id': 'cu',
                'product_class': '期货',
                'delivery_year': 2025,
                'delivery_month': 1,
                'volume_multiple': 5,
                'price_tick': 10.0,
                'create_date': '20241001',
                'open_date': '20241101',
                'expire_date': '20250115',
                'start_delivery_date': '20250101',
                'end_delivery_date': '20250115',
                'is_trading': 1,
                'long_margin_ratio': 0.1,
                'short_margin_ratio': 0.1,
                'max_market_order_volume': 100,
                'min_market_order_volume': 1,
                'max_limit_order_volume': 100,
                'min_limit_order_volume': 1
            },
            {
                'instrument_id': 'rb2501',
                'exchange_id': 'SHFE',
                'instrument_name': '螺纹钢2501',
                'product_id': 'rb',
                'product_class': '期货',
                'delivery_year': 2025,
                'delivery_month': 1,
                'volume_multiple': 10,
                'price_tick': 1.0,
                'create_date': '20241001',
                'open_date': '20241101',
                'expire_date': '20250115',
                'start_delivery_date': '20250101',
                'end_delivery_date': '20250115',
                'is_trading': 1,
                'long_margin_ratio': 0.08,
                'short_margin_ratio': 0.08,
                'max_market_order_volume': 200,
                'min_market_order_volume': 1,
                'max_limit_order_volume': 200,
                'min_limit_order_volume': 1
            }
        ]
        # 简单按条件过滤
        if instrument_id:
            insts = [i for i in insts if i['instrument_id'] == instrument_id]
        if exchange_id:
            insts = [i for i in insts if i['exchange_id'] == exchange_id]
        
        if self.callbacks['on_instrument_rsp']:
            self.callbacks['on_instrument_rsp'](insts)
        return insts


class CTPMarketAPI:
    """CTP行情API封装类"""
    
    def __init__(self, broker_id: str, user_id: str, password: str, front_addr: str):
        """
        初始化CTP行情API
        
        Args:
            broker_id: 经纪公司代码
            user_id: 用户代码
            password: 密码
            front_addr: 前置机地址
        """
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.front_addr = front_addr
        
        self.is_connected = False
        self.is_logged_in = False
        self.request_id = 0
        
        # 回调函数
        self.callbacks = {
            'on_connected': None,
            'on_disconnected': None,
            'on_login': None,
            'on_market_data': None
        }
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def connect(self) -> bool:
        """连接到行情服务器"""
        try:
            print(f"正在连接到行情服务器: {self.front_addr}")
            time.sleep(1)
            
            self.is_connected = True
            if self.callbacks['on_connected']:
                self.callbacks['on_connected']()
            
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def login(self) -> bool:
        """登录行情系统"""
        if not self.is_connected:
            print("请先连接到服务器")
            return False
        
        try:
            print(f"用户 {self.user_id} 正在登录行情系统...")
            time.sleep(1)
            
            self.is_logged_in = True
            self.request_id += 1
            
            if self.callbacks['on_login']:
                self.callbacks['on_login']({'user_id': self.user_id})
            
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def subscribe_market_data(self, instrument_ids: list) -> bool:
        """
        订阅行情
        
        Args:
            instrument_ids: 合约代码列表
            
        Returns:
            是否订阅成功
        """
        if not self.is_logged_in:
            print("请先登录")
            return False
        
        print(f"订阅行情: {instrument_ids}")
        return True
    
    def unsubscribe_market_data(self, instrument_ids: list) -> bool:
        """
        退订行情
        
        Args:
            instrument_ids: 合约代码列表
            
        Returns:
            是否退订成功
        """
        if not self.is_logged_in:
            print("请先登录")
            return False
        
        print(f"退订行情: {instrument_ids}")
        return True
    
    def disconnect(self):
        """断开连接"""
        self.is_connected = False
        self.is_logged_in = False
        if self.callbacks['on_disconnected']:
            self.callbacks['on_disconnected']()


if __name__ == "__main__":
    # 测试代码
    api = CTPTraderAPI(
        broker_id="9999",
        user_id="123456",
        password="password",
        front_addr="tcp://180.168.146.187:10130"
    )
    
    api.connect()
    api.login()
    api.query_orders()
    api.query_positions()
    api.logout()
    api.disconnect()