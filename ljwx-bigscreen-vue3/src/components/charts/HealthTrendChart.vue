<template>
  <div class="health-trend-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="chart-controls">
        <el-select 
          v-model="selectedMetric" 
          size="small" 
          style="width: 120px"
          @change="updateChart"
        >
          <el-option label="综合评分" value="overall" />
          <el-option label="心率" value="heartRate" />
          <el-option label="血氧" value="bloodOxygen" />
          <el-option label="血压" value="bloodPressure" />
          <el-option label="体温" value="temperature" />
        </el-select>
      </div>
    </div>
    
    <div class="trend-stats">
      <div class="stat-item">
        <div class="stat-label">当前值</div>
        <div class="stat-value" :class="getCurrentValueClass()">
          {{ currentValue }}
          <span class="stat-unit">{{ getUnit() }}</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-label">变化趋势</div>
        <div class="stat-trend" :class="trendClass">
          <el-icon><component :is="trendIcon" /></el-icon>
          <span>{{ trendText }}</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-label">24小时变化</div>
        <div class="stat-change" :class="changeClass">
          {{ changeValue }}{{ getUnit() }}
        </div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 健康趋势图 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { TrendingUp, TrendingDown, Minus } from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  trendData?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康趋势分析',
  height: '400px',
  trendData: () => []
})

// 响应式数据
const chartRef = ref<HTMLElement>()
const selectedMetric = ref('overall')
const currentValue = ref(85)
const trendDirection = ref<'up' | 'down' | 'stable'>('up')
const changeValue = ref(2.5)

// 计算属性
const trendClass = computed(() => ({
  'trend-up': trendDirection.value === 'up',
  'trend-down': trendDirection.value === 'down',
  'trend-stable': trendDirection.value === 'stable'
}))

const trendIcon = computed(() => {
  switch (trendDirection.value) {
    case 'up': return TrendingUp
    case 'down': return TrendingDown
    default: return Minus
  }
})

const trendText = computed(() => {
  switch (trendDirection.value) {
    case 'up': return '上升趋势'
    case 'down': return '下降趋势'
    default: return '稳定趋势'
  }
})

const changeClass = computed(() => ({
  'positive': changeValue.value > 0,
  'negative': changeValue.value < 0,
  'neutral': changeValue.value === 0
}))

// 生成图表数据
const generateTrendData = () => {
  const data = {
    xAxis: [] as string[],
    yData: [] as number[],
    targetLine: [] as number[]
  }
  
  const now = new Date()
  let baseValue = 80
  let targetValue = 85
  
  // 根据选中的指标调整基础值
  switch (selectedMetric.value) {
    case 'overall':
      baseValue = 80
      targetValue = 85
      break
    case 'heartRate':
      baseValue = 70
      targetValue = 75
      break
    case 'bloodOxygen':
      baseValue = 96
      targetValue = 98
      break
    case 'bloodPressure':
      baseValue = 120
      targetValue = 115
      break
    case 'temperature':
      baseValue = 36.5
      targetValue = 36.8
      break
  }
  
  for (let i = 23; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 3600000)
    data.xAxis.push(date.getHours() + ':00')
    
    // 模拟趋势数据
    const trend = Math.sin(i * 0.2) * 5 + Math.random() * 3 - 1.5
    const value = Math.max(0, baseValue + trend)
    
    data.yData.push(Math.round(value * 100) / 100)
    data.targetLine.push(targetValue)
  }
  
  // 更新当前值和趋势
  currentValue.value = data.yData[data.yData.length - 1]
  const prevValue = data.yData[data.yData.length - 2]
  changeValue.value = Math.round((currentValue.value - prevValue) * 100) / 100
  
  if (changeValue.value > 0.5) {
    trendDirection.value = 'up'
  } else if (changeValue.value < -0.5) {
    trendDirection.value = 'down'
  } else {
    trendDirection.value = 'stable'
  }
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = generateTrendData()
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const actual = params[0]
        const target = params[1]
        
        return `
          <div style="margin-bottom: 5px;">时间: ${actual.axisValue}</div>
          <div style="margin-bottom: 2px;">
            <span style="color: #00ff9d;">实际值: ${actual.value}${getUnit()}</span>
          </div>
          ${target ? `
          <div>
            <span style="color: #ffa726;">目标值: ${target.value}${getUnit()}</span>
          </div>
          ` : ''}
        `
      }
    },
    legend: {
      show: false
    },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLabel: {
        color: '#999',
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#333'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#999',
        fontSize: 12,
        formatter: `{value}${getUnit()}`
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    },
    series: [
      {
        name: '实际值',
        type: 'line',
        data: data.yData,
        lineStyle: {
          color: '#00ff9d',
          width: 3
        },
        itemStyle: {
          color: '#00ff9d',
          borderWidth: 2,
          borderColor: '#fff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 255, 157, 0.3)' },
              { offset: 1, color: 'rgba(0, 255, 157, 0.05)' }
            ]
          }
        },
        smooth: true,
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '目标值',
        type: 'line',
        data: data.targetLine,
        lineStyle: {
          color: '#ffa726',
          width: 2,
          type: 'dashed'
        },
        itemStyle: {
          color: '#ffa726'
        },
        symbol: 'none'
      }
    ]
  }
  
  chart.setOption(option)
  
  // 响应式调整
  const resizeChart = () => chart.resize()
  window.addEventListener('resize', resizeChart)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chart.dispose()
  })
}

