#!/usr/bin/env python3
"""系统规则同步脚本 - 将t_system_event_rule同步到t_alert_rules"""
import mysql.connector
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='lj-06'
    )

def sync_system_rules_to_alert_rules():
    """同步系统事件规则到告警规则表"""
    print("🔄 开始同步系统事件规则到告警规则表...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 获取所有系统事件规则
        cursor.execute("""
            SELECT rule_type, alert_message, severity_level, is_active, is_emergency
            FROM t_system_event_rule 
            WHERE is_active = 1
        """)
        
        system_rules = cursor.fetchall()
        print(f"📊 找到 {len(system_rules)} 个活跃的系统事件规则")
        
        synced_count = 0
        
        for rule in system_rules:
            rule_type, alert_message, severity_level, is_active, is_emergency = rule
            
            # 2. 检查告警规则表中是否已存在
            cursor.execute("""
                SELECT id FROM t_alert_rules 
                WHERE rule_type = %s AND is_deleted = 0
            """, (rule_type,))
            
            existing_rule = cursor.fetchone()
            
            if not existing_rule:
                # 3. 插入新的告警规则
                severity = 'high' if is_emergency else (severity_level or 'medium')
                
                insert_sql = """
                    INSERT INTO t_alert_rules 
                    (rule_type, alert_message, severity_level, trigger_condition, 
                     physical_sign, create_user, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_sql, (
                    rule_type,
                    alert_message or f"{rule_type}事件告警",
                    severity,
                    f"事件类型匹配: {rule_type}",
                    'event',
                    'system_sync',
                    datetime.now()
                ))
                
                synced_count += 1
                print(f"✅ 同步规则: {rule_type} -> 告警级别: {severity}")
            else:
                print(f"⏭️  规则已存在: {rule_type}")
        
        conn.commit()
        print(f"🎉 同步完成! 新增 {synced_count} 个告警规则")
        
        # 4. 显示同步后的告警规则
        cursor.execute("""
            SELECT id, rule_type, severity_level, alert_message 
            FROM t_alert_rules 
            WHERE rule_type IN ('SOS_EVENT', 'FALLDOWN_EVENT', 'ONE_KEY_ALARM')
            ORDER BY rule_type
        """)
        
        alert_rules = cursor.fetchall()
        print(f"\n📋 相关告警规则 ({len(alert_rules)}个):")
        for rule in alert_rules:
            print(f"   - ID={rule[0]}: {rule[1]} (级别: {rule[2]})")
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_rule_id_mapping():
    """获取规则ID映射关系"""
    print("\n🔍 获取规则ID映射关系...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, rule_type FROM t_alert_rules 
            WHERE rule_type IN ('SOS_EVENT', 'FALLDOWN_EVENT', 'ONE_KEY_ALARM', 'WEAR_STATUS_CHANGED')
            ORDER BY rule_type
        """)
        
        rules = cursor.fetchall()
        rule_mapping = {}
        
        print("📋 规则ID映射:")
        for rule in rules:
            rule_id, rule_type = rule
            rule_mapping[rule_type] = rule_id
            print(f"   - {rule_type}: {rule_id}")
        
        return rule_mapping
        
    except Exception as e:
        print(f"❌ 获取映射失败: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    print("🔧 系统事件规则同步工具")
    print("="*50)
    
    # 1. 同步规则
    sync_system_rules_to_alert_rules()
    
    # 2. 获取映射关系
    rule_mapping = get_rule_id_mapping()
    
    # 3. 生成配置文件
    if rule_mapping:
        config_content = f"""# 事件规则ID映射配置
# 生成时间: {datetime.now()}

RULE_ID_MAPPING = {rule_mapping}

def get_rule_id(event_type):
    \"\"\"根据事件类型获取规则ID\"\"\"
    return RULE_ID_MAPPING.get(event_type)
"""
        
        with open('rule_mapping_config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"\n📄 配置文件已生成: rule_mapping_config.py")
    
    print("\n" + "="*50)
    print("✅ 同步完成")

if __name__ == "__main__":
    main() 