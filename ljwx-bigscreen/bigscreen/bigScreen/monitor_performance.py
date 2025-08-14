#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大屏系统性能监控脚本
持续监控系统性能状态，发现性能问题时报警
"""

import requests,time,json,datetime
from threading import Thread

class PerformanceMonitor:
    def __init__(self, base_url="http://127.0.0.1:5001", customer_id="1"):
        self.base_url = base_url
        self.customer_id = customer_id
        self.running = False
        self.stats = {
            'total_requests': 0,
            'success_requests': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'min_response_time': float('inf'),
            'optimization_enabled': 0,
            'cache_hits': 0
        }
    
    def test_api_performance(self, endpoint, params=None): #测试API性能
        """测试单个API的性能"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", 
                                  params=params or {}, 
                                  timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                performance = data.get('performance', {})
                
                return {
                    'success': True,
                    'response_time': response_time,
                    'cached': performance.get('cached', False),
                    'optimized': performance.get('optimized', False),
                    'data_size': len(response.content),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def update_stats(self, result): #更新统计信息
        """更新性能统计信息"""
        self.stats['total_requests'] += 1
        
        if result['success']:
            self.stats['success_requests'] += 1
            rt = result['response_time']
            
            # 更新响应时间统计
            self.stats['avg_response_time'] = (
                self.stats['avg_response_time'] * (self.stats['success_requests'] - 1) + rt
            ) / self.stats['success_requests']
            
            self.stats['max_response_time'] = max(self.stats['max_response_time'], rt)
            self.stats['min_response_time'] = min(self.stats['min_response_time'], rt)
            
            # 统计优化和缓存情况
            if result.get('optimized'):
                self.stats['optimization_enabled'] += 1
            if result.get('cached'):
                self.stats['cache_hits'] += 1
    
    def check_performance_alerts(self, result): #性能告警检查
        """检查性能告警"""
        alerts = []
        
        if result['success']:
            rt = result['response_time']
            
            # 响应时间告警
            if rt > 10:
                alerts.append(f"⚠️  响应时间过长: {rt:.2f}秒")
            elif rt > 5:
                alerts.append(f"⚠️  响应时间较慢: {rt:.2f}秒")
            elif rt < 0.1:
                alerts.append(f"✅ 响应极快: {rt:.3f}秒")
            
            # 优化状态告警
            if not result.get('optimized') and self.stats['total_requests'] > 5:
                alerts.append("⚠️  优化模式未启用，建议检查用户数量")
                
        else:
            alerts.append(f"❌ 请求失败: {result.get('error', '未知错误')}")
        
        return alerts
    
    def print_status(self, result, alerts): #打印状态信息
        """打印当前状态"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        if result['success']:
            status = f"✅ {timestamp} | 响应时间: {result['response_time']:.3f}秒"
            if result.get('cached'):
                status += " | 缓存命中"
            if result.get('optimized'):
                status += " | 已优化"
        else:
            status = f"❌ {timestamp} | 失败: {result.get('error', '未知')}"
        
        print(status)
        
        # 打印告警
        for alert in alerts:
            print(f"   {alert}")
    
    def print_summary(self): #打印汇总统计
        """打印汇总统计"""
        if self.stats['total_requests'] == 0:
            return
            
        success_rate = (self.stats['success_requests'] / self.stats['total_requests']) * 100
        opt_rate = (self.stats['optimization_enabled'] / max(self.stats['success_requests'], 1)) * 100
        cache_rate = (self.stats['cache_hits'] / max(self.stats['success_requests'], 1)) * 100
        
        print("\n" + "="*60)
        print("📊 性能监控汇总统计:")
        print("-"*40)
        print(f"总请求数: {self.stats['total_requests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"平均响应时间: {self.stats['avg_response_time']:.3f}秒")
        print(f"最快响应: {self.stats['min_response_time']:.3f}秒")
        print(f"最慢响应: {self.stats['max_response_time']:.3f}秒")
        print(f"优化启用率: {opt_rate:.1f}%")
        print(f"缓存命中率: {cache_rate:.1f}%")
        
        # 性能评估
        if self.stats['avg_response_time'] < 1:
            rating = "🎉 性能优秀"
        elif self.stats['avg_response_time'] < 3:
            rating = "✅ 性能良好"
        elif self.stats['avg_response_time'] < 5:
            rating = "⚠️  性能一般"
        else:
            rating = "❌ 性能较差"
        
        print(f"性能评级: {rating}")
        print("="*60)
    
    def monitor_loop(self, interval=10): #监控循环
        """监控主循环"""
        print("🚀 大屏性能监控启动")
        print(f"📍 监控地址: {self.base_url}")
        print(f"👥 客户ID: {self.customer_id}")
        print(f"⏰ 监控间隔: {interval}秒")
        print("按 Ctrl+C 停止监控\n")
        
        self.running = True
        
        try:
            while self.running:
                # 测试主要接口
                result = self.test_api_performance(
                    "/get_total_info",
                    {'customer_id': self.customer_id, 'optimize': 'auto'}
                )
                
                # 更新统计和检查告警
                self.update_stats(result)
                alerts = self.check_performance_alerts(result)
                self.print_status(result, alerts)
                
                # 每10次请求打印一次汇总
                if self.stats['total_requests'] % 10 == 0:
                    self.print_summary()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 监控已停止")
            self.print_summary()
        except Exception as e:
            print(f"\n❌ 监控异常: {e}")
        finally:
            self.running = False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='大屏性能监控工具')
    parser.add_argument('--url', default='http://127.0.0.1:5001', help='服务地址')
    parser.add_argument('--customer-id', default='1', help='客户ID')
    parser.add_argument('--interval', type=int, default=10, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.url, args.customer_id)
    monitor.monitor_loop(args.interval)

if __name__ == "__main__":
    main() 