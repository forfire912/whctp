#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据导入工具
用于从CSV文件导入数据到数据库
"""

import csv
import os
from datetime import datetime
from database_manager import DatabaseManager


class DataImporter:
    """数据导入类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据导入器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def import_orders_from_csv(self, csv_file: str, trading_day: str = None) -> int:
        """
        从CSV导入委托数据
        
        Args:
            csv_file: CSV文件路径
            trading_day: 交易日(如果CSV中没有，可手动指定)
            
        Returns:
            导入的记录数
        """
        if not os.path.exists(csv_file):
            print(f"文件不存在: {csv_file}")
            return 0
        
        orders = []
        
        try:
            with open(csv_file, 'r', encoding='gbk') as f:
                # 跳过BOM（如果有）
                content = f.read()
                if content.startswith('\ufeff'):
                    content = content[1:]
                
                lines = content.split('\n')
                reader = csv.reader(lines)
                
                # 读取标题行
                headers = next(reader)
                print(f"CSV标题: {headers}")
                
                # 处理数据行
                for row in reader:
                    if len(row) < 9:  # 确保有足够的列
                        continue
                    
                    try:
                        order = {
                            'order_time': row[0].strip(),
                            'instrument_id': row[1].strip(),
                            'direction': row[2].strip(),
                            'offset_flag': row[3].strip(),
                            'order_price': float(row[4]) if row[4].strip() else 0,
                            'order_volume': int(row[5]) if row[5].strip() else 0,
                            'traded_volume': int(row[6]) if row[6].strip() else 0,
                            'order_status': row[7].strip(),
                            'remark': row[8].strip() if len(row) > 8 else '',
                            'trading_day': trading_day or datetime.now().strftime('%Y%m%d')
                        }
                        orders.append(order)
                    except Exception as e:
                        print(f"解析行失败: {row}, 错误: {e}")
                        continue
            
            # 批量插入数据库
            if orders:
                count = self.db.insert_orders(orders)
                print(f"成功导入 {count} 条委托记录")
                return count
            else:
                print("没有数据可导入")
                return 0
                
        except Exception as e:
            print(f"导入失败: {e}")
            return 0
    
    def import_positions_from_csv(self, csv_file: str, trading_day: str = None) -> int:
        """
        从CSV导入持仓数据
        
        Args:
            csv_file: CSV文件路径
            trading_day: 交易日
            
        Returns:
            导入的记录数
        """
        if not os.path.exists(csv_file):
            print(f"文件不存在: {csv_file}")
            return 0
        
        positions = []
        
        try:
            with open(csv_file, 'r', encoding='gbk') as f:
                # 跳过BOM
                content = f.read()
                if content.startswith('\ufeff'):
                    content = content[1:]
                
                lines = content.split('\n')
                reader = csv.reader(lines)
                
                # 读取标题行
                headers = next(reader)
                print(f"CSV标题: {headers}")
                
                # 处理数据行
                for row in reader:
                    if len(row) < 9:
                        continue
                    
                    try:
                        position = {
                            'instrument_id': row[0].strip(),
                            'direction': row[1].strip(),
                            'position_type': row[2].strip(),
                            'volume': int(row[3]) if row[3].strip() else 0,
                            'available_volume': int(row[4]) if row[4].strip() else 0,
                            'open_price': float(row[5]) if row[5].strip() else 0,
                            'position_price': float(row[6]) if row[6].strip() else 0,
                            'close_profit': float(row[7]) if row[7].strip() else 0,
                            'position_profit': float(row[8]) if row[8].strip() else 0,
                            'trading_day': trading_day or datetime.now().strftime('%Y%m%d')
                        }
                        positions.append(position)
                    except Exception as e:
                        print(f"解析行失败: {row}, 错误: {e}")
                        continue
            
            # 批量插入数据库
            if positions:
                count = self.db.insert_positions(positions)
                print(f"成功导入 {count} 条持仓记录")
                return count
            else:
                print("没有数据可导入")
                return 0
                
        except Exception as e:
            print(f"导入失败: {e}")
            return 0


def main():
    """测试主函数"""
    # 初始化数据库
    db = DatabaseManager(
        host="localhost",
        user="root",
        password="your_password",
        database="ctp_trading"
    )
    
    if not db.connect():
        print("数据库连接失败")
        return
    
    # 创建导入器
    importer = DataImporter(db)
    
    # 导入委托数据
    trading_day = "20250129"
    orders_file = "req/当日委托.csv"
    if os.path.exists(orders_file):
        importer.import_orders_from_csv(orders_file, trading_day)
    
    # 导入持仓数据
    positions_file = "req/当日持仓.csv"
    if os.path.exists(positions_file):
        importer.import_positions_from_csv(positions_file, trading_day)
    
    # 关闭数据库
    db.close()


if __name__ == "__main__":
    main()
