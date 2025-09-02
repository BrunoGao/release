#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动触发健康基线生成测试脚本
"""

import os
import sys
import json
from datetime import datetime, timedelta, date

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_manual_baseline_generation():
    """测试手动基线生成"""
    print("🏥 健康基线手动生成测试")
    print("=" * 50)
    
    try:
        # 导入Flask应用
        from bigScreen import app
        print("✅ Flask应用导入成功")
        
        # 在应用上下文中运行
        with app.app_context():
            from bigScreen.health_baseline_scheduler import get_health_baseline_scheduler
            from bigScreen.models import db
            
            # 检查数据库连接，不需要create_all
            print("✅ 数据库连接检查完成")
            
            # 获取调度器
            scheduler = get_health_baseline_scheduler(app)
            print(f"📊 调度器状态: {'运行中' if scheduler.running else '未启动'}")
            
            # 测试数据库连接
            try:
                from bigScreen.models import UserInfo, OrgInfo
                user_count = UserInfo.query.count()
                org_count = OrgInfo.query.count()
                print(f"👥 数据库用户总数: {user_count}")
                print(f"🏢 数据库组织总数: {org_count}")
            except Exception as e:
                print(f"❌ 数据库查询失败: {e}")
                return
            
            # 测试获取活跃用户
            print("\n🔍 测试获取活跃用户...")
            try:
                users = scheduler._get_active_users()
                print(f"✅ 找到活跃用户: {len(users)}")
                if users:
                    print(f"   示例用户: {users[0]}")
                else:
                    print("⚠️  没有找到活跃用户，尝试获取所有用户...")
                    all_users = UserInfo.query.filter(UserInfo.is_deleted == False).limit(5).all()
                    print(f"   数据库中前5个用户: {len(all_users)}")
                    for user in all_users:
                        print(f"   - ID: {user.id}, 姓名: {user.user_name}, 设备: {user.device_sn}")
            except Exception as e:
                print(f"❌ 获取用户失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试获取活跃组织
            print("\n🔍 测试获取活跃组织...")
            try:
                orgs = scheduler._get_active_orgs()
                print(f"✅ 找到活跃组织: {len(orgs)}")
                if orgs:
                    print(f"   示例组织: {orgs[0]}")
                else:
                    print("⚠️  没有找到活跃组织，尝试获取所有组织...")
                    all_orgs = OrgInfo.query.filter(OrgInfo.is_deleted == False).limit(5).all()
                    print(f"   数据库中前5个组织: {len(all_orgs)}")
                    for org in all_orgs:
                        print(f"   - ID: {org.id}, 名称: {org.name}, 状态: {org.status}")
            except Exception as e:
                print(f"❌ 获取组织失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 手动生成基线测试
            print("\n🚀 开始手动生成基线...")
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            try:
                result = scheduler.manual_generate_baseline(
                    start_date=yesterday,
                    end_date=yesterday
                )
                
                print("📊 基线生成结果:")
                print(f"   成功状态: {result.get('success')}")
                print(f"   消息: {result.get('message')}")
                if result.get('data'):
                    data = result['data']
                    print(f"   个人基线: {data.get('personal', 0)}")
                    print(f"   组织基线: {data.get('org', 0)}")
                    if data.get('errors'):
                        print(f"   错误信息: {data['errors']}")
                
            except Exception as e:
                print(f"❌ 手动生成基线失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 检查生成的基线数据
            print("\n📈 检查基线数据...")
            try:
                from bigScreen.models import HealthBaseline, OrgHealthBaseline
                
                personal_baselines = HealthBaseline.query.filter(
                    HealthBaseline.is_current == True
                ).count()
                
                org_baselines = OrgHealthBaseline.query.count()
                
                print(f"✅ 当前个人基线数量: {personal_baselines}")
                print(f"✅ 组织基线数量: {org_baselines}")
                
                # 显示最近的基线记录
                recent_personal = HealthBaseline.query.order_by(
                    HealthBaseline.baseline_time.desc()
                ).limit(3).all()
                
                if recent_personal:
                    print(f"\n📋 最近的个人基线记录:")
                    for baseline in recent_personal:
                        print(f"   - 用户ID: {baseline.user_id}, 特征: {baseline.feature_name}")
                        print(f"     日期: {baseline.baseline_date}, 均值: {baseline.mean_value:.2f}")
                
                recent_org = OrgHealthBaseline.query.order_by(
                    OrgHealthBaseline.update_time.desc()
                ).limit(3).all()
                
                if recent_org:
                    print(f"\n📋 最近的组织基线记录:")
                    for baseline in recent_org:
                        print(f"   - 组织ID: {baseline.org_id}, 特征: {baseline.feature_name}")
                        print(f"     日期: {baseline.baseline_date}, 均值: {baseline.mean_value:.2f}")
                        
            except Exception as e:
                print(f"❌ 检查基线数据失败: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 测试完成")

if __name__ == "__main__":
    test_manual_baseline_generation()