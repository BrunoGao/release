<template>
  <div class="performance-monitor">
    <div class="monitor-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <TrendCharts />
        </el-icon>
        <h3 class="monitor-title">{{ title }}</h3>
      </div>
      
      <div class="performance-status" :class="getOverallStatus()">
        <span class="status-indicator"></span>
        <span class="status-text">{{ getStatusText() }}</span>
      </div>
    </div>
    
    <!-- 性能指标概览 -->
    <div class="metrics-overview">
      <div class="metric-card cpu">
        <div class="metric-header">
          <el-icon><Cpu /></el-icon>
          <span>CPU使用率</span>
        </div>
        <div class="metric-value">{{ performanceData.cpu }}%</div>
        <div class="metric-chart">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: performanceData.cpu + '%' }"
              :class="getCpuClass(performanceData.cpu)"
            ></div>
          </div>
        </div>
      </div>
      
      <div class="metric-card memory">
        <div class="metric-header">
          <el-icon><Monitor /></el-icon>
          <span>内存使用</span>
        </div>
        <div class="metric-value">{{ performanceData.memory }}%</div>
        <div class="metric-chart">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: performanceData.memory + '%' }"
              :class="getMemoryClass(performanceData.memory)"
            ></div>
          </div>
        </div>
      </div>
      
      <div class="metric-card network">
        <div class="metric-header">
          <el-icon><Connection /></el-icon>
          <span>网络延迟</span>
        </div>
        <div class="metric-value">{{ performanceData.latency }}ms</div>
        <div class="metric-status" :class="getLatencyClass(performanceData.latency)">
          {{ getLatencyStatus(performanceData.latency) }}
        </div>
      </div>
      
      <div class="metric-card storage">
        <div class="metric-header">
          <el-icon><Files /></el-icon>
          <span>存储使用</span>
        </div>
        <div class="metric-value">{{ performanceData.storage }}%</div>
        <div class="metric-chart">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: performanceData.storage + '%' }"
              :class="getStorageClass(performanceData.storage)"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 实时监控图表 -->
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 性能趋势图 -->
    </div>
    
    <!-- 性能详情 -->
    <div class="performance-details">
      <div class="detail-section">
        <h4>系统信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">操作系统</span>
            <span class="value">{{ systemInfo.os }}</span>
          </div>
          <div class="info-item">
            <span class="label">运行时间</span>
            <span class="value">{{ systemInfo.uptime }}</span>
          </div>
          <div class="info-item">
            <span class="label">进程数</span>
            <span class="value">{{ systemInfo.processes }}</span>
          </div>
          <div class="info-item">
            <span class="label">负载均衡</span>
            <span class="value">{{ systemInfo.loadAverage }}</span>
          </div>
        </div>
      </div>
      
      <div class="detail-section">
        <h4>性能警告</h4>
        <div class="warning-list">
          <div 
            v-for="warning in performanceWarnings" 
            :key="warning.id"
            class="warning-item"
            :class="warning.level"
          >
            <el-icon class="warning-icon">
              <component :is="getWarningIcon(warning.level)" />
            </el-icon>
            <div class="warning-content">
              <div class="warning-title">{{ warning.title }}</div>
              <div class="warning-desc">{{ warning.description }}</div>
            </div>
            <div class="warning-time">{{ formatTime(warning.timestamp) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  TrendCharts, 
  Cpu, 
  Monitor, 
  Connection, 
  Files,
  Warning,
  CircleClose,
  InfoFilled
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '性能监控',
  height: '600px',
  autoRefresh: true,
  refreshInterval: 5000
})

const chartRef = ref<HTMLElement>()

// 性能数据
const performanceData = reactive({
  cpu: 45,
  memory: 62,
  latency: 23,
  storage: 38
})

// 系统信息
const systemInfo = reactive({
  os: 'Linux Ubuntu 20.04',
  uptime: '7天 12小时',
  processes: 142,
  loadAverage: '0.85'
})

// 性能警告
const performanceWarnings = ref([
  {
    id: 1,
    level: 'warning',
    title: '内存使用率较高',
    description: '当前内存使用率达到62%，建议关闭不必要的进程',
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: 2,
    level: 'info',
    title: '系统运行正常',
    description: 'CPU和存储使用率在正常范围内',
    timestamp: new Date(Date.now() - 600000)
  }
])

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  
  // 生成最近1小时的性能数据
  const timeData = []
  const cpuData = []
  const memoryData = []
  const latencyData = []
  
  for (let i = 59; i >= 0; i--) {
    const time = new Date(Date.now() - i * 60000)
    timeData.push(time.toLocaleTimeString())
    cpuData.push(30 + Math.random() * 40)
    memoryData.push(50 + Math.random() * 30)
    latencyData.push(10 + Math.random() * 30)
  }
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['CPU使用率', '内存使用率', '网络延迟'],
      textStyle: {
        color: '#999'
      }
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        color: '#999',
        fontSize: 12
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '使用率(%)',
        position: 'left',
        axisLabel: {
          color: '#999',
          formatter: '{value}%'
        }
      },
      {
        type: 'value',
        name: '延迟(ms)',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}ms'
        }
      }
    ],
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        yAxisIndex: 0,
        data: cpuData,
        smooth: true,
        lineStyle: {
          color: '#ff6b6b',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
              { offset: 1, color: 'rgba(255, 107, 107, 0.1)' }
            ]
          }
        }
      },
      {
        name: '内存使用率',
        type: 'line',
        yAxisIndex: 0,
        data: memoryData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(66, 165, 245, 0.3)' },
              { offset: 1, color: 'rgba(66, 165, 245, 0.1)' }
            ]
          }
        }
      },
      {
        name: '网络延迟',
        type: 'line',
        yAxisIndex: 1,
        data: latencyData,
        smooth: true,
        lineStyle: {
          color: '#66bb6a',
          width: 2
        }
      }
    ]
  }
  
  chart.setOption(option)
  
  const resizeChart = () => chart.resize()
  window.addEventListener('resize', resizeChart)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chart.dispose()
  })
}

