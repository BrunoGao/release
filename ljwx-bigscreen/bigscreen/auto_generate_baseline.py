#!/usr/bin/env python3
"""健康基线自动生成脚本 - 定时任务版"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import schedule
import time
import logging
from datetime import datetime, date, timedelta
from bigScreen.health_baseline import HealthBaselineGenerator
from bigScreen.models import db
from bigScreen.bigScreen import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_auto_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaselineScheduler:
    """基线生成调度器"""
    
    def __init__(self):
        self.generator = HealthBaselineGenerator()
    
    def generate_daily_baseline(self, target_date=None):
        """生成单日基线数据"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # 默认生成昨天的基线
        
        with app.app_context():
            try:
                logger.info(f"开始生成 {target_date} 的基线数据...")
                
                # 生成用户基线
                user_result = self.generator.generate_daily_user_baseline(target_date)
                user_count = user_result.get('count', 0) if user_result.get('success') else 0
                
                # 生成组织基线
                org_result = self.generator.generate_daily_org_baseline(target_date)
                org_count = org_result.get('count', 0) if org_result.get('success') else 0
                
                logger.info(f"基线生成完成 {target_date}: 用户基线 {user_count} 条, 组织基线 {org_count} 条")
                
                return {
                    'success': True,
                    'date': target_date.strftime('%Y-%m-%d'),
                    'user_count': user_count,
                    'org_count': org_count
                }
                
            except Exception as e:
                logger.error(f"基线生成失败 {target_date}: {e}")
                return {
                    'success': False,
                    'date': target_date.strftime('%Y-%m-%d'),
                    'error': str(e)
                }
    
    def backfill_missing_baselines(self, days=7):
        """补充缺失的基线数据"""
        with app.app_context():
            from bigScreen.models import HealthBaseline, OrgHealthBaseline
            
            logger.info(f"检查最近 {days} 天的基线数据缺失情况...")
            
            backfilled = 0
            for i in range(days):
                target_date = date.today() - timedelta(days=i+1)
                
                # 检查用户基线是否存在
                user_baseline_exists = db.session.query(HealthBaseline).filter(
                    HealthBaseline.baseline_date == target_date
                ).first() is not None
                
                # 检查组织基线是否存在
                org_baseline_exists = db.session.query(OrgHealthBaseline).filter(
                    OrgHealthBaseline.baseline_date == target_date
                ).first() is not None
                
                if not user_baseline_exists or not org_baseline_exists:
                    logger.info(f"补充缺失的基线数据: {target_date}")
                    result = self.generate_daily_baseline(target_date)
                    if result['success']:
                        backfilled += 1
                else:
                    logger.debug(f"基线数据已存在: {target_date}")
            
            logger.info(f"补充基线数据完成，共补充 {backfilled} 天")
            return backfilled
    
    def scheduled_task(self):
        """定时任务入口"""
        logger.info("执行定时基线生成任务...")
        
        # 1. 生成昨天的基线数据
        yesterday = date.today() - timedelta(days=1)
        result = self.generate_daily_baseline(yesterday)
        
        if result['success']:
            logger.info(f"定时任务成功: {result}")
        else:
            logger.error(f"定时任务失败: {result}")
        
        # 2. 检查并补充最近一周的缺失数据
        self.backfill_missing_baselines(7)
        
        return result
    
    def run_scheduler(self):
        """运行定时调度器"""
        logger.info("启动基线生成定时调度器...")
        
        # 设置每天凌晨1点执行
        schedule.every().day.at("01:00").do(self.scheduled_task)
        
        # 设置每小时检查一次缺失数据
        schedule.every().hour.do(lambda: self.backfill_missing_baselines(3))
        
        logger.info("调度器配置完成:")
        logger.info("- 每天 01:00 生成前一天的基线数据")
        logger.info("- 每小时检查并补充最近3天的缺失数据")
        
        # 启动时先运行一次
        logger.info("启动时执行初始化任务...")
        self.scheduled_task()
        
        # 持续运行
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止调度器")
                break
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
                time.sleep(300)  # 发生错误时等待5分钟再继续

def manual_generate(days=1):
    """手动生成指定天数的基线数据"""
    scheduler = BaselineScheduler()
    
    print(f"手动生成最近 {days} 天的基线数据...")
    
    for i in range(days):
        target_date = date.today() - timedelta(days=i+1)
        result = scheduler.generate_daily_baseline(target_date)
        
        if result['success']:
            print(f"✓ {result['date']}: 用户 {result['user_count']} 条, 组织 {result['org_count']} 条")
        else:
            print(f"✗ {result['date']}: {result['error']}")

def check_baseline_status():
    """检查基线数据状态"""
    with app.app_context():
        from bigScreen.models import HealthBaseline, OrgHealthBaseline
        from sqlalchemy import func
        
        print("=== 基线数据状态检查 ===")
        
        # 检查最近30天的基线数据覆盖情况
        thirty_days_ago = date.today() - timedelta(days=30)
        
        # 用户基线统计
        user_baseline_count = db.session.query(func.count(HealthBaseline.baseline_id)).filter(
            HealthBaseline.baseline_date >= thirty_days_ago
        ).scalar()
        
        user_baseline_days = db.session.query(func.count(func.distinct(HealthBaseline.baseline_date))).filter(
            HealthBaseline.baseline_date >= thirty_days_ago
        ).scalar()
        
        # 组织基线统计
        org_baseline_count = db.session.query(func.count(OrgHealthBaseline.id)).filter(
            OrgHealthBaseline.baseline_date >= thirty_days_ago
        ).scalar()
        
        org_baseline_days = db.session.query(func.count(func.distinct(OrgHealthBaseline.baseline_date))).filter(
            OrgHealthBaseline.baseline_date >= thirty_days_ago
        ).scalar()
        
        print(f"最近30天用户基线: {user_baseline_count} 条记录, 覆盖 {user_baseline_days} 天")
        print(f"最近30天组织基线: {org_baseline_count} 条记录, 覆盖 {org_baseline_days} 天")
        
        # 检查最近7天的具体覆盖情况
        print("\n最近7天基线覆盖详情:")
        for i in range(7):
            check_date = date.today() - timedelta(days=i+1)
            
            user_count = db.session.query(func.count(HealthBaseline.baseline_id)).filter(
                HealthBaseline.baseline_date == check_date
            ).scalar()
            
            org_count = db.session.query(func.count(OrgHealthBaseline.id)).filter(
                OrgHealthBaseline.baseline_date == check_date
            ).scalar()
            
            status = "✓" if user_count > 0 and org_count > 0 else "✗"
            print(f"{status} {check_date}: 用户 {user_count} 条, 组织 {org_count} 条")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='健康基线自动生成工具')
    parser.add_argument('--mode', choices=['schedule', 'manual', 'status'], default='status',
                       help='运行模式: schedule(定时调度), manual(手动生成), status(状态检查)')
    parser.add_argument('--days', type=int, default=1,
                       help='手动模式下生成的天数')
    
    args = parser.parse_args()
    
    if args.mode == 'schedule':
        scheduler = BaselineScheduler()
        scheduler.run_scheduler()
    elif args.mode == 'manual':
        manual_generate(args.days)
    elif args.mode == 'status':
        check_baseline_status() 