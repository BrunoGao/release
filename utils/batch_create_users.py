#!/usr/bin/env python3
"""
批量创建sys_user的脚本
为1000个手表序列号创建对应的用户
"""

import mysql.connector
import random
from datetime import datetime, date
import sys
import hashlib
import json

def generate_password_hash(password, salt):
    """生成密码哈希值"""
    return hashlib.md5((password + salt).encode()).hexdigest()

def generate_random_salt():
    """生成随机盐值"""
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def generate_user_data(serial_number, index):
    """生成单个用户的数据"""
    # 生成随机生日（20-65岁）
    birth_year = random.randint(1959, 2004)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # 简化处理，避免月份天数问题
    birthday = date(birth_year, birth_month, birth_day)
    
    # 生成随机手机号
    def random_phone():
        return f"1{random.choice([3,4,5,6,7,8,9])}{random.randint(0,9):01d}{random.randint(10000000,99999999)}"
    
    # 生成密码盐值和哈希
    salt = generate_random_salt()
    password = "123456"  # 默认密码
    password_hash = generate_password_hash(password, salt)
    
    now = datetime.now()
    
    return {
        'userName': serial_number,
        'password': password_hash,
        'userCardNumber': f"{random.randint(100000000000000000, 999999999999999999)}",  # 18位身份证号
        'nickName': f"用户{serial_number[-6:]}",
        'realName': f"测试用户{index:04d}",
        'avatar': None,
        'email': f"{serial_number.lower()}@test.com",
        'phone': random_phone(),
        'gender': random.choice(['0', '1', '2']),  # 0保密 1男 2女
        'status': '1',  # 启用
        'salt': salt,
        'deviceSn': serial_number,
        'customerId': 1,
        'workingYears': random.randint(0, 40),
        'orgId': 1939964806110937090,
        'orgName': '租户名称 123',
        'birthday': birthday,
        'lastLoginTime': None,
        'updatePasswordTime': None,
        'createBy': 'system',
        'createTime': now,
        'updateBy': 'system',
        'updateTime': now,
        'delFlag': '0'
    }

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(
            host='192.168.1.6',
            port=3306,
            database='ljwx',
            user='root',
            password='ljwx@admin123',
            charset='utf8mb4',
            autocommit=False
        )
        return connection
    except mysql.connector.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def insert_user(cursor, user_data):
    """插入单个用户"""
    sql = """
    INSERT INTO sys_user (
        user_name, password, user_card_number, nick_name, real_name, avatar, email, phone, 
        gender, status, salt, device_sn, customer_id, working_years, org_id, org_name, 
        birthday, last_login_time, update_password_time, create_by, create_time, 
        update_by, update_time, del_flag
    ) VALUES (
        %(userName)s, %(password)s, %(userCardNumber)s, %(nickName)s, %(realName)s, %(avatar)s, 
        %(email)s, %(phone)s, %(gender)s, %(status)s, %(salt)s, %(deviceSn)s, %(customerId)s, 
        %(workingYears)s, %(orgId)s, %(orgName)s, %(birthday)s, %(lastLoginTime)s, 
        %(updatePasswordTime)s, %(createBy)s, %(createTime)s, %(updateBy)s, %(updateTime)s, %(delFlag)s
    )
    """
    cursor.execute(sql, user_data)

def main():
    """主函数：批量创建1000个用户"""
    print("开始批量创建1000个sys_user用户...")
    print(f"手表序列号范围: CRFTQ23409000000 到 CRFTQ23409000999")
    print(f"组织: org_id=1939964806110937090, org_name='租户名称 123'")
    print("-" * 50)
    
    # 获取数据库连接
    connection = get_db_connection()
    if not connection:
        print("无法连接到数据库，脚本退出")
        return False
    
    success_count = 0
    failed_count = 0
    failed_users = []
    
    try:
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'sys_user'")
        if not cursor.fetchone():
            print("错误: sys_user表不存在")
            return False
        
        # 生成1000个用户
        for i in range(1000):
            serial_number = f"CRFTQ23409{i:06d}"
            
            try:
                # 检查用户是否已存在
                cursor.execute("SELECT id FROM sys_user WHERE user_name = %s", (serial_number,))
                if cursor.fetchone():
                    print(f"⚠ [{i+1:4d}/1000] {serial_number} - 用户已存在，跳过")
                    continue
                
                # 生成用户数据
                user_data = generate_user_data(serial_number, i)
                
                # 插入用户
                insert_user(cursor, user_data)
                
                success_count += 1
                print(f"✓ [{i+1:4d}/1000] {serial_number} - 创建成功")
                
                # 每100个用户提交一次事务
                if (i + 1) % 100 == 0:
                    connection.commit()
                    print(f"进度: {i+1}/1000 用户已处理 (成功: {success_count}, 失败: {failed_count})")
            
            except mysql.connector.Error as e:
                failed_count += 1
                error_msg = str(e)
                failed_users.append((serial_number, error_msg))
                print(f"✗ [{i+1:4d}/1000] {serial_number} - 失败: {error_msg}")
        
        # 最终提交
        connection.commit()
        
    except Exception as e:
        print(f"脚本执行出错: {e}")
        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()
    
    # 输出最终统计
    print("\n" + "=" * 50)
    print("批量创建用户完成!")
    print(f"总计: 1000 个用户")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    # 输出失败的用户详情
    if failed_users:
        print("\n失败的用户:")
        for username, error in failed_users[:10]:  # 只显示前10个失败的
            print(f"  {username}: {error}")
        if len(failed_users) > 10:
            print(f"  ... 还有 {len(failed_users) - 10} 个失败用户")
    
    # 输出默认密码信息
    print(f"\n默认密码: 123456")
    print(f"组织信息: org_id=1939964806110937090, org_name='租户名称 123'")
    
    return failed_count == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断创建...")
        sys.exit(1)
    except Exception as e:
        print(f"\n脚本执行出错: {e}")
        sys.exit(1)