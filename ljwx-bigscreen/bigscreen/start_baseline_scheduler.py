#!/usr/bin/env python3
"""ljwx-bigscreen健康基线调度器启动脚本"""
import os,sys,subprocess,signal,time
from pathlib import Path

# 添加项目路径
current_dir=Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir/"bigScreen"))

def start_scheduler():
    """启动基线调度器"""
    print("🚀 启动ljwx-bigscreen健康基线调度器...")
    
    try:
        # 检查auto_generate_baseline.py是否存在
        baseline_script=current_dir/"auto_generate_baseline.py"
        if not baseline_script.exists():
            print(f"❌ 基线生成脚本不存在: {baseline_script}")
            return False
        
        # 启动调度器
        cmd=[sys.executable,str(baseline_script),"--mode","schedule"]
        process=subprocess.Popen(cmd,cwd=str(current_dir))
        
        # 保存PID
        pid_file=current_dir/"baseline_scheduler.pid"
        with open(pid_file,'w') as f:
            f.write(str(process.pid))
        
        print(f"✅ 调度器启动成功 (PID: {process.pid})")
        print(f"📄 PID文件: {pid_file}")
        
        # 等待进程
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 收到中断信号，停止调度器...")
            process.terminate()
            process.wait()
            
        return True
        
    except Exception as e:
        print(f"❌ 启动调度器失败: {e}")
        return False

def stop_scheduler():
    """停止基线调度器"""
    print("🛑 停止ljwx-bigscreen健康基线调度器...")
    
    pid_file=current_dir/"baseline_scheduler.pid"
    if not pid_file.exists():
        print("⚠️ PID文件不存在，调度器可能未运行")
        return True
    
    try:
        with open(pid_file,'r') as f:
            pid=int(f.read().strip())
        
        # 检查进程是否存在
        try:
            os.kill(pid,0)  # 检查进程是否存在
            print(f"🔄 终止进程 (PID: {pid})...")
            os.kill(pid,signal.SIGTERM)
            
            # 等待进程结束
            for i in range(10):
                try:
                    os.kill(pid,0)
                    time.sleep(1)
                except ProcessLookupError:
                    break
            else:
                # 强制终止
                print("⚡ 强制终止进程...")
                os.kill(pid,signal.SIGKILL)
            
            print("✅ 调度器已停止")
            
        except ProcessLookupError:
            print(f"⚠️ 进程不存在 (PID: {pid})")
        
        # 清理PID文件
        pid_file.unlink()
        return True
        
    except Exception as e:
        print(f"❌ 停止调度器失败: {e}")
        return False

def status_scheduler():
    """查看调度器状态"""
    print("📊 检查ljwx-bigscreen健康基线调度器状态...")
    
    pid_file=current_dir/"baseline_scheduler.pid"
    if not pid_file.exists():
        print("⚠️ 调度器未运行 (PID文件不存在)")
        return False
    
    try:
        with open(pid_file,'r') as f:
            pid=int(f.read().strip())
        
        try:
            os.kill(pid,0)  # 检查进程是否存在
            print(f"✅ 调度器运行中 (PID: {pid})")
            
            # 显示日志
            log_file=current_dir/"baseline_auto_generation.log"
            if log_file.exists():
                print("\n📋 最近日志 (最后5行):")
                with open(log_file,'r',encoding='utf-8') as f:
                    lines=f.readlines()
                    for line in lines[-5:]:
                        print(f"  {line.rstrip()}")
            
            return True
            
        except ProcessLookupError:
            print(f"⚠️ PID文件存在但进程不运行 (PID: {pid})")
            pid_file.unlink()
            return False
            
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False

def manual_generate(days=1):
    """手动生成基线数据"""
    print(f"🔧 手动生成最近{days}天的基线数据...")
    
    try:
        baseline_script=current_dir/"auto_generate_baseline.py"
        if not baseline_script.exists():
            print(f"❌ 基线生成脚本不存在: {baseline_script}")
            return False
        
        cmd=[sys.executable,str(baseline_script),"--mode","manual","--days",str(days)]
        result=subprocess.run(cmd,cwd=str(current_dir),capture_output=True,text=True)
        
        if result.returncode==0:
            print("✅ 手动生成完成")
            print(result.stdout)
        else:
            print("❌ 手动生成失败")
            print(result.stderr)
        
        return result.returncode==0
        
    except Exception as e:
        print(f"❌ 手动生成失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    parser=argparse.ArgumentParser(description="ljwx-bigscreen健康基线调度器管理")
    parser.add_argument("action",choices=["start","stop","restart","status","manual"],help="操作类型")
    parser.add_argument("--days",type=int,default=1,help="手动模式生成天数")
    args=parser.parse_args()
    
    if args.action=="start":
        start_scheduler()
    elif args.action=="stop":
        stop_scheduler()
    elif args.action=="restart":
        stop_scheduler()
        time.sleep(2)
        start_scheduler()
    elif args.action=="status":
        status_scheduler()
    elif args.action=="manual":
        manual_generate(args.days)

if __name__=="__main__":
    main() 