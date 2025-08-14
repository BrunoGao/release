from celery import Celery
from redis import Redis
import json
from datetime import datetime, timedelta
from .models import db, UserHealthData
from .alert import generate_alerts
from .redis_helper import RedisHelper
from . import create_app
redis = RedisHelper()

# 创建Flask应用实例
flask_app = create_app()

# 创建Celery实例
celery_app = Celery('health_tasks',
                   broker='redis://localhost:6379/0',
                   backend='redis://localhost:6379/1')

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    worker_max_tasks_per_child=1000,  # 每个worker处理1000个任务后重启
    worker_prefetch_multiplier=1  # 限制worker预取任务数
)

def convert_empty_to_none(value):
    return None if value == ' ' else value

def save_health_data(data):
    """保存健康数据到数据库"""
    try:
        health_data = UserHealthData(
            user_id=data['user_id'],
            dept_id=data['dept_id'],
            heart_rate=convert_empty_to_none(data.get('heart_rate')),
            blood_pressure_high=convert_empty_to_none(data.get('blood_pressure_high')),
            blood_pressure_low=convert_empty_to_none(data.get('blood_pressure_low')),
            blood_oxygen=convert_empty_to_none(data.get('blood_oxygen')),
            temperature=convert_empty_to_none(data.get('temperature')),
            blood_sugar=convert_empty_to_none(data.get('blood_sugar')),
            weight=convert_empty_to_none(data.get('weight')),
            height=convert_empty_to_none(data.get('height')),
            bmi=convert_empty_to_none(data.get('bmi')),
            upload_time=datetime.now()
        )
        db.session.add(health_data)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"保存健康数据失败: {str(e)}")
        return False

@celery_app.task(bind=True)
def process_health_data(self, data):
    """处理健康数据的Celery任务"""
    with flask_app.app_context():
        try:
            # 保存数据到数据库
            if save_health_data(data):
                # 生成告警
                generate_alerts(data)
                return True
            return False
        except Exception as e:
            # 任务失败，重试
            self.retry(exc=e, countdown=60)  # 1分钟后重试

@celery_app.task
def cleanup_old_tasks():
    """清理旧的任务记录"""
    with flask_app.app_context():
        try:
            # 清理7天前的任务记录
            cutoff = datetime.now() - timedelta(days=7)
            redis.delete_pattern(f"celery-task-meta-*")
            return True
        except Exception as e:
            print(f"清理任务记录失败: {str(e)}")
            return False 