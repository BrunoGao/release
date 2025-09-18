<template>
  <div class="score-view">
    <div class="view-header">
      <h2 class="view-title">健康评分详情</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
        />
        <el-button size="small" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="score-overview">
      <div class="overall-score">
        <div class="score-circle">
          <svg viewBox="0 0 42 42" class="score-svg">
            <circle
              cx="21"
              cy="21"
              r="15.915"
              fill="transparent"
              stroke="var(--bg-secondary)"
              stroke-width="3"
            />
            <circle
              cx="21"
              cy="21"
              r="15.915"
              fill="transparent"
              :stroke="getScoreColor(overallScore)"
              stroke-width="3"
              stroke-linecap="round"
              :stroke-dasharray="`${overallScore} 100`"
              transform="rotate(-90 21 21)"
            />
          </svg>
          <div class="score-text">{{ overallScore }}</div>
        </div>
        <div class="score-info">
          <h3 class="score-title">综合健康评分</h3>
          <p class="score-description">{{ getScoreDescription(overallScore) }}</p>
          <div class="score-trend" :class="scoreTrend">
            <el-icon><component :is="getTrendIcon(scoreTrend)" /></el-icon>
            <span>{{ getTrendText(scoreTrend) }}</span>
          </div>
        </div>
      </div>

      <div class="score-breakdown">
        <div class="breakdown-item" v-for="item in scoreBreakdown" :key="item.category">
          <div class="breakdown-header">
            <span class="breakdown-label">{{ item.label }}</span>
            <span class="breakdown-score" :class="getScoreLevel(item.score)">{{ item.score }}</span>
          </div>
          <div class="breakdown-bar">
            <div 
              class="breakdown-fill" 
              :style="{ width: item.score + '%' }"
              :class="getScoreLevel(item.score)"
            ></div>
          </div>
          <div class="breakdown-description">{{ item.description }}</div>
        </div>
      </div>
    </div>

    <div class="score-history">
      <div class="history-header">
        <h4>评分历史趋势</h4>
        <el-radio-group v-model="historyPeriod" size="small">
          <el-radio-button label="week">近7天</el-radio-button>
          <el-radio-button label="month">近30天</el-radio-button>
          <el-radio-button label="quarter">近3个月</el-radio-button>
        </el-radio-group>
      </div>
      <div class="chart-container" ref="chartRef"></div>
    </div>

    <div class="score-factors">
      <div class="factors-header">
        <h4>影响因素分析</h4>
      </div>
      <div class="factors-grid">
        <div class="factor-item" v-for="factor in scoreFactors" :key="factor.name">
          <div class="factor-icon">
            <el-icon><component :is="factor.icon" /></el-icon>
          </div>
          <div class="factor-content">
            <div class="factor-name">{{ factor.name }}</div>
            <div class="factor-impact" :class="factor.impact">
              {{ getImpactText(factor.impact) }}
            </div>
            <div class="factor-suggestion">{{ factor.suggestion }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Refresh, 
  TrendUp, 
  TrendDown, 
  Minus,
  Monitor,
  Timer,
  Cpu,
  Setting
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
  new Date()
])
const historyPeriod = ref('month')
const chartRef = ref<HTMLElement>()

const overallScore = ref(82)
const scoreTrend = ref('up') // up, down, stable

const scoreBreakdown = ref([
  {
    category: 'vital',
    label: '生命体征',
    score: 85,
    description: '心率、血压、体温等指标良好'
  },
  {
    category: 'activity', 
    label: '运动活跃',
    score: 78,
    description: '日常活动量适中，建议增加'
  },
  {
    category: 'sleep',
    label: '睡眠质量',
    score: 90,
    description: '睡眠时长和质量优秀'
  },
  {
    category: 'mental',
    label: '心理健康',
    score: 76,
    description: '压力管理需要关注'
  }
])

const scoreFactors = ref([
  {
    name: '规律作息',
    icon: Timer,
    impact: 'positive',
    suggestion: '保持当前良好的作息习惯'
  },
  {
    name: '运动频率',
    icon: TrendUp,
    impact: 'neutral',
    suggestion: '建议增加运动频率和强度'
  },
  {
    name: '压力水平',
    icon: Cpu,
    impact: 'negative',
    suggestion: '需要更好的压力管理技巧'
  },
  {
    name: '环境因素',
    icon: Setting,
    impact: 'positive',
    suggestion: '当前环境有利于健康'
  }
])

