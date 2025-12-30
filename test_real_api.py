#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真实CTP API功能
"""

from ctp_api_real import CTPTraderAPIReal, CTPMarketAPIReal

def test_trader_api():
    print("=== 测试交易API ===")
    # 使用示例参数（请根据实际期货商信息修改）
    api = CTPTraderAPIReal(
        broker_id="9999",  # 示例经纪商代码
        user_id="123456",  # 示例用户ID
        password="password",  # 示例密码
        front_addr="tcp://180.168.146.187:10130",  # 示例前置地址
        app_id="simnow_client_test",
        auth_code="0000000000000000"
    )
    
    # 设置回调函数
    def on_connected(data):
        print("交易前置连接成功")
    
    def on_login(data):
        print(f"交易登录成功: {data}")
    
    def on_error(msg):
        print(f"错误: {msg}")
    
    api.set_callback('on_connected', on_connected)
    api.set_callback('on_login', on_login)
    api.set_callback('on_error', on_error)
    
    try:
        print("正在连接交易API...")
        api.connect()
        print(f"连接状态: is_connected={api.is_connected}, is_logged_in={api.is_logged_in}")
    except Exception as e:
        print(f"连接失败: {e}")


def test_market_api():
    print("\n=== 测试行情API ===")
    # 使用示例参数（请根据实际期货商信息修改）
    api = CTPMarketAPIReal(
        broker_id="9999",  # 示例经纪商代码
        user_id="123456",  # 示例用户ID
        password="password",  # 示例密码
        front_addr="tcp://180.168.146.187:10131"  # 示例行情前置地址
    )
    
    # 设置回调函数
    def on_connected():
        print("行情前置连接成功")
    
    def on_login(data):
        print(f"行情登录成功: {data}")
    
    def on_market_data(data):
        print(f"收到行情数据: {data.get('instrument_id', '')} - {data.get('last_price', 0)}")
    
    def on_error(msg):
        print(f"错误: {msg}")
    
    api.set_callback('on_connected', on_connected)
    api.set_callback('on_login', on_login)
    api.set_callback('on_market_data', on_market_data)
    api.set_callback('on_error', on_error)
    
    try:
        print("正在连接行情API...")
        api.connect()
        print(f"连接状态: is_connected={api.is_connected}, is_logged_in={api.is_logged_in}")
    except Exception as e:
        print(f"连接失败: {e}")


if __name__ == "__main__":
    print("测试真实CTP API功能")
    print("注意：此测试使用示例参数，实际使用时请替换为正确的账户信息")
    
    test_trader_api()
    test_market_api()