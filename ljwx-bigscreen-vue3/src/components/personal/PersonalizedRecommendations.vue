<template>
  <div class="personalized-recommendations">
    <div class="recommendations-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Guide />
        </el-icon>
        <h3 class="recommendations-title">{{ title }}</h3>
      </div>
      
      <div class="header-controls">
        <el-button size="small" @click="refreshRecommendations">
          <el-icon><Refresh /></el-icon>
          刷新建议
        </el-button>
        <el-button size="small" @click="customizeSettings">
          <el-icon><Setting /></el-icon>
          个性化设置
        </el-button>
      </div>
    </div>
    
    <!-- 智能推荐概览 -->
    <div class="recommendations-overview">
      <div class="overview-stats">
        <div class="stat-card total">
          <div class="stat-icon">
            <el-icon><Opportunity /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ recommendationStats.total }}</div>
            <div class="stat-label">总建议数</div>
          </div>
        </div>
        
        <div class="stat-card high-priority">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ recommendationStats.highPriority }}</div>
            <div class="stat-label">高优先级</div>
          </div>
        </div>
        
        <div class="stat-card completed">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ recommendationStats.completed }}</div>
            <div class="stat-label">已采纳</div>
          </div>
        </div>
        
        <div class="stat-card effectiveness">
          <div class="stat-icon">
            <el-icon><TrendUp /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ recommendationStats.effectiveness }}%</div>
            <div class="stat-label">有效率</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分类建议 -->
    <div class="recommendation-categories">
      <div class="categories-header">
        <h4>智能建议分类</h4>
        <el-segmented v-model="activeCategory" :options="categoryOptions" />
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in filteredRecommendations" 
          :key="recommendation.id"
          class="recommendation-card"
          :class="[recommendation.priority, recommendation.status]"
        >
          <div class="card-header">
            <div class="recommendation-icon">
              <el-icon>
                <component :is="getRecommendationIcon(recommendation.category)" />
              </el-icon>
            </div>
            <div class="recommendation-meta">
              <div class="recommendation-category">{{ getCategoryText(recommendation.category) }}</div>
              <div class="recommendation-time">{{ formatTime(recommendation.createdAt) }}</div>
            </div>
            <div class="recommendation-priority">
              <el-tag :type="getPriorityType(recommendation.priority)" size="small">
                {{ getPriorityText(recommendation.priority) }}
              </el-tag>
            </div>
          </div>
          
          <div class="card-content">
            <div class="recommendation-title">{{ recommendation.title }}</div>
            <div class="recommendation-description">{{ recommendation.description }}</div>
            
            <div class="recommendation-details">
              <div class="detail-item">
                <span class="detail-label">预期效果:</span>
                <span class="detail-value">{{ recommendation.expectedOutcome }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">实施难度:</span>
                <span class="detail-value">{{ getDifficultyText(recommendation.difficulty) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">建议时长:</span>
                <span class="detail-value">{{ recommendation.duration }}</span>
              </div>
            </div>
            
            <div class="recommendation-data" v-if="recommendation.supportingData">
              <div class="data-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>支持数据</span>
              </div>
              <div class="data-content">
                {{ recommendation.supportingData }}
              </div>
            </div>
          </div>
          
          <div class="card-actions">
            <div class="action-buttons">
              <el-button 
                v-if="recommendation.status === 'pending'"
                size="small" 
                type="primary" 
                @click="acceptRecommendation(recommendation)"
              >
                采纳建议
              </el-button>
              <el-button 
                v-if="recommendation.status === 'accepted'"
                size="small" 
                type="success" 
                @click="markAsCompleted(recommendation)"
              >
                标记完成
              </el-button>
              <el-button 
                size="small" 
                @click="viewDetails(recommendation)"
              >
                查看详情
              </el-button>
              <el-dropdown trigger="click">
                <el-button size="small" type="text">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="shareRecommendation(recommendation)">分享建议</el-dropdown-item>
                    <el-dropdown-item @click="postponeRecommendation(recommendation)">稍后处理</el-dropdown-item>
                    <el-dropdown-item @click="dismissRecommendation(recommendation)" divided>忽略建议</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            
            <div class="recommendation-feedback" v-if="recommendation.status === 'completed'">
              <div class="feedback-rating">
                <span class="rating-label">有用性评分:</span>
                <el-rate 
                  v-model="recommendation.userRating" 
                  size="small"
                  @change="updateRating(recommendation)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 个性化洞察 -->
    <div class="personalized-insights">
      <div class="insights-header">
        <h4>个性化洞察</h4>
        <el-button size="small" @click="generateInsights">
          <el-icon><Magic /></el-icon>
          生成新洞察
        </el-button>
      </div>
      
      <div class="insights-grid">
        <div 
          v-for="insight in personalizedInsights" 
          :key="insight.id"
          class="insight-card"
          :class="insight.type"
        >
          <div class="insight-icon">
            <el-icon>
              <component :is="getInsightIcon(insight.type)" />
            </el-icon>
          </div>
          <div class="insight-content">
            <div class="insight-title">{{ insight.title }}</div>
            <div class="insight-description">{{ insight.description }}</div>
            <div class="insight-metrics" v-if="insight.metrics">
              <div 
                v-for="metric in insight.metrics" 
                :key="metric.name"
                class="metric-item"
              >
                <span class="metric-name">{{ metric.name }}</span>
                <span class="metric-value">{{ metric.value }}</span>
              </div>
            </div>
          </div>
          <div class="insight-action">
            <el-button size="small" type="text" @click="exploreInsight(insight)">
              深入了解
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 建议历史 -->
    <div class="recommendation-history">
      <div class="history-header">
        <h4>建议历史</h4>
        <div class="history-filters">
          <el-select v-model="historyFilter" size="small" placeholder="筛选状态">
            <el-option label="全部" value="all" />
            <el-option label="已采纳" value="accepted" />
            <el-option label="已完成" value="completed" />
            <el-option label="已忽略" value="dismissed" />
          </el-select>
          <el-date-picker
            v-model="historyDateRange"
            type="daterange"
            size="small"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </div>
      </div>
      
      <div class="history-chart" ref="historyChartRef"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Guide, 
  Refresh, 
  Setting, 
  Opportunity, 
  Warning, 
  CircleCheck, 
  TrendUp,
  DataAnalysis,
  MoreFilled,
  Magic,
  Monitor,
  Lightning,
  Service,
  Cpu
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '个性化建议',
  userId: ''
})

const activeCategory = ref('all')
const historyFilter = ref('all')
const historyDateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
  new Date()
])
const historyChartRef = ref<HTMLElement>()

