#!/usr/bin/env python3
from continuous_uploader import ContinuousUploader
from datetime import datetime
import sys

def test_historical_short():
    """测试短期历史数据上传（1小时）"""
    print("🧪 测试历史数据上传功能")
    print("=" * 50)
    
    uploader = ContinuousUploader("http://192.168.1.83:5001", 300)
    
    # 测试1小时的历史数据（12个时间点）
    uploader.start_historical(days=0.042)  # 1小时 = 1/24天
    
    print("✅ 历史数据上传测试完成")

def test_continuous_short():
    """测试持续上传功能（3次上传）"""
    print("\n🔄 测试持续上传功能")
    print("=" * 50)
    
    uploader = ContinuousUploader("http://192.168.1.83:5001", 10)  # 10秒间隔
    
    import threading
    import time
    
    # 运行3次后自动停止
    def auto_stop():
        time.sleep(35)  # 让它运行3次（10秒间隔 * 3 + 一些缓冲）
        uploader.stop()
    
    stop_thread = threading.Thread(target=auto_stop)
    stop_thread.daemon = True
    stop_thread.start()
    
    uploader.start_continuous()
    
    print("✅ 持续上传测试完成")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "historical":
            test_historical_short()
        elif sys.argv[1] == "continuous":
            test_continuous_short()
        else:
            print("用法: python test_continuous.py [historical|continuous]")
    else:
        # 默认测试历史数据
        test_historical_short()