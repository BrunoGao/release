<template>
  <div class="exercise-health-stats">
    <div class="stats-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <TrendCharts />
        </el-icon>
        <h3 class="stats-title">{{ title }}</h3>
      </div>
      
      <div class="time-range-selector">
        <el-radio-group v-model="timeRange" size="small" @change="updateStats">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <!-- 运动总览 -->
    <div class="exercise-overview">
      <div class="overview-card steps">
        <div class="card-icon">
          <el-icon><Walking /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ exerciseData.steps.toLocaleString() }}</div>
          <div class="card-label">步数</div>
          <div class="card-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: getStepsProgress() + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ getStepsProgress() }}% 目标</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card calories">
        <div class="card-icon">
          <el-icon><Lightning /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ exerciseData.calories }}</div>
          <div class="card-label">卡路里 (kcal)</div>
          <div class="card-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: getCaloriesProgress() + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ getCaloriesProgress() }}% 目标</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card distance">
        <div class="card-icon">
          <el-icon><Position /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ exerciseData.distance }}km</div>
          <div class="card-label">运动距离</div>
          <div class="card-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: getDistanceProgress() + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ getDistanceProgress() }}% 目标</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card duration">
        <div class="card-icon">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ exerciseData.duration }}</div>
          <div class="card-label">运动时长</div>
          <div class="card-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: getDurationProgress() + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ getDurationProgress() }}% 目标</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 运动类型分布 -->
    <div class="exercise-distribution">
      <div class="distribution-header">
        <h4>运动类型分布</h4>
        <div class="total-time">
          <span class="time-label">总运动时间</span>
          <span class="time-value">{{ getTotalTime() }}分钟</span>
        </div>
      </div>
      
      <div class="exercise-types">
        <div 
          v-for="type in exerciseTypes" 
          :key="type.name"
          class="exercise-type"
          :class="type.level"
        >
          <div class="type-icon">
            <el-icon>
              <component :is="getExerciseIcon(type.name)" />
            </el-icon>
          </div>
          <div class="type-info">
            <div class="type-name">{{ type.name }}</div>
            <div class="type-time">{{ type.duration }}分钟</div>
          </div>
          <div class="type-progress">
            <div class="circular-progress" :class="type.intensity">
              <svg viewBox="0 0 36 36">
                <path
                  d="m18,2.0845
                  a 15.9155,15.9155 0 0,1 0,31.831
                  a 15.9155,15.9155 0 0,1 0,-31.831"
                  fill="none"
                  stroke="var(--bg-secondary)"
                  stroke-width="2"
                />
                <path
                  d="m18,2.0845
                  a 15.9155,15.9155 0 0,1 0,31.831
                  a 15.9155,15.9155 0 0,1 0,-31.831"
                  fill="none"
                  :stroke-dasharray="`${type.percentage}, 100`"
                  stroke-width="2"
                  class="progress-stroke"
                />
              </svg>
              <div class="progress-text">{{ type.percentage }}%</div>
            </div>
          </div>
          <div class="type-intensity">
            <el-tag :type="getIntensityType(type.intensity)" size="small">
              {{ getIntensityText(type.intensity) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 健康指标 -->
    <div class="health-metrics">
      <div class="metrics-header">
        <h4>健康指标</h4>
        <div class="health-score">
          <span class="score-label">健康评分</span>
          <span class="score-value" :class="getHealthScoreClass()">{{ healthMetrics.score }}/100</span>
        </div>
      </div>
      
      <div class="metrics-grid">
        <div class="metric-item heart-rate">
          <div class="metric-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">平均心率</div>
            <div class="metric-value">{{ healthMetrics.avgHeartRate }} bpm</div>
            <div class="metric-trend" :class="healthMetrics.heartRateTrend">
              <el-icon v-if="healthMetrics.heartRateTrend === 'up'"><CaretTop /></el-icon>
              <el-icon v-else-if="healthMetrics.heartRateTrend === 'down'"><CaretBottom /></el-icon>
              <el-icon v-else><Minus /></el-icon>
              <span>{{ getTrendText(healthMetrics.heartRateTrend) }}</span>
            </div>
          </div>
        </div>
        
        <div class="metric-item recovery">
          <div class="metric-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">恢复指数</div>
            <div class="metric-value">{{ healthMetrics.recoveryIndex }}%</div>
            <div class="metric-status" :class="getRecoveryClass()">
              {{ getRecoveryText() }}
            </div>
          </div>
        </div>
        
        <div class="metric-item stress">
          <div class="metric-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">压力水平</div>
            <div class="metric-value">{{ healthMetrics.stressLevel }}/10</div>
            <div class="metric-status" :class="getStressClass()">
              {{ getStressText() }}
            </div>
          </div>
        </div>
        
        <div class="metric-item energy">
          <div class="metric-icon">
            <el-icon><Sunny /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-label">能量水平</div>
            <div class="metric-value">{{ healthMetrics.energyLevel }}/10</div>
            <div class="metric-status" :class="getEnergyClass()">
              {{ getEnergyText() }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  TrendCharts, 
  Walking, 
  Lightning, 
  Position, 
  Timer,
  CircleCheck,
  Warning,
  Sunny,
  CaretTop,
  CaretBottom,
  Minus,
  Bicycle,
  Football
} from '@element-plus/icons-vue'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '运动健康统计',
  userId: ''
})

