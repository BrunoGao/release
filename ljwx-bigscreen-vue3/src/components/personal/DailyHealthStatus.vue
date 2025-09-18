<template>
  <div class="daily-health-status">
    <div class="status-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Calendar />
        </el-icon>
        <h3 class="status-title">{{ title }}</h3>
      </div>
      
      <div class="date-selector">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          size="small"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="onDateChange"
        />
      </div>
    </div>
    
    <!-- 健康状态总览 -->
    <div class="health-overview">
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
              :stroke="getScoreColor(healthStatus.overallScore)"
              stroke-width="3"
              stroke-linecap="round"
              :stroke-dasharray="`${healthStatus.overallScore} 100`"
              transform="rotate(-90 21 21)"
            />
          </svg>
          <div class="score-text">{{ healthStatus.overallScore }}</div>
        </div>
        <div class="score-info">
          <div class="score-label">健康总分</div>
          <div class="score-status" :class="getScoreLevel(healthStatus.overallScore)">
            {{ getScoreDescription(healthStatus.overallScore) }}
          </div>
        </div>
      </div>
      
      <div class="status-indicators">
        <div 
          v-for="indicator in statusIndicators" 
          :key="indicator.name"
          class="indicator-item"
          :class="indicator.status"
        >
          <el-icon class="indicator-icon">
            <component :is="indicator.icon" />
          </el-icon>
          <div class="indicator-content">
            <div class="indicator-name">{{ indicator.name }}</div>
            <div class="indicator-value">{{ indicator.value }}</div>
          </div>
          <div class="indicator-trend" :class="indicator.trend">
            <el-icon>
              <component :is="getTrendIcon(indicator.trend)" />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 每日健康打卡 -->
    <div class="daily-checklist">
      <div class="checklist-header">
        <h4>每日健康打卡</h4>
        <div class="completion-rate">
          <span>完成率: {{ getCompletionRate() }}%</span>
        </div>
      </div>
      
      <div class="checklist-items">
        <div 
          v-for="item in dailyChecklist" 
          :key="item.id"
          class="checklist-item"
          :class="{ completed: item.completed }"
          @click="toggleChecklistItem(item)"
        >
          <div class="item-checkbox">
            <el-icon v-if="item.completed" class="check-icon">
              <Check />
            </el-icon>
          </div>
          <div class="item-content">
            <div class="item-title">{{ item.title }}</div>
            <div class="item-description">{{ item.description }}</div>
          </div>
          <div class="item-time" v-if="item.completed">
            {{ formatTime(item.completedTime) }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 健康建议 -->
    <div class="health-suggestions">
      <div class="suggestions-header">
        <h4>今日健康建议</h4>
        <el-tag :type="getSuggestionLevel()" size="small">
          {{ getSuggestionText() }}
        </el-tag>
      </div>
      
      <div class="suggestions-list">
        <div 
          v-for="suggestion in healthSuggestions" 
          :key="suggestion.id"
          class="suggestion-item"
          :class="suggestion.priority"
        >
          <el-icon class="suggestion-icon">
            <component :is="getSuggestionIcon(suggestion.type)" />
          </el-icon>
          <div class="suggestion-content">
            <div class="suggestion-title">{{ suggestion.title }}</div>
            <div class="suggestion-desc">{{ suggestion.description }}</div>
          </div>
          <div class="suggestion-action">
            <el-button size="small" type="text" @click="handleSuggestion(suggestion)">
              {{ suggestion.actionText }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Calendar, 
  Check,
  Monitor,
  TrendUp,
  TrendDown,
  Minus,
  Warning,
  Sunny,
  Service,
  Guide
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '每日健康状态',
  userId: ''
})

const selectedDate = ref(new Date().toISOString().split('T')[0])

// 健康状态数据
const healthStatus = reactive({
  overallScore: 85,
  lastUpdated: new Date()
})

// 状态指标
const statusIndicators = ref([
  {
    name: '心率',
    value: '72 bpm',
    status: 'normal',
    trend: 'stable',
    icon: Monitor
  },
  {
    name: '血压',
    value: '120/80',
    status: 'normal',
    trend: 'up',
    icon: Monitor
  },
  {
    name: '体温',
    value: '36.5°C',
    status: 'normal',
    trend: 'stable',
    icon: Sunny
  },
  {
    name: '血氧',
    value: '98%',
    status: 'excellent',
    trend: 'up',
    icon: Monitor
  }
])

// 每日健康打卡
const dailyChecklist = ref([
  {
    id: 1,
    title: '晨间测量',
    description: '体重、血压、心率测量',
    completed: true,
    completedTime: new Date(Date.now() - 2 * 60 * 60 * 1000)
  },
  {
    id: 2,
    title: '用药提醒',
    description: '按时服用处方药物',
    completed: true,
    completedTime: new Date(Date.now() - 1 * 60 * 60 * 1000)
  },
  {
    id: 3,
    title: '运动打卡',
    description: '完成30分钟有氧运动',
    completed: false,
    completedTime: null
  },
  {
    id: 4,
    title: '饮水记录',
    description: '饮水量达到2000ml',
    completed: false,
    completedTime: null
  },
  {
    id: 5,
    title: '睡眠准备',
    description: '22:30前准备休息',
    completed: false,
    completedTime: null
  }
])

