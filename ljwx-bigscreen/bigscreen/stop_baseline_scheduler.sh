#!/bin/bash
# 停止健康基线定时任务脚本

cd "$(dirname "$0")"

PID_FILE="baseline_scheduler.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止基线定时任务，PID: $PID"
        kill $PID
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止任务..."
            kill -9 $PID
        fi
        rm -f "$PID_FILE"
        echo "基线定时任务已停止"
    else
        echo "基线定时任务未运行 (PID: $PID)"
        rm -f "$PID_FILE"
    fi
else
    echo "未找到PID文件，任务可能未启动"
fi 