const timeRange = ref('today')

// 运动数据
const exerciseData = reactive({
  steps: 8520,
  calories: 420,
  distance: 6.8,
  duration: '1小时25分'
})

// 运动类型数据
const exerciseTypes = ref([
  {
    name: '跑步',
    duration: 45,
    percentage: 45,
    intensity: 'high',
    level: 'primary'
  },
  {
    name: '步行',
    duration: 30,
    percentage: 30,
    intensity: 'medium',
    level: 'success'
  },
  {
    name: '骑行',
    duration: 25,
    percentage: 25,
    intensity: 'medium',
    level: 'info'
  }
])

// 健康指标
const healthMetrics = reactive({
  score: 85,
  avgHeartRate: 72,
  heartRateTrend: 'stable',
  recoveryIndex: 78,
  stressLevel: 3,
  energyLevel: 8
})

const updateStats = () => {
  console.log('更新统计数据:', timeRange.value)
  // 根据时间范围更新数据
  if (timeRange.value === 'week') {
    exerciseData.steps = 52000
    exerciseData.calories = 2450
    exerciseData.distance = 35.6
    exerciseData.duration = '8小时30分'
  } else if (timeRange.value === 'month') {
    exerciseData.steps = 240000
    exerciseData.calories = 11200
    exerciseData.distance = 156.8
    exerciseData.duration = '38小时15分'
  } else {
    exerciseData.steps = 8520
    exerciseData.calories = 420
    exerciseData.distance = 6.8
    exerciseData.duration = '1小时25分'
  }
}

// 工具方法
const getStepsProgress = () => {
  const target = 10000
  return Math.min(Math.round((exerciseData.steps / target) * 100), 100)
}

const getCaloriesProgress = () => {
  const target = 500
  return Math.min(Math.round((exerciseData.calories / target) * 100), 100)
}

const getDistanceProgress = () => {
  const target = 8
  return Math.min(Math.round((exerciseData.distance / target) * 100), 100)
}

const getDurationProgress = () => {
  // 假设目标是90分钟
  const durationMinutes = parseInt(exerciseData.duration)
  const target = 90
  return Math.min(Math.round((durationMinutes / target) * 100), 100)
}

const getTotalTime = () => {
  return exerciseTypes.value.reduce((sum, type) => sum + type.duration, 0)
}

const getExerciseIcon = (name: string) => {
  const iconMap = {
    '跑步': Walking,
    '步行': Walking,
    '骑行': Bicycle,
    '游泳': Lightning,
    '健身': Football
  }
  return iconMap[name as keyof typeof iconMap] || Walking
}

const getIntensityType = (intensity: string) => {
  const typeMap = {
    low: 'info',
    medium: 'warning',
    high: 'danger'
  }
  return typeMap[intensity as keyof typeof typeMap] || 'info'
}

const getIntensityText = (intensity: string) => {
  const textMap = {
    low: '低强度',
    medium: '中强度',
    high: '高强度'
  }
  return textMap[intensity as keyof typeof textMap] || '未知'
}

const getHealthScoreClass = () => {
  if (healthMetrics.score >= 80) return 'excellent'
  if (healthMetrics.score >= 60) return 'good'
  if (healthMetrics.score >= 40) return 'fair'
  return 'poor'
}

const getTrendText = (trend: string) => {
  const textMap = {
    up: '上升',
    down: '下降',
    stable: '稳定'
  }
  return textMap[trend as keyof typeof textMap] || ''
}

