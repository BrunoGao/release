<template>
  <div class="health-goals-progress">
    <div class="goals-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Flag />
        </el-icon>
        <h3 class="goals-title">{{ title }}</h3>
      </div>
      
      <div class="time-selector">
        <el-radio-group v-model="timeRange" size="small">
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="year">本年</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <!-- 目标概览 -->
    <div class="goals-overview">
      <div class="overview-stats">
        <div class="stat-card completed">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ achievedGoals }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
        
        <div class="stat-card in-progress">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ inProgressGoals }}</div>
            <div class="stat-label">进行中</div>
          </div>
        </div>
        
        <div class="stat-card total">
          <div class="stat-icon">
            <el-icon><Flag /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalGoals }}</div>
            <div class="stat-label">总目标</div>
          </div>
        </div>
        
        <div class="stat-card achievement">
          <div class="stat-icon">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ achievementRate }}%</div>
            <div class="stat-label">达成率</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 目标进度列表 -->
    <div class="goals-list">
      <div class="list-header">
        <h4>健康目标进度</h4>
        <el-button size="small" type="primary" @click="addNewGoal">
          <el-icon><Plus /></el-icon>
          新增目标
        </el-button>
      </div>
      
      <div class="goals-container">
        <div 
          v-for="goal in healthGoals" 
          :key="goal.id"
          class="goal-item"
          :class="getGoalStatusClass(goal)"
        >
          <div class="goal-info">
            <div class="goal-header">
              <div class="goal-title">{{ goal.title }}</div>
              <div class="goal-status" :class="goal.status">
                {{ getStatusText(goal.status) }}
              </div>
            </div>
            <div class="goal-description">{{ goal.description }}</div>
            <div class="goal-timeline">
              <span class="timeline-text">
                {{ formatDate(goal.startDate) }} - {{ formatDate(goal.endDate) }}
              </span>
              <span class="days-remaining" v-if="goal.status === 'active'">
                剩余 {{ getDaysRemaining(goal.endDate) }} 天
              </span>
            </div>
          </div>
          
          <div class="goal-progress">
            <div class="progress-circle">
              <svg viewBox="0 0 36 36" class="circular-chart">
                <path
                  class="circle-bg"
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  class="circle"
                  :class="getProgressClass(goal.progress)"
                  :stroke-dasharray="`${goal.progress}, 100`"
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div class="percentage">{{ goal.progress }}%</div>
            </div>
            
            <div class="progress-details">
              <div class="current-value">
                <span class="value">{{ goal.currentValue }}</span>
                <span class="unit">{{ goal.unit }}</span>
              </div>
              <div class="target-value">
                目标: {{ goal.targetValue }} {{ goal.unit }}
              </div>
            </div>
          </div>
          
          <div class="goal-actions">
            <el-button size="small" type="text" @click="updateProgress(goal)">
              更新进度
            </el-button>
            <el-dropdown trigger="click">
              <el-button size="small" type="text">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="editGoal(goal)">编辑目标</el-dropdown-item>
                  <el-dropdown-item @click="viewDetails(goal)">查看详情</el-dropdown-item>
                  <el-dropdown-item @click="deleteGoal(goal)" divided>删除目标</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 目标建议 -->
    <div class="goal-recommendations">
      <div class="recommendations-header">
        <h4>目标建议</h4>
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in goalRecommendations" 
          :key="recommendation.id"
          class="recommendation-item"
          :class="recommendation.type"
        >
          <el-icon class="rec-icon">
            <component :is="getRecommendationIcon(recommendation.type)" />
          </el-icon>
          <div class="rec-content">
            <div class="rec-title">{{ recommendation.title }}</div>
            <div class="rec-description">{{ recommendation.description }}</div>
          </div>
          <div class="rec-action">
            <el-button size="small" type="text" @click="handleRecommendation(recommendation)">
              {{ recommendation.actionText }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Flag, 
  CircleCheck, 
  Clock, 
  Trophy, 
  Plus, 
  MoreFilled,
  TrendUp,
  Warning,
  Guide,
  Opportunity
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康目标进度',
  userId: ''
})

const timeRange = ref('week')

// 目标统计数据
const achievedGoals = ref(3)
const inProgressGoals = ref(5)
const totalGoals = ref(8)
const achievementRate = computed(() => {
  return Math.round((achievedGoals.value / totalGoals.value) * 100)
})

// 健康目标数据
const healthGoals = ref([
  {
    id: 1,
    title: '每日步数目标',
    description: '每天走10,000步，提高心血管健康',
    currentValue: 8520,
    targetValue: 10000,
    unit: '步',
    progress: 85,
    status: 'active',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    category: 'exercise'
  },
  {
    id: 2,
    title: '体重管理',
    description: '将体重控制在健康范围内',
    currentValue: 68.5,
    targetValue: 65,
    unit: 'kg',
    progress: 71,
    status: 'active',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
    category: 'weight'
  },
  {
    id: 3,
    title: '血压控制',
    description: '保持血压在正常范围',
    currentValue: 120,
    targetValue: 120,
    unit: 'mmHg',
    progress: 100,
    status: 'completed',
    startDate: '2024-01-01',
    endDate: '2024-03-31',
    category: 'health'
  },
  {
    id: 4,
    title: '睡眠质量',
    description: '每晚保证7-8小时优质睡眠',
    currentValue: 6.5,
    targetValue: 8,
    unit: '小时',
    progress: 81,
    status: 'active',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    category: 'sleep'
  },
  {
    id: 5,
    title: '水分摄入',
    description: '每天饮水2000ml以上',
    currentValue: 1600,
    targetValue: 2000,
    unit: 'ml',
    progress: 80,
    status: 'active',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    category: 'nutrition'
  }
])

