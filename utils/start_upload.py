#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from continuous_uploader import ContinuousUploader

def main():
    print("🚀 数据上传工具")
    print("=" * 60)
    
    print("请选择运行模式:")
    print("1. 上传过去1个月的历史数据（每5分钟一次）")
    print("2. 持续上传当前数据（每5分钟）")
    print("3. 先上传历史数据，然后持续上传")
    print("4. 测试模式 - 上传过去1小时数据")
    print("5. 自定义天数的历史数据")
    
    try:
        choice = input("\n请输入选择 (1-5): ").strip()
        
        uploader = ContinuousUploader("http://192.168.1.83:5001", 300)
        
        if choice == "1":
            print("\n📅 开始上传过去30天的历史数据...")
            print("⚠️  这将花费较长时间，请耐心等待")
            print("📊 预计操作数: 约 25,920 次上传 (30天 × 288次/天 × 3个接口)")
            print("⏱️  预计时间: 约 3-4 小时")
            
            confirm = input("确认开始? (y/N): ").strip().lower()
            if confirm == 'y':
                uploader.start_historical(30)
            else:
                print("已取消")
        
        elif choice == "2":
            print("\n🔄 开始持续数据上传...")
            print("📡 每5分钟上传一次当前数据")
            print("💡 按 Ctrl+C 停止")
            uploader.start_continuous()
        
        elif choice == "3":
            print("\n📅 先上传历史数据，然后持续上传...")
            confirm = input("确认开始历史数据上传? (y/N): ").strip().lower()
            if confirm == 'y':
                uploader.start_historical(30)
                print("\n🔄 历史数据完成，开始持续上传...")
                uploader = ContinuousUploader("http://192.168.1.83:5001", 300)
                uploader.start_continuous()
            else:
                print("已取消")
        
        elif choice == "4":
            print("\n🧪 测试模式 - 上传过去1小时数据...")
            uploader.start_historical(days=0.042)  # 1小时
        
        elif choice == "5":
            try:
                days = int(input("请输入天数: ").strip())
                if days <= 0:
                    print("天数必须大于0")
                    return
                
                operations = days * 288 * 3  # 每天288个时间点，3个接口
                hours = operations * 0.5 / 3600  # 预计每次操作0.5秒
                
                print(f"\n📊 预计操作数: {operations}")
                print(f"⏱️  预计时间: {hours:.1f} 小时")
                
                confirm = input("确认开始? (y/N): ").strip().lower()
                if confirm == 'y':
                    uploader.start_historical(days)
                else:
                    print("已取消")
                    
            except ValueError:
                print("无效的天数")
        
        else:
            print("无效的选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main()