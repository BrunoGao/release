#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from fast_uploader import FastUploader

def main():
    print("🚀 30天历史数据高速上传")
    print("=" * 60)
    print("🎯 模拟客户手表每分钟上传一次数据")
    print("⚡ 高并发模式，最大化上传速度")
    print("📊 预计统计:")
    print("   • 时间范围: 过去30天")
    print("   • 上传频率: 每分钟1次")
    print("   • 时间点数: 43,200个 (30天 × 24小时 × 60分钟)")
    print("   • 总操作数: ~130,000次 (假设3个设备)")
    print("   • 预计速度: 600+ 次/秒")
    print("   • 预计耗时: 3-5分钟")
    print()
    
    # 检查虚拟环境
    if not os.path.exists("test_env/bin/activate"):
        print("❌ 虚拟环境不存在，请先运行:")
        print("   python3 -m venv test_env")
        print("   source test_env/bin/activate")
        print("   pip install -r requirements.txt")
        return
    
    # 显示当前配置
    print("🔧 当前配置:")
    print("   • API地址: http://192.168.1.83:5001")
    print("   • 数据库: 127.0.0.1:3306/test")
    print("   • 线程池: 20个并发线程")
    print()
    
    # 确认开始
    print("⚠️  注意事项:")
    print("   • 这将生成大量测试数据")
    print("   • 请确保API服务器能承受高并发")
    print("   • 可以随时按 Ctrl+C 安全停止")
    print("   • 建议在测试环境中运行")
    print()
    
    choice = input("选择运行方式:\n1. 完整30天上传\n2. 测试模式(1小时数据)\n3. 自定义天数\n请选择 (1-3): ").strip()
    
    days = 30
    if choice == "2":
        days = 0.042  # 1小时
        print(f"🧪 测试模式 - 上传1小时数据")
    elif choice == "3":
        try:
            days = float(input("请输入天数: ").strip())
            print(f"📅 自定义模式 - 上传{days}天数据")
        except ValueError:
            print("❌ 无效输入")
            return
    elif choice == "1":
        print(f"🚀 完整模式 - 上传30天数据")
    else:
        print("❌ 无效选择")
        return
    
    print()
    confirm = input("确认开始上传? (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    print()
    print("🚀 开始高速上传...")
    print("=" * 60)
    
    # 开始上传
    uploader = FastUploader()
    
    try:
        uploader.upload_historical_data_fast(days)
        print("✅ 上传完成!")
    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断上传")
        uploader.running = False
    except Exception as e:
        print(f"\n❌ 上传错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()