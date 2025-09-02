#!/usr/bin/env python3
import subprocess,time

def run_update():
    result=subprocess.run(['python','update_sleep_data.py','update'],capture_output=True,text=True)
    output=result.stdout
    
    #提取更新数量
    for line in output.split('\n'):
        if '成功更新:' in line:
            updated=int(line.split(':')[1].strip())
            return updated
    return 0

def check_remaining():
    result=subprocess.run(['python','update_sleep_data.py','check'],capture_output=True,text=True)
    output=result.stdout
    
    for line in output.split('\n'):
        if '可更新记录数:' in line:
            remaining=int(line.split(':')[1].strip().replace(',',''))
            return remaining
    return 0

print("开始批量更新睡眠数据...")
total_updated=0
batch=1

while True:
    remaining=check_remaining()
    if remaining==0:
        print(f"\\n✅ 所有记录更新完成！总共更新了 {total_updated:,} 条记录")
        break
    
    print(f"\\n第{batch}批次 - 剩余{remaining:,}条记录待更新")
    updated=run_update()
    
    if updated==0:
        print("没有更多记录可更新，退出")
        break
    
    total_updated+=updated
    print(f"本批次更新: {updated:,} 条，累计更新: {total_updated:,} 条")
    batch+=1
    
    time.sleep(1)#短暂休息避免数据库压力

print(f"\\n批量更新完成！总共处理了{batch-1}个批次，更新了{total_updated:,}条记录") 