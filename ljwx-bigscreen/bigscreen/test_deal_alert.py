#!/usr/bin/env python3
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigScreen.alert import deal_alert
from bigScreen.bigScreen import app

def test_deal_alert():
    """测试deal_alert函数是否正常工作"""
    try:
        with app.app_context():
            # 测试处理告警ID 1921075162350915586
            test_alert_id = "1921075162350915586"
            print(f"=== 测试处理告警 ID: {test_alert_id} ===")
            
            result = deal_alert(test_alert_id)
            print(f"处理结果: {result}")
            
            # 如果找不到该ID，测试一个存在的ID
            if "未找到告警记录" in str(result) or (isinstance(result, dict) and result.get('success') == False):
                print("\n=== 测试处理第一个可用的告警 ===")
                from bigScreen.models import AlertInfo
                
                # 找一个存在的告警ID
                alert = AlertInfo.query.filter_by(alert_status='pending').first()
                if alert:
                    test_alert_id = str(alert.id)
                    print(f"找到待处理告警 ID: {test_alert_id}")
                    result = deal_alert(test_alert_id)
                    print(f"处理结果: {result}")
                else:
                    print("没有找到待处理的告警记录")
            
            print("\n✅ deal_alert功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deal_alert() 