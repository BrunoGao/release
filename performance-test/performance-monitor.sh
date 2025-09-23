#!/bin/bash

# ljwx-boot 性能监控脚本
# 用法: ./performance-monitor.sh [duration_minutes] [output_dir]

DURATION=${1:-10}  # 默认监控10分钟
OUTPUT_DIR=${2:-"./monitoring-results"}  # 默认输出目录
INTERVAL=5  # 监控间隔5秒

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 获取ljwx-boot进程ID
LJWX_PID=$(pgrep -f "ljwx-boot")
if [ -z "$LJWX_PID" ]; then
    echo "错误: 未找到ljwx-boot进程，请确保服务已启动"
    exit 1
fi

echo "=== ljwx-boot 性能监控启动 ==="
echo "进程ID: $LJWX_PID"
echo "监控时长: $DURATION 分钟"
echo "监控间隔: $INTERVAL 秒"
echo "输出目录: $OUTPUT_DIR"
echo "开始时间: $(date)"

# 监控文件
SYSTEM_LOG="$OUTPUT_DIR/system-metrics.log"
JVM_LOG="$OUTPUT_DIR/jvm-metrics.log"
APP_LOG="$OUTPUT_DIR/app-metrics.log"
DB_LOG="$OUTPUT_DIR/db-metrics.log"
SUMMARY_LOG="$OUTPUT_DIR/performance-summary.log"

# 初始化日志文件
echo "timestamp,cpu_percent,memory_percent,memory_rss_mb,memory_vms_mb,threads,open_files" > "$SYSTEM_LOG"
echo "timestamp,heap_used_mb,heap_max_mb,heap_usage_percent,non_heap_used_mb,gc_count,gc_time_ms" > "$JVM_LOG"
echo "timestamp,active_threads,total_requests,response_time_avg,error_rate" > "$APP_LOG"
echo "timestamp,connections,slow_queries,queries_per_sec" > "$DB_LOG"