// 目标建议
const goalRecommendations = ref([
  {
    id: 1,
    type: 'improvement',
    title: '加强运动强度',
    description: '您的步数目标接近完成，建议增加运动强度或延长运动时间',
    actionText: '查看建议'
  },
  {
    id: 2,
    type: 'reminder',
    title: '饮水提醒',
    description: '今日饮水量不足，建议设置定时饮水提醒',
    actionText: '设置提醒'
  },
  {
    id: 3,
    type: 'adjustment',
    title: '目标调整',
    description: '根据您的进度，建议适当调整部分目标的时间线',
    actionText: '调整目标'
  }
])

const getGoalStatusClass = (goal: any) => {
  return goal.status
}

const getStatusText = (status: string) => {
  const statusMap = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停',
    expired: '已过期'
  }
  return statusMap[status as keyof typeof statusMap] || '未知'
}

const getProgressClass = (progress: number) => {
  if (progress >= 90) return 'excellent'
  if (progress >= 70) return 'good'
  if (progress >= 50) return 'fair'
  return 'poor'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getDaysRemaining = (endDate: string) => {
  const end = new Date(endDate)
  const now = new Date()
  const diffTime = end.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays)
}

const getRecommendationIcon = (type: string) => {
  const iconMap = {
    improvement: TrendUp,
    reminder: Warning,
    adjustment: Guide,
    achievement: Trophy
  }
  return iconMap[type as keyof typeof iconMap] || Opportunity
}

const addNewGoal = () => {
  ElMessage.info('打开新增目标对话框')
}

const updateProgress = (goal: any) => {
  ElMessage.info(`更新目标进度: ${goal.title}`)
}

const editGoal = (goal: any) => {
  ElMessage.info(`编辑目标: ${goal.title}`)
}

const viewDetails = (goal: any) => {
  ElMessage.info(`查看目标详情: ${goal.title}`)
}

const deleteGoal = (goal: any) => {
  ElMessage.warning(`删除目标: ${goal.title}`)
}

const handleRecommendation = (recommendation: any) => {
  ElMessage.info(`执行建议: ${recommendation.title}`)
}

onMounted(() => {
  console.log('Health Goals Progress mounted')
})
</script>

<style lang="scss" scoped>
.health-goals-progress {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.goals-header {
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
    
    .goals-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.goals-overview {
  margin-bottom: var(--spacing-lg);
  
  .overview-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-lg);
    
    .stat-card {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
      }
      
      .stat-content {
        .stat-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: 2px;
        }
        
        .stat-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      &.completed .stat-icon {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
      }
      
      &.in-progress .stat-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
      }
      
      &.total .stat-icon {
        background: linear-gradient(135deg, #9c27b0, #673ab7);
      }
      
      &.achievement .stat-icon {
        background: linear-gradient(135deg, #ffa726, #ff9800);
      }
    }
  }
}

.goals-list {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .list-header {
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
  
  .goals-container {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .goal-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-lg);
      padding: var(--spacing-md);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      border: 1px solid var(--border-light);
      
      .goal-info {
        flex: 1;
        
        .goal-header {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-xs);
          
          .goal-title {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
          }
          
          .goal-status {
            font-size: var(--font-xs);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            
            &.active {
              background: rgba(66, 165, 245, 0.2);
              color: var(--primary-500);
            }
            
            &.completed {
              background: rgba(102, 187, 106, 0.2);
              color: var(--success-500);
            }
            
            &.paused {
              background: rgba(255, 167, 38, 0.2);
              color: var(--warning-500);
            }
          }
        }
        
        .goal-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .goal-timeline {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          
          .timeline-text {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
          
          .days-remaining {
            font-size: var(--font-xs);
            color: var(--warning-500);
            background: rgba(255, 167, 38, 0.1);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
          }
        }
      }
      
      .goal-progress {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        
        .progress-circle {
          position: relative;
          width: 60px;
          height: 60px;
          
          .circular-chart {
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
            
            .circle-bg {
              fill: none;
              stroke: var(--bg-secondary);
              stroke-width: 2;
            }
            
            .circle {
              fill: none;
              stroke-width: 2;
              stroke-linecap: round;
              transition: stroke-dasharray 0.3s ease;
              
              &.excellent {
                stroke: var(--success-500);
              }
              
              &.good {
                stroke: var(--primary-500);
              }
              
              &.fair {
                stroke: var(--warning-500);
              }
              
              &.poor {
                stroke: var(--error-500);
              }
            }
          }
          
          .percentage {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: var(--font-xs);
            font-weight: 600;
            color: var(--text-primary);
          }
        }
        
        .progress-details {
          text-align: right;
          
          .current-value {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 2px;
            
            .value {
              font-family: var(--font-tech);
            }
            
            .unit {
              font-size: var(--font-xs);
              color: var(--text-secondary);
              margin-left: 2px;
            }
          }
          
          .target-value {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
      
      .goal-actions {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.completed {
        opacity: 0.8;
        background: rgba(102, 187, 106, 0.1);
        border-color: var(--success-500);
      }
    }
  }
}

.goal-recommendations {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .recommendations-header {
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    
    .recommendation-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .rec-icon {
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
      
      .rec-content {
        flex: 1;
        
        .rec-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .rec-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .rec-action {
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.improvement {
        border-left: 3px solid var(--success-500);
      }
      
      &.reminder {
        border-left: 3px solid var(--warning-500);
      }
      
      &.adjustment {
        border-left: 3px solid var(--info-500);
      }
    }
  }
}

@media (max-width: 1024px) {
  .overview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .goals-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .overview-stats {
    grid-template-columns: 1fr;
  }
  
  .goal-item {
    flex-direction: column;
    align-items: flex-start;
    
    .goal-progress {
      align-self: stretch;
      justify-content: space-between;
    }
  }
}
</style>