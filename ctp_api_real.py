#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTP Mini API真实实现
基于SFIT CTP Mini API V1.7.3-P2文档，使用openctp-ctp库进行实际的API调用

说明：
    该模块提供真实CTP实现，并在未安装openctp-ctp时自动降级为模拟实现。
"""

import os
import sys
from datetime import datetime
from typing import Callable, Dict, Any, List
import time
from threading import Event

# 是否强制使用模拟CTP实现：
# 1) 优先读取环境变量 USE_MOCK_CTP（"1"/"true" 表示启用模拟）;
# 2) 若环境变量未设置，则使用下面的默认值。
_env_mock = os.environ.get("USE_MOCK_CTP", "").lower()
USE_MOCK_CTP = True if _env_mock in ("1", "true", "yes", "y") or _env_mock == "" else False

# 尝试导入CTP库
try:
    from openctp_ctp import tdapi, mdapi
    CTP_AVAILABLE = True
except ImportError:
    print("警告: 未安装openctp-ctp库，将使用模拟模式")
    print("请运行: pip install openctp-ctp")
    CTP_AVAILABLE = False


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
        self._account_cache = []
        self._investor_cache = []
        
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
            'on_instrument_rsp': None,
            'on_account_rsp': None
        }
        
        # CTP API对象
        self.api = None
        self.spi = None
        
        # 创建流文件目录
        self.flow_path = "./flow/"
        if not os.path.exists(self.flow_path):
            os.makedirs(self.flow_path)
        
        # 查询结果存储
        self._pos_results = []
        self._pos_event = Event()
        self._qry_results = []
        self._qry_event = Event()
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def _next_req_id(self):
        """获取下一个请求ID"""
        self.request_id += 1
        return self.request_id

    def connect(self):
        """连接到CTP交易前置"""
        if not CTP_AVAILABLE:
            raise RuntimeError("openctp-ctp 库不可用，请先安装并检查环境")

        try:
            # 创建API实例
            self.api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi()

            # 创建并注册SPI
            self.spi = CTPTraderSpi(self)
            self.api.RegisterSpi(self.spi)

            # 注意：RegisterFront 需要的是 char*，SWIG 绑定接受 Python 字符串，
            # 不要再手动 .encode('utf-8')，否则会出现参数类型不匹配错误
            self.api.RegisterFront(self.front_addr)

            # 可选：订阅私有/公共流，这里使用快速模式
            try:
                self.api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
                self.api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)
            except AttributeError:
                # 某些版本可能枚举名不同，忽略即可
                pass

            # 初始化，开始连接
            self.api.Init()
            return True
        except Exception as e:
            # 这里的异常会被 GUI 捕获并显示
            raise RuntimeError(f"连接真实CTP失败: {e}")

    def _do_authenticate(self):
        """发送认证请求，对应 C++ demo 中的 ReqAuthenticate"""
        if not self.api:
            return
        req = tdapi.CThostFtdcReqAuthenticateField()
        req.BrokerID = self.broker_id
        req.UserID = self.user_id
        if self.app_id:
            req.AppID = self.app_id
        if self.auth_code:
            req.AuthCode = self.auth_code
        self.api.ReqAuthenticate(req, self._next_req_id())

    def _do_login(self):
        """发送登录请求，对应 C++ demo 中的 ReqUserLogin"""
        if not self.api:
            return
        req = tdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = self.broker_id
        req.UserID = self.user_id
        req.Password = self.password
        self.api.ReqUserLogin(req, self._next_req_id())

    def login(self):
        """登录：这里返回 True/False，仅表示是否已进入登录流程，实际结果由回调通知"""
        # 真实 CTP 登录是异步的，这里简单返回 True，表示已发起流程
        return True

    def disconnect(self):
        if self.api:
            try:
                self.api.Release()
            except Exception:
                pass
            self.api = None
            self.spi = None
        self.is_connected = False
        self.is_logged_in = False

    def query_orders(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """查询当日委托：真实环境下应调用 ReqQryOrder"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法查询委托")
            return []

        # 发送查询请求
        try:
            req = tdapi.CThostFtdcQryOrderField()
            req.BrokerID = self.broker_id
            req.InvestorID = self.user_id
            if instrument_id:
                req.InstrumentID = instrument_id
            if exchange_id:
                req.ExchangeID = exchange_id
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"构造委托查询请求失败: {e}")
            return []

        try:
            ret = self.api.ReqQryOrder(req, self._next_req_id())
            if ret != 0:
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](f"委托查询请求发送失败，错误码: {ret}")
                return []
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"发送委托查询失败: {e}")
            return []

        # 由于CTP查询是异步的，这里暂时返回空列表，实际数据通过回调处理
        # 如果需要同步返回数据，需要类似持仓查询的事件等待机制
        return []

    def query_positions(self, instrument_id: str = "") -> list:
        """查询持仓：发送 ReqQryInvestorPosition，并同步等待 SPI 返回全部结果"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法查询持仓")
            return []

        # 清空上一次结果
        self._pos_results = []
        self._pos_event.clear()

        # 构造查询请求结构体，参考 C++ Demo 中 ReqQryInvestorPosition(nullptr,...)
        try:
            req = tdapi.CThostFtdcQryInvestorPositionField()
            # 经纪商、投资者必填
            req.BrokerID = self.broker_id
            req.InvestorID = self.user_id
            # 合约可选过滤
            if instrument_id:
                req.InstrumentID = instrument_id
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"构造持仓查询请求失败: {e}")
            return []

        # 发送查询请求
        try:
            ret = self.api.ReqQryInvestorPosition(req, self._next_req_id())
            if ret != 0:
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](f"持仓查询请求发送失败，错误码: {ret}")
                return []
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"发送持仓查询失败: {e}")
            return []

        # 等待 SPI 回调结束（bIsLast=True 时会 set 事件），最多等 10 秒
        finished = self._pos_event.wait(timeout=10)
        if not finished:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("持仓查询超时")

        return list(self._pos_results)

    def query_instruments(self, instrument_id: str = "", exchange_id: str = "") -> list:
        """查询合约：真实环境下应调用 ReqQryInstrument，这里先占位返回空列表"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法查询合约")
            return []

        # 清空之前的查询结果
        self._qry_results = []
        self._qry_event.clear()

        # 发送查询请求
        try:
            req = tdapi.CThostFtdcQryInstrumentField()
            req.BrokerID = self.broker_id
            req.InstrumentID = instrument_id
            req.ExchangeID = exchange_id
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"构造合约查询请求失败: {e}")
            return []

        try:
            ret = self.api.ReqQryInstrument(req, self._next_req_id())
            if ret != 0:
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](f"合约查询请求发送失败，错误码: {ret}")
                return []
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"发送合约查询失败: {e}")
            return []

        # 等待查询完成
        finished = self._qry_event.wait(timeout=10)
        if not finished:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("合约查询超时")

        return list(self._qry_results)

    def query_trades(self, instrument_id: str = "") -> list:
        """查询成交：发送 ReqQryTrade，并同步等待结果"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法查询成交")
            return []

        # 清空上一次结果
        self._qry_results = []
        self._qry_event.clear()

        # 构造查询请求结构体
        try:
            req = tdapi.CThostFtdcQryTradeField()
            req.BrokerID = self.broker_id
            req.InvestorID = self.user_id
            if instrument_id:
                req.InstrumentID = instrument_id
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"构造成交查询请求失败: {e}")
            return []

        # 发送查询请求
        try:
            ret = self.api.ReqQryTrade(req, self._next_req_id())
            if ret != 0:
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](f"成交查询请求发送失败，错误码: {ret}")
                return []
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"发送成交查询失败: {e}")
            return []

        # 等待查询完成
        finished = self._qry_event.wait(timeout=10)
        if not finished:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("成交查询超时")

        return list(self._qry_results)

    def query_accounts(self) -> list:
        """查询资金：发送 ReqQryTradingAccount 并同步等待结果"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法查询资金")
            return []

        # 清空上一次结果
        self._qry_results = []
        self._qry_event.clear()

        # 构造查询请求结构体
        try:
            req = tdapi.CThostFtdcQryTradingAccountField()
            req.BrokerID = self.broker_id
            req.InvestorID = self.user_id
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"构造资金查询请求失败: {e}")
            return []

        # 发送查询请求
        try:
            ret = self.api.ReqQryTradingAccount(req, self._next_req_id())
            if ret != 0:
                if self.callbacks['on_error']:
                    self.callbacks['on_error'](f"资金查询请求发送失败，错误码: {ret}")
                return []
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"发送资金查询失败: {e}")
            return []

        # 等待查询完成
        finished = self._qry_event.wait(timeout=10)
        if not finished:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("资金查询超时")

        return list(self._qry_results)


