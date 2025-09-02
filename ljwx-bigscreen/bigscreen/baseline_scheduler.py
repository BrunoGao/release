#!/usr/bin/env python3
"""健康基线定时生成调度器"""
import schedule
import time
import logging
from datetime import datetime, date, timedelta
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bigScreen.health_baseline import generate_baseline_task

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_baseline_generation():
    """执行基线生成任务"""
    try:
        logger.info("开始执行基线生成任务...")
        result = generate_baseline_task()
        
        user_result = result.get('user_baseline', {})
        org_result = result.get('org_baseline', {})
        
        if user_result.get('success') and org_result.get('success'):
            logger.info(f"基线生成成功 - 用户基线: {user_result.get('count', 0)}条, 组织基线: {org_result.get('count', 0)}条")
        else:
            logger.error(f"基线生成失败 - 用户基线: {user_result}, 组织基线: {org_result}")
            
    except Exception as e:
        logger.error(f"基线生成任务执行失败: {e}")

def main():
    """主函数"""
    logger.info("基线生成调度器启动...")
    
    # 每天凌晨2点执行基线生成
    schedule.every().day.at("02:00").do(run_baseline_generation)
    
    # 也可以手动触发一次（用于测试）
    if len(sys.argv) > 1 and sys.argv[1] == '--run-now':
        logger.info("手动执行基线生成任务...")
        run_baseline_generation()
        return
    
    logger.info("调度器已启动，等待执行时间...")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("调度器停止")
            break
        except Exception as e:
            logger.error(f"调度器运行错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main() 