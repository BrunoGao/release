#!/usr/bin/env python3
"""测试配置加载逻辑"""

import sys
import os
sys.path.append('/Users/bg/work/codes/springboot/ljwx/docker/ljwx-bigscreen/bigscreen')

from bigScreen.bigScreen import create_app
from bigScreen.models import db, HealthDataConfig
from bigScreen.user_health_data import get_health_data_config_by_org

def test_config_loading():
    """测试配置加载逻辑"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 测试配置加载逻辑...")
            
            # 1. 直接查询数据库
            print("\n📋 数据库直接查询 customer_id=1:")
            configs = db.session.query(HealthDataConfig).filter_by(customer_id=1).all()
            for config in configs:
                status = "✅" if config.is_enabled else "❌"
                print(f"   {status} {config.data_type}: {config.is_enabled}")
            
            # 2. 测试配置加载函数
            print("\n🔧 测试get_health_data_config_by_org函数:")
            org_config = get_health_data_config_by_org(1)
            print(f"   函数返回的配置: {org_config}")
            
            # 3. 检查pressure相关配置
            pressure_configs = ['pressure', 'pressure_high', 'pressure_low']
            print(f"\n🩺 pressure相关配置检查:")
            for p_config in pressure_configs:
                is_enabled = org_config.get(p_config, False)
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {p_config}: {is_enabled}")
            
            # 4. 检查其他配置
            print(f"\n📊 所有启用的配置:")
            enabled_configs = [k for k, v in org_config.items() if v]
            print(f"   启用的配置: {enabled_configs}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_config_loading() 