class CTPTraderSpi(tdapi.CThostFtdcTraderSpi if CTP_AVAILABLE else object):
    """交易API回调类，必须继承CThostFtdcTraderSpi以满足RegisterSpi类型要求"""
    
    def __init__(self, api_wrapper):
        # 当CTP_AVAILABLE为True时，父类是CThostFtdcTraderSpi，需要显式调用其构造
        try:
            super().__init__()
        except TypeError:
            # 当父类为object或构造签名不匹配时，忽略
            pass
        self.api_wrapper = api_wrapper
    
    def OnFrontConnected(self):
        """前置机连接成功"""
        print("交易前置连接成功")
        self.api_wrapper.is_connected = True
        if self.api_wrapper.callbacks['on_connected']:
            self.api_wrapper.callbacks['on_connected']()
        
        # 连接成功后进行认证（如果配置了认证信息）
        if self.api_wrapper.app_id and self.api_wrapper.auth_code:
            self.api_wrapper._do_authenticate()
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
        """持仓查询响应：将 CTP 结构转换成我们自己的 daily_positions 字段"""
        # 错误处理
        if pRspInfo and pRspInfo.ErrorID != 0:
            err = f"查询持仓失败: {pRspInfo.ErrorID} {getattr(pRspInfo, 'ErrorMsg', '')}"
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](err)
            # 即使出错也结束等待
            if bIsLast:
                self.api_wrapper._pos_event.set()
            return

        if pInvestorPosition:
            try:
                # CTP 方向/今昨字段映射为我们的 direction/position_type
                posi = pInvestorPosition
                direction = '多头' if getattr(posi, 'PosiDirection', '') == getattr(tdapi, 'THOST_FTDC_D_Buy', '0') else '空头'
                # position_type 暂时用 "总仓"，后续如有需要可根据 TodayPosition/YdPosition 拆分
                position_type = '总仓'
                volume = getattr(posi, 'Position', 0) or 0
                available_volume = getattr(posi, 'TodayPosition', 0) or 0
                # 开仓/持仓均价近似处理：使用 OpenCost / (Position * VolumeMultiple)
                vol_mult = getattr(posi, 'VolumeMultiple', 0) or 1
                if volume * vol_mult > 0:
                    open_price = (getattr(posi, 'OpenCost', 0.0) or 0.0) / (volume * vol_mult)
                else:
                    open_price = 0.0
                position_price = open_price
                close_profit = getattr(posi, 'CloseProfit', 0.0) or 0.0
                position_profit = getattr(posi, 'PositionProfit', 0.0) or 0.0
                trading_day = getattr(posi, 'TradingDay', '') or ''

                row = {
                    'instrument_id': getattr(posi, 'InstrumentID', ''),
                    'direction': direction,
                    'position_type': position_type,
                    'volume': int(volume),
                    'available_volume': int(available_volume),
                    'open_price': float(open_price),
                    'position_price': float(position_price),
                    'close_profit': float(close_profit),
                    'position_profit': float(position_profit),
                    'trading_day': trading_day,
                }
                self.api_wrapper._pos_results.append(row)
            except Exception as e:
                if self.api_wrapper.callbacks['on_error']:
                    self.api_wrapper.callbacks['on_error'](f"处理持仓数据时异常: {e}")

        if bIsLast:
            # 通知等待方查询结束
            self.api_wrapper._pos_event.set()
    
    def OnRspQryOrder(self, pOrder, pRspInfo, nRequestID, bIsLast):
        """查询报单响应"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            err = f"查询委托失败: {pRspInfo.ErrorID} {getattr(pRspInfo, 'ErrorMsg', '')}"
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](err)
            return

        if pOrder:
            order = {
                'order_time': pOrder.InsertTime if hasattr(pOrder, 'InsertTime') else '',
                'instrument_id': pOrder.InstrumentID,
                'direction': '买入' if pOrder.Direction == getattr(tdapi, 'THOST_FTDC_D_Buy', '0') else '卖出',
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
        if pRspInfo and pRspInfo.ErrorID != 0:
            err = f"查询成交失败: {pRspInfo.ErrorID} {getattr(pRspInfo, 'ErrorMsg', '')}"
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](err)
            # 即使出错也要通知结束
            if bIsLast:
                self.api_wrapper._qry_event.set()
            return

        if pTrade:
            trade = {
                'trade_time': pTrade.TradeTime if hasattr(pTrade, 'TradeTime') else '',
                'instrument_id': pTrade.InstrumentID,
                'direction': '买入' if pTrade.Direction == getattr(tdapi, 'THOST_FTDC_D_Buy', '0') else '卖出',
                'offset_flag': self._parse_offset_flag(pTrade.OffsetFlag),
                'price': pTrade.Price,
                'volume': pTrade.Volume,
                'trade_id': pTrade.TradeID,
                'trading_day': pTrade.TradingDay if hasattr(pTrade, 'TradingDay') else ''
            }
            self.api_wrapper._qry_results.append(trade)
        
        if bIsLast:
            # 通知等待方查询结束
            self.api_wrapper._qry_event.set()
    
    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """查询合约响应"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            err = f"查询合约失败: {pRspInfo.ErrorID} {getattr(pRspInfo, 'ErrorMsg', '')}"
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](err)
            # 即使出错也要通知结束
            if bIsLast:
                self.api_wrapper._qry_event.set()
            return

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
            self.api_wrapper._qry_results.append(instrument)
        
        if bIsLast:
            # 通知等待方查询结束
            self.api_wrapper._qry_event.set()
    
    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        """查询资金响应"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            err = f"查询资金失败: {pRspInfo.ErrorID} {getattr(pRspInfo, 'ErrorMsg', '')}"
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](err)
            # 即使出错也要通知结束
            if bIsLast:
                self.api_wrapper._qry_event.set()
            return

        if pTradingAccount:
            account = {
                'account_id': pTradingAccount.AccountID,
                'pre_balance': pTradingAccount.PreBalance,
                'balance': pTradingAccount.Balance,
                'available': pTradingAccount.Available,
                'withdraw': pTradingAccount.WithdrawQuota,
                'margin': pTradingAccount.CurrMargin,
                'frozen_margin': pTradingAccount.FrozenMargin,
                'frozen_cash': pTradingAccount.FrozenCash,
                'frozen_commission': pTradingAccount.FrozenCommission,
                'commission': pTradingAccount.Commission,
                'close_profit': pTradingAccount.CloseProfit,
                'position_profit': pTradingAccount.PositionProfit,
                'trading_day': pTradingAccount.TradingDay
            }
            self.api_wrapper._qry_results.append(account)
        
        if bIsLast:
            # 通知等待方查询结束
            self.api_wrapper._qry_event.set()
    
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


class CTPMarketAPIReal:
    """CTP行情API真实实现"""
    
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
        
        # CTP API对象
        self.api = None
        self.spi = None
        
        # 创建流文件目录
        self.flow_path = "./flow/md/"
        if not os.path.exists(self.flow_path):
            os.makedirs(self.flow_path)
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback

    def connect(self):
        """连接到CTP行情前置"""
        if not CTP_AVAILABLE:
            raise RuntimeError("openctp-ctp 库不可用，请先安装并检查环境")

        try:
            # 创建API实例
            self.api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi()

            # 创建并注册SPI
            self.spi = CTPMdSpi(self)
            self.api.RegisterSpi(self.spi)

            # 注册前置地址
            self.api.RegisterFront(self.front_addr)

            # 初始化，开始连接
            self.api.Init()
            return True
        except Exception as e:
            # 这里的异常会被 GUI 捕获并显示
            raise RuntimeError(f"连接真实CTP行情失败: {e}")

    def login(self):
        """登录行情API：这里返回 True/False，仅表示是否已进入登录流程，实际结果由回调通知"""
        if not self.api:
            return False
        # 真实 CTP 登录是异步的，这里简单返回 True，表示已发起流程
        return True

    def subscribe_market_data(self, instrument_ids: list) -> bool:
        """订阅行情数据"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法订阅行情")
            return False

        try:
            # 转换为字符串数组
            ids = [str(id) for id in instrument_ids]
            ret = self.api.SubscribeMarketData(ids, len(ids))
            return ret == 0
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"订阅行情失败: {e}")
            return False

    def unsubscribe_market_data(self, instrument_ids: list) -> bool:
        """取消订阅行情数据"""
        if not self.api or not self.is_logged_in:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("尚未登录，无法取消订阅行情")
            return False

        try:
            # 转换为字符串数组
            ids = [str(id) for id in instrument_ids]
            ret = self.api.UnSubscribeMarketData(ids, len(ids))
            return ret == 0
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](f"取消订阅行情失败: {e}")
            return False

    def disconnect(self):
        if self.api:
            try:
                self.api.Release()
            except Exception:
                pass
            self.api = None
            self.spi = None
        self.is_connected = False
        self.is_logged_in = False


