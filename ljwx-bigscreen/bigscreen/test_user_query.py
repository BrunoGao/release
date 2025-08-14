#!/usr/bin/env python3
"""测试用户查询问题的诊断脚本"""
import os
os.environ['IS_DOCKER'] = 'false'

from bigScreen.org import fetch_users_by_orgId
from bigScreen.models import db, UserInfo, UserOrg, OrgInfo
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_user_query():
    print("=" * 60)
    print("🔍 测试用户查询问题")
    print("=" * 60)
    
    # 1. 测试递归查询部门
    org_id = 1
    recursive_sql = text("""
        WITH RECURSIVE sub_orgs AS (
            SELECT id
            FROM sys_org_units
            WHERE id = :org_id AND is_deleted = 0

            UNION ALL

            SELECT o.id
            FROM sys_org_units o
            INNER JOIN sub_orgs so ON o.parent_id = so.id
            WHERE o.is_deleted = 0
        )
        SELECT id FROM sub_orgs
    """)
    
    try:
        result = db.session.execute(recursive_sql, {'org_id': org_id})
        department_ids = [row[0] for row in result.fetchall()]
        print(f"📋 递归查询到的部门IDs: {department_ids}")
        
        # 2. 测试用户查询
        users = db.session.query(
            UserInfo, UserOrg, OrgInfo
        ).join(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).join(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserOrg.org_id.in_(department_ids),
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1',
            UserOrg.is_deleted.is_(False)
        ).all()
        
        print(f"👤 查询到 {len(users)} 个用户记录")
        for i, (user_info, user_org, org_info) in enumerate(users[:5]):  # 显示前5个
            print(f"  用户{i+1}: ID={user_info.id}, 姓名={user_info.user_name}, 设备={user_info.device_sn}, 部门={org_info.name}")
            
        # 3. 测试fetch_users_by_orgId函数
        print(f"\n🔧 测试fetch_users_by_orgId函数:")
        users_from_function = fetch_users_by_orgId(org_id)
        print(f"📊 函数返回用户数量: {len(users_from_function)}")
        
        if users_from_function:
            for i, user in enumerate(users_from_function[:3]):
                print(f"  用户{i+1}: {user}")
        else:
            print("⚠️  函数未返回任何用户数据")
            
        # 4. 检查数据库连接状态
        print(f"\n🔗 数据库连接状态检查:")
        test_query = db.session.execute(text("SELECT COUNT(*) FROM sys_user WHERE is_deleted = 0"))
        total_users = test_query.fetchone()[0]
        print(f"📈 数据库中总用户数: {total_users}")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_query() 