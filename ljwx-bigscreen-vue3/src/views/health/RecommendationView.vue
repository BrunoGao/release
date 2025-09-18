<template>
  <div class="recommendation-view">
    <div class="view-header">
      <h2 class="view-title">健康建议</h2>
      <div class="header-actions">
        <el-select v-model="recommendationType" size="small" placeholder="选择建议类型">
          <el-option label="全部建议" value="all" />
          <el-option label="运动健康" value="exercise" />
          <el-option label="饮食营养" value="nutrition" />
          <el-option label="睡眠改善" value="sleep" />
          <el-option label="心理健康" value="mental" />
        </el-select>
        <el-button size="small" @click="refreshRecommendations">
          <el-icon><Refresh /></el-icon>
          刷新建议
        </el-button>
      </div>
    </div>

    <div class="recommendation-overview">
      <div class="priority-card urgent">
        <div class="card-header">
          <el-icon><Warning /></el-icon>
          <h3>紧急建议</h3>
        </div>
        <div class="priority-list">
          <div class="priority-item" v-for="item in urgentRecommendations" :key="item.id">
            <div class="item-icon">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="item-content">
              <div class="item-title">{{ item.title }}</div>
              <div class="item-description">{{ item.description }}</div>
            </div>
            <div class="item-action">
              <el-button size="small" type="danger" @click="markAsRead(item)">
                立即处理
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="priority-card important">
        <div class="card-header">
          <el-icon><Star /></el-icon>
          <h3>重要建议</h3>
        </div>
        <div class="priority-list">
          <div class="priority-item" v-for="item in importantRecommendations" :key="item.id">
            <div class="item-icon">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="item-content">
              <div class="item-title">{{ item.title }}</div>
              <div class="item-description">{{ item.description }}</div>
            </div>
            <div class="item-action">
              <el-button size="small" type="warning" @click="markAsRead(item)">
                查看详情
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="recommendation-categories">
      <div class="category-tabs">
        <div class="tab-item" 
             v-for="category in categories" 
             :key="category.key"
             :class="{ active: activeCategory === category.key }"
             @click="activeCategory = category.key">
          <el-icon><component :is="category.icon" /></el-icon>
          <span>{{ category.label }}</span>
          <div class="tab-count">{{ category.count }}</div>
        </div>
      </div>

      <div class="category-content">
        <div class="recommendation-list">
          <div class="recommendation-item" 
               v-for="rec in filteredRecommendations" 
               :key="rec.id"
               :class="rec.priority">
            <div class="rec-header">
              <div class="rec-icon" :class="rec.category">
                <el-icon><component :is="getCategoryIcon(rec.category)" /></el-icon>
              </div>
              <div class="rec-meta">
                <h4 class="rec-title">{{ rec.title }}</h4>
                <div class="rec-tags">
                  <el-tag v-for="tag in rec.tags" :key="tag" size="small" type="info">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              <div class="rec-priority" :class="rec.priority">
                {{ getPriorityText(rec.priority) }}
              </div>
            </div>

            <div class="rec-content">
              <p class="rec-description">{{ rec.description }}</p>
              
              <div class="rec-details" v-if="rec.details">
                <div class="detail-item" v-for="detail in rec.details" :key="detail.label">
                  <span class="detail-label">{{ detail.label }}:</span>
                  <span class="detail-value">{{ detail.value }}</span>
                </div>
              </div>

              <div class="rec-benefits" v-if="rec.benefits">
                <h5>预期效果:</h5>
                <ul>
                  <li v-for="benefit in rec.benefits" :key="benefit">{{ benefit }}</li>
                </ul>
              </div>

              <div class="rec-steps" v-if="rec.steps">
                <h5>执行步骤:</h5>
                <ol>
                  <li v-for="step in rec.steps" :key="step">{{ step }}</li>
                </ol>
              </div>
            </div>

            <div class="rec-footer">
              <div class="rec-info">
                <span class="rec-source">来源: {{ rec.source }}</span>
                <span class="rec-date">{{ formatDate(rec.createdAt) }}</span>
              </div>
              <div class="rec-actions">
                <el-button size="small" @click="markAsRead(rec)">
                  <el-icon><Check /></el-icon>
                  已完成
                </el-button>
                <el-button size="small" @click="saveRecommendation(rec)">
                  <el-icon><Star /></el-icon>
                  收藏
                </el-button>
                <el-button size="small" @click="shareRecommendation(rec)">
                  <el-icon><Share /></el-icon>
                  分享
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="recommendation-summary">
      <div class="summary-header">
        <h4>建议执行情况</h4>
      </div>
      <div class="summary-stats">
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><DocumentChecked /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ completedCount }}</div>
            <div class="stat-label">已完成建议</div>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ pendingCount }}</div>
            <div class="stat-label">待处理建议</div>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><TrendUp /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ improvementRate }}%</div>
            <div class="stat-label">健康改善率</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Refresh, 
  Warning, 
  Star, 
  Check, 
  Share,
  Timer,
  FoodBowl,
  Moon,
  Heart,
  TrendUp,
  Clock,
  DocumentChecked
} from '@element-plus/icons-vue'

