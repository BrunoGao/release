#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备批量处理器调试脚本"""
import sys
sys.path.append('.')
sys.path.append('./bigscreen')
sys.path.append('./bigscreen/bigScreen')

import os
import logging
from datetime import datetime
import mysql.connector

# 设置环境变量
os.environ['FLASK_ENV'] = 'development'

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'lj-06',
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("DESCRIBE t_device_info")
        columns = cursor.fetchall()
        print(f"✅ t_device_info 表结构: {len(columns)}个字段")
        for col in columns[:5]:  # 显示前5个字段
            print(f"  - {col[0]}: {col[1]}")
        
        cursor.execute("DESCRIBE t_device_info_history")
        history_columns = cursor.fetchall()
        print(f"✅ t_device_info_history 表结构: {len(history_columns)}个字段")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_manual_insert():
    """测试手动插入数据"""
    print("\n🔧 测试手动插入数据...")
    try:
        config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'lj-06',
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 测试插入数据
        test_sn = f"MANUAL_TEST_{int(datetime.now().timestamp())}"
        
        insert_sql = """
        INSERT INTO t_device_info (
            serial_number, system_software_version, battery_level, 
            charging_status, wearable_status, status, update_time, 
            is_deleted
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            battery_level=VALUES(battery_level),
            update_time=VALUES(update_time)
        """
        
        data = (
            test_sn, 'TEST_VERSION', 50, 'NOT_CHARGING', 
            'NOT_WORN', 'ACTIVE', datetime.now(), 0
        )
        
        cursor.execute(insert_sql, data)
        conn.commit()
        
        # 验证插入
        cursor.execute("SELECT * FROM t_device_info WHERE serial_number = %s", (test_sn,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 手动插入成功: {test_sn}")
            print(f"  数据: {result[:5]}...")
        else:
            print("❌ 手动插入失败")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 手动插入失败: {e}")
        return False

def test_batch_processor_import():
    """测试批量处理器导入"""
    print("\n📦 测试批量处理器导入...")
    try:
        from bigscreen.bigScreen.device_batch_processor import DeviceBatchProcessor
        print("✅ 批量处理器导入成功")
        
        # 尝试创建实例
        processor = DeviceBatchProcessor(batch_size=5, max_wait_time=1.0, max_workers=2)
        print("✅ 批量处理器创建成功")
        
        # 测试数据标准化
        test_data = {
            "System Software Version": "TEST_VERSION",
            "SerialNumber": "TEST_DEVICE_001",
            "batteryLevel": 50,
            "chargingStatus": "NOT_CHARGING",
            "wearState": 0,
            "status": "ACTIVE"
        }
        
        normalized = processor._normalize_device_data(test_data)
        if normalized:
            print("✅ 数据标准化成功")
            print(f"  设备数据: {normalized['device']['serial_number']}")
        else:
            print("❌ 数据标准化失败")
            
        return True
        
    except Exception as e:
        print(f"❌ 批量处理器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app_context():
    """测试Flask应用上下文"""
    print("\n🌐 测试Flask应用上下文...")
    try:
        from bigscreen.bigScreen.bigScreen import app
        
        with app.app_context():
            from bigscreen.bigScreen.models import db, DeviceInfo
            
            # 测试数据库连接
            result = db.session.execute("SELECT 1 as test").fetchone()
            print(f"✅ Flask数据库连接成功: {result}")
            
            # 测试ORM查询
            count = DeviceInfo.query.count()
            print(f"✅ ORM查询成功: 设备总数 {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Flask应用上下文测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processing_with_context():
    """测试带上下文的批量处理"""
    print("\n⚙️ 测试带上下文的批量处理...")
    try:
        from bigscreen.bigScreen.bigScreen import app
        from bigscreen.bigScreen.device_batch_processor import DeviceBatchProcessor
        
        with app.app_context():
            processor = DeviceBatchProcessor(batch_size=2, max_wait_time=1.0, max_workers=1, app=app)
            
            # 准备测试数据
            test_data = {
                "System Software Version": "DEBUG_TEST_VERSION",
                "SerialNumber": f"DEBUG_TEST_{int(datetime.now().timestamp())}",
                "batteryLevel": 75,
                "chargingStatus": "CHARGING",
                "wearState": 1,
                "status": "ACTIVE",
                "customerId": 1
            }
            
            # 测试数据标准化
            normalized = processor._normalize_device_data(test_data)
            if not normalized:
                print("❌ 数据标准化失败")
                return False
            
            print(f"✅ 数据标准化成功: {normalized['device']['serial_number']}")
            
            # 测试批量插入
            try:
                processor._batch_upsert_devices([normalized['device']])
                processor._batch_insert_histories([normalized['history']])
                print("✅ 批量数据库操作成功")
                
                # 验证插入结果
                from bigscreen.bigScreen.models import DeviceInfo
                device = DeviceInfo.query.filter_by(serial_number=normalized['device']['serial_number']).first()
                if device:
                    print(f"✅ 数据验证成功: {device.serial_number} - 电量{device.battery_level}%")
                else:
                    print("❌ 数据验证失败: 未找到插入的记录")
                    
            except Exception as e:
                print(f"❌ 批量数据库操作失败: {e}")
                import traceback
                traceback.print_exc()
                return False
                
            return True
            
    except Exception as e:
        print(f"❌ 带上下文批量处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有调试测试"""
    print("🐛 设备批量处理器调试开始")
    print("=" * 50)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("手动插入", test_manual_insert), 
        ("批量处理器导入", test_batch_processor_import),
        ("Flask应用上下文", test_flask_app_context),
        ("带上下文批量处理", test_batch_processing_with_context)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    print("\n📊 调试结果汇总:")
    print("-" * 30)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    print(f"\n总计: {success_count}/{len(results)} 个测试通过")

if __name__ == "__main__":
    main() 