# 监控函数
monitor_system() {
    while [ $SECONDS -lt $((DURATION * 60)) ]; do
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 系统资源监控
        if command -v ps &> /dev/null; then
            PS_OUTPUT=$(ps -p $LJWX_PID -o pid,pcpu,pmem,rss,vsz,nlwp 2>/dev/null | tail -n 1)
            if [ ! -z "$PS_OUTPUT" ]; then
                CPU_PERCENT=$(echo $PS_OUTPUT | awk '{print $2}')
                MEM_PERCENT=$(echo $PS_OUTPUT | awk '{print $3}')
                RSS_MB=$(echo $PS_OUTPUT | awk '{printf "%.2f", $4/1024}')
                VSS_MB=$(echo $PS_OUTPUT | awk '{printf "%.2f", $5/1024}')
                THREADS=$(echo $PS_OUTPUT | awk '{print $6}')
                
                # 获取打开文件数
                OPEN_FILES=$(lsof -p $LJWX_PID 2>/dev/null | wc -l)
                
                echo "$TIMESTAMP,$CPU_PERCENT,$MEM_PERCENT,$RSS_MB,$VSS_MB,$THREADS,$OPEN_FILES" >> "$SYSTEM_LOG"
            fi
        fi
        
        # JVM内存监控
        if command -v jstat &> /dev/null; then
            JSTAT_OUTPUT=$(jstat -gc $LJWX_PID 2>/dev/null | tail -n 1)
            if [ ! -z "$JSTAT_OUTPUT" ]; then
                # 解析jstat输出 (S0U S1U EU OU MU CCSU YGC YGCT FGC FGCT CGC CGCT GCT)
                read -ra JSTAT_ARRAY <<< "$JSTAT_OUTPUT"
                if [ ${#JSTAT_ARRAY[@]} -ge 13 ]; then
                    # 计算堆内存使用情况
                    EDEN_USED=${JSTAT_ARRAY[2]}
                    OLD_USED=${JSTAT_ARRAY[3]}
                    HEAP_USED=$(echo "$EDEN_USED + $OLD_USED" | bc -l 2>/dev/null || echo "0")
                    
                    YGC=${JSTAT_ARRAY[6]}
                    YGCT=${JSTAT_ARRAY[7]}
                    FGC=${JSTAT_ARRAY[8]}
                    FGCT=${JSTAT_ARRAY[9]}
                    
                    TOTAL_GC=$((YGC + FGC))
                    TOTAL_GC_TIME=$(echo "$YGCT + $FGCT" | bc -l 2>/dev/null || echo "0")
                    
                    # 获取堆内存最大值（需要jmap）
                    HEAP_MAX=1024  # 默认1GB，实际应从jmap获取
                    HEAP_USAGE_PERCENT=$(echo "scale=2; $HEAP_USED * 100 / $HEAP_MAX" | bc -l 2>/dev/null || echo "0")
                    
                    echo "$TIMESTAMP,$HEAP_USED,$HEAP_MAX,$HEAP_USAGE_PERCENT,0,$TOTAL_GC,$TOTAL_GC_TIME" >> "$JVM_LOG"
                fi
            fi
        fi
        
        # 应用指标监控 (通过actuator接口)
        if command -v curl &> /dev/null; then
            # HTTP连接池状态
            HTTP_METRICS=$(curl -s http://localhost:8080/actuator/metrics 2>/dev/null)
            if [ $? -eq 0 ]; then
                # 提取关键指标（需要解析JSON，这里简化处理）
                echo "$TIMESTAMP,0,0,0,0" >> "$APP_LOG"
            else
                echo "$TIMESTAMP,ERROR,ERROR,ERROR,ERROR" >> "$APP_LOG"
            fi
        fi
        
        # 数据库监控 (MySQL)
        DB_METRICS=$(mysql -h localhost -u root -e "SHOW STATUS LIKE 'Threads_connected'; SHOW STATUS LIKE 'Slow_queries'; SHOW STATUS LIKE 'Questions';" 2>/dev/null | grep -E "Threads_connected|Slow_queries|Questions" | awk '{print $2}')
        if [ ! -z "$DB_METRICS" ]; then
            CONNECTIONS=$(echo "$DB_METRICS" | sed -n '1p')
            SLOW_QUERIES=$(echo "$DB_METRICS" | sed -n '2p')  
            QUESTIONS=$(echo "$DB_METRICS" | sed -n '3p')
            echo "$TIMESTAMP,$CONNECTIONS,$SLOW_QUERIES,$QUESTIONS" >> "$DB_LOG"
        fi
        
        sleep $INTERVAL
    done
}

# 生成性能摘要报告
generate_summary() {
    echo "=== ljwx-boot 性能监控摘要报告 ===" > "$SUMMARY_LOG"
    echo "监控时间: $(date)" >> "$SUMMARY_LOG"
    echo "监控时长: $DURATION 分钟" >> "$SUMMARY_LOG"
    echo "进程ID: $LJWX_PID" >> "$SUMMARY_LOG"
    echo "" >> "$SUMMARY_LOG"
    
    # 系统资源摘要
    if [ -f "$SYSTEM_LOG" ]; then
        echo "=== 系统资源使用摘要 ===" >> "$SUMMARY_LOG"
        # CPU使用率统计
        CPU_AVG=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' '{sum+=$2; count++} END {if(count>0) printf "%.2f", sum/count}')
        CPU_MAX=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' 'BEGIN{max=0} {if($2>max) max=$2} END {printf "%.2f", max}')
        
        # 内存使用率统计
        MEM_AVG=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' '{sum+=$3; count++} END {if(count>0) printf "%.2f", sum/count}')
        MEM_MAX=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' 'BEGIN{max=0} {if($3>max) max=$3} END {printf "%.2f", max}')
        
        # RSS内存统计
        RSS_AVG=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' '{sum+=$4; count++} END {if(count>0) printf "%.2f", sum/count}')
        RSS_MAX=$(tail -n +2 "$SYSTEM_LOG" | awk -F',' 'BEGIN{max=0} {if($4>max) max=$4} END {printf "%.2f", max}')
        
        echo "CPU使用率 - 平均: ${CPU_AVG}%, 最大: ${CPU_MAX}%" >> "$SUMMARY_LOG"
        echo "内存使用率 - 平均: ${MEM_AVG}%, 最大: ${MEM_MAX}%" >> "$SUMMARY_LOG"
        echo "RSS内存 - 平均: ${RSS_AVG}MB, 最大: ${RSS_MAX}MB" >> "$SUMMARY_LOG"
        echo "" >> "$SUMMARY_LOG"
    fi
    
    # JVM内存摘要
    if [ -f "$JVM_LOG" ]; then
        echo "=== JVM内存使用摘要 ===" >> "$SUMMARY_LOG"
        HEAP_AVG=$(tail -n +2 "$JVM_LOG" | awk -F',' '{sum+=$2; count++} END {if(count>0) printf "%.2f", sum/count}')
        HEAP_MAX=$(tail -n +2 "$JVM_LOG" | awk -F',' 'BEGIN{max=0} {if($2>max) max=$2} END {printf "%.2f", max}')
        
        echo "堆内存使用 - 平均: ${HEAP_AVG}MB, 最大: ${HEAP_MAX}MB" >> "$SUMMARY_LOG"
        echo "" >> "$SUMMARY_LOG"
    fi
    
    # 性能建议
    echo "=== 性能分析建议 ===" >> "$SUMMARY_LOG"
    
    # CPU分析
    if [ ! -z "$CPU_AVG" ] && [ $(echo "$CPU_AVG > 80" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        echo "⚠️  CPU使用率过高 (平均${CPU_AVG}%)，建议:" >> "$SUMMARY_LOG"
        echo "   - 检查是否有CPU密集型操作" >> "$SUMMARY_LOG"
        echo "   - 考虑优化算法或增加服务器资源" >> "$SUMMARY_LOG"
        echo "   - 检查是否有死循环或无限递归" >> "$SUMMARY_LOG"
        echo "" >> "$SUMMARY_LOG"
    fi
    
    # 内存分析
    if [ ! -z "$MEM_AVG" ] && [ $(echo "$MEM_AVG > 80" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        echo "⚠️  内存使用率过高 (平均${MEM_AVG}%)，建议:" >> "$SUMMARY_LOG"
        echo "   - 检查是否有内存泄漏" >> "$SUMMARY_LOG"
        echo "   - 优化JVM堆内存配置" >> "$SUMMARY_LOG"
        echo "   - 检查缓存策略是否合理" >> "$SUMMARY_LOG"
        echo "" >> "$SUMMARY_LOG"
    fi
    
    echo "📊 详细监控数据请查看:" >> "$SUMMARY_LOG"
    echo "   - 系统指标: $SYSTEM_LOG" >> "$SUMMARY_LOG"
    echo "   - JVM指标: $JVM_LOG" >> "$SUMMARY_LOG"
    echo "   - 应用指标: $APP_LOG" >> "$SUMMARY_LOG"
    echo "   - 数据库指标: $DB_LOG" >> "$SUMMARY_LOG"
}

# 清理函数
cleanup() {
    echo ""
    echo "监控结束，正在生成摘要报告..."
    generate_summary
    echo "性能监控完成！"
    echo "摘要报告: $SUMMARY_LOG"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 开始监控
echo "正在监控 ljwx-boot 性能指标..."
echo "按 Ctrl+C 提前结束监控"
monitor_system

# 正常结束时也生成报告
cleanup