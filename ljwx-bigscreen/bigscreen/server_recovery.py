#!/usr/bin/env python3
import time,requests,os,sys,gc
from datetime import datetime

class ServerRecovery:#服务器恢复工具
    def __init__(self):
        self.base_url='http://localhost:5001'#服务器地址
        self.recovery_steps=['检查服务状态','清理临时文件','重启服务','验证恢复']#恢复步骤
        
    def check_server_health(self):#检查服务器健康状态
        print('🔍检查服务器健康状态...')
        try:
            response=requests.get(f'{self.base_url}/api/performance_test/metrics',timeout=5)
            if response.status_code==200:
                data=response.json()
                if data.get('success'):
                    server=data['server']
                    print(f'✅服务器响应正常')
                    print(f'  CPU: {server["cpu"]}% | 内存: {server["memory"]}% | 连接数: {server["connections"]}')
                    return True
            print('❌服务器响应异常')
            return False
        except Exception as e:
            print(f'❌服务器连接失败: {e}')
            return False
            
    def cleanup_temp_files(self):#清理临时文件
        print('🧹清理临时文件...')
        temp_files=['test_report.html','test_progress.json','app.log']#临时文件列表
        cleaned=0
        
        for file in temp_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f'  ✅删除: {file}')
                    cleaned+=1
                else:
                    print(f'  ⚪跳过: {file} (不存在)')
            except Exception as e:
                print(f'  ❌删除失败: {file} - {e}')
                
        print(f'🗑️清理完成，删除{cleaned}个文件')
        
    def force_gc(self):#强制垃圾回收
        print('♻️执行垃圾回收...')
        for i in range(3):
            collected=gc.collect()
            print(f'  第{i+1}轮回收: {collected}个对象')
            time.sleep(1)
        print('✅垃圾回收完成')
        
    def restart_service(self):#重启服务(模拟)
        print('🔄准备重启服务...')
        print('⚠️注意: 实际环境中需要手动重启Flask服务')
        print('  命令: pkill -f "python.*bigScreen.py" && nohup python bigScreen/bigScreen.py &')
        
        #模拟重启等待
        for i in range(5,0,-1):
            print(f'  等待重启... {i}秒')
            time.sleep(1)
        print('✅模拟重启完成')
        
    def verify_recovery(self):#验证恢复状态
        print('✅验证系统恢复状态...')
        max_attempts=3
        
        for attempt in range(1,max_attempts+1):
            print(f'第{attempt}次验证...')
            if self.check_server_health():
                print('🎉系统恢复成功！')
                return True
            if attempt<max_attempts:
                print(f'等待{5}秒后重试...')
                time.sleep(5)
                
        print('❌系统恢复验证失败')
        return False
        
    def full_recovery(self):#完整恢复流程
        print(f'🚀启动服务器恢复流程 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('='*60)
        
        success_steps=0
        
        #步骤1: 检查当前状态
        if self.check_server_health():
            print('✅步骤1: 服务器状态检查通过')
            success_steps+=1
        else:
            print('⚠️步骤1: 服务器状态异常，继续恢复流程')
            
        #步骤2: 清理临时文件
        try:
            self.cleanup_temp_files()
            print('✅步骤2: 临时文件清理完成')
            success_steps+=1
        except Exception as e:
            print(f'❌步骤2: 文件清理失败 - {e}')
            
        #步骤3: 垃圾回收
        try:
            self.force_gc()
            print('✅步骤3: 内存清理完成')
            success_steps+=1
        except Exception as e:
            print(f'❌步骤3: 内存清理失败 - {e}')
            
        #步骤4: 验证恢复
        if self.verify_recovery():
            print('✅步骤4: 系统恢复验证通过')
            success_steps+=1
        else:
            print('❌步骤4: 系统恢复验证失败')
            
        #总结
        print('='*60)
        print(f'🎯恢复流程完成: {success_steps}/4 步骤成功')
        
        if success_steps>=3:
            print('🎉系统恢复成功，可以继续使用')
            return True
        else:
            print('⚠️系统恢复不完整，建议手动重启服务')
            print('手动重启命令:')
            print('  1. 停止服务: pkill -f "python.*bigScreen.py"')
            print('  2. 启动服务: cd bigscreen && python bigScreen/bigScreen.py')
            return False

def main():
    recovery=ServerRecovery()
    
    if len(sys.argv)>1:
        action=sys.argv[1].lower()
        if action=='check':
            recovery.check_server_health()
        elif action=='clean':
            recovery.cleanup_temp_files()
        elif action=='gc':
            recovery.force_gc()
        elif action=='verify':
            recovery.verify_recovery()
        else:
            print('用法: python server_recovery.py [check|clean|gc|verify]')
    else:
        recovery.full_recovery()

if __name__=='__main__':
    main() 