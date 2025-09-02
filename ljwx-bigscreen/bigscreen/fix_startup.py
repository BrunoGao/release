#!/usr/bin/env python3 #启动异常修复脚本
# -*- coding: utf-8 -*-
import os,sys,subprocess,time,pymysql
from redis import Redis

def check_and_kill_port(port): #检查并释放端口
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid and pid.isdigit():
                    try:
                        subprocess.run(['kill', '-9', pid], check=False)
                        print(f"✅ 已杀掉进程 {pid} (端口 {port})")
                    except:
                        pass
            time.sleep(1)
            return True
        return False
    except Exception as e:
        print(f"❌ 端口检查失败: {e}")
        return False

def test_mysql_connection(): #测试MySQL连接
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456'),
            database=os.getenv('MYSQL_DATABASE', 'lj-06'),
            connect_timeout=5
        )
        conn.close()
        print(f"✅ MySQL连接正常")
        return True
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        return False

def test_redis_connection(): #测试Redis连接
    try:
        redis_client = Redis(
            host=os.getenv('REDIS_HOST', '127.0.0.1'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', '123456'),
            db=0,
            socket_timeout=5
        )
        redis_client.ping()
        print(f"✅ Redis连接正常")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

def main():
    print("🔧 启动异常修复中...")
    
    # 检查端口
    ports = [5001, 8001, 3001, 3000]
    for port in ports:
        if check_and_kill_port(port):
            print(f"🔧 已释放端口 {port}")
    
    # 检查数据库连接
    mysql_ok = test_mysql_connection()
    redis_ok = test_redis_connection()
    
    if not mysql_ok:
        print("❌ MySQL连接失败，请检查配置和服务状态")
    if not redis_ok:
        print("❌ Redis连接失败，请检查配置和服务状态")
    
    # 设置环境变量
    os.environ['APP_PORT'] = '5001'
    os.environ['DEBUG'] = 'False'
    
    if mysql_ok and redis_ok:
        print("✅ 所有检查通过，可以启动应用")
        return True
    else:
        print("❌ 部分检查失败，请修复后重试")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 