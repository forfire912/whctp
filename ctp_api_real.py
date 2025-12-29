#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTP Mini API真实实现
基于SFIT CTP Mini API V1.7.3-P2文档
使用openctp-ctp库进行实际的API调用
"""

import os
import sys
from datetime import datetime
from typing import Callable, Dict, Any, List
import time

# 尝试导入CTP库
try:
    from openctp_ctp import tdapi, mdapi
    CTP_AVAILABLE = True
except ImportError:
    print("警告: 未安装openctp-ctp库，将使用模拟模式")
    print("请运行: pip install openctp-ctp")
    CTP_AVAILABLE = False


class CTPTraderSpi:
    """交易API回调类"""
    
    def __init__(self, api_wrapper):
        self.api_wrapper = api_wrapper
    
    def OnFrontConnected(self):
        """前置机连接成功"""
        print("交易前置连接成功")
        self.api_wrapper.is_connected = True
        if self.api_wrapper.callbacks['on_connected']:
            self.api_wrapper.callbacks['on_connected']()
        
        # 连接成功后进行认证（如果配置了认证信息）
        if self.api_wrapper.app_id and self.api_wrapper.auth_code:
            self.api_wrapper._authenticate()
        else:
            # 无认证直接登录
            self.api_wrapper._do_login()
    
    def OnFrontDisconnected(self, nReason):
        """前置机断开"""
        print(f"交易前置断开，原因：{nReason}")
        self.api_wrapper.is_connected = False
        self.api_wrapper.is_logged_in = False
        if self.api_wrapper.callbacks['on_disconnected']:
            self.api_wrapper.callbacks['on_disconnected']()
    
    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告"""
        print(f"心跳超时警告：{nTimeLapse}秒")
    
    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """客户端认证响应"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"认证失败：{pRspInfo.ErrorMsg}")
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](f"认证失败：{pRspInfo.ErrorMsg}")
        else:
            print("认证成功")
            # 认证成功后登录
            self.api_wrapper._do_login()
    
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录响应"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"登录失败：{pRspInfo.ErrorMsg}")
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](f"登录失败：{pRspInfo.ErrorMsg}")
        else:
            print("登录成功")
            self.api_wrapper.is_logged_in = True
            self.api_wrapper.front_id = pRspUserLogin.FrontID
            self.api_wrapper.session_id = pRspUserLogin.SessionID
            self.api_wrapper.max_order_ref = int(pRspUserLogin.MaxOrderRef)
            
            login_info = {
                'broker_id': self.api_wrapper.broker_id,
                'user_id': self.api_wrapper.user_id,
                'trading_day': pRspUserLogin.TradingDay,
                'login_time': pRspUserLogin.LoginTime,
                'front_id': pRspUserLogin.FrontID,
                'session_id': pRspUserLogin.SessionID,
                'system_name': pRspUserLogin.SystemName if hasattr(pRspUserLogin, 'SystemName') else ''
            }
            
            if self.api_wrapper.callbacks['on_login']:
                self.api_wrapper.callbacks['on_login'](login_info)
    
    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出响应"""
        print("登出成功")
        self.api_wrapper.is_logged_in = False
        if self.api_wrapper.callbacks['on_logout']:
            self.api_wrapper.callbacks['on_logout']()
    
    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """查询投资者持仓响应"""
        if pInvestorPosition:
            position = {
                'instrument_id': pInvestorPosition.InstrumentID,
                'direction': '多' if pInvestorPosition.PosiDirection == '2' else '空',
                'position_type': '总仓',
                'volume': pInvestorPosition.Position,
                'available_volume': pInvestorPosition.Position - pInvestorPosition.LongFrozen - pInvestorPosition.ShortFrozen,
                'open_price': pInvestorPosition.OpenCost / pInvestorPosition.Position if pInvestorPosition.Position > 0 else 0,
                'position_price': pInvestorPosition.PositionCost / pInvestorPosition.Position if pInvestorPosition.Position > 0 else 0,
                'close_profit': pInvestorPosition.CloseProfit,
                'position_profit': pInvestorPosition.PositionProfit,
                'trading_day': pInvestorPosition.TradingDay if hasattr(pInvestorPosition, 'TradingDay') else ''
            }
            self.api_wrapper._position_cache.append(position)
        
        if bIsLast and self.api_wrapper.callbacks['on_position_rsp']:
            self.api_wrapper.callbacks['on_position_rsp'](self.api_wrapper._position_cache)
            self.api_wrapper._position_cache = []
    
    def OnRspQryOrder(self, pOrder, pRspInfo, nRequestID, bIsLast):
        """查询报单响应"""
        if pOrder:
            order = {
                'order_time': pOrder.InsertTime if hasattr(pOrder, 'InsertTime') else '',
                'instrument_id': pOrder.InstrumentID,
                'direction': '买入' if pOrder.Direction == '0' else '卖出',
                'offset_flag': self._parse_offset_flag(pOrder.CombOffsetFlag[0]) if pOrder.CombOffsetFlag else '',
                'order_price': pOrder.LimitPrice,
                'order_volume': pOrder.VolumeTotalOriginal,
                'traded_volume': pOrder.VolumeTraded,
                'order_status': self._parse_order_status(pOrder.OrderStatus),
                'remark': pOrder.StatusMsg if hasattr(pOrder, 'StatusMsg') else '',
                'trading_day': pOrder.TradingDay if hasattr(pOrder, 'TradingDay') else ''
            }
            self.api_wrapper._order_cache.append(order)
        
        if bIsLast and self.api_wrapper.callbacks['on_order_rsp']:
            self.api_wrapper.callbacks['on_order_rsp'](self.api_wrapper._order_cache)
            self.api_wrapper._order_cache = []
    
    def OnRspQryTrade(self, pTrade, pRspInfo, nRequestID, bIsLast):
        """查询成交响应"""
        if pTrade:
            trade = {
                'trade_time': pTrade.TradeTime if hasattr(pTrade, 'TradeTime') else '',
                'instrument_id': pTrade.InstrumentID,
                'direction': '买入' if pTrade.Direction == '0' else '卖出',
                'offset_flag': self._parse_offset_flag(pTrade.OffsetFlag),
                'price': pTrade.Price,
                'volume': pTrade.Volume,
                'trade_id': pTrade.TradeID,
                'trading_day': pTrade.TradingDay if hasattr(pTrade, 'TradingDay') else ''
            }
            self.api_wrapper._trade_cache.append(trade)
        
        if bIsLast and self.api_wrapper.callbacks['on_trade_rsp']:
            self.api_wrapper.callbacks['on_trade_rsp'](self.api_wrapper._trade_cache)
            self.api_wrapper._trade_cache = []
    
    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """查询合约响应"""
        if pInstrument:
            instrument = {
                'instrument_id': pInstrument.InstrumentID,
                'exchange_id': pInstrument.ExchangeID,
                'instrument_name': pInstrument.InstrumentName,
                'product_id': pInstrument.ProductID,
                'product_class': str(pInstrument.ProductClass),
                'delivery_year': pInstrument.DeliveryYear,
                'delivery_month': pInstrument.DeliveryMonth,
                'volume_multiple': pInstrument.VolumeMultiple,
                'price_tick': pInstrument.PriceTick,
                'create_date': pInstrument.CreateDate if hasattr(pInstrument, 'CreateDate') else '',
                'open_date': pInstrument.OpenDate,
                'expire_date': pInstrument.ExpireDate,
                'is_trading': pInstrument.IsTrading,
                'long_margin_ratio': pInstrument.LongMarginRatio,
                'short_margin_ratio': pInstrument.ShortMarginRatio
            }
            self.api_wrapper._instrument_cache.append(instrument)
        
        if bIsLast and self.api_wrapper.callbacks['on_instrument_rsp']:
            self.api_wrapper.callbacks['on_instrument_rsp'](self.api_wrapper._instrument_cache)
            self.api_wrapper._instrument_cache = []
    
    def _parse_offset_flag(self, flag):
        """解析开平标志"""
        flag_map = {
            '0': '开仓',
            '1': '平仓',
            '2': '强平',
            '3': '平今',
            '4': '平昨',
            '5': '强减',
            '6': '本地强平'
        }
        return flag_map.get(flag, '未知')
    
    def _parse_order_status(self, status):
        """解析报单状态"""
        status_map = {
            '0': '全部成交',
            '1': '部分成交还在队列中',
            '2': '部分成交不在队列中',
            '3': '未成交还在队列中',
            '4': '未成交不在队列中',
            '5': '撤单',
            'a': '未知',
            'b': '尚未触发',
            'c': '已触发'
        }
        return status_map.get(status, '未知')


