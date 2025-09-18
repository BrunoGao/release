<template>
  <div class="sleep-quality-analysis">
    <div class="analysis-header">
      <h4 class="analysis-title">睡眠质量分析</h4>
      <div class="analysis-controls">
        <el-radio-group v-model="timeRange" size="small" @change="updateData">
          <el-radio-button label="week">最近7天</el-radio-button>
          <el-radio-button label="month">最近30天</el-radio-button>
        </el-radio-group>
        <el-button size="small" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 睡眠概览 -->
    <div class="sleep-overview">
      <!-- 睡眠评分 -->
      <div class="sleep-score-card">
        <div class="score-header">
          <div class="score-icon">
            <el-icon><Moon /></el-icon>
          </div>
          <div class="score-info">
            <div class="score-title">睡眠质量评分</div>
            <div class="score-subtitle">基于多维度数据分析</div>
          </div>
        </div>
        
        <div class="score-display">
          <el-progress 
            type="circle" 
            :percentage="sleepScore.value" 
            :width="100"
            :stroke-width="8"
            :color="getSleepScoreColor(sleepScore.value)"
          >
            <template #default="{ percentage }">
              <span class="score-number">{{ percentage }}</span>
              <span class="score-unit">分</span>
            </template>
          </el-progress>
          
          <div class="score-details">
            <div class="score-level" :class="`level-${sleepScore.level}`">
              {{ sleepScore.levelText }}
            </div>
            <div class="score-trend" :class="`trend-${sleepScore.trend}`">
              <el-icon><component :is="getTrendIcon(sleepScore.trend)" /></el-icon>
              <span>{{ sleepScore.change }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 睡眠指标 -->
      <div class="sleep-metrics">
        <div 
          v-for="metric in sleepMetrics" 
          :key="metric.key"
          class="metric-item"
        >
          <div class="metric-icon" :style="{ color: metric.color }">
            <el-icon><component :is="metric.icon" /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">
              <span class="value-number">{{ metric.value }}</span>
              <span class="value-unit">{{ metric.unit }}</span>
            </div>
            <div class="metric-target">目标: {{ metric.target }}{{ metric.unit }}</div>
          </div>
          <div class="metric-progress">
            <el-progress 
              type="circle" 
              :percentage="metric.progress" 
              :width="60"
              :stroke-width="6"
              :color="metric.color"
              :show-text="false"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 睡眠阶段分析 -->
    <div class="sleep-stages">
      <div class="stages-header">
        <h5>睡眠阶段分析</h5>
        <div class="last-night-info">
          <span>昨晚睡眠时长: {{ lastNightData.totalSleep }}小时</span>
        </div>
      </div>
      
      <div class="stages-content">
        <div class="stages-chart" ref="stagesChartRef"></div>
        <div class="stages-breakdown">
          <div 
            v-for="stage in sleepStages" 
            :key="stage.type"
            class="stage-item"
          >
            <div class="stage-indicator" :style="{ background: stage.color }"></div>
            <div class="stage-info">
              <div class="stage-name">{{ stage.name }}</div>
              <div class="stage-duration">{{ stage.duration }}小时</div>
              <div class="stage-percentage">{{ stage.percentage }}%</div>
            </div>
            <div class="stage-quality" :class="`quality-${stage.quality}`">
              {{ getQualityText(stage.quality) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 睡眠趋势图表 -->
    <div class="sleep-trends">
      <div class="trends-header">
        <h5>睡眠趋势分析</h5>
        <el-radio-group v-model="trendsView" size="small">
          <el-radio-button label="duration">睡眠时长</el-radio-button>
          <el-radio-button label="efficiency">睡眠效率</el-radio-button>
          <el-radio-button label="deep_sleep">深度睡眠</el-radio-button>
        </el-radio-group>
      </div>
      <div class="trends-chart" ref="trendsChartRef"></div>
    </div>

    <!-- 睡眠质量因素 -->
    <div class="sleep-factors">
      <h5>影响睡眠质量的因素</h5>
      <div class="factors-grid">
        <div 
          v-for="factor in sleepFactors" 
          :key="factor.key"
          class="factor-card"
          :class="`factor-${factor.impact}`"
        >
          <div class="factor-header">
            <div class="factor-icon" :style="{ color: factor.color }">
              <el-icon><component :is="factor.icon" /></el-icon>
            </div>
            <div class="factor-name">{{ factor.name }}</div>
          </div>
          
          <div class="factor-value">{{ factor.value }}{{ factor.unit }}</div>
          
          <div class="factor-impact">
            <div class="impact-level" :class="`level-${factor.impact}`">
              {{ getImpactText(factor.impact) }}
            </div>
            <div class="impact-description">{{ factor.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 睡眠建议 -->
    <div class="sleep-recommendations">
      <h5>睡眠改善建议</h5>
      <div class="recommendations-list">
        <div 
          v-for="recommendation in recommendations" 
          :key="recommendation.id"
          class="recommendation-item"
          :class="`recommendation-${recommendation.priority}`"
        >
          <div class="recommendation-icon">
            <el-icon><component :is="recommendation.icon" /></el-icon>
          </div>
          <div class="recommendation-content">
            <div class="recommendation-title">{{ recommendation.title }}</div>
            <div class="recommendation-desc">{{ recommendation.description }}</div>
            <div class="recommendation-benefit">{{ recommendation.benefit }}</div>
          </div>
          <div class="recommendation-actions">
            <el-button size="small" text @click="dismissRecommendation(recommendation.id)">
              忽略
            </el-button>
            <el-button size="small" type="primary" @click="applyRecommendation(recommendation.id)">
              采纳
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 睡眠目标设置 -->
    <div class="sleep-goals">
      <div class="goals-header">
        <h5>睡眠目标</h5>
        <el-button size="small" @click="showGoalModal = true">
          <el-icon><Setting /></el-icon>
          设置目标
        </el-button>
      </div>
      
      <div class="goals-progress">
        <div 
          v-for="goal in sleepGoals" 
          :key="goal.type"
          class="goal-item"
        >
          <div class="goal-info">
            <div class="goal-name">{{ goal.name }}</div>
            <div class="goal-target">目标: {{ goal.target }}{{ goal.unit }}</div>
          </div>
          <div class="goal-progress">
            <el-progress 
              :percentage="goal.progress" 
              :color="getGoalColor(goal.progress)"
              :show-text="false"
            />
            <div class="progress-text">{{ goal.current }}/{{ goal.target }}{{ goal.unit }}</div>
          </div>
          <div class="goal-status" :class="`status-${goal.status}`">
            {{ getGoalStatusText(goal.status) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 目标设置模态框 -->
    <el-dialog 
      v-model="showGoalModal" 
      title="设置睡眠目标"
      width="500px"
    >
      <el-form :model="goalForm" label-width="120px">
        <el-form-item label="睡眠时长目标">
          <el-input-number 
            v-model="goalForm.sleepDuration" 
            :min="6" 
            :max="12" 
            :step="0.5"
          />
          <span style="margin-left: 8px;">小时</span>
        </el-form-item>
        <el-form-item label="就寝时间">
          <el-time-picker 
            v-model="goalForm.bedtime" 
            format="HH:mm"
            placeholder="选择就寝时间"
          />
        </el-form-item>
        <el-form-item label="起床时间">
          <el-time-picker 
            v-model="goalForm.wakeupTime" 
            format="HH:mm"
            placeholder="选择起床时间"
          />
        </el-form-item>
        <el-form-item label="睡眠效率目标">
          <el-input-number 
            v-model="goalForm.efficiency" 
            :min="70" 
            :max="100" 
            :step="1"
          />
          <span style="margin-left: 8px;">%</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showGoalModal = false">取消</el-button>
        <el-button type="primary" @click="saveGoals">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { 
  Refresh, Moon, Timer, TrendingUp, TrendingDown, Minus, Setting,
  Sunny, Cloudy, Warning, InfoFilled, CircleCheck
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface SleepMetric {
  key: string
  label: string
  value: number
  unit: string
  target: number
  progress: number
  color: string
  icon: any
}

interface SleepStage {
  type: string
  name: string
  duration: number
  percentage: number
  quality: 'excellent' | 'good' | 'fair' | 'poor'
  color: string
}

interface SleepFactor {
  key: string
  name: string
  value: number
  unit: string
  impact: 'positive' | 'neutral' | 'negative'
  description: string
  color: string
  icon: any
}

interface Recommendation {
  id: string
  title: string
  description: string
  benefit: string
  priority: 'high' | 'medium' | 'low'
  icon: any
}

interface SleepGoal {
  type: string
  name: string
  current: number
  target: number
  unit: string
  progress: number
  status: 'achieved' | 'on_track' | 'behind'
}

// 响应式数据
const timeRange = ref('week')
const trendsView = ref('duration')
const showGoalModal = ref(false)
const stagesChartRef = ref<HTMLElement>()
const trendsChartRef = ref<HTMLElement>()

// 睡眠评分
const sleepScore = ref({
  value: 82,
  level: 'good',
  levelText: '良好',
  trend: 'up',
  change: '+3分'
})

// 昨晚数据
const lastNightData = ref({
  totalSleep: 7.5,
  bedtime: '23:15',
  wakeupTime: '06:45',
  efficiency: 88
})

// 睡眠指标
const sleepMetrics = ref<SleepMetric[]>([
  {
    key: 'duration',
    label: '睡眠时长',
    value: 7.5,
    unit: '小时',
    target: 8,
    progress: 94,
    color: '#9c27b0',
    icon: Timer
  },
  {
    key: 'efficiency',
    label: '睡眠效率',
    value: 88,
    unit: '%',
    target: 85,
    progress: 100,
    color: '#67c23a',
    icon: TrendingUp
  },
  {
    key: 'deep_sleep',
    label: '深度睡眠',
    value: 1.8,
    unit: '小时',
    target: 2,
    progress: 90,
    color: '#409eff',
    icon: Moon
  },
  {
    key: 'rem_sleep',
    label: 'REM睡眠',
    value: 1.5,
    unit: '小时',
    target: 1.5,
    progress: 100,
    color: '#ffa726',
    icon: Sunny
  }
])

// 睡眠阶段
const sleepStages = ref<SleepStage[]>([
  {
    type: 'awake',
    name: '清醒',
    duration: 0.3,
    percentage: 4,
    quality: 'good',
    color: '#ff6b6b'
  },
  {
    type: 'light',
    name: '浅睡眠',
    duration: 3.9,
    percentage: 52,
    quality: 'good',
    color: '#4ecdc4'
  },
  {
    type: 'deep',
    name: '深度睡眠',
    duration: 1.8,
    percentage: 24,
    quality: 'excellent',
    color: '#409eff'
  },
  {
    type: 'rem',
    name: 'REM睡眠',
    duration: 1.5,
    percentage: 20,
    quality: 'good',
    color: '#ffa726'
  }
])

// 睡眠因素
const sleepFactors = ref<SleepFactor[]>([
  {
    key: 'room_temp',
    name: '房间温度',
    value: 22,
    unit: '°C',
    impact: 'positive',
    description: '温度适宜，有利于睡眠',
    color: '#67c23a',
    icon: Sunny
  },
  {
    key: 'caffeine',
    name: '咖啡因摄入',
    value: 2,
    unit: '杯',
    impact: 'negative',
    description: '下午摄入过多，影响入睡',
    color: '#ff6b6b',
    icon: Warning
  },
  {
    key: 'exercise',
    name: '运动时长',
    value: 45,
    unit: '分钟',
    impact: 'positive',
    description: '适量运动，改善睡眠质量',
    color: '#409eff',
    icon: TrendingUp
  },
  {
    key: 'screen_time',
    name: '睡前屏幕时间',
    value: 30,
    unit: '分钟',
    impact: 'negative',
    description: '建议减少睡前电子设备使用',
    color: '#ffa726',
    icon: Cloudy
  }
])

// 建议
const recommendations = ref<Recommendation[]>([
  {
    id: '1',
    title: '优化睡眠环境',
    description: '保持卧室温度在18-22°C，确保房间安静黑暗',
    benefit: '可提升睡眠质量15-20%',
    priority: 'high',
    icon: Moon
  },
  {
    id: '2',
    title: '建立睡前仪式',
    description: '睡前1小时避免使用电子设备，可以阅读或冥想',
    benefit: '有助于更快入睡',
    priority: 'medium',
    icon: InfoFilled
  },
  {
    id: '3',
    title: '规律作息时间',
    description: '每天在相同时间上床和起床，包括周末',
    benefit: '改善生物钟，提升整体睡眠质量',
    priority: 'high',
    icon: Timer
  }
])

// 睡眠目标
const sleepGoals = ref<SleepGoal[]>([
  {
    type: 'duration',
    name: '睡眠时长',
    current: 7.5,
    target: 8,
    unit: '小时',
    progress: 94,
    status: 'on_track'
  },
  {
    type: 'efficiency',
    name: '睡眠效率',
    current: 88,
    target: 85,
    unit: '%',
    progress: 100,
    status: 'achieved'
  },
  {
    type: 'bedtime_consistency',
    name: '作息规律',
    current: 6,
    target: 7,
    unit: '天/周',
    progress: 86,
    status: 'on_track'
  }
])

// 目标表单
const goalForm = ref({
  sleepDuration: 8,
  bedtime: null,
  wakeupTime: null,
  efficiency: 85
})

// 工具方法
const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return TrendingUp
    case 'down': return TrendingDown
    default: return Minus
  }
}

const getSleepScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#ffa726'
  return '#ff6b6b'
}

const getQualityText = (quality: string) => {
  const qualityMap = {
    excellent: '优秀',
    good: '良好',
    fair: '一般',
    poor: '较差'
  }
  return qualityMap[quality] || '未知'
}

const getImpactText = (impact: string) => {
  const impactMap = {
    positive: '有利',
    neutral: '中性',
    negative: '不利'
  }
  return impactMap[impact] || '未知'
}

const getGoalColor = (progress: number) => {
  if (progress >= 100) return '#67c23a'
  if (progress >= 80) return '#409eff'
  if (progress >= 60) return '#ffa726'
  return '#ff6b6b'
}

const getGoalStatusText = (status: string) => {
  const statusMap = {
    achieved: '已达成',
    on_track: '进展良好',
    behind: '需努力'
  }
  return statusMap[status] || '未知'
}

// 生成睡眠趋势数据
const generateSleepTrendsData = () => {
  const data = {
    dates: [] as string[],
    duration: [] as number[],
    efficiency: [] as number[],
    deepSleep: [] as number[]
  }
  
  const days = timeRange.value === 'week' ? 7 : 30
  const now = new Date()
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 86400000)
    data.dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
    
    // 生成模拟数据
    data.duration.push(Number((Math.random() * 2 + 6.5).toFixed(1))) // 6.5-8.5小时
    data.efficiency.push(Math.round(Math.random() * 20 + 75)) // 75-95%
    data.deepSleep.push(Number((Math.random() * 1 + 1.2).toFixed(1))) // 1.2-2.2小时
  }
  
  return data
}

// 更新睡眠阶段图表
const updateStagesChart = () => {
  if (!stagesChartRef.value) return
  
  const chart = echarts.init(stagesChartRef.value, 'health-tech')
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}小时 ({d}%)'
    },
    series: [{
      name: '睡眠阶段',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: sleepStages.value.map(stage => ({
        value: stage.duration,
        name: stage.name,
        itemStyle: {
          color: stage.color
        }
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}\n{d}%',
        color: '#fff'
      }
    }]
  }
  
  chart.setOption(option)
}

// 更新趋势图表
const updateTrendsChart = () => {
  if (!trendsChartRef.value) return
  
  const chart = echarts.init(trendsChartRef.value, 'health-tech')
  const data = generateSleepTrendsData()
  
  let seriesData = []
  let yAxisFormatter = ''
  
  switch (trendsView.value) {
    case 'duration':
      seriesData = data.duration
      yAxisFormatter = '{value}小时'
      break
    case 'efficiency':
      seriesData = data.efficiency
      yAxisFormatter = '{value}%'
      break
    case 'deep_sleep':
      seriesData = data.deepSleep
      yAxisFormatter = '{value}小时'
      break
  }
  
  const option = {
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
        const unit = trendsView.value === 'efficiency' ? '%' : '小时'
        return `日期: ${param.axisValue}<br/>${param.seriesName}: ${param.value}${unit}`
      }
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: {
        color: '#999'
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#999',
        formatter: yAxisFormatter
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    },
    series: [{
      name: trendsView.value === 'duration' ? '睡眠时长' : 
            trendsView.value === 'efficiency' ? '睡眠效率' : '深度睡眠',
      type: 'line',
      data: seriesData,
      lineStyle: {
        color: '#9c27b0',
        width: 3
      },
      itemStyle: {
        color: '#9c27b0'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(156, 39, 176, 0.4)' },
            { offset: 1, color: 'rgba(156, 39, 176, 0.1)' }
          ]
        }
      },
      smooth: true
    }]
  }
  
  chart.setOption(option)
}