class CTPMdSpi(mdapi.CThostFtdcMdSpi if CTP_AVAILABLE else object):
    """行情API回调类，必须继承CThostFtdcMdSpi以满足RegisterSpi类型要求"""
    
    def __init__(self, api_wrapper):
        # 当CTP_AVAILABLE为True时，父类是CThostFtdcMdSpi，需要显式调用其构造
        try:
            super().__init__()
        except TypeError:
            # 当父类为object或构造签名不匹配时，忽略
            pass
        self.api_wrapper = api_wrapper

    def OnFrontConnected(self):
        """行情前置机连接成功"""
        print("行情前置连接成功，开始登录...")
        self.api_wrapper.is_connected = True
        if self.api_wrapper.callbacks['on_connected']:
            self.api_wrapper.callbacks['on_connected']()
        
        # 连接成功后登录
        field = mdapi.CThostFtdcReqUserLoginField()
        field.BrokerID = self.api_wrapper.broker_id
        field.UserID = self.api_wrapper.user_id
        field.Password = self.api_wrapper.password
        self.api_wrapper.api.ReqUserLogin(field, 1)

    def OnFrontDisconnected(self, nReason):
        """行情前置机断开"""
        print(f"行情前置断开，原因：{nReason}")
        self.api_wrapper.is_connected = False
        self.api_wrapper.is_logged_in = False
        if self.api_wrapper.callbacks['on_disconnected']:
            self.api_wrapper.callbacks['on_disconnected']()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """行情登录应答"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"行情登录失败：{pRspInfo.ErrorMsg}")
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](f"行情登录失败：{pRspInfo.ErrorMsg}")
        else:
            print("行情登录成功")
            self.api_wrapper.is_logged_in = True
            if self.api_wrapper.callbacks['on_login']:
                self.api_wrapper.callbacks['on_login']({'user_id': self.api_wrapper.user_id})

    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """订阅行情应答"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"订阅行情失败：{pRspInfo.ErrorMsg}")
            if self.api_wrapper.callbacks['on_error']:
                self.api_wrapper.callbacks['on_error'](f"订阅行情失败：{pRspInfo.ErrorMsg}")

    def OnRspUnSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """取消订阅行情应答"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"取消订阅行情失败：{pRspInfo.ErrorMsg}")

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """深度行情推送"""
        if pDepthMarketData:
            market_data = {
                'instrument_id': pDepthMarketData.InstrumentID,
                'last_price': pDepthMarketData.LastPrice,
                'pre_settlement_price': pDepthMarketData.PreSettlementPrice,
                'pre_close_price': pDepthMarketData.PreClosePrice,
                'pre_open_interest': pDepthMarketData.PreOpenInterest,
                'open_price': pDepthMarketData.OpenPrice,
                'high_price': pDepthMarketData.HighestPrice,
                'low_price': pDepthMarketData.LowestPrice,
                'upper_limit_price': pDepthMarketData.UpperLimitPrice,
                'lower_limit_price': pDepthMarketData.LowerLimitPrice,
                'volume': pDepthMarketData.Volume,
                'turnover': pDepthMarketData.Turnover,
                'open_interest': pDepthMarketData.OpenInterest,
                'bid_price1': pDepthMarketData.BidPrice1,
                'bid_volume1': pDepthMarketData.BidVolume1,
                'ask_price1': pDepthMarketData.AskPrice1,
                'ask_volume1': pDepthMarketData.AskVolume1,
                'update_time': pDepthMarketData.UpdateTime,
                'update_millisec': pDepthMarketData.UpdateMillisec,
                'average_price': pDepthMarketData.AveragePrice,
                'trading_day': pDepthMarketData.TradingDay
            }
            if self.api_wrapper.callbacks['on_market_data']:
                self.api_wrapper.callbacks['on_market_data'](market_data)


# 导出API类（根据开关与是否安装CTP库选择实现）
if not USE_MOCK_CTP and CTP_AVAILABLE:
    # 使用真实实现
    CTPTraderAPI = CTPTraderAPIReal
    CTPMarketAPI = CTPMarketAPIReal
    print("使用真实CTP API")
else:
    # 使用模拟实现
    from ctp_api_wrapper import CTPTraderAPI as CTPTraderAPIMock
    from ctp_api_wrapper import CTPMarketAPI as CTPMarketAPIMock
    CTPTraderAPI = CTPTraderAPIMock
    CTPMarketAPI = CTPMarketAPIMock
    if USE_MOCK_CTP:
        print("使用模拟CTP API（配置开关：USE_MOCK_CTP = True）")
    else:
        print("使用模拟CTP API（CTP库未安装，自动降级）")


if __name__ == "__main__":
    # 简单测试
    print(f"CTP库状态: {'已安装' if CTP_AVAILABLE else '未安装'}，当前模式: {'模拟' if CTPTraderAPI is not CTPTraderAPIReal else '真实'}")
    
    # 使用模拟实现进行简单测试
    api = CTPTraderAPIMock(
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