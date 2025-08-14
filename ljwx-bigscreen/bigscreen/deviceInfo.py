import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bigScreen.device import batch_insert_device_data

if __name__ == '__main__':
    try:
        batch_insert_device_data()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
