<template>
  <div class="vital-sign-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="vital-status" :class="getStatusClass(vitalData.status)">
        <span class="status-indicator"></span>
        <span class="status-text">{{ getStatusText(vitalData.status) }}</span>
      </div>
    </div>
    
    <div class="vital-metrics">
      <div class="metric-item heartrate">
        <div class="metric-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ vitalData.heartRate }}</div>
          <div class="metric-label">心率 (bpm)</div>
          <div class="metric-trend" :class="vitalData.heartRateTrend">
            <el-icon v-if="vitalData.heartRateTrend === 'up'"><CaretTop /></el-icon>
            <el-icon v-else-if="vitalData.heartRateTrend === 'down'"><CaretBottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
          </div>
        </div>
      </div>
      
      <div class="metric-item bloodpressure">
        <div class="metric-icon">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ vitalData.bloodPressure }}</div>
          <div class="metric-label">血压 (mmHg)</div>
          <div class="metric-trend" :class="vitalData.bloodPressureTrend">
            <el-icon v-if="vitalData.bloodPressureTrend === 'up'"><CaretTop /></el-icon>
            <el-icon v-else-if="vitalData.bloodPressureTrend === 'down'"><CaretBottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
          </div>
        </div>
      </div>
      
      <div class="metric-item temperature">
        <div class="metric-icon">
          <el-icon><Sunny /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ vitalData.temperature }}°C</div>
          <div class="metric-label">体温</div>
          <div class="metric-trend" :class="vitalData.temperatureTrend">
            <el-icon v-if="vitalData.temperatureTrend === 'up'"><CaretTop /></el-icon>
            <el-icon v-else-if="vitalData.temperatureTrend === 'down'"><CaretBottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
          </div>
        </div>
      </div>
      
      <div class="metric-item oxygen">
        <div class="metric-icon">
          <el-icon><Lightning /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ vitalData.bloodOxygen }}%</div>
          <div class="metric-label">血氧</div>
          <div class="metric-trend" :class="vitalData.bloodOxygenTrend">
            <el-icon v-if="vitalData.bloodOxygenTrend === 'up'"><CaretTop /></el-icon>
            <el-icon v-else-if="vitalData.bloodOxygenTrend === 'down'"><CaretBottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 生命体征趋势图 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  TrendCharts, 
  Timer, 
  Sunny, 
  Lightning, 
  CaretTop, 
  CaretBottom, 
  Minus 
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '生命体征监测',
  height: '400px',
  userId: ''
})

const chartRef = ref<HTMLElement>()

// 生命体征数据
const vitalData = reactive({
  status: 'normal',
  heartRate: 72,
  heartRateTrend: 'stable',
  bloodPressure: '120/80',
  bloodPressureTrend: 'stable',
  temperature: 36.5,
  temperatureTrend: 'stable',
  bloodOxygen: 98,
  bloodOxygenTrend: 'stable'
})

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  
  // 生成24小时生命体征数据
  const timeData = []
  const heartRateData = []
  const temperatureData = []
  const oxygenData = []
  
  for (let i = 0; i < 24; i++) {
    timeData.push(i.toString().padStart(2, '0') + ':00')
    heartRateData.push(65 + Math.random() * 20)
    temperatureData.push(36.2 + Math.random() * 0.8)
    oxygenData.push(95 + Math.random() * 5)
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
      data: ['心率', '体温', '血氧'],
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
        name: '心率/血氧',
        position: 'left',
        axisLabel: {
          color: '#999',
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '体温',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}°C'
        }
      }
    ],
    series: [
      {
        name: '心率',
        type: 'line',
        yAxisIndex: 0,
        data: heartRateData,
        smooth: true,
        lineStyle: {
          color: '#ff6b6b',
          width: 2
        },
        itemStyle: {
          color: '#ff6b6b'
        }
      },
      {
        name: '体温',
        type: 'line',
        yAxisIndex: 1,
        data: temperatureData,
        smooth: true,
        lineStyle: {
          color: '#ffa726',
          width: 2
        },
        itemStyle: {
          color: '#ffa726'
        }
      },
      {
        name: '血氧',
        type: 'line',
        yAxisIndex: 0,
        data: oxygenData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        },
        itemStyle: {
          color: '#42a5f5'
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

const getStatusClass = (status: string) => {
  const classMap = {
    normal: 'normal',
    warning: 'warning',
    critical: 'critical'
  }
  return classMap[status as keyof typeof classMap] || 'normal'
}

const getStatusText = (status: string) => {
  const textMap = {
    normal: '正常',
    warning: '预警',
    critical: '异常'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})
</script>

<style lang="scss" scoped>
.vital-sign-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .chart-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .vital-status {
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

.vital-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .metric-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    
    .metric-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 18px;
    }
    
    .metric-content {
      flex: 1;
      
      .metric-value {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
        margin-bottom: 2px;
      }
      
      .metric-label {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
      
      .metric-trend {
        position: absolute;
        right: var(--spacing-sm);
        top: var(--spacing-sm);
        
        &.up {
          color: var(--error-500);
        }
        
        &.down {
          color: var(--success-500);
        }
        
        &.stable {
          color: var(--text-secondary);
        }
      }
    }
    
    position: relative;
    
    &.heartrate .metric-icon {
      background: linear-gradient(135deg, #ff6b6b, #f44336);
    }
    
    &.bloodpressure .metric-icon {
      background: linear-gradient(135deg, #ffa726, #ff9800);
    }
    
    &.temperature .metric-icon {
      background: linear-gradient(135deg, #42a5f5, #2196f3);
    }
    
    &.oxygen .metric-icon {
      background: linear-gradient(135deg, #66bb6a, #4caf50);
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 200px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

@media (max-width: 1024px) {
  .vital-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .vital-metrics {
    grid-template-columns: 1fr;
  }
}
</style>