const categoryOptions = [
  { label: '全部', value: 'all' },
  { label: '健康', value: 'health' },
  { label: '运动', value: 'exercise' },
  { label: '睡眠', value: 'sleep' },
  { label: '营养', value: 'nutrition' }
]

// 建议统计
const recommendationStats = reactive({
  total: 12,
  highPriority: 3,
  completed: 8,
  effectiveness: 85
})

// 建议列表
const recommendations = ref([
  {
    id: 1,
    category: 'health',
    priority: 'high',
    status: 'pending',
    title: '血压监测建议',
    description: '根据您最近的血压数据分析，建议增加监测频率并调整生活方式',
    expectedOutcome: '血压控制改善15%',
    difficulty: 'medium',
    duration: '2-3周',
    supportingData: '最近7天血压平均值135/85，比正常值偏高8%',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    userRating: 0
  },
  {
    id: 2,
    category: 'exercise',
    priority: 'medium',
    status: 'accepted',
    title: '运动强度优化',
    description: '基于您的心率数据，建议调整运动强度分配，增加中等强度训练',
    expectedOutcome: '运动效果提升25%',
    difficulty: 'low',
    duration: '1周',
    supportingData: '当前低强度运动占70%，建议调整为50%',
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
    userRating: 0
  },
  {
    id: 3,
    category: 'sleep',
    priority: 'low',
    status: 'completed',
    title: '睡眠规律调整',
    description: '建议保持固定的就寝时间，提高睡眠质量',
    expectedOutcome: '睡眠质量改善20%',
    difficulty: 'easy',
    duration: '1-2周',
    supportingData: '睡眠时间波动范围达到2小时',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
    userRating: 4
  },
  {
    id: 4,
    category: 'nutrition',
    priority: 'medium',
    status: 'pending',
    title: '营养搭配优化',
    description: '根据您的活动量和身体指标，建议调整营养搭配比例',
    expectedOutcome: '体重管理改善',
    difficulty: 'medium',
    duration: '2-4周',
    supportingData: '当前蛋白质摄入不足15%',
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000),
    userRating: 0
  }
])

