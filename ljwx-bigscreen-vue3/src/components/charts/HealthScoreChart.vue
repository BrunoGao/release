<template>
  <div class="health-score-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="chart-controls">
        <el-radio-group 
          v-model="chartType" 
          size="small"
          @change="updateChart"
        >
          <el-radio-button label="line">趋势图</el-radio-button>
          <el-radio-button label="bar">柱状图</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <div class="score-summary">
      <div class="summary-item">
        <div class="summary-label">平均评分</div>
        <div class="summary-value average">{{ averageScore }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">最高评分</div>
        <div class="summary-value high">{{ maxScore }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">最低评分</div>
        <div class="summary-value low">{{ minScore }}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">评分趋势</div>
        <div class="summary-trend" :class="trendClass">
          <el-icon><component :is="trendIcon" /></el-icon>
          <span>{{ trendText }}</span>
        </div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 健康评分图 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { TrendingUp, TrendingDown, Minus } from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  scoreData?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康评分统计',
  height: '400px',
  scoreData: () => []
})

// 响应式数据
const chartRef = ref<HTMLElement>()
const chartType = ref('line')

// 评分统计
const averageScore = ref(85)
const maxScore = ref(96)
const minScore = ref(72)
const trend = ref<'up' | 'down' | 'stable'>('up')

// 计算属性
const trendClass = computed(() => ({
  'trend-up': trend.value === 'up',
  'trend-down': trend.value === 'down',
  'trend-stable': trend.value === 'stable'
}))

const trendIcon = computed(() => {
  switch (trend.value) {
    case 'up': return TrendingUp
    case 'down': return TrendingDown
    default: return Minus
  }
})

const trendText = computed(() => {
  switch (trend.value) {
    case 'up': return '上升趋势'
    case 'down': return '下降趋势'
    default: return '趋势平稳'
  }
})

// 生成图表数据
const generateChartData = () => {
  const data = {
    xAxis: [] as string[],
    scores: [] as number[]
  }
  
  const now = new Date()
  let totalScore = 0
  let maxVal = 0
  let minVal = 100
  
  for (let i = 13; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 86400000) // 每天
    data.xAxis.push((date.getMonth() + 1) + '/' + date.getDate())
    
    // 生成模拟评分数据 (70-100之间)
    const score = Math.floor(Math.random() * 30) + 70
    data.scores.push(score)
    
    totalScore += score
    maxVal = Math.max(maxVal, score)
    minVal = Math.min(minVal, score)
  }
  
  // 更新统计数据
  averageScore.value = Math.floor(totalScore / data.scores.length)
  maxScore.value = maxVal
  minScore.value = minVal
  
  // 计算趋势
  const firstHalf = data.scores.slice(0, 7).reduce((sum, val) => sum + val, 0) / 7
  const secondHalf = data.scores.slice(7).reduce((sum, val) => sum + val, 0) / 7
  
  if (secondHalf - firstHalf > 2) {
    trend.value = 'up'
  } else if (firstHalf - secondHalf > 2) {
    trend.value = 'down'
  } else {
    trend.value = 'stable'
  }
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = generateChartData()
  
  const baseOption = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0]
        return `
          <div style="margin-bottom: 5px;">日期: ${param.axisValue}</div>
          <div>
            <span style="color: #00ff9d;">健康评分: ${param.value}分</span>
          </div>
          <div style="margin-top: 5px; color: #999;">
            ${getScoreLevel(param.value)}
          </div>
        `
      }
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
      min: 60,
      max: 100,
      axisLabel: {
        color: '#999',
        fontSize: 12,
        formatter: '{value}分'
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    }
  }
  
  let seriesOption = {}
  
  if (chartType.value === 'line') {
    seriesOption = {
      series: [{
        type: 'line',
        data: data.scores,
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
              { offset: 0, color: 'rgba(0, 255, 157, 0.4)' },
              { offset: 1, color: 'rgba(0, 255, 157, 0.05)' }
            ]
          }
        },
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        markLine: {
          silent: true,
          lineStyle: {
            color: '#ffa726',
            type: 'dashed'
          },
          data: [
            { yAxis: 85, label: { formatter: '优秀线 (85)' } }
          ]
        }
      }]
    }
  } else {
    seriesOption = {
      series: [{
        type: 'bar',
        data: data.scores,
        itemStyle: {
          color: (params: any) => {
            const value = params.value
            if (value >= 90) return '#00ff9d'
            if (value >= 80) return '#66bb6a'
            if (value >= 70) return '#ffa726'
            return '#ff6b6b'
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '60%'
      }]
    }
  }
  
  const option = { ...baseOption, ...seriesOption }
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
const getScoreLevel = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  return '需改进'
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.scoreData, () => {
  updateChart()
}, { deep: true })
</script>

<style lang="scss" scoped>
.health-score-chart {
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

.score-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .summary-item {
    text-align: center;
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    
    .summary-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .summary-value {
      font-size: var(--font-xl);
      font-weight: 700;
      font-family: var(--font-tech);
      
      &.average {
        color: var(--primary-500);
      }
      
      &.high {
        color: var(--success-500);
      }
      
      &.low {
        color: var(--warning-500);
      }
    }
    
    .summary-trend {
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
  }
}

.chart-container {
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

@media (max-width: 1024px) {
  .score-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .score-summary {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
}
</style>