<template>
  <div class="mental-health-metrics">
    <div class="metrics-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Opportunity />
        </el-icon>
        <h3 class="metrics-title">{{ title }}</h3>
      </div>
      
      <div class="overall-status" :class="getOverallMentalStatus()">
        <span class="status-indicator"></span>
        <span class="status-text">{{ getMentalStatusText() }}</span>
      </div>
    </div>
    
    <!-- 心理健康概览 -->
    <div class="mental-overview">
      <div class="overview-card stress">
        <div class="card-header">
          <el-icon><Warning /></el-icon>
          <span>压力水平</span>
        </div>
        <div class="stress-meter">
          <div class="meter-track">
            <div 
              class="meter-fill" 
              :style="{ width: mentalData.stressLevel * 10 + '%' }"
              :class="getStressClass(mentalData.stressLevel)"
            ></div>
          </div>
          <div class="stress-value">{{ mentalData.stressLevel }}/10</div>
        </div>
        <div class="stress-description">{{ getStressDescription() }}</div>
      </div>
      
      <div class="overview-card mood">
        <div class="card-header">
          <el-icon><Sunny /></el-icon>
          <span>情绪状态</span>
        </div>
        <div class="mood-indicator">
          <div class="mood-emoji">{{ getMoodEmoji() }}</div>
          <div class="mood-text">{{ mentalData.mood }}</div>
        </div>
        <div class="mood-trend" :class="mentalData.moodTrend">
          <el-icon v-if="mentalData.moodTrend === 'improving'"><TrendUp /></el-icon>
          <el-icon v-else-if="mentalData.moodTrend === 'declining'"><TrendDown /></el-icon>
          <el-icon v-else><Minus /></el-icon>
          <span>{{ getMoodTrendText() }}</span>
        </div>
      </div>
      
      <div class="overview-card energy">
        <div class="card-header">
          <el-icon><Lightning /></el-icon>
          <span>精力状态</span>
        </div>
        <div class="energy-gauge">
          <svg viewBox="0 0 100 50" class="gauge-svg">
            <path 
              d="M 10 40 A 30 30 0 0 1 90 40" 
              stroke="var(--bg-secondary)" 
              stroke-width="8" 
              fill="none"
            />
            <path 
              d="M 10 40 A 30 30 0 0 1 90 40" 
              :stroke="getEnergyColor()"
              stroke-width="8" 
              fill="none"
              :stroke-dasharray="getEnergyDashArray()"
              stroke-linecap="round"
            />
          </svg>
          <div class="energy-value">{{ mentalData.energyLevel }}%</div>
        </div>
        <div class="energy-description">{{ getEnergyDescription() }}</div>
      </div>
      
      <div class="overview-card sleep">
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>睡眠质量</span>
        </div>
        <div class="sleep-score">
          <div class="score-ring">
            <svg viewBox="0 0 42 42" class="ring-svg">
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
                :stroke="getSleepColor()"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${mentalData.sleepQuality} 100`"
                transform="rotate(-90 21 21)"
              />
            </svg>
            <div class="score-text">{{ mentalData.sleepQuality }}</div>
          </div>
        </div>
        <div class="sleep-description">{{ getSleepDescription() }}</div>
      </div>
    </div>
    
    <!-- 心理健康评估 -->
    <div class="mental-assessment">
      <div class="assessment-header">
        <h4>心理健康评估</h4>
        <div class="assessment-score">
          <span class="score-label">综合评分</span>
          <span class="score-value" :class="getAssessmentClass()">{{ getOverallScore() }}/100</span>
        </div>
      </div>
      
      <div class="assessment-factors">
        <div 
          v-for="factor in assessmentFactors" 
          :key="factor.name"
          class="factor-item"
          :class="factor.level"
        >
          <div class="factor-info">
            <div class="factor-name">{{ factor.name }}</div>
            <div class="factor-description">{{ factor.description }}</div>
          </div>
          <div class="factor-score">
            <div class="score-bar">
              <div 
                class="score-fill" 
                :style="{ width: factor.score + '%' }"
                :class="getFactorClass(factor.score)"
              ></div>
            </div>
            <span class="score-text">{{ factor.score }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 建议和干预 -->
    <div class="mental-recommendations">
      <div class="recommendations-header">
        <h4>健康建议</h4>
        <el-tag :type="getRecommendationType()" size="small">
          {{ getRecommendationLevel() }}
        </el-tag>
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in mentalRecommendations" 
          :key="recommendation.id"
          class="recommendation-item"
          :class="recommendation.urgency"
        >
          <el-icon class="rec-icon">
            <component :is="getRecommendationIcon(recommendation.type)" />
          </el-icon>
          <div class="rec-content">
            <div class="rec-title">{{ recommendation.title }}</div>
            <div class="rec-description">{{ recommendation.description }}</div>
            <div class="rec-actions">
              <el-button 
                v-for="action in recommendation.actions" 
                :key="action"
                size="small" 
                type="text"
                @click="handleRecommendationAction(recommendation, action)"
              >
                {{ action }}
              </el-button>
            </div>
          </div>
          <div class="rec-priority">
            <el-tag :type="getPriorityType(recommendation.urgency)" size="small">
              {{ getPriorityText(recommendation.urgency) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Opportunity, 
  Warning, 
  Sunny, 
  Lightning, 
  Clock,
  TrendUp,
  TrendDown,
  Minus,
  Reading,
  Guide,
  Service
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '心理健康指标',
  userId: ''
})

// 心理健康数据
const mentalData = reactive({
  stressLevel: 4, // 1-10
  mood: '良好',
  moodTrend: 'stable', // improving, declining, stable
  energyLevel: 75, // 0-100
  sleepQuality: 82 // 0-100
})

// 评估因子
const assessmentFactors = ref([
  {
    name: '情绪稳定性',
    description: '情绪波动控制和稳定程度',
    score: 78,
    level: 'good'
  },
  {
    name: '压力管理',
    description: '处理和应对压力的能力',
    score: 65,
    level: 'fair'
  },
  {
    name: '社交关系',
    description: '人际交往和社会支持情况',
    score: 85,
    level: 'excellent'
  },
  {
    name: '生活满意度',
    description: '对当前生活状态的满意程度',
    score: 72,
    level: 'good'
  },
  {
    name: '自我效能感',
    description: '对自己能力和价值的认知',
    score: 68,
    level: 'fair'
  }
])

// 心理健康建议
const mentalRecommendations = ref([
  {
    id: 1,
    type: 'relaxation',
    urgency: 'medium',
    title: '压力缓解建议',
    description: '您的压力水平稍高，建议进行放松训练和深呼吸练习',
    actions: ['开始冥想', '深呼吸练习', '查看指导']
  },
  {
    id: 2,
    type: 'social',
    urgency: 'low',
    title: '社交活动推荐',
    description: '保持良好的社交关系有助于心理健康，建议多参与社交活动',
    actions: ['查看活动', '联系朋友']
  },
  {
    id: 3,
    type: 'self-care',
    urgency: 'low',
    title: '自我关爱提醒',
    description: '定期关注自己的内心感受，进行自我反思和调节',
    actions: ['情绪日记', '自我评估']
  }
])

// 工具方法
const getOverallMentalStatus = () => {
  const overallScore = getOverallScore()
  if (overallScore >= 80) return 'excellent'
  if (overallScore >= 70) return 'good'
  if (overallScore >= 60) return 'fair'
  return 'poor'
}

const getMentalStatusText = () => {
  const status = getOverallMentalStatus()
  const textMap = {
    excellent: '心理状态优秀',
    good: '心理状态良好',
    fair: '心理状态一般',
    poor: '需要关注'
  }
  return textMap[status]
}

const getOverallScore = () => {
  const factors = assessmentFactors.value
  const totalScore = factors.reduce((sum, factor) => sum + factor.score, 0)
  return Math.round(totalScore / factors.length)
}

const getStressClass = (level: number) => {
  if (level <= 3) return 'low'
  if (level <= 6) return 'medium'
  return 'high'
}

const getStressDescription = () => {
  const level = mentalData.stressLevel
  if (level <= 3) return '压力较低，状态良好'
  if (level <= 6) return '压力适中，需要关注'
  return '压力较高，建议放松'
}

const getMoodEmoji = () => {
  const moodMap = {
    '优秀': '😄',
    '良好': '😊',
    '一般': '😐',
    '较差': '😔',
    '很差': '😢'
  }
  return moodMap[mentalData.mood as keyof typeof moodMap] || '😊'
}

const getMoodTrendText = () => {
  const trendMap = {
    improving: '改善中',
    declining: '需关注',
    stable: '稳定'
  }
  return trendMap[mentalData.moodTrend as keyof typeof trendMap] || '稳定'
}

const getEnergyColor = () => {
  if (mentalData.energyLevel >= 80) return 'var(--success-500)'
  if (mentalData.energyLevel >= 60) return 'var(--primary-500)'
  if (mentalData.energyLevel >= 40) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getEnergyDashArray = () => {
  const percentage = mentalData.energyLevel
  const circumference = 2 * Math.PI * 30 * 0.5 // 半圆
  return `${circumference * percentage / 100} ${circumference}`
}

const getEnergyDescription = () => {
  if (mentalData.energyLevel >= 80) return '精力充沛'
  if (mentalData.energyLevel >= 60) return '精力良好'
  if (mentalData.energyLevel >= 40) return '精力一般'
  return '精力不足'
}

const getSleepColor = () => {
  if (mentalData.sleepQuality >= 80) return 'var(--success-500)'
  if (mentalData.sleepQuality >= 70) return 'var(--primary-500)'
  if (mentalData.sleepQuality >= 60) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getSleepDescription = () => {
  if (mentalData.sleepQuality >= 80) return '睡眠优质'
  if (mentalData.sleepQuality >= 70) return '睡眠良好'
  if (mentalData.sleepQuality >= 60) return '睡眠一般'
  return '睡眠较差'
}

const getAssessmentClass = () => {
  const score = getOverallScore()
  if (score >= 80) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 60) return 'fair'
  return 'poor'
}

const getFactorClass = (score: number) => {
  if (score >= 80) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 60) return 'fair'
  return 'poor'
}

const getRecommendationType = () => {
  const score = getOverallScore()
  if (score >= 80) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 60) return 'warning'
  return 'danger'
}

const getRecommendationLevel = () => {
  const score = getOverallScore()
  if (score >= 80) return '状态优良'
  if (score >= 70) return '建议关注'
  if (score >= 60) return '需要改善'
  return '重点关注'
}

const getRecommendationIcon = (type: string) => {
  const iconMap = {
    relaxation: Reading,
    social: Service,
    'self-care': Guide,
    exercise: Lightning,
    therapy: Opportunity
  }
  return iconMap[type as keyof typeof iconMap] || Guide
}

const getPriorityType = (urgency: string) => {
  const typeMap = {
    low: 'info',
    medium: 'warning',
    high: 'danger'
  }
  return typeMap[urgency as keyof typeof typeMap] || 'info'
}

const getPriorityText = (urgency: string) => {
  const textMap = {
    low: '低优先级',
    medium: '中优先级',
    high: '高优先级'
  }
  return textMap[urgency as keyof typeof textMap] || '低优先级'
}

const handleRecommendationAction = (recommendation: any, action: string) => {
  ElMessage.info(`执行建议: ${recommendation.title} - ${action}`)
  // 这里可以添加具体的行动逻辑
}
</script>

<style lang="scss" scoped>
.mental-health-metrics {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.metrics-header {
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
    
    .metrics-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .overall-status {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    
    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: var(--radius-full);
    }
    
    .status-text {
      font-size: var(--font-sm);
      font-weight: 500;
    }
    
    &.excellent {
      background: rgba(102, 187, 106, 0.1);
      color: var(--success-500);
      
      .status-indicator {
        background: var(--success-500);
      }
    }
    
    &.good {
      background: rgba(0, 255, 157, 0.1);
      color: var(--primary-500);
      
      .status-indicator {
        background: var(--primary-500);
      }
    }
    
    &.fair {
      background: rgba(255, 167, 38, 0.1);
      color: var(--warning-500);
      
      .status-indicator {
        background: var(--warning-500);
      }
    }
    
    &.poor {
      background: rgba(255, 107, 107, 0.1);
      color: var(--error-500);
      
      .status-indicator {
        background: var(--error-500);
      }
    }
  }
}

.mental-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overview-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    text-align: center;
    
    .card-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-md);
      color: var(--text-secondary);
      font-size: var(--font-sm);
      
      .el-icon {
        font-size: 16px;
      }
    }
    
    .stress-meter {
      margin-bottom: var(--spacing-sm);
      
      .meter-track {
        width: 100%;
        height: 8px;
        background: var(--bg-secondary);
        border-radius: var(--radius-full);
        overflow: hidden;
        margin-bottom: var(--spacing-sm);
        
        .meter-fill {
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
        font-size: var(--font-xl);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
      }
    }
    
    .mood-indicator {
      margin-bottom: var(--spacing-sm);
      
      .mood-emoji {
        font-size: 2rem;
        margin-bottom: var(--spacing-xs);
      }
      
      .mood-text {
        font-size: var(--font-lg);
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-xs);
      }
    }
    
    .mood-trend {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-xs);
      font-size: var(--font-xs);
      
      &.improving {
        color: var(--success-500);
      }
      
      &.declining {
        color: var(--error-500);
      }
      
      &.stable {
        color: var(--text-secondary);
      }
    }
    
    .energy-gauge {
      position: relative;
      margin-bottom: var(--spacing-sm);
      
      .gauge-svg {
        width: 100%;
        height: 60px;
      }
      
      .energy-value {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
      }
    }
    
    .sleep-score {
      display: flex;
      justify-content: center;
      margin-bottom: var(--spacing-sm);
      
      .score-ring {
        position: relative;
        width: 60px;
        height: 60px;
        
        .ring-svg {
          width: 100%;
          height: 100%;
          transform: rotate(-90deg);
        }
        
        .score-text {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
      }
    }
    
    .stress-description,
    .energy-description,
    .sleep-description {
      font-size: var(--font-xs);
      color: var(--text-secondary);
    }
  }
}

.mental-assessment {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .assessment-header {
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
    
    .assessment-score {
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
  
  .assessment-factors {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .factor-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .factor-info {
        flex: 1;
        
        .factor-name {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .factor-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .factor-score {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        min-width: 120px;
        
        .score-bar {
          flex: 1;
          height: 6px;
          background: var(--bg-card);
          border-radius: var(--radius-full);
          overflow: hidden;
          
          .score-fill {
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
        
        .score-text {
          font-size: var(--font-xs);
          font-weight: 600;
          color: var(--text-primary);
          font-family: var(--font-tech);
          min-width: 35px;
        }
      }
    }
  }
}

.mental-recommendations {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .recommendations-header {
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
  
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .recommendation-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .rec-icon {
        width: 32px;
        height: 32px;
        background: var(--primary-500);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        flex-shrink: 0;
      }
      
      .rec-content {
        flex: 1;
        
        .rec-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .rec-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .rec-actions {
          display: flex;
          gap: var(--spacing-sm);
          flex-wrap: wrap;
          
          .el-button {
            font-size: var(--font-xs);
            padding: 2px 8px;
          }
        }
      }
      
      .rec-priority {
        flex-shrink: 0;
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

@media (max-width: 1024px) {
  .mental-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .mental-overview {
    grid-template-columns: 1fr;
  }
}
</style>