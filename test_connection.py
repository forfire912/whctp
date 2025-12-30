#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTP连接测试脚本
用于测试CTP API连接和登录功能
"""

import json
import os
import time
import threading
from datetime import datetime

# 从main_gui导入相关类
from ctp_api_real import CTPTraderAPIReal
from database_manager import DatabaseManager


def test_connection():
    """测试CTP连接功能"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始测试CTP连接...")
    
    # 读取配置
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        print("配置文件不存在，请先配置config.json")
        return

    # 初始化数据库
    db_manager = DatabaseManager(
        host=config['database']['host'],
        user=config['database']['user'],
        password=config['database']['password'],
        database=config['database']['database']
    )
    if not db_manager.connect():
        print("数据库连接失败")
        return
    print("数据库连接成功")

    # 初始化CTP API
    ctp_conf = config['ctp']
    trader_api = CTPTraderAPIReal(
        broker_id=ctp_conf['broker_id'],
        user_id=ctp_conf['user_id'],
        password=ctp_conf['password'],
        front_addr=ctp_conf['trade_front'],
        app_id=ctp_conf.get('app_id', ''),
        auth_code=ctp_conf.get('auth_code', '')
    )

    # 设置回调
    def on_connected():
        print("交易前置连接成功")
    
    def on_login(login_info):
        print(f"登录成功: {login_info}")
        
    def on_error(error_msg):
        print(f"错误: {error_msg}")
    
    def on_disconnected():
        print("前置机断开连接")

    trader_api.set_callback('on_connected', on_connected)
    trader_api.set_callback('on_login', on_login)
    trader_api.set_callback('on_error', on_error)
    trader_api.set_callback('on_disconnected', on_disconnected)

    # 连接和登录
    try:
        print("正在连接到CTP系统...")
        if trader_api.connect():
            print("CTP系统连接成功")
            
            # 等待一段时间以观察登录结果
            print("等待登录结果...（最多等待15秒）")
            for i in range(15):  # 等待15秒
                time.sleep(1)
                print(f"等待中... {i+1}/15秒")
                
                # 检查是否登录成功
                if hasattr(trader_api, 'is_logged_in') and trader_api.is_logged_in:
                    print("检测到已登录状态")
                    break
        else:
            print("CTP连接失败")
    except Exception as e:
        print(f"连接过程出现异常: {e}")

    # 输出最终状态
    print(f"最终状态 - 已连接: {trader_api.is_connected}, 已登录: {trader_api.is_logged_in}")

    # 测试查询功能
    if trader_api.is_logged_in:
        print("开始测试查询功能...")
        
        # 测试查询持仓
        print("正在查询持仓数据...")
        positions = trader_api.query_positions()
        print(f"查询到 {len(positions)} 条持仓记录")
        
        # 测试查询委托
        print("正在查询委托数据...")
        orders = trader_api.query_orders()
        print(f"查询到 {len(orders)} 条委托记录")
        
        # 测试查询合约
        print("正在查询合约参数...")
        instruments = trader_api.query_instruments()
        print(f"查询到 {len(instruments)} 条合约参数")
    else:
        print("未登录，无法进行查询操作")

    # 断开连接
    trader_api.disconnect()
    db_manager.close()
    print("测试完成")


if __name__ == "__main__":
    test_connection()