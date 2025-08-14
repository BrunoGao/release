#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/bg/work/codes/springboot/ljwx/docker/ljwx-bigscreen/bigScreen')

from bigScreen import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 更新公众号配置，添加appsecret
        update_sql = """
        UPDATE t_wechat_alarm_config 
        SET appsecret = 'temp_appsecret_for_testing' 
        WHERE id = 6 AND type = 'official'
        """
        
        result = db.session.execute(text(update_sql))
        db.session.commit()
        
        print(f"✅ 更新了公众号配置的appsecret，影响行数: {result.rowcount}")
        
        # 验证配置
        query_sql = "SELECT id, type, enabled, appid, appsecret FROM t_wechat_alarm_config WHERE enabled=1"
        result = db.session.execute(text(query_sql))
        configs = result.fetchall()
        
        print("\n📋 当前微信配置:")
        for config in configs:
            print(f"ID={config[0]} type={config[1]} enabled={config[2]} appid={config[3]} appsecret={'已设置' if config[4] else '未设置'}")
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        db.session.rollback() 