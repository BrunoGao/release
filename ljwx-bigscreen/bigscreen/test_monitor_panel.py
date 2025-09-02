#!/usr/bin/env python3
import requests,time,json
from datetime import datetime

class MonitorPanelTester:#监控面板测试工具
    def __init__(self):
        self.base_url='http://localhost:5001'
        
    def test_metrics_api(self):#测试监控指标API
        print('📊测试监控指标API...')
        try:
            response=requests.get(f'{self.base_url}/api/performance_test/metrics',timeout=5)
            if response.status_code==200:
                data=response.json()
                if data.get('success') and 'server' in data and 'database' in data:
                    server=data['server']
                    database=data['database']
                    print(f'✅监控API正常')
                    print(f'  服务器: CPU:{server["cpu"]}% 内存:{server["memory"]}% 连接:{server["connections"]} 磁盘IO:{server["disk_io"]}MB/s')
                    print(f'  数据库: 连接:{database["connections"]} QPS:{database["qps"]} 缓存命中:{database["cache_hit_rate"]}% 慢查询:{database["slow_queries"]}')
                    return True,data
                else:
                    print(f'❌监控API数据异常: {data}')
                    return False,None
            else:
                print(f'❌监控API响应异常: {response.status_code}')
                return False,None
        except Exception as e:
            print(f'❌监控API失败: {e}')
            return False,None
            
    def test_real_time_updates(self,duration=30):#测试实时更新
        print(f'🔄测试实时监控更新({duration}秒)...')
        start_time=time.time()
        update_count=0
        
        while time.time()-start_time<duration:
            success,data=self.test_metrics_api()
            if success:
                update_count+=1
                print(f'  第{update_count}次更新 - 时间:{datetime.now().strftime("%H:%M:%S")}')
            else:
                print('  ❌更新失败')
            time.sleep(3)#每3秒更新一次
            
        print(f'✅实时更新测试完成，共{update_count}次成功更新')
        return update_count>0
        
    def run_full_test(self):#运行完整测试
        print(f'🎯启动监控面板完整测试 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('='*70)
        
        #基础API测试
        print('\n🔍基础功能测试:')
        success,_=self.test_metrics_api()
        
        if success:
            print('\n🔄实时更新测试:')
            self.test_real_time_updates(15)#测试15秒
        else:
            print('❌基础API测试失败，跳过实时更新测试')
            
        print('\n'+'='*70)
        print('🎯监控面板测试完成')
        print('💡提示: 访问 http://localhost:5001/performance_test_report 查看实时监控面板')

def main():
    tester=MonitorPanelTester()
    
    print('🚀监控面板测试工具')
    print('确保Flask服务已启动: python -m bigScreen.bigScreen')
    print()
    
    tester.run_full_test()

if __name__=='__main__':
    main() 