const recommendationType = ref('all')
const activeCategory = ref('exercise')

const urgentRecommendations = ref([
  {
    id: 1,
    title: '血压异常提醒',
    description: '检测到您的血压持续偏高，建议立即就医咨询',
    icon: Warning,
    category: 'health'
  },
  {
    id: 2,
    title: '睡眠不足警告',
    description: '连续3天睡眠时间不足6小时，需要调整作息',
    icon: Moon,
    category: 'sleep'
  }
])

const importantRecommendations = ref([
  {
    id: 3,
    title: '增加有氧运动',
    description: '建议每周增加2次30分钟的有氧运动',
    icon: Timer,
    category: 'exercise'
  },
  {
    id: 4,
    title: '饮食结构调整',
    description: '减少高盐食物摄入，增加蔬菜和水果比例',
    icon: FoodBowl,
    category: 'nutrition'
  }
])

const categories = ref([
  { key: 'exercise', label: '运动健康', icon: Timer, count: 8 },
  { key: 'nutrition', label: '饮食营养', icon: FoodBowl, count: 6 },
  { key: 'sleep', label: '睡眠改善', icon: Moon, count: 4 },
  { key: 'mental', label: '心理健康', icon: Heart, count: 3 }
])

const recommendations = ref([
  {
    id: 5,
    category: 'exercise',
    priority: 'high',
    title: '制定个人运动计划',
    description: '根据您的身体状况和健康目标，制定一个循序渐进的运动计划',
    tags: ['运动', '计划', '个性化'],
    details: [
      { label: '推荐频率', value: '每周3-4次' },
      { label: '运动时长', value: '30-45分钟' },
      { label: '运动强度', value: '中等强度' }
    ],
    benefits: [
      '改善心血管健康',
      '增强肌肉力量',
      '提高新陈代谢',
      '改善睡眠质量'
    ],
    steps: [
      '制定每周运动时间表',
      '选择适合的运动类型',
      '逐步增加运动强度',
      '记录运动进度'
    ],
    source: 'AI健康分析',
    createdAt: new Date('2023-12-15')
  },
  {
    id: 6,
    category: 'nutrition',
    priority: 'medium',
    title: '优化饮食搭配',
    description: '调整饮食结构，增加营养密度，减少空热量食物',
    tags: ['营养', '饮食', '健康'],
    details: [
      { label: '蛋白质比例', value: '20-25%' },
      { label: '碳水化合物', value: '45-50%' },
      { label: '脂肪比例', value: '25-30%' }
    ],
    benefits: [
      '稳定血糖水平',
      '提供充足营养',
      '增强免疫力',
      '控制体重'
    ],
    steps: [
      '增加蔬菜摄入量',
      '选择优质蛋白质',
      '减少精制糖摄入',
      '保持规律进餐'
    ],
    source: '营养师建议',
    createdAt: new Date('2023-12-14')
  },
  {
    id: 7,
    category: 'sleep',
    priority: 'high',
    title: '改善睡眠质量',
    description: '建立良好的睡眠习惯，提高睡眠效率和深度睡眠时间',
    tags: ['睡眠', '作息', '恢复'],
    details: [
      { label: '建议睡眠时长', value: '7-8小时' },
      { label: '入睡时间', value: '22:00-23:00' },
      { label: '起床时间', value: '06:00-07:00' }
    ],
    benefits: [
      '增强免疫力',
      '改善记忆力',
      '减少压力',
      '促进身体修复'
    ],
    steps: [
      '制定固定作息时间',
      '创造舒适睡眠环境',
      '睡前1小时避免电子设备',
      '建立睡前放松仪式'
    ],
    source: '睡眠专家',
    createdAt: new Date('2023-12-13')
  },
  {
    id: 8,
    category: 'mental',
    priority: 'medium',
    title: '压力管理技巧',
    description: '学习有效的压力管理方法，保持心理健康平衡',
    tags: ['压力', '心理', '放松'],
    details: [
      { label: '推荐练习', value: '冥想、深呼吸' },
      { label: '练习频率', value: '每日10-15分钟' },
      { label: '效果评估', value: '2周后评估' }
    ],
    benefits: [
      '降低压力激素',
      '改善情绪状态',
      '提高专注力',
      '增强应对能力'
    ],
    steps: [
      '学习基础冥想技巧',
      '建立日常练习习惯',
      '使用压力监测工具',
      '寻求专业指导'
    ],
    source: '心理健康专家',
    createdAt: new Date('2023-12-12')
  }
])

const completedCount = ref(12)
const pendingCount = ref(8)
const improvementRate = ref(85)

