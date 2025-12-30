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
        self.is_logged_in = True
        self.update_status("已登录")
        self.log(f"登录成功: {login_info}")
        # 登录成功后，可以显示连接成功的提示
        messagebox.showinfo("成功", "连接成功！")