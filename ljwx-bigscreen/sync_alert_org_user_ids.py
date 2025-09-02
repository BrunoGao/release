#!/usr/bin/env python3
"""AlertInfo表org_id和user_id字段数据同步脚本"""
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Flask应用和数据库
from bigscreen.bigScreen.bigScreen import app
from bigscreen.bigScreen.models import db,AlertInfo,UserInfo,UserOrg
from bigscreen.bigScreen.device import get_device_user_org_info

def sync_alert_org_user_ids():
    """同步AlertInfo表的org_id和user_id字段"""
    print("🔄 开始同步AlertInfo表的org_id和user_id字段...")
    
    # 查询所有缺少org_id或user_id的AlertInfo记录
    alerts_to_update = AlertInfo.query.filter(
        (AlertInfo.org_id.is_(None)) | (AlertInfo.user_id.is_(None))
    ).all()
    
    print(f"📊 找到{len(alerts_to_update)}条需要更新的记录")
    
    updated_count = 0
    error_count = 0
    
    for alert in alerts_to_update:
        try:
            # 根据device_sn获取用户和组织信息
            device_info = get_device_user_org_info(alert.device_sn)
            
            if device_info.get('success'):
                # 更新org_id和user_id
                if not alert.org_id and device_info.get('org_id'):
                    alert.org_id = device_info.get('org_id')
                
                if not alert.user_id and device_info.get('user_id'):
                    alert.user_id = device_info.get('user_id')
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"⏳ 已处理{updated_count}条记录...")
                    db.session.commit()  # 批量提交
            else:
                print(f"⚠️ 设备{alert.device_sn}未找到对应用户信息")
                error_count += 1
                
        except Exception as e:
            print(f"❌ 处理告警ID={alert.id}失败: {e}")
            error_count += 1
            
    # 最终提交
    try:
        db.session.commit()
        print(f"✅ 同步完成!")
        print(f"📈 成功更新: {updated_count}条")
        print(f"❌ 失败: {error_count}条")
    except Exception as e:
        print(f"❌ 最终提交失败: {e}")
        db.session.rollback()

def verify_sync_result():
    """验证同步结果"""
    print("\n🔍 验证同步结果...")
    
    # 统计有org_id和user_id的记录数
    total_alerts = AlertInfo.query.count()
    alerts_with_org = AlertInfo.query.filter(AlertInfo.org_id.isnot(None)).count()
    alerts_with_user = AlertInfo.query.filter(AlertInfo.user_id.isnot(None)).count()
    alerts_with_both = AlertInfo.query.filter(
        (AlertInfo.org_id.isnot(None)) & (AlertInfo.user_id.isnot(None))
    ).count()
    
    print(f"📊 告警记录统计:")
    print(f"  总记录数: {total_alerts}")
    print(f"  有org_id: {alerts_with_org} ({alerts_with_org/total_alerts*100:.1f}%)")
    print(f"  有user_id: {alerts_with_user} ({alerts_with_user/total_alerts*100:.1f}%)")
    print(f"  两者都有: {alerts_with_both} ({alerts_with_both/total_alerts*100:.1f}%)")

def create_indexes():
    """为新字段创建索引以优化查询性能"""
    print("\n🔧 创建索引优化查询性能...")
    
    try:
        # 为org_id创建索引
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_alert_org_id ON t_alert_info(org_id)")
        
        # 为user_id创建索引  
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_alert_user_id ON t_alert_info(user_id)")
        
        # 为org_id+user_id组合创建索引
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_alert_org_user ON t_alert_info(org_id, user_id)")
        
        db.session.commit()
        print("✅ 索引创建完成")
        
    except Exception as e:
        print(f"⚠️ 索引创建失败(可能已存在): {e}")

if __name__ == "__main__":
    print("🚀 AlertInfo表org_id和user_id字段同步工具")
    print("="*50)
    
    # 在Flask应用上下文中运行
    with app.app_context():
        # 1. 同步数据
        sync_alert_org_user_ids()
        
        # 2. 验证结果
        verify_sync_result()
        
        # 3. 创建索引
        create_indexes()
        
    print("\n🎉 同步任务完成!") 