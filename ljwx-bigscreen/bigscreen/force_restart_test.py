#!/usr/bin/env python3
"""强制重启应用并清除缓存测试"""

import os
import time
import subprocess
import requests
import redis

def force_restart_test():
    """强制重启应用，清除缓存，然后测试"""
    print("🔄 强制重启应用并清除缓存...")
    
    try:
        # 1. 杀死所有python3进程
        print("🛑 停止所有python3进程...")
        subprocess.run(['pkill', '-f', 'python3'], capture_output=True)
        time.sleep(2)
        
        # 2. 清除Redis缓存
        print("🧹 清除Redis缓存...")
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.flushall()
            print("✅ Redis缓存清除成功")
        except Exception as e:
            print(f"⚠️ Redis缓存清除失败: {e}")
        
        # 3. 启动新的应用实例
        print("🚀 启动新应用实例...")
        os.chdir('/Users/bg/work/codes/springboot/ljwx/docker/ljwx-bigscreen/bigscreen')
        
        # 启动应用
        process = subprocess.Popen(['python3', 'run.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 cwd='/Users/bg/work/codes/springboot/ljwx/docker/ljwx-bigscreen/bigscreen')
        
        # 等待应用启动
        print("⏳ 等待应用启动...")
        time.sleep(10)
        
        # 4. 测试API
        print("🔧 测试API是否正常...")
        max_retries = 5
        for i in range(max_retries):
            try:
                # 测试基础连接
                response = requests.get('http://127.0.0.1:5001/health_data/page', 
                                      params={'orgId': 1, 'pageSize': 1}, 
                                      timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ API连接成功!")
                    
                    # 检查配置
                    enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
                    print(f"📊 启用的指标: {enabled_metrics}")
                    
                    # 检查pressure是否在指标中
                    pressure_exists = any('pressure' in metric for metric in enabled_metrics)
                    print(f"🩺 Pressure配置状态: {'✅ 已启用' if pressure_exists else '❌ 未启用'}")
                    
                    # 检查实际数据
                    health_data = data.get('data', {}).get('healthData', [])
                    if health_data:
                        first_item = health_data[0]
                        print(f"\n📝 第一条数据:")
                        print(f"   pressureHigh: {first_item.get('pressureHigh')}")
                        print(f"   pressureLow: {first_item.get('pressureLow')}")
                        print(f"   heartRate: {first_item.get('heartRate')}")
                        print(f"   bloodOxygen: {first_item.get('bloodOxygen')}")
                    
                    break
                else:
                    print(f"❌ API返回错误状态: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ 第{i+1}次测试失败: {e}")
                if i < max_retries - 1:
                    print(f"⏳ 等待5秒后重试...")
                    time.sleep(5)
                else:
                    print(f"❌ API测试完全失败")
        
        return process
        
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return None

if __name__ == "__main__":
    process = force_restart_test()
    if process:
        print(f"\n🎉 应用已启动，PID: {process.pid}")
        print("📋 如需停止应用，使用: kill", process.pid)
    else:
        print("❌ 应用启动失败") 