<template>
  <div class="time-distribution-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="chart-controls">
        <el-radio-group v-model="viewType" size="small" @change="updateChart">
          <el-radio-button label="daily">日分布</el-radio-button>
          <el-radio-button label="weekly">周分布</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <div class="distribution-stats">
      <div class="stat-item">
        <div class="stat-label">活跃高峰</div>
        <div class="stat-value peak">{{ peakTime }}</div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">活跃低谷</div>
        <div class="stat-value low">{{ lowTime }}</div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">平均活跃度</div>
        <div class="stat-value average">{{ averageActivity }}%</div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 时间分布图表 -->
    </div>
    
    <div class="activity-legend">
      <div class="legend-item high">
        <span class="legend-color"></span>
        <span class="legend-label">高活跃</span>
        <span class="legend-range">80-100%</span>
      </div>
      
      <div class="legend-item medium">
        <span class="legend-color"></span>
        <span class="legend-label">中活跃</span>
        <span class="legend-range">50-80%</span>
      </div>
      
      <div class="legend-item low">
        <span class="legend-color"></span>
        <span class="legend-label">低活跃</span>
        <span class="legend-range">0-50%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  timeRange?: 'daily' | 'weekly'
}

const props = withDefaults(defineProps<Props>(), {
  title: '时间分布分析',
  timeRange: 'daily'
})

const viewType = ref(props.timeRange)
const chartRef = ref<HTMLElement>()

const peakTime = ref('14:00-16:00')
const lowTime = ref('02:00-06:00')
const averageActivity = ref(68)

const generateDailyData = () => {
  const data = []
  const hours = Array.from({ length: 24 }, (_, i) => i)
  
  hours.forEach(hour => {
    // 模拟活跃度数据，工作时间和晚上较高
    let activity = 20 + Math.random() * 30
    
    if (hour >= 9 && hour <= 17) {
      activity = 60 + Math.random() * 30 // 工作时间
    } else if (hour >= 19 && hour <= 22) {
      activity = 70 + Math.random() * 25 // 晚上娱乐时间
    } else if (hour >= 2 && hour <= 6) {
      activity = Math.random() * 20 // 深夜时间
    }
    
    data.push({
      hour: `${hour.toString().padStart(2, '0')}:00`,
      activity: Math.round(activity),
      category: activity > 80 ? 'high' : activity > 50 ? 'medium' : 'low'
    })
  })
  
  return data
}

const generateWeeklyData = () => {
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const data = []
  
  weekdays.forEach((day, index) => {
    // 模拟周分布数据，工作日较高，周末不同
    let activity = 40 + Math.random() * 30
    
    if (index < 5) { // 工作日
      activity = 65 + Math.random() * 25
    } else if (index === 5) { // 周六
      activity = 75 + Math.random() * 20
    } else { // 周日
      activity = 55 + Math.random() * 25
    }
    
    data.push({
      day,
      activity: Math.round(activity),
      category: activity > 80 ? 'high' : activity > 50 ? 'medium' : 'low'
    })
  })
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = viewType.value === 'daily' ? generateDailyData() : generateWeeklyData()
  
  const getColor = (category: string) => {
    const colorMap = {
      high: '#e53935',
      medium: '#ffa726', 
      low: '#66bb6a'
    }
    return colorMap[category as keyof typeof colorMap] || '#999'
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        const time = viewType.value === 'daily' ? data.name : data.name
        return `${time}<br/>活跃度: ${data.value}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => viewType.value === 'daily' ? item.hour : item.day),
      axisLabel: {
        color: '#999',
        fontSize: 12,
        rotate: viewType.value === 'daily' ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: '活跃度(%)',
      max: 100,
      axisLabel: {
        color: '#999',
        formatter: '{value}%'
      }
    },
    series: [
      {
        type: 'bar',
        data: data.map(item => ({
          value: item.activity,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: getColor(item.category) },
                { offset: 1, color: getColor(item.category) + '80' }
              ]
            }
          }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        animationDelay: (idx: number) => idx * 20
      }
    ],
    animationEasing: 'elasticOut',
    animationDelayUpdate: (idx: number) => idx * 5
  }
  
  chart.setOption(option)
  
  // 更新统计信息
  if (viewType.value === 'daily') {
    const maxActivity = Math.max(...data.map(d => d.activity))
    const minActivity = Math.min(...data.map(d => d.activity))
    const maxHour = data.find(d => d.activity === maxActivity)?.hour
    const minHour = data.find(d => d.activity === minActivity)?.hour
    
    peakTime.value = maxHour || '14:00'
    lowTime.value = minHour || '04:00'
  } else {
    const maxActivity = Math.max(...data.map(d => d.activity))
    const minActivity = Math.min(...data.map(d => d.activity))
    const maxDay = data.find(d => d.activity === maxActivity)?.day
    const minDay = data.find(d => d.activity === minActivity)?.day
    
    peakTime.value = maxDay || '周六'
    lowTime.value = minDay || '周日'
  }
  
  averageActivity.value = Math.round(data.reduce((sum, d) => sum + d.activity, 0) / data.length)
  
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

watch(viewType, () => {
  updateChart()
})
</script>

<style lang="scss" scoped>
.time-distribution-chart {
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
}

.distribution-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  
  .stat-item {
    text-align: center;
    padding: var(--spacing-sm);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    
    .stat-label {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-value {
      font-size: var(--font-md);
      font-weight: 700;
      font-family: var(--font-tech);
      
      &.peak {
        color: var(--error-500);
      }
      
      &.low {
        color: var(--primary-500);
      }
      
      &.average {
        color: var(--warning-500);
      }
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 300px;
}

.activity-legend {
  display: flex;
  justify-content: center;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-md);
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    
    .legend-color {
      width: 12px;
      height: 12px;
      border-radius: var(--radius-sm);
    }
    
    .legend-label {
      font-size: var(--font-sm);
      color: var(--text-primary);
      font-weight: 500;
    }
    
    .legend-range {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      font-family: var(--font-tech);
    }
    
    &.high .legend-color {
      background: var(--error-500);
    }
    
    &.medium .legend-color {
      background: var(--warning-500);
    }
    
    &.low .legend-color {
      background: var(--success-500);
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .distribution-stats {
    grid-template-columns: 1fr;
  }
  
  .activity-legend {
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-sm);
  }
}
</style>