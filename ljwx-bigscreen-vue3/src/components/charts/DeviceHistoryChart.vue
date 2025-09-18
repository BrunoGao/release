<template>
  <div class="device-history-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="device-selector">
        <el-select v-model="selectedDevice" size="small" @change="updateChart">
          <el-option 
            v-for="device in devices" 
            :key="device.id"
            :label="device.name" 
            :value="device.id"
          />
        </el-select>
      </div>
    </div>
    
    <div class="device-status">
      <div class="status-item">
        <div class="status-label">设备状态</div>
        <el-tag :type="getStatusType(currentDevice.status)" size="small">
          {{ getStatusText(currentDevice.status) }}
        </el-tag>
      </div>
      
      <div class="status-item">
        <div class="status-label">数据质量</div>
        <div class="quality-indicator" :class="getQualityClass(currentDevice.quality)">
          {{ currentDevice.quality }}%
        </div>
      </div>
      
      <div class="status-item">
        <div class="status-label">最后更新</div>
        <div class="last-update">{{ formatTime(currentDevice.lastUpdate) }}</div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 设备历史数据图表 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'

interface Device {
  id: string
  name: string
  status: 'online' | 'offline' | 'error'
  quality: number
  lastUpdate: Date
}

interface Props {
  title?: string
  devices?: Device[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '设备历史数据',
  devices: () => [
    {
      id: '1',
      name: '智能手环 Pro',
      status: 'online',
      quality: 98,
      lastUpdate: new Date()
    },
    {
      id: '2', 
      name: '血压监测仪',
      status: 'online',
      quality: 95,
      lastUpdate: new Date(Date.now() - 5 * 60 * 1000)
    },
    {
      id: '3',
      name: '体温传感器',
      status: 'offline',
      quality: 0,
      lastUpdate: new Date(Date.now() - 30 * 60 * 1000)
    }
  ]
})

const selectedDevice = ref(props.devices[0]?.id || '')
const chartRef = ref<HTMLElement>()

const currentDevice = computed(() => {
  return props.devices.find(device => device.id === selectedDevice.value) || props.devices[0]
})

const getStatusType = (status: string) => {
  const typeMap = {
    online: 'success',
    offline: 'info',
    error: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    online: '在线',
    offline: '离线',
    error: '异常'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getQualityClass = (quality: number) => {
  if (quality >= 95) return 'excellent'
  if (quality >= 85) return 'good'
  if (quality >= 70) return 'fair'
  return 'poor'
}

const formatTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return time.toLocaleDateString('zh-CN')
}

const generateMockData = () => {
  const data = []
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000)
    data.push({
      time: time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      heartRate: 60 + Math.random() * 40,
      temperature: 36 + Math.random() * 2,
      bloodPressure: 120 + Math.random() * 20,
      dataQuality: 80 + Math.random() * 20
    })
  }
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = generateMockData()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['心率', '体温', '血压', '数据质量'],
      textStyle: {
        color: '#999'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.time),
      axisLabel: {
        color: '#999',
        fontSize: 12
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '数值',
        position: 'left',
        axisLabel: {
          color: '#999'
        }
      },
      {
        type: 'value',
        name: '质量(%)',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '心率',
        type: 'line',
        yAxisIndex: 0,
        data: data.map(item => item.heartRate.toFixed(0)),
        smooth: true,
        lineStyle: {
          color: '#e53935',
          width: 2
        },
        itemStyle: {
          color: '#e53935'
        }
      },
      {
        name: '体温',
        type: 'line',
        yAxisIndex: 0,
        data: data.map(item => item.temperature.toFixed(1)),
        smooth: true,
        lineStyle: {
          color: '#ff9800',
          width: 2
        },
        itemStyle: {
          color: '#ff9800'
        }
      },
      {
        name: '血压',
        type: 'line',
        yAxisIndex: 0,
        data: data.map(item => item.bloodPressure.toFixed(0)),
        smooth: true,
        lineStyle: {
          color: '#2196f3',
          width: 2
        },
        itemStyle: {
          color: '#2196f3'
        }
      },
      {
        name: '数据质量',
        type: 'bar',
        yAxisIndex: 1,
        data: data.map(item => item.dataQuality.toFixed(0)),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(76, 175, 80, 0.8)' },
              { offset: 1, color: 'rgba(76, 175, 80, 0.3)' }
            ]
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
  
  const resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    chart.dispose()
  })
}

onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

watch(selectedDevice, () => {
  updateChart()
})
</script>

<style lang="scss" scoped>
.device-history-chart {
  width: 100%;
  height: 100%;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  
  .chart-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .device-selector {
    .el-select {
      width: 160px;
    }
  }
}

.device-status {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  
  .status-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--spacing-sm);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    
    .status-label {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .quality-indicator {
      font-size: var(--font-sm);
      font-weight: 600;
      font-family: var(--font-tech);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      
      &.excellent {
        background: rgba(76, 175, 80, 0.2);
        color: var(--success-500);
      }
      
      &.good {
        background: rgba(66, 165, 245, 0.2);
        color: var(--primary-500);
      }
      
      &.fair {
        background: rgba(255, 167, 38, 0.2);
        color: var(--warning-500);
      }
      
      &.poor {
        background: rgba(244, 67, 54, 0.2);
        color: var(--error-500);
      }
    }
    
    .last-update {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      font-family: var(--font-tech);
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 300px;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .device-status {
    grid-template-columns: 1fr;
  }
}
</style>