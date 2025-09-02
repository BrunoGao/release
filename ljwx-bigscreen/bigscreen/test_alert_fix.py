#!/usr/bin/env python3
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bigScreen.models import db, AlertInfo
    from bigScreen.bigScreen import app
    from datetime import datetime
    
    def test_alert_query():
        """测试AlertInfo查询是否正常"""
        try:
            with app.app_context():
                print("=== 测试AlertInfo模型查询 ===")
                
                # 测试查询所有告警
                print("1. 查询所有告警记录...")
                alerts = AlertInfo.query.limit(5).all()
                print(f"   成功查询到 {len(alerts)} 条告警记录")
                
                # 测试按ID查询
                if alerts:
                    test_alert_id = alerts[0].id
                    print(f"2. 测试按ID查询告警 {test_alert_id}...")
                    alert = AlertInfo.query.filter_by(id=test_alert_id).first()
                    if alert:
                        print(f"   查询成功: {alert.alert_type} - {alert.severity_level}")
                        print(f"   设备编号: {alert.device_sn}")
                        print(f"   告警时间: {alert.alert_timestamp}")
                    else:
                        print("   查询失败：未找到记录")
                
                # 测试查询待处理告警
                print("3. 查询待处理告警...")
                pending_alerts = AlertInfo.query.filter_by(alert_status='pending').limit(3).all()
                print(f"   找到 {len(pending_alerts)} 条待处理告警")
                
                print("\n✅ AlertInfo模型查询测试完成，所有查询正常工作！")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        test_alert_query()
        
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请确保在正确的目录中运行此脚本") 