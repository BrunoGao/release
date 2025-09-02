#!/usr/bin/env python3
"""清除所有健康数据相关的缓存"""

import redis
import time

def clear_all_health_cache():
    """清除所有健康数据相关的缓存"""
    try:
        # 连接Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        print("🧹 开始清除健康数据相关缓存...")
        
        # 获取所有缓存键
        all_keys = r.keys('*')
        print(f"📋 总缓存键数量: {len(all_keys)}")
        
        # 匹配健康数据相关的缓存键模式
        health_patterns = [
            'health_opt*',     # 优化查询缓存
            'health_page*',    # 分页查询缓存
            'health_trends*',  # 趋势查询缓存
            'baseline*',       # 基线查询缓存
            'fetch_health*',   # 基础查询缓存
            'health_data*',    # 健康数据缓存
            'total_info*',     # 总信息缓存
            '*health*',        # 所有包含health的缓存
        ]
        
        deleted_count = 0
        
        for pattern in health_patterns:
            matching_keys = r.keys(pattern)
            if matching_keys:
                print(f"🗑️  删除模式 '{pattern}' 的缓存: {len(matching_keys)} 个")
                for key in matching_keys:
                    r.delete(key)
                    deleted_count += 1
        
        # 另外，直接清除所有缓存（最彻底的方法）
        print("🧹 执行完全清除...")
        r.flushall()
        
        print(f"✅ 缓存清除完成！删除了 {deleted_count} 个健康数据相关缓存键")
        print("✅ 已执行完全清除 (flushall)")
        
    except redis.ConnectionError as e:
        print(f"❌ Redis连接失败: {e}")
    except Exception as e:
        print(f"❌ 清除缓存失败: {e}")

if __name__ == "__main__":
    clear_all_health_cache()
    
    # 等待一下让清除完成
    time.sleep(1)
    
    print("\n🔧 缓存清除完成，建议重启应用以确保配置重新加载") 