#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from main_gui import main
    main()