// 工具方法
const getUnit = () => {
  const unitMap = {
    overall: '',
    heartRate: ' BPM',
    bloodOxygen: '%',
    bloodPressure: ' mmHg',
    temperature: '°C'
  }
  return unitMap[selectedMetric.value as keyof typeof unitMap] || ''
}

const getCurrentValueClass = () => {
  const value = currentValue.value
  
  switch (selectedMetric.value) {
    case 'overall':
      if (value >= 90) return 'excellent'
      if (value >= 80) return 'good'
      if (value >= 70) return 'fair'
      return 'poor'
      
    case 'heartRate':
      if (value >= 60 && value <= 80) return 'good'
      if (value >= 50 && value <= 90) return 'fair'
      return 'poor'
      
    case 'bloodOxygen':
      if (value >= 98) return 'excellent'
      if (value >= 95) return 'good'
      if (value >= 90) return 'fair'
      return 'poor'
      
    default:
      return 'good'
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.trendData, () => {
  updateChart()
}, { deep: true })
</script>

<style lang="scss" scoped>
.health-trend-chart {
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
}

.trend-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .stat-item {
    text-align: center;
    
    .stat-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-value {
      font-size: var(--font-xl);
      font-weight: 700;
      font-family: var(--font-tech);
      
      .stat-unit {
        font-size: var(--font-md);
        color: var(--text-secondary);
        font-weight: 400;
      }
      
      &.excellent {
        color: var(--success-500);
      }
      
      &.good {
        color: var(--primary-500);
      }
      
      &.fair {
        color: var(--warning-500);
      }
      
      &.poor {
        color: var(--error-500);
      }
    }
    
    .stat-trend {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-xs);
      font-size: var(--font-sm);
      font-weight: 600;
      
      &.trend-up {
        color: var(--success-500);
      }
      
      &.trend-down {
        color: var(--error-500);
      }
      
      &.trend-stable {
        color: var(--text-secondary);
      }
    }
    
    .stat-change {
      font-size: var(--font-md);
      font-weight: 600;
      font-family: var(--font-tech);
      
      &.positive {
        color: var(--success-500);
        
        &::before {
          content: '+';
        }
      }
      
      &.negative {
        color: var(--error-500);
      }
      
      &.neutral {
        color: var(--text-secondary);
      }
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .trend-stats {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
}
</style>