// 事件处理
const updateData = () => {
  updateTrendsChart()
}

const refreshData = () => {
  // 模拟数据刷新
  sleepMetrics.value.forEach(metric => {
    const variation = Math.random() * 0.2 - 0.1
    metric.value = Math.max(0, metric.value + variation)
    metric.progress = Math.min(100, (metric.value / metric.target) * 100)
  })
  
  updateStagesChart()
  updateTrendsChart()
}

const dismissRecommendation = (id: string) => {
  const index = recommendations.value.findIndex(rec => rec.id === id)
  if (index > -1) {
    recommendations.value.splice(index, 1)
  }
}

const applyRecommendation = (id: string) => {
  // 应用建议的逻辑
  dismissRecommendation(id)
}

const saveGoals = () => {
  // 保存目标的逻辑
  showGoalModal.value = false
}

// 监听视图变化
watch(trendsView, () => {
  updateTrendsChart()
})

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateStagesChart()
    updateTrendsChart()
  })
})
</script>

<style lang="scss" scoped>
.sleep-quality-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow-y: auto;
  gap: var(--spacing-lg);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .analysis-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .analysis-controls {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.sleep-overview {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--spacing-lg);
  
  .sleep-score-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    border: 1px solid var(--border-light);
    
    .score-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-lg);
      
      .score-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(156, 39, 176, 0.1);
        color: #9c27b0;
        font-size: var(--font-lg);
      }
      
      .score-info {
        .score-title {
          font-size: var(--font-base);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .score-subtitle {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
    
    .score-display {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-lg);
      
      .score-number {
        font-size: var(--font-xl);
        font-weight: 700;
        color: var(--text-primary);
      }
      
      .score-unit {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
      
      .score-details {
        text-align: center;
        
        .score-level {
          font-size: var(--font-lg);
          font-weight: 600;
          margin-bottom: var(--spacing-sm);
          
          &.level-excellent {
            color: var(--success);
          }
          
          &.level-good {
            color: var(--info);
          }
          
          &.level-fair {
            color: var(--warning);
          }
          
          &.level-poor {
            color: var(--error);
          }
        }
        
        .score-trend {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-xs);
          font-size: var(--font-sm);
          
          &.trend-up {
            color: var(--success);
          }
          
          &.trend-down {
            color: var(--error);
          }
          
          &.trend-stable {
            color: var(--text-secondary);
          }
        }
      }
    }
  }
  
  .sleep-metrics {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
    
    .metric-item {
      background: var(--bg-elevated);
      border-radius: var(--radius-lg);
      padding: var(--spacing-lg);
      border: 1px solid var(--border-light);
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      
      .metric-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.1);
        font-size: var(--font-lg);
      }
      
      .metric-content {
        flex: 1;
        
        .metric-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .metric-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
          
          .value-unit {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            margin-left: var(--spacing-xs);
          }
        }
        
        .metric-target {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
      
      .metric-progress {
        flex-shrink: 0;
      }
    }
  }
}

