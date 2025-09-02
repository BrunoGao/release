#!/usr/bin/env python3
import requests,time,json
from datetime import datetime

class PerformanceUITester:#性能测试UI测试工具
    def __init__(self):
        self.base_url='http://localhost:5001'
        
    def test_page_access(self):#测试页面访问
        print('🌐测试页面访问...')
        try:
            response=requests.get(f'{self.base_url}/performance_test_report',timeout=10)
            if response.status_code==200:
                content=response.text
                if '实时监控面板' in content and 'createMonitorPanel' in content:
                    print('✅页面访问正常，包含监控面板')
                    return True
                else:
                    print('❌页面内容异常，缺少监控面板')
                    return False
            else:
                print(f'❌页面访问失败: {response.status_code}')
                return False
        except Exception as e:
            print(f'❌页面访问异常: {e}')
            return False
            
    def test_metrics_api(self):#测试监控API
        print('📊测试监控API...')
        try:
            response=requests.get(f'{self.base_url}/api/performance_test/metrics',timeout=5)
            if response.status_code==200:
                data=response.json()
                if data.get('success') and 'server' in data and 'database' in data:
                    server=data['server']
                    database=data['database']
                    print('✅监控API正常')
                    print(f'  服务器: CPU:{server["cpu"]}% 内存:{server["memory"]}% 连接:{server["connections"]} 磁盘IO:{server["disk_io"]}MB/s')
                    print(f'  数据库: 连接:{database["connections"]} QPS:{database["qps"]} 缓存命中:{database["cache_hit_rate"]}% 慢查询:{database["slow_queries"]}')
                    return True
                else:
                    print(f'❌监控API数据异常: {data}')
                    return False
            else:
                print(f'❌监控API响应异常: {response.status_code}')
                return False
        except Exception as e:
            print(f'❌监控API失败: {e}')
            return False
            
    def test_performance_test_start(self):#测试性能测试启动
        print('🚀测试性能测试启动...')
        try:
            response=requests.post(
                f'{self.base_url}/api/performance_test/start',
                json={'type':'normal'},
                timeout=10
            )
            if response.status_code==200:
                data=response.json()
                if data.get('success'):
                    print(f'✅性能测试启动成功: {data["message"]}')
                    return True
                else:
                    print(f'❌性能测试启动失败: {data.get("error","")}')
                    return False
            else:
                print(f'❌性能测试启动异常: {response.status_code}')
                return False
        except Exception as e:
            print(f'❌性能测试启动异常: {e}')
            return False
            
    def run_full_test(self):#运行完整测试
        print(f'🎯启动性能测试UI完整测试 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('='*70)
        
        #页面访问测试
        print('\n🔍页面访问测试:')
        page_ok=self.test_page_access()
        
        #监控API测试
        print('\n📊监控API测试:')
        api_ok=self.test_metrics_api()
        
        #性能测试启动测试
        print('\n🚀性能测试启动测试:')
        test_ok=self.test_performance_test_start()
        
        #总结
        print('\n'+'='*70)
        print('🎯测试结果总结:')
        print(f'  页面访问: {"✅通过" if page_ok else "❌失败"}')
        print(f'  监控API: {"✅通过" if api_ok else "❌失败"}')
        print(f'  测试启动: {"✅通过" if test_ok else "❌失败"}')
        
        if page_ok and api_ok:
            print('\n✅监控面板功能正常，可以正常使用')
            print('💡访问 http://localhost:5001/performance_test_report 查看实时监控')
        else:
            print('\n❌部分功能异常，请检查服务状态')

def main():
    tester=PerformanceUITester()
    
    print('🚀性能测试UI测试工具')
    print('确保Flask服务已启动: PYTHONPATH=. python bigScreen/bigScreen.py')
    print()
    
    tester.run_full_test()

if __name__=='__main__':
    main() 