// 工具方法
const getOverallStatus = () => {
  if (performanceData.cpu > 80 || performanceData.memory > 80) return 'critical'
  if (performanceData.cpu > 60 || performanceData.memory > 60) return 'warning'
  return 'normal'
}

const getStatusText = () => {
  const status = getOverallStatus()
  const textMap = {
    normal: '运行正常',
    warning: '性能警告',
    critical: '性能异常'
  }
  return textMap[status]
}

const getCpuClass = (value: number) => {
  if (value > 80) return 'critical'
  if (value > 60) return 'warning'
  return 'normal'
}

const getMemoryClass = (value: number) => {
  if (value > 80) return 'critical'
  if (value > 60) return 'warning'
  return 'normal'
}

const getStorageClass = (value: number) => {
  if (value > 80) return 'critical'
  if (value > 60) return 'warning'
  return 'normal'
}

const getLatencyClass = (value: number) => {
  if (value > 100) return 'critical'
  if (value > 50) return 'warning'
  return 'normal'
}

const getLatencyStatus = (value: number) => {
  if (value > 100) return '延迟过高'
  if (value > 50) return '延迟较高'
  return '延迟正常'
}

const getWarningIcon = (level: string) => {
  const iconMap = {
    critical: CircleClose,
    warning: Warning,
    info: InfoFilled
  }
  return iconMap[level as keyof typeof iconMap] || InfoFilled
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return date.toLocaleDateString()
}

// 自动刷新
let refreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  if (!props.autoRefresh) return
  
  refreshTimer = setInterval(() => {
    // 模拟数据更新
    performanceData.cpu = 30 + Math.random() * 50
    performanceData.memory = 40 + Math.random() * 40
    performanceData.latency = 10 + Math.random() * 40
    performanceData.storage = 30 + Math.random() * 40
    
    updateChart()
  }, props.refreshInterval)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  nextTick(() => {
    updateChart()
    startAutoRefresh()
  })
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.performance-monitor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .monitor-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .performance-status {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    
    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: var(--radius-full);
    }
    
    .status-text {
      font-size: var(--font-sm);
      font-weight: 500;
    }
    
    &.normal {
      background: rgba(102, 187, 106, 0.1);
      color: var(--success-500);
      
      .status-indicator {
        background: var(--success-500);
      }
    }
    
    &.warning {
      background: rgba(255, 167, 38, 0.1);
      color: var(--warning-500);
      
      .status-indicator {
        background: var(--warning-500);
      }
    }
    
    &.critical {
      background: rgba(255, 107, 107, 0.1);
      color: var(--error-500);
      
      .status-indicator {
        background: var(--error-500);
      }
    }
  }
}

.metrics-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .metric-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    
    .metric-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-sm);
      
      .el-icon {
        color: var(--primary-500);
        font-size: 16px;
      }
      
      span {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
    
    .metric-value {
      font-size: var(--font-xl);
      font-weight: 700;
      color: var(--text-primary);
      font-family: var(--font-tech);
      margin-bottom: var(--spacing-sm);
    }
    
    .metric-chart {
      .progress-bar {
        width: 100%;
        height: 6px;
        background: var(--bg-secondary);
        border-radius: var(--radius-full);
        overflow: hidden;
        
        .progress-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width 0.3s ease;
          
          &.normal {
            background: linear-gradient(90deg, #66bb6a, #4caf50);
          }
          
          &.warning {
            background: linear-gradient(90deg, #ffa726, #ff9800);
          }
          
          &.critical {
            background: linear-gradient(90deg, #ff6b6b, #f44336);
          }
        }
      }
    }
    
    .metric-status {
      font-size: var(--font-xs);
      font-weight: 500;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      
      &.normal {
        background: rgba(102, 187, 106, 0.2);
        color: var(--success-500);
      }
      
      &.warning {
        background: rgba(255, 167, 38, 0.2);
        color: var(--warning-500);
      }
      
      &.critical {
        background: rgba(255, 107, 107, 0.2);
        color: var(--error-500);
      }
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 200px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.performance-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  
  .detail-section {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-md) 0;
    }
    
    .info-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-sm);
      
      .info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-xs) 0;
        
        .label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
        
        .value {
          font-size: var(--font-sm);
          color: var(--text-primary);
          font-weight: 500;
        }
      }
    }
    
    .warning-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      
      .warning-item {
        display: flex;
        align-items: flex-start;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm);
        border-radius: var(--radius-sm);
        
        .warning-icon {
          font-size: 16px;
          margin-top: 2px;
        }
        
        .warning-content {
          flex: 1;
          
          .warning-title {
            font-size: var(--font-sm);
            font-weight: 500;
            margin-bottom: 2px;
          }
          
          .warning-desc {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
        
        .warning-time {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
        
        &.critical {
          background: rgba(255, 107, 107, 0.1);
          
          .warning-icon {
            color: var(--error-500);
          }
          
          .warning-title {
            color: var(--error-500);
          }
        }
        
        &.warning {
          background: rgba(255, 167, 38, 0.1);
          
          .warning-icon {
            color: var(--warning-500);
          }
          
          .warning-title {
            color: var(--warning-500);
          }
        }
        
        &.info {
          background: rgba(66, 165, 245, 0.1);
          
          .warning-icon {
            color: var(--info-500);
          }
          
          .warning-title {
            color: var(--info-500);
          }
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .metrics-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .performance-details {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .metrics-overview {
    grid-template-columns: 1fr;
  }
}
</style>