const getScoreColor = (score: number) => {
  if (score >= 85) return 'var(--success-500)'
  if (score >= 70) return 'var(--primary-500)'
  if (score >= 60) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getScoreDescription = (score: number) => {
  if (score >= 85) return '您的健康状况非常优秀，请继续保持！'
  if (score >= 70) return '您的健康状况良好，有一些需要改善的地方'
  if (score >= 60) return '您的健康状况一般，建议加强健康管理'
  return '您的健康状况需要重点关注和改善'
}

const getScoreLevel = (score: number) => {
  if (score >= 85) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 60) return 'fair'
  return 'poor'
}

const getTrendIcon = (trend: string) => {
  const iconMap = {
    up: TrendUp,
    down: TrendDown,
    stable: Minus
  }
  return iconMap[trend as keyof typeof iconMap] || Minus
}

const getTrendText = (trend: string) => {
  const textMap = {
    up: '评分上升',
    down: '评分下降',
    stable: '评分稳定'
  }
  return textMap[trend as keyof typeof textMap] || '评分稳定'
}

const getImpactText = (impact: string) => {
  const textMap = {
    positive: '积极影响',
    negative: '负面影响',
    neutral: '中性影响'
  }
  return textMap[impact as keyof typeof textMap] || '中性影响'
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  
  // 生成模拟数据
  const days = historyPeriod.value === 'week' ? 7 : historyPeriod.value === 'month' ? 30 : 90
  const dates = []
  const scores = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    scores.push(70 + Math.random() * 25)
  }
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        color: '#999'
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        color: '#999'
      }
    },
    series: [
      {
        type: 'line',
        data: scores,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 3
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

const refreshData = () => {
  // 刷新数据逻辑
}

watch(historyPeriod, () => {
  updateChart()
})

onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})
</script>

<style lang="scss" scoped>
.score-view {
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  min-height: 100vh;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  
  .view-title {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }
}

.score-overview {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  
  .overall-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: var(--spacing-xl);
    
    .score-circle {
      position: relative;
      width: 120px;
      height: 120px;
      margin-bottom: var(--spacing-lg);
      
      .score-svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }
      
      .score-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: var(--font-xxl);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
      }
    }
    
    .score-info {
      text-align: center;
      
      .score-title {
        font-size: var(--font-lg);
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 var(--spacing-sm) 0;
      }
      
      .score-description {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-md);
      }
      
      .score-trend {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--spacing-xs);
        font-size: var(--font-sm);
        
        &.up {
          color: var(--success-500);
        }
        
        &.down {
          color: var(--error-500);
        }
        
        &.stable {
          color: var(--text-secondary);
        }
      }
    }
  }
  
  .score-breakdown {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    
    .breakdown-item {
      margin-bottom: var(--spacing-lg);
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .breakdown-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-xs);
        
        .breakdown-label {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
        }
        
        .breakdown-score {
          font-size: var(--font-sm);
          font-weight: 700;
          font-family: var(--font-tech);
          
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
      }
      
      .breakdown-bar {
        width: 100%;
        height: 8px;
        background: var(--bg-secondary);
        border-radius: var(--radius-full);
        overflow: hidden;
        margin-bottom: var(--spacing-xs);
        
        .breakdown-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width 0.3s ease;
          
          &.excellent {
            background: linear-gradient(90deg, #66bb6a, #4caf50);
          }
          
          &.good {
            background: linear-gradient(90deg, #42a5f5, #2196f3);
          }
          
          &.fair {
            background: linear-gradient(90deg, #ffa726, #ff9800);
          }
          
          &.poor {
            background: linear-gradient(90deg, #ff6b6b, #f44336);
          }
        }
      }
      
      .breakdown-description {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
    }
  }
}

.score-history {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  
  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .chart-container {
    height: 200px;
  }
}

.score-factors {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .factors-header {
    margin-bottom: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .factors-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
    
    .factor-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .factor-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        flex-shrink: 0;
      }
      
      .factor-content {
        flex: 1;
        
        .factor-name {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .factor-impact {
          font-size: var(--font-xs);
          font-weight: 500;
          margin-bottom: var(--spacing-xs);
          
          &.positive {
            color: var(--success-500);
          }
          
          &.negative {
            color: var(--error-500);
          }
          
          &.neutral {
            color: var(--warning-500);
          }
        }
        
        .factor-suggestion {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .score-overview {
    grid-template-columns: 1fr;
  }
  
  .factors-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
}
</style>