// 个性化洞察
const personalizedInsights = ref([
  {
    id: 1,
    type: 'trend',
    title: '健康趋势分析',
    description: '您的整体健康指标呈上升趋势，保持当前生活方式',
    metrics: [
      { name: '改善幅度', value: '+12%' },
      { name: '持续天数', value: '15天' }
    ]
  },
  {
    id: 2,
    type: 'pattern',
    title: '行为模式发现',
    description: '检测到您在周末的运动量显著降低，建议制定周末运动计划',
    metrics: [
      { name: '周末运动量', value: '-35%' },
      { name: '影响程度', value: '中等' }
    ]
  },
  {
    id: 3,
    type: 'correlation',
    title: '关联性分析',
    description: '睡眠质量与次日运动表现存在强关联，优质睡眠提升运动效果',
    metrics: [
      { name: '关联强度', value: '0.78' },
      { name: '影响系数', value: '+22%' }
    ]
  }
])

const filteredRecommendations = computed(() => {
  if (activeCategory.value === 'all') {
    return recommendations.value
  }
  return recommendations.value.filter(rec => rec.category === activeCategory.value)
})

const updateHistoryChart = () => {
  if (!historyChartRef.value) return
  
  const chart = echarts.init(historyChartRef.value, 'health-tech')
  
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
    legend: {
      data: ['新增建议', '已采纳', '已完成'],
      textStyle: {
        color: '#999'
      }
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLabel: {
        color: '#999'
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#999'
      }
    },
    series: [
      {
        name: '新增建议',
        type: 'bar',
        data: [2, 1, 3, 2, 1, 1, 2],
        itemStyle: {
          color: '#42a5f5'
        }
      },
      {
        name: '已采纳',
        type: 'bar',
        data: [1, 1, 2, 1, 1, 0, 1],
        itemStyle: {
          color: '#66bb6a'
        }
      },
      {
        name: '已完成',
        type: 'bar',
        data: [1, 0, 1, 1, 0, 1, 1],
        itemStyle: {
          color: '#ffa726'
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
const formatTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

const getRecommendationIcon = (category: string) => {
  const iconMap = {
    health: Monitor,
    exercise: TrendUp,
    sleep: Cpu,
    nutrition: Service
  }
  return iconMap[category as keyof typeof iconMap] || Monitor
}

const getCategoryText = (category: string) => {
  const textMap = {
    health: '健康监控',
    exercise: '运动健身',
    sleep: '睡眠管理',
    nutrition: '营养饮食'
  }
  return textMap[category as keyof typeof textMap] || '其他'
}

const getPriorityType = (priority: string) => {
  const typeMap = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return typeMap[priority as keyof typeof typeMap] || 'info'
}

const getPriorityText = (priority: string) => {
  const textMap = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return textMap[priority as keyof typeof textMap] || '低优先级'
}

const getDifficultyText = (difficulty: string) => {
  const textMap = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return textMap[difficulty as keyof typeof textMap] || '中等'
}

const getInsightIcon = (type: string) => {
  const iconMap = {
    trend: TrendUp,
    pattern: DataAnalysis,
    correlation: Lightning
  }
  return iconMap[type as keyof typeof iconMap] || DataAnalysis
}

// 事件处理
const refreshRecommendations = () => {
  ElMessage.info('刷新建议列表')
}

const customizeSettings = () => {
  ElMessage.info('打开个性化设置')
}

const acceptRecommendation = (recommendation: any) => {
  recommendation.status = 'accepted'
  ElMessage.success(`已采纳建议: ${recommendation.title}`)
}

const markAsCompleted = (recommendation: any) => {
  recommendation.status = 'completed'
  ElMessage.success(`已完成建议: ${recommendation.title}`)
}

const viewDetails = (recommendation: any) => {
  ElMessage.info(`查看建议详情: ${recommendation.title}`)
}

const shareRecommendation = (recommendation: any) => {
  ElMessage.info(`分享建议: ${recommendation.title}`)
}

const postponeRecommendation = (recommendation: any) => {
  ElMessage.info(`延后处理: ${recommendation.title}`)
}

const dismissRecommendation = (recommendation: any) => {
  recommendation.status = 'dismissed'
  ElMessage.warning(`已忽略建议: ${recommendation.title}`)
}

const updateRating = (recommendation: any) => {
  ElMessage.success('感谢您的反馈!')
}

const generateInsights = () => {
  ElMessage.info('正在生成新的个性化洞察...')
}

const exploreInsight = (insight: any) => {
  ElMessage.info(`深入了解: ${insight.title}`)
}

onMounted(() => {
  nextTick(() => {
    updateHistoryChart()
  })
})
</script>

<style lang="scss" scoped>
.personalized-recommendations {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.recommendations-header {
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
    
    .recommendations-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .header-controls {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.recommendations-overview {
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
      
      &.total .stat-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
      }
      
      &.high-priority .stat-icon {
        background: linear-gradient(135deg, #ff6b6b, #f44336);
      }
      
      &.completed .stat-icon {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
      }
      
      &.effectiveness .stat-icon {
        background: linear-gradient(135deg, #ffa726, #ff9800);
      }
    }
  }
}

.recommendation-categories {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .categories-header {
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
    
    .recommendation-card {
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-light);
      overflow: hidden;
      
      .card-header {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--bg-card);
        border-bottom: 1px solid var(--border-light);
        
        .recommendation-icon {
          width: 28px;
          height: 28px;
          border-radius: var(--radius-sm);
          background: var(--primary-500);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 14px;
        }
        
        .recommendation-meta {
          flex: 1;
          
          .recommendation-category {
            font-size: var(--font-sm);
            font-weight: 500;
            color: var(--text-primary);
          }
          
          .recommendation-time {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
      
      .card-content {
        padding: var(--spacing-md);
        
        .recommendation-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .recommendation-description {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-md);
          line-height: 1.5;
        }
        
        .recommendation-details {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-md);
          
          .detail-item {
            .detail-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
              display: block;
              margin-bottom: 2px;
            }
            
            .detail-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 500;
            }
          }
        }
        
        .recommendation-data {
          background: var(--bg-card);
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm);
          
          .data-header {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            margin-bottom: var(--spacing-xs);
            color: var(--primary-500);
            font-size: var(--font-xs);
            font-weight: 600;
          }
          
          .data-content {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
      
      .card-actions {
        padding: var(--spacing-md);
        border-top: 1px solid var(--border-light);
        
        .action-buttons {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-sm);
          
          .el-button {
            font-size: var(--font-xs);
          }
        }
        
        .recommendation-feedback {
          .feedback-rating {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            
            .rating-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
          }
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
      
      &.completed {
        opacity: 0.8;
        
        .recommendation-icon {
          background: var(--success-500);
        }
      }
    }
  }
}

.personalized-insights {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .insights-header {
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
  
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
    
    .insight-card {
      display: flex;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .insight-icon {
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
      
      .insight-content {
        flex: 1;
        
        .insight-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .insight-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .insight-metrics {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-xs);
          
          .metric-item {
            display: flex;
            justify-content: space-between;
            
            .metric-name {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
            
            .metric-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 600;
              font-family: var(--font-tech);
            }
          }
        }
      }
      
      .insight-action {
        .el-button {
          font-size: var(--font-xs);
        }
      }
    }
  }
}

.recommendation-history {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .history-header {
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
    
    .history-filters {
      display: flex;
      gap: var(--spacing-sm);
    }
  }
  
  .history-chart {
    height: 200px;
  }
}

@media (max-width: 1024px) {
  .overview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .insights-grid {
    grid-template-columns: 1fr;
  }
  
  .recommendation-details {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .recommendations-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .overview-stats {
    grid-template-columns: 1fr;
  }
  
  .categories-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
  
  .history-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
}
</style>