class CTPTraderAPIReal:
    """CTP交易API真实实现"""
    
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
        self.max_order_ref = 0
        
        # 数据缓存
        self._position_cache = []
        self._order_cache = []
        self._trade_cache = []
        self._instrument_cache = []
        
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
        
        # CTP API对象
        self.api = None
        self.spi = None
        
        # 创建流文件目录
        self.flow_path = "./flow/"
        if not os.path.exists(self.flow_path):
            os.makedirs(self.flow_path)
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def connect(self) -> bool:
        """连接到CTP服务器"""
        if not CTP_AVAILABLE:
            print("CTP库未安装，使用模拟模式")
            return False
        
        try:
            print(f"正在连接到CTP服务器: {self.front_addr}")
            
            # 创建TraderAPI实例
            self.api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi(self.flow_path.encode('utf-8'))
            
            # 创建SPI实例
            self.spi = CTPTraderSpi(self)
            
            # 注册SPI
            self.api.RegisterSpi(self.spi)
            
            # 订阅私有流和公共流
            # THOST_TERT_RESTART: 从本交易日开始重传
            # THOST_TERT_RESUME: 从上次收到的续传
            # THOST_TERT_QUICK: 只传送登录后的内容
            self.api.SubscribePrivateTopic(2)  # THOST_TERT_QUICK
            self.api.SubscribePublicTopic(2)   # THOST_TERT_QUICK
            
            # 注册前置地址
            self.api.RegisterFront(self.front_addr.encode('utf-8'))
            
            # 初始化API
            self.api.Init()
            
            print("等待连接建立...")
            # 等待连接建立（最多10秒）
            for i in range(100):
                if self.is_connected:
                    return True
                time.sleep(0.1)
            
            print("连接超时")
            return False
            
        except Exception as e:
            print(f"连接失败: {e}")
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"连接失败: {e}")
            return False
    
    def _authenticate(self):
        """客户端认证"""
        if not self.api:
            return
        
        req = tdapi.CThostFtdcReqAuthenticateField()
        req.BrokerID = self.broker_id.encode('utf-8')
        req.UserID = self.user_id.encode('utf-8')
        req.AppID = self.app_id.encode('utf-8')
        req.AuthCode = self.auth_code.encode('utf-8')
        
        self.request_id += 1
        self.api.ReqAuthenticate(req, self.request_id)
    
    def _do_login(self):
        """执行登录"""
        if not self.api:
            return
        
        req = tdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = self.broker_id.encode('utf-8')
        req.UserID = self.user_id.encode('utf-8')
        req.Password = self.password.encode('utf-8')
        
        self.request_id += 1
        self.api.ReqUserLogin(req, self.request_id)
    
    def login(self) -> bool:
        """登录CTP系统（实际登录在连接成功后自动进行）"""
        # 等待登录完成（最多20秒）
        for i in range(200):
            if self.is_logged_in:
                return True
            time.sleep(0.1)
        
        print("登录超时")
        return False
    
    def logout(self) -> bool:
        """登出CTP系统"""
        if not self.api or not self.is_logged_in:
            return False
        
        try:
            req = tdapi.CThostFtdcUserLogoutField()
            req.BrokerID = self.broker_id.encode('utf-8')
            req.UserID = self.user_id.encode('utf-8')
            
            self.request_id += 1
            self.api.ReqUserLogout(req, self.request_id)
            
            time.sleep(1)  # 等待登出完成
            return True
        except Exception as e:
            print(f"登出失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.is_logged_in:
            self.logout()
        
        if self.api:
            self.api.Release()
            self.api = None
        
        self.is_connected = False
        if self.callbacks['on_disconnected']:
            self.callbacks['on_disconnected']()
    
    def query_orders(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """查询当日委托"""
        if not self.api or not self.is_logged_in:
            print("请先登录")
            return []
        
        try:
            req = tdapi.CThostFtdcQryOrderField()
            req.BrokerID = self.broker_id.encode('utf-8')
            req.InvestorID = self.user_id.encode('utf-8')
            if instrument_id:
                req.InstrumentID = instrument_id.encode('utf-8')
            if exchange_id:
                req.ExchangeID = exchange_id.encode('utf-8')
            
            self.request_id += 1
            self._order_cache = []
            self.api.ReqQryOrder(req, self.request_id)
            
            # 等待查询完成
            time.sleep(1.5)  # CTP查询限流，需要间隔
            return self._order_cache
        except Exception as e:
            print(f"查询委托失败: {e}")
            return []
    
    def query_positions(self, instrument_id: str = "") -> list:
        """查询持仓"""
        if not self.api or not self.is_logged_in:
            print("请先登录")
            return []
        
        try:
            req = tdapi.CThostFtdcQryInvestorPositionField()
            req.BrokerID = self.broker_id.encode('utf-8')
            req.InvestorID = self.user_id.encode('utf-8')
            if instrument_id:
                req.InstrumentID = instrument_id.encode('utf-8')
            
            self.request_id += 1
            self._position_cache = []
            self.api.ReqQryInvestorPosition(req, self.request_id)
            
            # 等待查询完成
            time.sleep(1.5)
            return self._position_cache
        except Exception as e:
            print(f"查询持仓失败: {e}")
            return []
    
    def query_trades(self, instrument_id: str = "") -> list:
        """查询成交"""
        if not self.api or not self.is_logged_in:
            print("请先登录")
            return []
        
        try:
            req = tdapi.CThostFtdcQryTradeField()
            req.BrokerID = self.broker_id.encode('utf-8')
            req.InvestorID = self.user_id.encode('utf-8')
            if instrument_id:
                req.InstrumentID = instrument_id.encode('utf-8')
            
            self.request_id += 1
            self._trade_cache = []
            self.api.ReqQryTrade(req, self.request_id)
            
            # 等待查询完成
            time.sleep(1.5)
            return self._trade_cache
        except Exception as e:
            print(f"查询成交失败: {e}")
            return []
    
    def query_instruments(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """查询合约"""
        if not self.api or not self.is_logged_in:
            print("请先登录")
            return []
        
        try:
            req = tdapi.CThostFtdcQryInstrumentField()
            if instrument_id:
                req.InstrumentID = instrument_id.encode('utf-8')
            if exchange_id:
                req.ExchangeID = exchange_id.encode('utf-8')
            
            self.request_id += 1
            self._instrument_cache = []
            self.api.ReqQryInstrument(req, self.request_id)
            
            # 等待查询完成
            time.sleep(1.5)
            return self._instrument_cache
        except Exception as e:
            print(f"查询合约失败: {e}")
            return []


# 导出API类（根据是否安装了CTP库选择实现）
if CTP_AVAILABLE:
    CTPTraderAPI = CTPTraderAPIReal
    print("使用真实CTP API")
else:
    # 如果没有安装CTP库，使用原来的模拟实现
    from ctp_api_wrapper import CTPTraderAPI as CTPTraderAPIMock
    CTPTraderAPI = CTPTraderAPIMock
    print("使用模拟CTP API")


if __name__ == "__main__":
    # 测试代码
    print(f"CTP库状态: {'已安装' if CTP_AVAILABLE else '未安装'}")
    
    if CTP_AVAILABLE:
        api = CTPTraderAPIReal(
            broker_id="9999",
            user_id="123456",
            password="password",
            front_addr="tcp://180.168.146.187:10130"
        )
        
        if api.connect():
            api.login()
            if api.is_logged_in:
                # 查询持仓
                positions = api.query_positions()
                print(f"持仓数量: {len(positions)}")
                
                # 查询委托
                orders = api.query_orders()
                print(f"委托数量: {len(orders)}")
            
            api.disconnect()
