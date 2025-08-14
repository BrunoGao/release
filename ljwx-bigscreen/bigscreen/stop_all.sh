#!/bin/bash
pkill -f 'python run.py'
pkill -f 'celery -A bigScreen.tasks worker'
pkill -f 'python monitor.py'
echo '所有服务已关闭' 