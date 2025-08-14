#!/bin/bash
# 一键启动健康大屏所有服务

# 启动主服务
nohup python run.py > run.log 2>&1 &

# 启动Celery worker
cd bigScreen
nohup celery -A bigScreen.tasks worker --loglevel=info --concurrency=4 > celery.log 2>&1 &

# 启动监控
nohup python ../monitor.py > monitor.log 2>&1 &
cd ..

echo "全部服务已后台启动，日志见 run.log、bigScreen/celery.log、monitor.log" 