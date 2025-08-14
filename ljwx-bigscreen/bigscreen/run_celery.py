from celery import Celery
from celery.schedules import crontab
from bigScreen.tasks import celery_app

# 配置定时任务
celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'bigScreen.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=0, minute=0),  # 每天凌晨执行
    },
    'process-health-data': {
        'task': 'bigScreen.tasks.process_health_data',
        'schedule': crontab(minute='*/10'),  # 每10分钟执行一次
    }
}

if __name__ == '__main__':
    celery_app.start() 