// 健康建议
const healthSuggestions = ref([
  {
    id: 1,
    type: 'exercise',
    priority: 'high',
    title: '运动提醒',
    description: '您今天还未完成运动目标，建议进行30分钟轻度运动',
    actionText: '开始运动'
  },
  {
    id: 2,
    type: 'hydration',
    priority: 'medium',
    title: '补充水分',
    description: '当前饮水量不足，建议增加水分摄入',
    actionText: '记录饮水'
  },
  {
    id: 3,
    type: 'rest',
    priority: 'low',
    title: '休息提醒',
    description: '保持良好的作息规律，有助于身体恢复',
    actionText: '查看详情'
  }
])

const onDateChange = (date: string) => {
  console.log('Date changed:', date)
  // 这里可以加载指定日期的健康数据
  loadHealthDataForDate(date)
}

const loadHealthDataForDate = (date: string) => {
  // 模拟加载指定日期的数据
  ElMessage.info(`加载 ${date} 的健康数据`)
}

const getScoreColor = (score: number) => {
  if (score >= 90) return 'var(--success-500)'
  if (score >= 80) return 'var(--primary-500)'
  if (score >= 70) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getScoreLevel = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
}

const getScoreDescription = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  return '需改善'
}

const getTrendIcon = (trend: string) => {
  const iconMap = {
    up: TrendUp,
    down: TrendDown,
    stable: Minus
  }
  return iconMap[trend as keyof typeof iconMap] || Minus
}

const getCompletionRate = () => {
  const completed = dailyChecklist.value.filter(item => item.completed).length
  return Math.round((completed / dailyChecklist.value.length) * 100)
}

const toggleChecklistItem = (item: any) => {
  if (!item.completed) {
    item.completed = true
    item.completedTime = new Date()
    ElMessage.success(`完成打卡: ${item.title}`)
  }
}

const formatTime = (date: Date | null) => {
  if (!date) return ''
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getSuggestionLevel = () => {
  const highPriority = healthSuggestions.value.some(s => s.priority === 'high')
  if (highPriority) return 'warning'
  const mediumPriority = healthSuggestions.value.some(s => s.priority === 'medium')
  if (mediumPriority) return 'primary'
  return 'success'
}

const getSuggestionText = () => {
  const highPriority = healthSuggestions.value.some(s => s.priority === 'high')
  if (highPriority) return '需要关注'
  const mediumPriority = healthSuggestions.value.some(s => s.priority === 'medium')
  if (mediumPriority) return '建议关注'
  return '状态良好'
}

const getSuggestionIcon = (type: string) => {
  const iconMap = {
    exercise: Service,
    hydration: Guide,
    rest: Sunny,
    medication: Warning
  }
  return iconMap[type as keyof typeof iconMap] || Guide
}

const handleSuggestion = (suggestion: any) => {
  ElMessage.info(`执行建议: ${suggestion.title}`)
}

onMounted(() => {
  console.log('Daily Health Status mounted')
})
</script>

<style lang="scss" scoped>
.daily-health-status {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.status-header {
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
    
    .status-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.health-overview {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overall-score {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    
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
      
      .score-status {
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
  
  .status-indicators {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
    
    .indicator-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .indicator-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
      }
      
      .indicator-content {
        flex: 1;
        
        .indicator-name {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
        
        .indicator-value {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
      }
      
      .indicator-trend {
        font-size: 14px;
        
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
      
      &.normal .indicator-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
      }
      
      &.excellent .indicator-icon {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
      }
      
      &.warning .indicator-icon {
        background: linear-gradient(135deg, #ffa726, #ff9800);
      }
    }
  }
}

.daily-checklist {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .checklist-header {
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
    
    .completion-rate {
      font-size: var(--font-sm);
      color: var(--primary-500);
      font-weight: 600;
    }
  }
  
  .checklist-items {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    
    .checklist-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: var(--bg-card);
      }
      
      &.completed {
        opacity: 0.8;
        
        .item-content {
          .item-title {
            text-decoration: line-through;
            color: var(--text-secondary);
          }
        }
      }
      
      .item-checkbox {
        width: 20px;
        height: 20px;
        border: 2px solid var(--border-light);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        
        .check-icon {
          color: var(--success-500);
          font-size: 14px;
        }
      }
      
      &.completed .item-checkbox {
        background: var(--success-500);
        border-color: var(--success-500);
        
        .check-icon {
          color: white;
        }
      }
      
      .item-content {
        flex: 1;
        
        .item-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .item-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .item-time {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
    }
  }
}

.health-suggestions {
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
    gap: var(--spacing-sm);
    
    .suggestion-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .suggestion-icon {
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
        background: var(--primary-500);
      }
      
      .suggestion-content {
        flex: 1;
        
        .suggestion-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .suggestion-desc {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .suggestion-action {
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.high {
        border-left: 3px solid var(--error-500);
      }
      
      &.medium {
        border-left: 3px solid var(--warning-500);
      }
      
      &.low {
        border-left: 3px solid var(--info-500);
      }
    }
  }
}

@media (max-width: 768px) {
  .health-overview {
    flex-direction: column;
    
    .status-indicators {
      grid-template-columns: 1fr;
    }
  }
  
  .status-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
}
</style>