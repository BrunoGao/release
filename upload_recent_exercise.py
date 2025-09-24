#!/usr/bin/env python3
"""
上传最近几天包含运动数据的记录
"""

from upload_monthly_health_data import HealthDataUploader
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)

def main():
    uploader = HealthDataUploader()
    
    print("🏃 上传最近3天的运动数据")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # 上传最近3天，每天4条记录（上午、下午各2条，确保有运动数据）
    for day_offset in range(3):
        for hour in [10, 14, 16, 18]:  # 选择日间时段确保生成运动数据
            timestamp = datetime.now() - timedelta(days=day_offset, hours=datetime.now().hour-hour)
            
            health_data = uploader.generate_realistic_health_data(timestamp)
            total_count += 1
            
            if uploader.upload_health_data(health_data):
                success_count += 1
                print(f"✅ {timestamp.strftime('%m-%d %H:%M')} 上传成功")
            else:
                print(f"❌ {timestamp.strftime('%m-%d %H:%M')} 上传失败")
    
    print(f"\n📊 上传完成: {success_count}/{total_count} 成功")
    print("💡 现在可以查询运动数据了")

if __name__ == "__main__":
    main()