#!/usr/bin/env python3
"""生成健康基线数据脚本"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, timedelta
from bigScreen.health_baseline import HealthBaselineGenerator
from bigScreen.models import db
from bigScreen.bigScreen import app

def generate_baseline_data_for_period(days=30):
    """生成指定天数的基线数据"""
    with app.app_context():
        generator = HealthBaselineGenerator()
        total_user_count = 0
        total_org_count = 0
        
        print(f"开始生成最近 {days} 天的基线数据...")
        
        for i in range(days):
            target_date = date.today() - timedelta(days=i)
            print(f"\n正在生成 {target_date} 的基线数据...")
            
            try:
                # 生成用户基线
                user_result = generator.generate_daily_user_baseline(target_date)
                user_count = user_result.get('count', 0) if user_result.get('success') else 0
                total_user_count += user_count
                
                # 生成组织基线
                org_result = generator.generate_daily_org_baseline(target_date)
                org_count = org_result.get('count', 0) if org_result.get('success') else 0
                total_org_count += org_count
                
                print(f"✓ {target_date}: 用户基线 {user_count} 条, 组织基线 {org_count} 条")
                
            except Exception as e:
                print(f"✗ {target_date}: 生成失败 - {e}")
        
        print(f"\n基线数据生成完成!")
        print(f"总计: 用户基线 {total_user_count} 条, 组织基线 {total_org_count} 条")
        
        return {
            'total_user_count': total_user_count,
            'total_org_count': total_org_count,
            'days': days
        }

def check_health_data_availability():
    """检查健康数据可用性"""
    with app.app_context():
        from bigScreen.models import UserHealthData, UserInfo
        
        # 检查最近30天有健康数据的用户数量
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # 查询有设备号的用户
        users_with_device = db.session.query(UserInfo.id, UserInfo.device_sn).filter(
            UserInfo.device_sn.isnot(None),
            UserInfo.device_sn != '',
            UserInfo.device_sn != '-',
            UserInfo.is_deleted == False
        ).all()
        
        print(f"有设备号的用户数量: {len(users_with_device)}")
        
        # 检查最近30天有数据的设备
        devices_with_data = db.session.query(UserHealthData.device_sn).filter(
            UserHealthData.create_time >= thirty_days_ago,
            UserHealthData.is_deleted == False
        ).distinct().all()
        
        print(f"最近30天有数据的设备数量: {len(devices_with_data)}")
        
        # 检查按日期分布的数据量
        from sqlalchemy import func, text
        daily_counts = db.session.query(
            func.date(UserHealthData.create_time).label('date'),
            func.count(UserHealthData.id).label('count')
        ).filter(
            UserHealthData.create_time >= thirty_days_ago,
            UserHealthData.is_deleted == False
        ).group_by(
            func.date(UserHealthData.create_time)
        ).order_by(
            func.date(UserHealthData.create_time).desc()
        ).limit(10).all()
        
        print("\n最近10天的数据分布:")
        for day_count in daily_counts:
            print(f"{day_count.date}: {day_count.count} 条记录")
        
        return {
            'users_with_device': len(users_with_device),
            'devices_with_data': len(devices_with_data),
            'daily_distribution': [(str(dc.date), dc.count) for dc in daily_counts]
        }

if __name__ == '__main__':
    print("=== 健康基线数据生成工具 ===\n")
    
    # 首先检查数据可用性
    print("1. 检查健康数据可用性...")
    data_info = check_health_data_availability()
    
    if data_info['devices_with_data'] == 0:
        print("警告: 没有发现健康数据，无法生成基线")
        sys.exit(1)
    
    print(f"\n2. 开始生成基线数据...")
    
    # 生成基线数据
    days = 30  # 生成最近30天的基线
    result = generate_baseline_data_for_period(days)
    
    print(f"\n=== 完成 ===")
    print(f"生成了 {result['days']} 天的基线数据")
    print(f"用户基线: {result['total_user_count']} 条")
    print(f"组织基线: {result['total_org_count']} 条") 