const getRecoveryClass = () => {
  if (healthMetrics.recoveryIndex >= 80) return 'excellent'
  if (healthMetrics.recoveryIndex >= 60) return 'good'
  return 'poor'
}

const getRecoveryText = () => {
  if (healthMetrics.recoveryIndex >= 80) return '恢复良好'
  if (healthMetrics.recoveryIndex >= 60) return '恢复中等'
  return '需要休息'
}

const getStressClass = () => {
  if (healthMetrics.stressLevel <= 3) return 'good'
  if (healthMetrics.stressLevel <= 6) return 'fair'
  return 'poor'
}

const getStressText = () => {
  if (healthMetrics.stressLevel <= 3) return '压力较低'
  if (healthMetrics.stressLevel <= 6) return '压力适中'
  return '压力较高'
}

const getEnergyClass = () => {
  if (healthMetrics.energyLevel >= 8) return 'excellent'
  if (healthMetrics.energyLevel >= 6) return 'good'
  return 'poor'
}

const getEnergyText = () => {
  if (healthMetrics.energyLevel >= 8) return '精力充沛'
  if (healthMetrics.energyLevel >= 6) return '精力良好'
  return '精力不足'
}
</script>

<style lang="scss" scoped>
.exercise-health-stats {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.stats-header {
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
    
    .stats-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.exercise-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overview-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    
    .card-icon {
      width: 50px;
      height: 50px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 20px;
    }
    
    .card-content {
      flex: 1;
      
      .card-value {
        font-size: var(--font-xl);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
        margin-bottom: 2px;
      }
      
      .card-label {
        font-size: var(--font-xs);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-xs);
      }
      
      .card-progress {
        .progress-bar {
          width: 100%;
          height: 4px;
          background: var(--bg-secondary);
          border-radius: var(--radius-full);
          overflow: hidden;
          margin-bottom: var(--spacing-xs);
          
          .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
            border-radius: var(--radius-full);
            transition: width 0.3s ease;
          }
        }
        
        .progress-text {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
    
    &.steps .card-icon {
      background: linear-gradient(135deg, #66bb6a, #4caf50);
    }
    
    &.calories .card-icon {
      background: linear-gradient(135deg, #ff6b6b, #f44336);
    }
    
    &.distance .card-icon {
      background: linear-gradient(135deg, #42a5f5, #2196f3);
    }
    
    &.duration .card-icon {
      background: linear-gradient(135deg, #ffa726, #ff9800);
    }
  }
}

.exercise-distribution {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .distribution-header {
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
    
    .total-time {
      text-align: right;
      
      .time-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        display: block;
        margin-bottom: 2px;
      }
      
      .time-value {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--primary-500);
        font-family: var(--font-tech);
      }
    }
  }
  
  .exercise-types {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .exercise-type {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .type-icon {
        width: 32px;
        height: 32px;
        background: var(--primary-500);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
      }
      
      .type-info {
        flex: 1;
        
        .type-name {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .type-time {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .type-progress {
        .circular-progress {
          position: relative;
          width: 40px;
          height: 40px;
          
          svg {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
          }
          
          .progress-stroke {
            stroke: var(--primary-500);
            transition: stroke-dasharray 0.3s ease;
          }
          
          .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: var(--font-xs);
            font-weight: 600;
            color: var(--text-primary);
          }
          
          &.high .progress-stroke {
            stroke: var(--error-500);
          }
          
          &.medium .progress-stroke {
            stroke: var(--warning-500);
          }
          
          &.low .progress-stroke {
            stroke: var(--info-500);
          }
        }
      }
      
      .type-intensity {
        min-width: 60px;
        text-align: center;
      }
    }
  }
}

.health-metrics {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .metrics-header {
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
    
    .health-score {
      text-align: right;
      
      .score-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        display: block;
        margin-bottom: 2px;
      }
      
      .score-value {
        font-size: var(--font-lg);
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
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-md);
    
    .metric-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .metric-icon {
        width: 32px;
        height: 32px;
        background: var(--primary-500);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
      }
      
      .metric-content {
        flex: 1;
        
        .metric-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: 2px;
        }
        
        .metric-value {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: 2px;
        }
        
        .metric-trend {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          font-size: var(--font-xs);
          
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
        
        .metric-status {
          font-size: var(--font-xs);
          
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
}

@media (max-width: 1024px) {
  .exercise-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .exercise-overview {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>