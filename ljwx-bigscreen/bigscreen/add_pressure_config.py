#!/usr/bin/env python3
"""添加血压配置到健康数据配置"""

import sys
import os
sys.path.append('/Users/bg/work/codes/springboot/ljwx/docker/ljwx-bigscreen/bigscreen')

from bigScreen.bigScreen import create_app
from bigScreen.models import db, HealthDataConfig

def add_pressure_config():
    """为组织ID=1添加血压配置"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查是否已存在pressure配置
            existing = db.session.query(HealthDataConfig).filter_by(
                customer_id=1, 
                data_type='pressure'
            ).first()
            
            if existing:
                print("✅ pressure配置已存在，更新为启用状态")
                existing.is_enabled = True
            else:
                print("➕ 添加新的pressure配置")
                pressure_config = HealthDataConfig(
                    customer_id=1,
                    data_type='pressure',
                    is_enabled=True
                )
                db.session.add(pressure_config)
            
            # 同样添加pressure_high和pressure_low配置
            for field in ['pressure_high', 'pressure_low']:
                existing = db.session.query(HealthDataConfig).filter_by(
                    customer_id=1, 
                    data_type=field
                ).first()
                
                if existing:
                    print(f"✅ {field}配置已存在，更新为启用状态")
                    existing.is_enabled = True
                else:
                    print(f"➕ 添加新的{field}配置")
                    config = HealthDataConfig(
                        customer_id=1,
                        data_type=field,
                        is_enabled=True
                    )
                    db.session.add(config)
            
            db.session.commit()
            print("🎉 血压配置添加成功！")
            
            # 查看所有配置
            all_configs = db.session.query(HealthDataConfig).filter_by(customer_id=1).all()
            print(f"\n📋 组织1的所有健康数据配置:")
            for config in all_configs:
                status = "✅" if config.is_enabled else "❌"
                print(f"   {status} {config.data_type}: {config.is_enabled}")
                
        except Exception as e:
            print(f"❌ 添加配置失败: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_pressure_config() 