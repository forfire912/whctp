#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTP期货交易管理系统 - 主界面
基于Tkinter的GUI程序，支持数据下载、查询和管理
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime, timedelta, date
import json
import os
from typing import Dict, Any
from tkcalendar import Calendar

# 市场行情暂时仍使用模拟封装
from ctp_api_wrapper import CTPMarketAPI

from database_manager import DatabaseManager


class CTPTradingGUI:
    """CTP交易管理系统主界面"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("CTP期货交易管理系统")
        self.root.geometry("1200x800")
        
        # 当前交易日（默认为今天）
        self.current_trading_day = datetime.now().strftime('%Y%m%d')
        
        # 配置文件路径
        self.config_file = "config.json"
        self.config = self.load_config()
        
        # API和数据库实例
        self.trader_api = None
        self.market_api = None
        self.db_manager = None
        
        # 连接状态
        self.is_connected = False
        self.is_logged_in = False
        
        # 自动下载定时器
        self.auto_download_timer = None
        
        # 创建UI
        self.create_widgets()
        
        # 加载配置到界面
        self.load_config_to_ui()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "ctp": {
                "broker_id": "9999",
                "user_id": "",
                "password": "",
                "trade_front": "tcp://180.168.146.187:10130",
                "market_front": "tcp://180.168.146.187:10131",
                "app_id": "",
                "auth_code": ""
            },
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "ctp_trading"
            },
            "auto_download": {
                "enabled": False,
                "interval": 300
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            except Exception as e:
                self.log(f"加载配置文件失败: {e}")
                return default_config
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.log("配置已保存")
        except Exception as e:
            self.log(f"保存配置失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 1. 连接配置区域
        self.create_connection_frame(main_frame)
        
        # 2. 功能按钮区域
        self.create_action_frame(main_frame)
        
        # 3. 数据显示区域（使用Notebook）
        self.create_data_notebook(main_frame)
        
        # 4. 日志区域
        self.create_log_frame(main_frame)
        
        # 5. 状态栏
        self.create_status_bar()
    
    def create_connection_frame(self, parent):
        """创建连接配置区域"""
        frame = ttk.LabelFrame(parent, text="连接配置", padding="10")
        frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # CTP配置
        ttk.Label(frame, text="经纪商代码:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.broker_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.broker_id_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="用户名:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.user_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.user_id_var, width=15).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="密码:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=15).grid(row=0, column=5, sticky=tk.W, padx=5)
        
        # 前置地址
        ttk.Label(frame, text="交易前置:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.trade_front_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.trade_front_var, width=40).grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(frame, text="行情前置:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)
        self.market_front_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.market_front_var, width=30).grid(row=1, column=5, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 数据库配置
        ttk.Label(frame, text="数据库:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.db_host_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.db_host_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="用户:").grid(row=2, column=2, sticky=tk.W, padx=5)
        self.db_user_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.db_user_var, width=15).grid(row=2, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="密码:").grid(row=2, column=4, sticky=tk.W, padx=5)
        self.db_password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.db_password_var, show="*", width=15).grid(row=2, column=5, sticky=tk.W, padx=5)
        
        # 使用模拟CTP开关
        ttk.Label(frame, text="使用模拟CTP:").grid(row=2, column=6, sticky=tk.W, padx=5)
        self.use_mock_ctp_var = tk.BooleanVar(value=self.config.get('ctp', {}).get('use_mock', False))
        ttk.Checkbutton(frame, variable=self.use_mock_ctp_var).grid(row=2, column=7, sticky=tk.W, padx=5)

        # 连接按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=7, pady=10)
        
        self.connect_btn = ttk.Button(button_frame, text="连接", command=self.connect_to_ctp)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="断开", command=self.disconnect_from_ctp, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_config_btn = ttk.Button(button_frame, text="保存配置", command=self.save_config_from_ui)
        self.save_config_btn.pack(side=tk.LEFT, padx=5)
    
    def create_action_frame(self, parent):
        """创建功能按钮区域"""
        frame = ttk.LabelFrame(parent, text="功能操作", padding="10")
        frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 数据下载按钮
        ttk.Button(frame, text="下载委托数据", command=self.download_orders, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="下载持仓数据", command=self.download_positions, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="下载行情数据", command=self.download_market_data, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="下载合约参数", command=self.download_instruments, width=15).pack(side=tk.LEFT, padx=5)
        
        # 自动下载开关
        self.auto_download_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="自动下载", variable=self.auto_download_var, 
                       command=self.toggle_auto_download).pack(side=tk.LEFT, padx=20)
        
        ttk.Label(frame, text="间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="300")
        ttk.Entry(frame, textvariable=self.interval_var, width=10).pack(side=tk.LEFT, padx=5)
    
    def create_data_notebook(self, parent):
        """创建数据显示区域"""
        notebook = ttk.Notebook(parent)
        notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 委托数据标签页
        self.orders_frame = ttk.Frame(notebook)
        notebook.add(self.orders_frame, text="当日委托")
        self.create_orders_tab(self.orders_frame)
        
        # 持仓数据标签页
        self.positions_frame = ttk.Frame(notebook)
        notebook.add(self.positions_frame, text="当日持仓")
        self.create_positions_tab(self.positions_frame)
        
        # 行情数据标签页
        self.market_frame = ttk.Frame(notebook)
        notebook.add(self.market_frame, text="商品行情")
        self.create_market_tab(self.market_frame)
        
        # 合约参数标签页
        self.instruments_frame = ttk.Frame(notebook)
        notebook.add(self.instruments_frame, text="商品参数")
        self.create_instruments_tab(self.instruments_frame)
    
    def _select_trading_day(self, var: tk.StringVar, table: str):
        """弹出日历对话框，选择交易日（仅限数据库中已有的交易日）"""
        if not self.db_manager:
            messagebox.showwarning("警告", "请先连接数据库")
            return

        # 从指定表获取已存在的交易日列表，如 daily_orders / daily_positions
        days = self.db_manager.get_distinct_trading_days(table)
        if not days:
            messagebox.showinfo("提示", "当前没有可选择的交易日，请先下载数据")
            return

        # 转为 date 集合，便于校验
        available_dates = set()
        for d in days:
            try:
                available_dates.add(datetime.strptime(d, "%Y%m%d").date())
            except Exception:
                continue

        if not available_dates:
            messagebox.showinfo("提示", "交易日数据格式异常，无法选择")
            return

        # 当前默认选中值：优先用 var 当前值，否则用最新一个交易日
        try:
            current_value = var.get().strip() or days[0]
            current_date = datetime.strptime(current_value, "%Y%m%d").date()
        except Exception:
            # 回退到可用日期中的最大值（最近交易日）
            current_date = max(available_dates)

        top = tk.Toplevel(self.root)
        top.title("选择交易日")
        top.grab_set()
        top.resizable(False, False)

        ttk.Label(top, text="请选择交易日（仅高亮日期为有数据的交易日）").grid(row=0, column=0, columnspan=2, padx=10, pady=5)

        # 创建日历控件
        cal = Calendar(
            top,
            selectmode="day",
            year=current_date.year,
            month=current_date.month,
            day=current_date.day,
            date_pattern="yyyyMMdd"
        )
        cal.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        def on_ok():
            selected = cal.selection_get()  # datetime.date
            if selected not in available_dates:
                messagebox.showwarning("提示", "该日期无数据，请选择有数据的交易日")
                return
            var.set(selected.strftime("%Y%m%d"))
            top.destroy()

        ttk.Button(top, text="确定", command=on_ok).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(top, text="取消", command=top.destroy).grid(row=2, column=1, padx=10, pady=10)

    def create_orders_tab(self, parent):
        """创建委托数据标签页"""
        # 查询条件
        query_frame = ttk.Frame(parent)
        query_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(query_frame, text="交易日:").pack(side=tk.LEFT, padx=5)
        self.orders_trading_day_var = tk.StringVar(value=self.current_trading_day)
        entry = ttk.Entry(query_frame, textvariable=self.orders_trading_day_var, width=12, state='readonly')
        entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            query_frame,
            text="选择...",
            command=lambda: self._select_trading_day(self.orders_trading_day_var, 'daily_orders')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(query_frame, text="合约:").pack(side=tk.LEFT, padx=5)
        self.orders_instrument_var = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.orders_instrument_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(query_frame, text="查询", command=self.query_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="刷新", command=self.query_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="导出", command=self.export_orders).pack(side=tk.LEFT, padx=5)
        
        # 数据表格
        self.orders_tree = self.create_treeview(parent, [
            "委托时间", "合约", "方向", "开平", "委托价", "委托量", "成交量", "状态", "备注"
        ])
    
    def create_positions_tab(self, parent):
        """创建持仓数据标签页"""
        # 查询条件
        query_frame = ttk.Frame(parent)
        query_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(query_frame, text="交易日:").pack(side=tk.LEFT, padx=5)
        self.positions_trading_day_var = tk.StringVar(value=self.current_trading_day)
        entry = ttk.Entry(query_frame, textvariable=self.positions_trading_day_var, width=12, state='readonly')
        entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            query_frame,
            text="选择...",
            command=lambda: self._select_trading_day(self.positions_trading_day_var, 'daily_positions')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(query_frame, text="合约:").pack(side=tk.LEFT, padx=5)
        self.positions_instrument_var = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.positions_instrument_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(query_frame, text="查询", command=self.query_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="刷新", command=self.query_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="导出", command=self.export_positions).pack(side=tk.LEFT, padx=5)
        
        # 数据表格
        self.positions_tree = self.create_treeview(parent, [
            "合约", "方向", "类型", "持仓量", "可用", "开仓价", "持仓价", "平仓盈亏", "持仓盈亏"
        ])
    
    def create_market_tab(self, parent):
        """创建行情数据标签页"""
        # 查询条件
        query_frame = ttk.Frame(parent)
        query_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(query_frame, text="合约:").pack(side=tk.LEFT, padx=5)
        self.market_instrument_var = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.market_instrument_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(query_frame, text="查询", command=self.query_market_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="刷新", command=self.refresh_market_data).pack(side=tk.LEFT, padx=5)
        
        # 数据表格
        self.market_tree = self.create_treeview(parent, [
            "合约", "更新时间", "最新价", "涨跌", "开盘", "最高", "最低", "成交量", "持仓量"
        ])
    
    def create_instruments_tab(self, parent):
        """创建合约参数标签页"""
        # 查询条件
        query_frame = ttk.Frame(parent)
        query_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(query_frame, text="合约:").pack(side=tk.LEFT, padx=5)
        self.instruments_instrument_var = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.instruments_instrument_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(query_frame, text="交易所:").pack(side=tk.LEFT, padx=5)
        self.instruments_exchange_var = tk.StringVar()
        ttk.Combobox(query_frame, textvariable=self.instruments_exchange_var, width=12,
                    values=["", "SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"]).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(query_frame, text="查询", command=self.query_instruments).pack(side=tk.LEFT, padx=5)
        ttk.Button(query_frame, text="刷新", command=self.refresh_instruments).pack(side=tk.LEFT, padx=5)
        
        # 数据表格
        self.instruments_tree = self.create_treeview(parent, [
            "合约代码", "交易所", "合约名称", "品种", "合约乘数", "最小变动价位", "保证金率"
        ])
    
    def create_treeview(self, parent, columns):
        """创建通用的Treeview表格"""
        # 创建框架
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # 创建Treeview
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        
        # 布局
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        return tree
    
    def create_log_frame(self, parent):
        """创建日志区域"""
        frame = ttk.LabelFrame(parent, text="日志", padding="5")
        frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def load_config_to_ui(self):
        """加载配置到界面"""
        # CTP配置
        self.broker_id_var.set(self.config['ctp']['broker_id'])
        self.user_id_var.set(self.config['ctp']['user_id'])
        self.password_var.set(self.config['ctp']['password'])
        self.trade_front_var.set(self.config['ctp']['trade_front'])
        self.market_front_var.set(self.config['ctp']['market_front'])
        
        # 数据库配置
        self.db_host_var.set(self.config['database']['host'])
        self.db_user_var.set(self.config['database']['user'])
        self.db_password_var.set(self.config['database']['password'])
        
        # 使用模拟CTP配置
        self.use_mock_ctp_var.set(self.config['ctp'].get('use_mock', False))

        # 自动下载配置
        self.auto_download_var.set(self.config['auto_download']['enabled'])
        self.interval_var.set(str(self.config['auto_download']['interval']))
        
        # 初始化交易日选择为当前交易日
        if hasattr(self, 'orders_trading_day_var'):
            self.orders_trading_day_var.set(self.current_trading_day)
        if hasattr(self, 'positions_trading_day_var'):
            self.positions_trading_day_var.set(self.current_trading_day)

    def save_config_from_ui(self):
        """从界面保存配置"""
        self.config['ctp']['broker_id'] = self.broker_id_var.get()
        self.config['ctp']['user_id'] = self.user_id_var.get()
        self.config['ctp']['password'] = self.password_var.get()
        self.config['ctp']['trade_front'] = self.trade_front_var.get()
        self.config['ctp']['market_front'] = self.market_front_var.get()
        # 保存是否使用模拟CTP
        self.config['ctp']['use_mock'] = self.use_mock_ctp_var.get()

        # 数据库配置
        self.config['database']['host'] = self.db_host_var.get()
        self.config['database']['user'] = self.db_user_var.get()
        self.config['database']['password'] = self.db_password_var.get()
        
        self.config['auto_download']['enabled'] = self.auto_download_var.get()
        try:
            self.config['auto_download']['interval'] = int(self.interval_var.get())
        except:
            self.config['auto_download']['interval'] = 300
        
        self.save_config()
    
    def log(self, message):
        """输出日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        print(log_message.strip())
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def connect_to_ctp(self):
        """连接到CTP系统"""
        try:
            self.log("正在连接到CTP系统...")

            # 初始化数据库
            self.db_manager = DatabaseManager(
                host=self.db_host_var.get(),
                user=self.db_user_var.get(),
                password=self.db_password_var.get(),
                database=self.config['database']['database']
            )
            if not self.db_manager.connect():
                messagebox.showerror("错误", "数据库连接失败")
                return
            self.log("数据库连接成功")

            # 根据界面开关唯一决定使用真实/模拟CTP
            use_mock = self.use_mock_ctp_var.get()
            if use_mock:
                from ctp_api_wrapper import CTPTraderAPI as TraderCls
                self.log("当前选择: 使用模拟CTP API")
            else:
                # 严格使用真实实现，若导入失败或库不可用则直接报错
                try:
                    from ctp_api_real import CTPTraderAPIReal as TraderCls
                except Exception as e:
                    err = f"导入真实CTP实现失败，请检查openctp-ctp安装和环境: {e}"
                    self.log(err)
                    messagebox.showerror("错误", err)
                    return
                self.log("当前选择: 使用真实CTP API")

            # 初始化CTP API
            if use_mock:
                self.trader_api = TraderCls(
                    broker_id=self.broker_id_var.get(),
                    user_id=self.user_id_var.get(),
                    password=self.password_var.get(),
                    front_addr=self.trade_front_var.get()
                )
            else:
                # 真实 CTP 需要 AppID 和 AuthCode，用于认证
                ctp_conf = self.config.get('ctp', {})
                self.trader_api = TraderCls(
                    broker_id=self.broker_id_var.get(),
                    user_id=self.user_id_var.get(),
                    password=self.password_var.get(),
                    front_addr=self.trade_front_var.get(),
                    app_id=ctp_conf.get('app_id'),
                    auth_code=ctp_conf.get('auth_code')
                )

            # 设置回调
            self.trader_api.set_callback('on_connected', lambda: self.log("交易前置连接成功"))
            self.trader_api.set_callback('on_login', lambda d: self.on_ctp_login_success(d))
            self.trader_api.set_callback('on_error', lambda e: self.log(f"错误: {e}"))

            # 连接和登录
            if self.trader_api.connect():
                self.is_connected = True
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.update_status("已连接")
                self.log("CTP系统连接成功")
                # 注意：这里不能立即设置 is_logged_in = True，必须等待 on_login 回调
                # 所以不要在这里显示“连接成功”的提示框，而是等待登录完成
            else:
                messagebox.showerror("错误", "CTP连接失败")

        except Exception as e:
            self.log(f"连接失败: {e}")
            messagebox.showerror("错误", f"连接失败: {e}")

    def on_ctp_login_success(self, login_info):
        """处理CTP登录成功回调"""
        self.is_logged_in = True  # 确保正确设置登录状态
        self.update_status("已登录")
        self.log(f"登录成功: {login_info}")
        # 登录成功后，可以显示连接成功的提示
        messagebox.showinfo("成功", "连接成功！")

    def disconnect_from_ctp(self):
        """断开CTP连接"""
        if self.trader_api:
            self.trader_api.disconnect()
        if self.db_manager:
            self.db_manager.close()
        
        self.is_connected = False
        self.is_logged_in = False
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.update_status("已断开")
        self.log("已断开连接")

    def download_orders(self):
        """下载委托数据"""
        if not self.is_logged_in:  # 检查登录状态而非连接状态
            messagebox.showwarning("警告", "请先连接到CTP系统")
            return

        def task():
            self.log("开始下载委托数据...")
            # 调用API获取委托列表
            orders = self.trader_api.query_orders()
            # 如果有数据库连接，则写入数据库
            if self.db_manager and orders:
                count = self.db_manager.insert_orders(orders)
                self.log(f"已写入 {count} 条委托记录到数据库")
            self.log("委托数据下载完成")
            # 刷新界面显示
            self.query_orders()

        threading.Thread(target=task, daemon=True).start()
    
    def download_positions(self):
        """下载持仓数据"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先连接到CTP系统")
            return

        def task():
            self.log("开始下载持仓数据...")
            positions = self.trader_api.query_positions()
            if self.db_manager and positions:
                count = self.db_manager.insert_positions(positions)
                self.log(f"已写入 {count} 条持仓记录到数据库")
            self.log("持仓数据下载完成")
            self.query_positions()

        threading.Thread(target=task, daemon=True).start()
    
    def download_market_data(self):
        """下载行情数据"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先连接到CTP系统")
            return
        
        self.log("行情数据需要订阅实时行情")
    
    def download_instruments(self):
        """下载合约参数"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先连接到CTP系统")
            return

        def task():
            self.log("开始下载合约参数...")
            instruments = self.trader_api.query_instruments()
            if self.db_manager and instruments:
                count = self.db_manager.insert_instrument_info(instruments)
                self.log(f"已写入 {count} 条合约参数记录到数据库")
            self.log("合约参数下载完成")
            self.query_instruments()

        threading.Thread(target=task, daemon=True).start()
    
    def query_orders(self):
        """查询委托数据"""
        if not self.db_manager:
            return
        
        trading_day = self.orders_trading_day_var.get() or None
        instrument_id = self.orders_instrument_var.get() or None
        
        orders = self.db_manager.query_orders(trading_day, instrument_id)
        
        # 清空表格
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        # 填充数据
        for order in orders:
            self.orders_tree.insert('', tk.END, values=(
                order.get('order_time', ''),
                order.get('instrument_id', ''),
                order.get('direction', ''),
                order.get('offset_flag', ''),
                order.get('order_price', ''),
                order.get('order_volume', ''),
                order.get('traded_volume', ''),
                order.get('order_status', ''),
                order.get('remark', '')
            ))
        
        self.log(f"查询到 {len(orders)} 条委托记录")
    
    def refresh_orders(self):
        """刷新委托数据：只重新查询数据库，不再触发下载"""
        self.query_orders()
    
    def export_orders(self):
        """导出委托数据"""
        self.log("导出功能开发中...")
    
    def query_positions(self):
        """查询持仓数据"""
        if not self.db_manager:
            return
        
        trading_day = self.positions_trading_day_var.get() or None
        instrument_id = self.positions_instrument_var.get() or None
        
        positions = self.db_manager.query_positions(trading_day, instrument_id)
        
        # 清空表格
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        # 填充数据
        for pos in positions:
            self.positions_tree.insert('', tk.END, values=(
                pos.get('instrument_id', ''),
                pos.get('direction', ''),
                pos.get('position_type', ''),
                pos.get('volume', ''),
                pos.get('available_volume', ''),
                pos.get('open_price', ''),
                pos.get('position_price', ''),
                pos.get('close_profit', ''),
                pos.get('position_profit', '')
            ))
        
        self.log(f"查询到 {len(positions)} 条持仓记录")
    
    def refresh_positions(self):
        """刷新持仓数据：只重新查询数据库，不再触发下载"""
        self.query_positions()
    
    def export_positions(self):
        """导出持仓数据"""
        self.log("导出功能开发中...")
    
    def query_market_data(self):
        """查询行情数据"""
        if not self.db_manager:
            return
        
        instrument_id = self.market_instrument_var.get() or None
        market_data = self.db_manager.query_market_data(instrument_id=instrument_id)
        
        # 清空表格
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        
        # 填充数据
        for data in market_data:
            change = ""
            if data.get('last_price') and data.get('pre_settlement_price'):
                change = f"{float(data['last_price']) - float(data['pre_settlement_price']):.2f}"
            
            self.market_tree.insert('', tk.END, values=(
                data.get('instrument_id', ''),
                data.get('update_time', ''),
                data.get('last_price', ''),
                change,
                data.get('open_price', ''),
                data.get('highest_price', ''),
                data.get('lowest_price', ''),
                data.get('volume', ''),
                data.get('open_interest', '')
            ))
        
        self.log(f"查询到 {len(market_data)} 条行情记录")
    
    def refresh_market_data(self):
        """刷新行情数据"""
        self.download_market_data()
    
    def query_instruments(self):
        """查询合约参数"""
        if not self.db_manager:
            return
        
        instrument_id = self.instruments_instrument_var.get() or None
        exchange_id = self.instruments_exchange_var.get() or None
        
        instruments = self.db_manager.query_instrument_info(instrument_id, exchange_id, is_trading=True)
        
        # 清空表格
        for item in self.instruments_tree.get_children():
            self.instruments_tree.delete(item)
        
        # 填充数据
        for inst in instruments:
            self.instruments_tree.insert('', tk.END, values=(
                inst.get('instrument_id', ''),
                inst.get('exchange_id', ''),
                inst.get('instrument_name', ''),
                inst.get('product_id', ''),
                inst.get('volume_multiple', ''),
                inst.get('price_tick', ''),
                inst.get('long_margin_ratio', '')
            ))
        
        self.log(f"查询到 {len(instruments)} 条合约参数")
    
    def refresh_instruments(self):
        """刷新合约参数"""
        self.download_instruments()
    
    def toggle_auto_download(self):
        """切换自动下载"""
        if self.auto_download_var.get():
            self.start_auto_download()
        else:
            self.stop_auto_download()
    
    def start_auto_download(self):
        """启动自动下载"""
        try:
            interval = int(self.interval_var.get())
        except:
            interval = 300
        
        self.log(f"启动自动下载，间隔 {interval} 秒")
        self.schedule_auto_download(interval)
    
    def stop_auto_download(self):
        """停止自动下载"""
        if self.auto_download_timer:
            self.root.after_cancel(self.auto_download_timer)
            self.auto_download_timer = None
        self.log("停止自动下载")
    
    def schedule_auto_download(self, interval):
        """调度自动下载"""
        if self.auto_download_var.get() and self.is_logged_in:
            self.log("执行自动下载...")
            self.download_orders()
            self.download_positions()
            
            # 下次调度
            self.auto_download_timer = self.root.after(interval * 1000, 
                                                       lambda: self.schedule_auto_download(interval))


def main():
    """主函数"""
    root = tk.Tk()
    app = CTPTradingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
