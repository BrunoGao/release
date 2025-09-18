<template>
  <div class="mental-health-dashboard">
    <div class="dashboard-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Opportunity />
        </el-icon>
        <h3 class="dashboard-title">{{ title }}</h3>
      </div>
      
      <div class="dashboard-controls">
        <el-button-group size="small">
          <el-button @click="openAssessment">
            <el-icon><DocumentAdd /></el-icon>
            心理评估
          </el-button>
          <el-button @click="openMoodTracker">
            <el-icon><EditPen /></el-icon>
            情绪记录
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 心理健康概览 -->
    <div class="mental-overview">
      <div class="overview-card main-score">
        <div class="score-container">
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
                :stroke="getMentalScoreColor()"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${mentalData.overallScore} 100`"
                transform="rotate(-90 21 21)"
              />
            </svg>
            <div class="score-text">{{ mentalData.overallScore }}</div>
          </div>
          <div class="score-info">
            <div class="score-label">心理健康评分</div>
            <div class="score-level" :class="getMentalScoreLevel()">
              {{ getMentalScoreText() }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="overview-card mood-status">
        <div class="card-header">
          <el-icon><Sunny /></el-icon>
          <span>当前情绪</span>
        </div>
        <div class="mood-display">
          <div class="mood-emoji">{{ getCurrentMoodEmoji() }}</div>
          <div class="mood-text">{{ mentalData.currentMood }}</div>
          <div class="mood-trend" :class="mentalData.moodTrend">
            <el-icon>
              <component :is="getMoodTrendIcon()" />
            </el-icon>
            <span>{{ getMoodTrendText() }}</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card stress-level">
        <div class="card-header">
          <el-icon><Warning /></el-icon>
          <span>压力水平</span>
        </div>
        <div class="stress-meter">
          <div class="stress-bar">
            <div 
              class="stress-fill" 
              :style="{ width: (mentalData.stressLevel / 10 * 100) + '%' }"
              :class="getStressLevelClass()"
            ></div>
          </div>
          <div class="stress-value">{{ mentalData.stressLevel }}/10</div>
          <div class="stress-description">{{ getStressDescription() }}</div>
        </div>
      </div>
      
      <div class="overview-card sleep-quality">
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>睡眠质量</span>
        </div>
        <div class="sleep-score">
          <div class="sleep-ring">
            <div class="ring-progress" :style="{ '--progress': mentalData.sleepQuality + '%' }">
              <span class="sleep-value">{{ mentalData.sleepQuality }}%</span>
            </div>
          </div>
          <div class="sleep-status">{{ getSleepQualityText() }}</div>
        </div>
      </div>
    </div>
    
    <!-- 情绪趋势图表 -->
    <div class="mood-trends">
      <div class="trends-header">
        <h4>情绪趋势分析</h4>
        <el-radio-group v-model="trendPeriod" size="small">
          <el-radio-button label="week">近7天</el-radio-button>
          <el-radio-button label="month">近30天</el-radio-button>
        </el-radio-group>
      </div>
      <div class="chart-container" ref="moodChartRef"></div>
    </div>
    
    <!-- 心理健康活动 -->
    <div class="mental-activities">
      <div class="activities-header">
        <h4>推荐活动</h4>
        <el-button size="small" type="text" @click="viewAllActivities">
          查看全部
        </el-button>
      </div>
      
      <div class="activities-grid">
        <div 
          v-for="activity in mentalActivities" 
          :key="activity.id"
          class="activity-card"
          :class="activity.type"
          @click="startActivity(activity)"
        >
          <div class="activity-icon">
            <el-icon>
              <component :is="getActivityIcon(activity.type)" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-description">{{ activity.description }}</div>
            <div class="activity-duration">{{ activity.duration }}</div>
          </div>
          <div class="activity-status" v-if="activity.completed">
            <el-icon class="completed-icon">
              <CircleCheck />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 心理咨询建议 -->
    <div class="counseling-suggestions">
      <div class="suggestions-header">
        <h4>专业建议</h4>
        <el-tag :type="getSuggestionUrgency()" size="small">
          {{ getSuggestionLevel() }}
        </el-tag>
      </div>
      
      <div class="suggestions-list">
        <div 
          v-for="suggestion in counselingSuggestions" 
          :key="suggestion.id"
          class="suggestion-item"
          :class="suggestion.urgency"
        >
          <div class="suggestion-icon">
            <el-icon>
              <component :is="getSuggestionIcon(suggestion.type)" />
            </el-icon>
          </div>
          <div class="suggestion-content">
            <div class="suggestion-title">{{ suggestion.title }}</div>
            <div class="suggestion-desc">{{ suggestion.description }}</div>
            <div class="suggestion-actions">
              <el-button 
                v-for="action in suggestion.actions" 
                :key="action"
                size="small" 
                type="text"
                @click="handleSuggestionAction(suggestion, action)"
              >
                {{ action }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Opportunity, 
  DocumentAdd, 
  EditPen, 
  Sunny, 
  Warning, 
  Clock,
  CircleCheck,
  TrendUp,
  TrendDown,
  Minus,
  Reading,
  Service,
  Guide
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '心理健康仪表板',
  userId: ''
})

const trendPeriod = ref('week')
const moodChartRef = ref<HTMLElement>()

// 心理健康数据
const mentalData = reactive({
  overallScore: 78,
  currentMood: '良好',
  moodTrend: 'stable', // up, down, stable
  stressLevel: 4, // 1-10
  sleepQuality: 82 // 0-100
})

// 心理健康活动
const mentalActivities = ref([
  {
    id: 1,
    type: 'meditation',
    title: '冥想练习',
    description: '10分钟正念冥想，放松身心',
    duration: '10分钟',
    completed: true
  },
  {
    id: 2,
    type: 'breathing',
    title: '深呼吸练习',
    description: '缓解压力的呼吸技巧',
    duration: '5分钟',
    completed: false
  },
  {
    id: 3,
    type: 'journal',
    title: '情绪日记',
    description: '记录和反思今日情绪',
    duration: '15分钟',
    completed: false
  },
  {
    id: 4,
    type: 'music',
    title: '音乐放松',
    description: '舒缓音乐减压',
    duration: '20分钟',
    completed: false
  }
])

// 咨询建议
const counselingSuggestions = ref([
  {
    id: 1,
    type: 'professional',
    urgency: 'normal',
    title: '心理咨询建议',
    description: '您的整体心理状态良好，建议保持当前的生活节奏和自我关爱习惯',
    actions: ['预约咨询', '了解更多']
  },
  {
    id: 2,
    type: 'lifestyle',
    urgency: 'low',
    title: '生活方式调整',
    description: '适当增加社交活动和户外运动，有助于改善心理健康',
    actions: ['制定计划', '查看活动']
  }
])

const updateMoodChart = () => {
  if (!moodChartRef.value) return
  
  const chart = echarts.init(moodChartRef.value, 'health-tech')
  
  // 生成模拟数据
  const days = trendPeriod.value === 'week' ? 7 : 30
  const timeData = []
  const moodData = []
  const stressData = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    timeData.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    moodData.push(60 + Math.random() * 40) // 60-100
    stressData.push(2 + Math.random() * 6) // 2-8
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
      data: ['情绪指数', '压力水平'],
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
        name: '情绪指数',
        position: 'left',
        axisLabel: {
          color: '#999'
        }
      },
      {
        type: 'value',
        name: '压力水平',
        position: 'right',
        axisLabel: {
          color: '#999'
        }
      }
    ],
    series: [
      {
        name: '情绪指数',
        type: 'line',
        yAxisIndex: 0,
        data: moodData,
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
      },
      {
        name: '压力水平',
        type: 'line',
        yAxisIndex: 1,
        data: stressData,
        smooth: true,
        lineStyle: {
          color: '#ff6b6b',
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
const getMentalScoreColor = () => {
  if (mentalData.overallScore >= 80) return 'var(--success-500)'
  if (mentalData.overallScore >= 70) return 'var(--primary-500)'
  if (mentalData.overallScore >= 60) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getMentalScoreLevel = () => {
  if (mentalData.overallScore >= 80) return 'excellent'
  if (mentalData.overallScore >= 70) return 'good'
  if (mentalData.overallScore >= 60) return 'fair'
  return 'poor'
}

const getMentalScoreText = () => {
  if (mentalData.overallScore >= 80) return '心理状态优秀'
  if (mentalData.overallScore >= 70) return '心理状态良好'
  if (mentalData.overallScore >= 60) return '心理状态一般'
  return '需要关注'
}

const getCurrentMoodEmoji = () => {
  const moodMap = {
    '优秀': '😄',
    '良好': '😊',
    '一般': '😐',
    '较差': '😔',
    '很差': '😢'
  }
  return moodMap[mentalData.currentMood as keyof typeof moodMap] || '😊'
}

const getMoodTrendIcon = () => {
  const iconMap = {
    up: TrendUp,
    down: TrendDown,
    stable: Minus
  }
  return iconMap[mentalData.moodTrend as keyof typeof iconMap] || Minus
}

const getMoodTrendText = () => {
  const trendMap = {
    up: '情绪上升',
    down: '情绪下降',
    stable: '情绪稳定'
  }
  return trendMap[mentalData.moodTrend as keyof typeof trendMap] || '情绪稳定'
}

const getStressLevelClass = () => {
  if (mentalData.stressLevel <= 3) return 'low'
  if (mentalData.stressLevel <= 6) return 'medium'
  return 'high'
}

const getStressDescription = () => {
  if (mentalData.stressLevel <= 3) return '压力较低'
  if (mentalData.stressLevel <= 6) return '压力适中'
  return '压力较高'
}

const getSleepQualityText = () => {
  if (mentalData.sleepQuality >= 80) return '睡眠优质'
  if (mentalData.sleepQuality >= 70) return '睡眠良好'
  if (mentalData.sleepQuality >= 60) return '睡眠一般'
  return '睡眠较差'
}

const getActivityIcon = (type: string) => {
  const iconMap = {
    meditation: Reading,
    breathing: Service,
    journal: EditPen,
    music: Sunny
  }
  return iconMap[type as keyof typeof iconMap] || Guide
}

const getSuggestionUrgency = () => {
  const hasHighUrgency = counselingSuggestions.value.some(s => s.urgency === 'high')
  if (hasHighUrgency) return 'danger'
  const hasMediumUrgency = counselingSuggestions.value.some(s => s.urgency === 'medium')
  if (hasMediumUrgency) return 'warning'
  return 'success'
}

const getSuggestionLevel = () => {
  const hasHighUrgency = counselingSuggestions.value.some(s => s.urgency === 'high')
  if (hasHighUrgency) return '需要关注'
  const hasMediumUrgency = counselingSuggestions.value.some(s => s.urgency === 'medium')
  if (hasMediumUrgency) return '建议关注'
  return '状态良好'
}

const getSuggestionIcon = (type: string) => {
  const iconMap = {
    professional: Service,
    lifestyle: Guide,
    emergency: Warning
  }
  return iconMap[type as keyof typeof iconMap] || Guide
}

// 事件处理
const openAssessment = () => {
  ElMessage.info('打开心理评估')
}

const openMoodTracker = () => {
  ElMessage.info('打开情绪记录')
}

const startActivity = (activity: any) => {
  ElMessage.info(`开始活动: ${activity.title}`)
}

const viewAllActivities = () => {
  ElMessage.info('查看所有活动')
}

const handleSuggestionAction = (suggestion: any, action: string) => {
  ElMessage.info(`执行建议: ${suggestion.title} - ${action}`)
}

watch(trendPeriod, () => {
  updateMoodChart()
})

onMounted(() => {
  nextTick(() => {
    updateMoodChart()
  })
})
</script>

<style lang="scss" scoped>
.mental-health-dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.dashboard-header {
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
    
    .dashboard-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.mental-overview {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overview-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    
    .card-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-sm);
      color: var(--text-secondary);
      font-size: var(--font-sm);
      
      .el-icon {
        font-size: 16px;
      }
    }
    
    &.main-score {
      .score-container {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
        
        .score-circle {
          position: relative;
          width: 80px;
          height: 80px;
          
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
            font-size: var(--font-xl);
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-tech);
          }
        }
        
        .score-info {
          .score-label {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            margin-bottom: 4px;
          }
          
          .score-level {
            font-size: var(--font-md);
            font-weight: 600;
            
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
      }
    }
    
    &.mood-status {
      text-align: center;
      
      .mood-display {
        .mood-emoji {
          font-size: 2rem;
          margin-bottom: var(--spacing-sm);
        }
        
        .mood-text {
          font-size: var(--font-lg);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-sm);
        }
        
        .mood-trend {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-xs);
          font-size: var(--font-xs);
          
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
    
    &.stress-level {
      .stress-meter {
        .stress-bar {
          width: 100%;
          height: 8px;
          background: var(--bg-secondary);
          border-radius: var(--radius-full);
          overflow: hidden;
          margin-bottom: var(--spacing-sm);
          
          .stress-fill {
            height: 100%;
            border-radius: var(--radius-full);
            transition: width 0.3s ease;
            
            &.low {
              background: linear-gradient(90deg, #66bb6a, #4caf50);
            }
            
            &.medium {
              background: linear-gradient(90deg, #ffa726, #ff9800);
            }
            
            &.high {
              background: linear-gradient(90deg, #ff6b6b, #f44336);
            }
          }
        }
        
        .stress-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          text-align: center;
          margin-bottom: var(--spacing-xs);
        }
        
        .stress-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          text-align: center;
        }
      }
    }
    
    &.sleep-quality {
      text-align: center;
      
      .sleep-score {
        .sleep-ring {
          margin-bottom: var(--spacing-sm);
          
          .ring-progress {
            position: relative;
            width: 60px;
            height: 60px;
            margin: 0 auto;
            border-radius: 50%;
            background: conic-gradient(var(--primary-500) calc(var(--progress) * 1%), var(--bg-secondary) 0%);
            display: flex;
            align-items: center;
            justify-content: center;
            
            &::before {
              content: '';
              position: absolute;
              width: 80%;
              height: 80%;
              background: var(--bg-elevated);
              border-radius: 50%;
            }
            
            .sleep-value {
              position: relative;
              z-index: 1;
              font-size: var(--font-sm);
              font-weight: 700;
              color: var(--text-primary);
              font-family: var(--font-tech);
            }
          }
        }
        
        .sleep-status {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.mood-trends {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .trends-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
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

.mental-activities {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .activities-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .activities-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-md);
    
    .activity-card {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: var(--bg-card);
        transform: translateY(-2px);
      }
      
      .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        margin-bottom: var(--spacing-sm);
      }
      
      .activity-content {
        .activity-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .activity-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .activity-duration {
          font-size: var(--font-xs);
          color: var(--primary-500);
          font-weight: 500;
        }
      }
      
      .activity-status {
        position: absolute;
        top: var(--spacing-xs);
        right: var(--spacing-xs);
        
        .completed-icon {
          color: var(--success-500);
          font-size: 16px;
        }
      }
      
      &.completed {
        opacity: 0.8;
        
        .activity-icon {
          background: var(--success-500);
        }
      }
    }
  }
}

.counseling-suggestions {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .suggestions-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .suggestions-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .suggestion-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .suggestion-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        flex-shrink: 0;
      }
      
      .suggestion-content {
        flex: 1;
        
        .suggestion-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .suggestion-desc {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .suggestion-actions {
          display: flex;
          gap: var(--spacing-sm);
          
          .el-button {
            font-size: var(--font-xs);
            padding: 2px 8px;
          }
        }
      }
      
      &.high {
        border-left: 3px solid var(--error-500);
      }
      
      &.medium {
        border-left: 3px solid var(--warning-500);
      }
      
      &.normal {
        border-left: 3px solid var(--primary-500);
      }
      
      &.low {
        border-left: 3px solid var(--info-500);
      }
    }
  }
}

@media (max-width: 1024px) {
  .mental-overview {
    grid-template-columns: 1fr 1fr;
  }
  
  .activities-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .mental-overview {
    grid-template-columns: 1fr;
  }
  
  .activities-grid {
    grid-template-columns: 1fr;
  }
}
</style>