.sleep-stages {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-light);
  
  .stages-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .last-night-info {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
  }
  
  .stages-content {
    display: grid;
    grid-template-columns: 1fr 200px;
    gap: var(--spacing-lg);
    
    .stages-chart {
      height: 200px;
    }
    
    .stages-breakdown {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
      
      .stage-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        
        .stage-indicator {
          width: 12px;
          height: 12px;
          border-radius: var(--radius-full);
        }
        
        .stage-info {
          flex: 1;
          
          .stage-name {
            font-size: var(--font-sm);
            color: var(--text-primary);
            font-weight: 600;
          }
          
          .stage-duration {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
          
          .stage-percentage {
            font-size: var(--font-xs);
            color: var(--text-tertiary);
          }
        }
        
        .stage-quality {
          font-size: var(--font-xs);
          padding: 2px 6px;
          border-radius: var(--radius-sm);
          
          &.quality-excellent {
            background: rgba(103, 194, 58, 0.2);
            color: var(--success);
          }
          
          &.quality-good {
            background: rgba(64, 158, 255, 0.2);
            color: var(--info);
          }
          
          &.quality-fair {
            background: rgba(255, 167, 38, 0.2);
            color: var(--warning);
          }
          
          &.quality-poor {
            background: rgba(255, 107, 107, 0.2);
            color: var(--error);
          }
        }
      }
    }
  }
}