const filteredRecommendations = computed(() => {
  let filtered = recommendations.value
  
  if (activeCategory.value !== 'all') {
    filtered = filtered.filter(rec => rec.category === activeCategory.value)
  }
  
  if (recommendationType.value !== 'all') {
    filtered = filtered.filter(rec => rec.category === recommendationType.value)
  }
  
  return filtered
})

const getCategoryIcon = (category: string) => {
  const iconMap = {
    exercise: Timer,
    nutrition: FoodBowl,
    sleep: Moon,
    mental: Heart
  }
  return iconMap[category as keyof typeof iconMap] || Timer
}

const getPriorityText = (priority: string) => {
  const textMap = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return textMap[priority as keyof typeof textMap] || '一般'
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN')
}

const refreshRecommendations = () => {
  // 刷新建议逻辑
}

const markAsRead = (recommendation: any) => {
  // 标记为已读逻辑
}

const saveRecommendation = (recommendation: any) => {
  // 收藏建议逻辑
}

const shareRecommendation = (recommendation: any) => {
  // 分享建议逻辑
}
</script>

<style lang="scss" scoped>
.recommendation-view {
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

.recommendation-overview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.priority-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border-left: 4px solid;
  
  &.urgent {
    border-left-color: var(--error-500);
  }
  
  &.important {
    border-left-color: var(--warning-500);
  }
  
  .card-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    
    .el-icon {
      font-size: 18px;
    }
    
    h3 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .priority-list {
    .priority-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      margin-bottom: var(--spacing-sm);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .item-icon {
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
      
      .item-content {
        flex: 1;
        
        .item-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .item-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.recommendation-categories {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.category-tabs {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .tab-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-md);
    cursor: pointer;
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    transition: all 0.2s ease;
    position: relative;
    
    &:hover {
      background: var(--bg-elevated);
    }
    
    &.active {
      background: var(--primary-50);
      color: var(--primary-500);
      
      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--primary-500);
      }
    }
    
    .tab-count {
      background: var(--bg-secondary);
      color: var(--text-secondary);
      font-size: var(--font-xs);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      min-width: 20px;
      text-align: center;
    }
  }
}

.recommendation-list {
  .recommendation-item {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    margin-bottom: var(--spacing-lg);
    overflow: hidden;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    &.high {
      border-left: 4px solid var(--error-500);
    }
    
    &.medium {
      border-left: 4px solid var(--warning-500);
    }
    
    &.low {
      border-left: 4px solid var(--success-500);
    }
    
    .rec-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-card);
      
      .rec-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        
        &.exercise {
          background: var(--primary-500);
        }
        
        &.nutrition {
          background: var(--success-500);
        }
        
        &.sleep {
          background: var(--info-500);
        }
        
        &.mental {
          background: var(--warning-500);
        }
      }
      
      .rec-meta {
        flex: 1;
        
        .rec-title {
          font-size: var(--font-md);
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 var(--spacing-xs) 0;
        }
        
        .rec-tags {
          display: flex;
          gap: var(--spacing-xs);
        }
      }
      
      .rec-priority {
        font-size: var(--font-xs);
        font-weight: 600;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        
        &.high {
          background: rgba(244, 67, 54, 0.2);
          color: var(--error-500);
        }
        
        &.medium {
          background: rgba(255, 167, 38, 0.2);
          color: var(--warning-500);
        }
        
        &.low {
          background: rgba(76, 175, 80, 0.2);
          color: var(--success-500);
        }
      }
    }
    
    .rec-content {
      padding: var(--spacing-lg);
      
      .rec-description {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-lg);
        line-height: 1.6;
      }
      
      .rec-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--spacing-md);
        margin-bottom: var(--spacing-lg);
        
        .detail-item {
          display: flex;
          justify-content: space-between;
          padding: var(--spacing-sm);
          background: var(--bg-secondary);
          border-radius: var(--radius-sm);
          
          .detail-label {
            font-size: var(--font-sm);
            color: var(--text-secondary);
          }
          
          .detail-value {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
          }
        }
      }
      
      .rec-benefits,
      .rec-steps {
        margin-bottom: var(--spacing-lg);
        
        h5 {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 var(--spacing-sm) 0;
        }
        
        ul,
        ol {
          padding-left: var(--spacing-lg);
          
          li {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            margin-bottom: var(--spacing-xs);
            line-height: 1.5;
          }
        }
      }
    }
    
    .rec-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-md);
      background: var(--bg-card);
      border-top: 1px solid var(--border-light);
      
      .rec-info {
        display: flex;
        gap: var(--spacing-md);
        
        .rec-source,
        .rec-date {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .rec-actions {
        display: flex;
        gap: var(--spacing-sm);
      }
    }
  }
}

.recommendation-summary {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .summary-header {
    margin-bottom: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .summary-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-lg);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      
      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        background: var(--primary-500);
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
        }
        
        .stat-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .recommendation-overview {
    grid-template-columns: 1fr;
  }
  
  .summary-stats {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .category-tabs {
    flex-wrap: wrap;
  }
  
  .rec-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .rec-footer {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
}
</style>