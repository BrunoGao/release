<template>
  <div class="alert-trend-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="chart-controls">
        <el-radio-group 
          v-model="selectedPeriod" 
          size="small"
          @change="updateChart"
        >
          <el-radio-button label="hour">小时</el-radio-button>
          <el-radio-button label="day">天</el-radio-button>
          <el-radio-button label="week">周</el-radio-button>
          <el-radio-button label="month">月</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 预警趋势图 -->
    </div>
    
    <div class="chart-legend">
      <div class="legend-item critical">
        <span class="legend-color"></span>
        <span class="legend-label">严重预警</span>
        <span class="legend-value">{{ alertStats.critical }}</span>
      </div>
      <div class="legend-item high">
        <span class="legend-color"></span>
        <span class="legend-label">高优先级</span>
        <span class="legend-value">{{ alertStats.high }}</span>
      </div>
      <div class="legend-item medium">
        <span class="legend-color"></span>
        <span class="legend-label">中等预警</span>
        <span class="legend-value">{{ alertStats.medium }}</span>
      </div>
      <div class="legend-item low">
        <span class="legend-color"></span>
        <span class="legend-label">低级预警</span>
        <span class="legend-value">{{ alertStats.low }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  alertData?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '预警趋势分析',
  height: '300px',
  alertData: () => []
})

// 响应式数据
const chartRef = ref<HTMLElement>()
const selectedPeriod = ref('day')

// 预警统计数据
const alertStats = reactive({
  critical: 12,
  high: 28,
  medium: 45,
  low: 23
})

// 生成模拟数据
const generateChartData = () => {
  const data = {
    xAxis: [] as string[],
    critical: [] as number[],
    high: [] as number[],
    medium: [] as number[],
    low: [] as number[]
  }
  
  const now = new Date()
  let periods = 24
  let unit = 'hour'
  
  switch (selectedPeriod.value) {
    case 'hour':
      periods = 24
      unit = 'hour'
      break
    case 'day':
      periods = 7
      unit = 'day'
      break
    case 'week':
      periods = 4
      unit = 'week'
      break
    case 'month':
      periods = 12
      unit = 'month'
      break
  }
  
  for (let i = periods - 1; i >= 0; i--) {
    let date: Date
    let label: string
    
    switch (unit) {
      case 'hour':
        date = new Date(now.getTime() - i * 3600000)
        label = date.getHours() + ':00'
        break
      case 'day':
        date = new Date(now.getTime() - i * 86400000)
        label = (date.getMonth() + 1) + '/' + date.getDate()
        break
      case 'week':
        date = new Date(now.getTime() - i * 604800000)
        label = '第' + (Math.floor((now.getTime() - date.getTime()) / 604800000) + 1) + '周'
        break
      case 'month':
        date = new Date(now.getFullYear(), now.getMonth() - i, 1)
        label = (date.getMonth() + 1) + '月'
        break
      default:
        date = now
        label = ''
    }
    
    data.xAxis.push(label)
    data.critical.push(Math.floor(Math.random() * 5) + 1)
    data.high.push(Math.floor(Math.random() * 8) + 2)
    data.medium.push(Math.floor(Math.random() * 12) + 5)
    data.low.push(Math.floor(Math.random() * 6) + 2)
  }
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = generateChartData()
  
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
        let html = `<div style="margin-bottom: 5px;">${params[0].axisValue}</div>`
        params.forEach((param: any) => {
          html += `
            <div style="display: flex; align-items: center; margin-bottom: 2px;">
              <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; margin-right: 8px;"></span>
              <span>${param.seriesName}: ${param.value}</span>
            </div>
          `
        })
        return html
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
        fontSize: 12
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
        name: '严重预警',
        type: 'line',
        data: data.critical,
        lineStyle: {
          color: '#ff6b6b',
          width: 3
        },
        itemStyle: {
          color: '#ff6b6b'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 107, 107, 0.4)' },
              { offset: 1, color: 'rgba(255, 107, 107, 0.05)' }
            ]
          }
        },
        smooth: true
      },
      {
        name: '高优先级',
        type: 'line',
        data: data.high,
        lineStyle: {
          color: '#ffa726',
          width: 2
        },
        itemStyle: {
          color: '#ffa726'
        },
        smooth: true
      },
      {
        name: '中等预警',
        type: 'line',
        data: data.medium,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        },
        itemStyle: {
          color: '#42a5f5'
        },
        smooth: true
      },
      {
        name: '低级预警',
        type: 'line',
        data: data.low,
        lineStyle: {
          color: '#66bb6a',
          width: 2
        },
        itemStyle: {
          color: '#66bb6a'
        },
        smooth: true
      }
    ]
  }
  
  chart.setOption(option)
  
  // 更新统计数据
  alertStats.critical = data.critical.reduce((sum, val) => sum + val, 0)
  alertStats.high = data.high.reduce((sum, val) => sum + val, 0)
  alertStats.medium = data.medium.reduce((sum, val) => sum + val, 0)
  alertStats.low = data.low.reduce((sum, val) => sum + val, 0)
  
  // 响应式调整
  const resizeChart = () => chart.resize()
  window.addEventListener('resize', resizeChart)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chart.dispose()
  })
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.alertData, () => {
  updateChart()
}, { deep: true })
</script>

<style lang="scss" scoped>
.alert-trend-chart {
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

.chart-container {
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.chart-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    background: var(--bg-elevated);
    border-radius: var(--radius-sm);
    
    .legend-color {
      width: 12px;
      height: 12px;
      border-radius: var(--radius-full);
    }
    
    .legend-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      flex: 1;
    }
    
    .legend-value {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
    }
    
    &.critical .legend-color {
      background: #ff6b6b;
    }
    
    &.high .legend-color {
      background: #ffa726;
    }
    
    &.medium .legend-color {
      background: #42a5f5;
    }
    
    &.low .legend-color {
      background: #66bb6a;
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .chart-legend {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>