.sleep-trends {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-light);
  
  .trends-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .trends-chart {
    height: 250px;
  }
}

.sleep-factors {
  h5 {
    font-size: var(--font-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg);
  }
  
  .factors-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-md);
    
    .factor-card {
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      padding: var(--spacing-md);
      border: 1px solid var(--border-light);
      border-left: 4px solid;
      
      &.factor-positive {
        border-left-color: var(--success);
      }
      
      &.factor-neutral {
        border-left-color: var(--info);
      }
      
      &.factor-negative {
        border-left-color: var(--error);
      }
      
      .factor-header {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        margin-bottom: var(--spacing-md);
        
        .factor-icon {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .factor-name {
          font-size: var(--font-base);
          font-weight: 600;
          color: var(--text-primary);
        }
      }
      
      .factor-value {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: var(--spacing-sm);
      }
      
      .factor-impact {
        .impact-level {
          font-size: var(--font-sm);
          font-weight: 600;
          margin-bottom: var(--spacing-xs);
          
          &.level-positive {
            color: var(--success);
          }
          
          &.level-neutral {
            color: var(--info);
          }
          
          &.level-negative {
            color: var(--error);
          }
        }
        
        .impact-description {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.sleep-recommendations {
  h5 {
    font-size: var(--font-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg);
  }
  
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .recommendation-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      border-left: 4px solid;
      
      &.recommendation-high {
        border-left-color: var(--error);
      }
      
      &.recommendation-medium {
        border-left-color: var(--warning);
      }
      
      &.recommendation-low {
        border-left-color: var(--info);
      }
      
      .recommendation-icon {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-md);
        background: rgba(156, 39, 176, 0.1);
        color: #9c27b0;
        flex-shrink: 0;
      }
      
      .recommendation-content {
        flex: 1;
        
        .recommendation-title {
          font-size: var(--font-base);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .recommendation-desc {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .recommendation-benefit {
          font-size: var(--font-sm);
          color: var(--success);
          font-style: italic;
        }
      }
      
      .recommendation-actions {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        flex-shrink: 0;
      }
    }
  }
}

.sleep-goals {
  .goals-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .goals-progress {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .goal-item {
      display: grid;
      grid-template-columns: 150px 1fr 100px;
      gap: var(--spacing-md);
      align-items: center;
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .goal-info {
        .goal-name {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .goal-target {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .goal-progress {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        
        .progress-text {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          white-space: nowrap;
        }
      }
      
      .goal-status {
        font-size: var(--font-sm);
        font-weight: 600;
        text-align: center;
        
        &.status-achieved {
          color: var(--success);
        }
        
        &.status-on_track {
          color: var(--info);
        }
        
        &.status-behind {
          color: var(--warning);
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .sleep-overview {
    grid-template-columns: 1fr;
    
    .sleep-metrics {
      grid-template-columns: 1fr;
    }
  }
  
  .stages-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analysis-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .trends-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .factors-grid {
    grid-template-columns: 1fr;
  }
  
  .goal-item {
    grid-template-columns: 1fr !important;
    gap: var(--spacing-sm) !important;
    text-align: center;
  }
}
</style>