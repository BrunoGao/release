<template>
  <div class="personal-data-stats">
    <div class="stats-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <DataAnalysis />
        </el-icon>
        <h3 class="stats-title">{{ title }}</h3>
      </div>
      
      <div class="stats-controls">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="onDateRangeChange"
        />
        <el-button size="small" @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </div>
    </div>
    
    <!-- 数据概览 -->
    <div class="data-overview">
      <div class="overview-grid">
        <div class="overview-card total-records">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ dataStats.totalRecords }}</div>
            <div class="card-label">总记录数</div>
          </div>
          <div class="card-trend positive">
            <el-icon><TrendUp /></el-icon>
            <span>+12%</span>
          </div>
        </div>
        
        <div class="overview-card data-types">
          <div class="card-icon">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ dataStats.dataTypes }}</div>
            <div class="card-label">数据类型</div>
          </div>
          <div class="card-info">
            <span>覆盖完整</span>
          </div>
        </div>
        
        <div class="overview-card data-quality">
          <div class="card-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ dataStats.qualityScore }}%</div>
            <div class="card-label">数据质量</div>
          </div>
          <div class="card-trend positive">
            <el-icon><TrendUp /></el-icon>
            <span>+3%</span>
          </div>
        </div>
        
        <div class="overview-card storage-used">
          <div class="card-icon">
            <el-icon><Files /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ formatBytes(dataStats.storageUsed) }}</div>
            <div class="card-label">存储使用</div>
          </div>
          <div class="card-info">
            <span>{{ getStoragePercentage() }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据分类统计 -->
    <div class="data-categories">
      <div class="categories-header">
        <h4>数据分类统计</h4>
        <el-button-group size="small">
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="viewDetails">
            <el-icon><View /></el-icon>
            详情
          </el-button>
        </el-button-group>
      </div>
      
      <div class="categories-grid">
        <div 
          v-for="category in dataCategories" 
          :key="category.type"
          class="category-card"
          :class="category.type"
        >
          <div class="category-header">
            <div class="category-icon">
              <el-icon>
                <component :is="getCategoryIcon(category.type)" />
              </el-icon>
            </div>
            <div class="category-info">
              <div class="category-name">{{ category.name }}</div>
              <div class="category-count">{{ category.count }} 条记录</div>
            </div>
          </div>
          
          <div class="category-stats">
            <div class="stat-item">
              <span class="stat-label">今日新增</span>
              <span class="stat-value">{{ category.todayAdded }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">数据完整度</span>
              <span class="stat-value">{{ category.completeness }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">最后更新</span>
              <span class="stat-value">{{ formatTime(category.lastUpdate) }}</span>
            </div>
          </div>
          
          <div class="category-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: category.completeness + '%' }"
                :class="getCompletenessClass(category.completeness)"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据趋势图表 -->
    <div class="data-trends">
      <div class="trends-header">
        <h4>数据增长趋势</h4>
        <el-radio-group v-model="trendPeriod" size="small">
          <el-radio-button label="week">最近7天</el-radio-button>
          <el-radio-button label="month">最近30天</el-radio-button>
          <el-radio-button label="quarter">最近3个月</el-radio-button>
        </el-radio-group>
      </div>
      <div class="chart-container" ref="trendsChartRef"></div>
    </div>
    
    <!-- 数据质量分析 -->
    <div class="data-quality-analysis">
      <div class="quality-header">
        <h4>数据质量分析</h4>
        <div class="quality-score" :class="getQualityLevel()">
          <span class="score-text">总体评分: {{ dataStats.qualityScore }}分</span>
          <span class="score-level">{{ getQualityLevelText() }}</span>
        </div>
      </div>
      
      <div class="quality-metrics">
        <div 
          v-for="metric in qualityMetrics" 
          :key="metric.name"
          class="metric-item"
          :class="metric.level"
        >
          <div class="metric-info">
            <div class="metric-name">{{ metric.name }}</div>
            <div class="metric-description">{{ metric.description }}</div>
          </div>
          <div class="metric-score">
            <div class="score-bar">
              <div 
                class="score-fill" 
                :style="{ width: metric.score + '%' }"
                :class="getMetricClass(metric.score)"
              ></div>
            </div>
            <span class="score-text">{{ metric.score }}%</span>
          </div>
          <div class="metric-status">
            <el-tag :type="getMetricTagType(metric.score)" size="small">
              {{ getMetricStatusText(metric.score) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据建议 -->
    <div class="data-recommendations">
      <div class="recommendations-header">
        <h4>数据优化建议</h4>
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in dataRecommendations" 
          :key="recommendation.id"
          class="recommendation-item"
          :class="recommendation.priority"
        >
          <el-icon class="rec-icon">
            <component :is="getRecommendationIcon(recommendation.type)" />
          </el-icon>
          <div class="rec-content">
            <div class="rec-title">{{ recommendation.title }}</div>
            <div class="rec-description">{{ recommendation.description }}</div>
            <div class="rec-impact">预期改善: {{ recommendation.expectedImprovement }}</div>
          </div>
          <div class="rec-action">
            <el-button size="small" type="primary" @click="handleRecommendation(recommendation)">
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
  DataAnalysis, 
  Download, 
  Document, 
  Collection, 
  CircleCheck, 
  Files,
  TrendUp,
  Refresh,
  View,
  Monitor,
  Cpu,
  Camera,
  Setting,
  Warning,
  Guide
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '个人数据统计',
  userId: ''
})

const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
  new Date()
])
const trendPeriod = ref('month')
const trendsChartRef = ref<HTMLElement>()

// 数据统计
const dataStats = reactive({
  totalRecords: 15420,
  dataTypes: 12,
  qualityScore: 94,
  storageUsed: 2.8 * 1024 * 1024 * 1024 // 2.8GB
})

// 数据分类
const dataCategories = ref([
  {
    type: 'health',
    name: '健康数据',
    count: 8540,
    todayAdded: 36,
    completeness: 96,
    lastUpdate: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    type: 'activity',
    name: '活动数据',
    count: 3280,
    todayAdded: 48,
    completeness: 89,
    lastUpdate: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    type: 'sleep',
    name: '睡眠数据',
    count: 1850,
    todayAdded: 1,
    completeness: 98,
    lastUpdate: new Date(Date.now() - 8 * 60 * 60 * 1000)
  },
  {
    type: 'environment',
    name: '环境数据',
    count: 920,
    todayAdded: 24,
    completeness: 78,
    lastUpdate: new Date(Date.now() - 10 * 60 * 1000)
  },
  {
    type: 'device',
    name: '设备数据',
    count: 830,
    todayAdded: 12,
    completeness: 92,
    lastUpdate: new Date(Date.now() - 1 * 60 * 1000)
  }
])

// 质量指标
const qualityMetrics = ref([
  {
    name: '数据完整性',
    description: '数据字段完整程度',
    score: 96,
    level: 'excellent'
  },
  {
    name: '数据准确性',
    description: '数据值准确性评估',
    score: 92,
    level: 'good'
  },
  {
    name: '数据一致性',
    description: '跨数据源一致性',
    score: 89,
    level: 'good'
  },
  {
    name: '数据时效性',
    description: '数据更新及时性',
    score: 98,
    level: 'excellent'
  },
  {
    name: '数据唯一性',
    description: '重复数据控制',
    score: 94,
    level: 'excellent'
  }
])

// 数据建议
const dataRecommendations = ref([
  {
    id: 1,
    type: 'improvement',
    priority: 'high',
    title: '环境数据质量提升',
    description: '环境数据完整度较低，建议检查传感器连接状态',
    expectedImprovement: '提升15%数据完整度',
    actionText: '立即检查'
  },
  {
    id: 2,
    type: 'optimization',
    priority: 'medium',
    title: '存储空间优化',
    description: '历史数据可以进行压缩存储，释放空间',
    expectedImprovement: '节省30%存储空间',
    actionText: '开始压缩'
  },
  {
    id: 3,
    type: 'backup',
    priority: 'low',
    title: '数据备份建议',
    description: '建议定期备份重要健康数据',
    expectedImprovement: '提升数据安全性',
    actionText: '设置备份'
  }
])

const updateTrendsChart = () => {
  if (!trendsChartRef.value) return
  
  const chart = echarts.init(trendsChartRef.value, 'health-tech')
  
  // 生成趋势数据
  const days = trendPeriod.value === 'week' ? 7 : trendPeriod.value === 'month' ? 30 : 90
  const timeData = []
  const healthData = []
  const activityData = []
  const sleepData = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    timeData.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    healthData.push(20 + Math.random() * 30)
    activityData.push(10 + Math.random() * 20)
    sleepData.push(1 + Math.random() * 3)
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
      data: ['健康数据', '活动数据', '睡眠数据'],
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
    yAxis: {
      type: 'value',
      name: '记录数',
      axisLabel: {
        color: '#999'
      }
    },
    series: [
      {
        name: '健康数据',
        type: 'line',
        data: healthData,
        smooth: true,
        lineStyle: {
          color: '#66bb6a',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(102, 187, 106, 0.3)' },
              { offset: 1, color: 'rgba(102, 187, 106, 0.1)' }
            ]
          }
        }
      },
      {
        name: '活动数据',
        type: 'line',
        data: activityData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        }
      },
      {
        name: '睡眠数据',
        type: 'line',
        data: sleepData,
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
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStoragePercentage = () => {
  const totalStorage = 10 * 1024 * 1024 * 1024 // 10GB
  return Math.round((dataStats.storageUsed / totalStorage) * 100)
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return date.toLocaleDateString('zh-CN')
}

const getCategoryIcon = (type: string) => {
  const iconMap = {
    health: Monitor,
    activity: TrendUp,
    sleep: Cpu,
    environment: Camera,
    device: Setting
  }
  return iconMap[type as keyof typeof iconMap] || Document
}

const getCompletenessClass = (completeness: number) => {
  if (completeness >= 95) return 'excellent'
  if (completeness >= 85) return 'good'
  if (completeness >= 70) return 'fair'
  return 'poor'
}

const getQualityLevel = () => {
  if (dataStats.qualityScore >= 95) return 'excellent'
  if (dataStats.qualityScore >= 85) return 'good'
  if (dataStats.qualityScore >= 70) return 'fair'
  return 'poor'
}

const getQualityLevelText = () => {
  if (dataStats.qualityScore >= 95) return '优秀'
  if (dataStats.qualityScore >= 85) return '良好'
  if (dataStats.qualityScore >= 70) return '一般'
  return '需改善'
}

const getMetricClass = (score: number) => {
  if (score >= 95) return 'excellent'
  if (score >= 85) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
}

const getMetricTagType = (score: number) => {
  if (score >= 95) return 'success'
  if (score >= 85) return 'primary'
  if (score >= 70) return 'warning'
  return 'danger'
}

const getMetricStatusText = (score: number) => {
  if (score >= 95) return '优秀'
  if (score >= 85) return '良好'
  if (score >= 70) return '一般'
  return '需改善'
}

const getRecommendationIcon = (type: string) => {
  const iconMap = {
    improvement: Warning,
    optimization: Setting,
    backup: Files
  }
  return iconMap[type as keyof typeof iconMap] || Guide
}

// 事件处理
const onDateRangeChange = (range: [Date, Date]) => {
  console.log('Date range changed:', range)
  // 重新加载数据
  refreshData()
}

const exportData = () => {
  ElMessage.info('开始导出数据...')
}

const refreshData = () => {
  ElMessage.info('刷新数据中...')
}

const viewDetails = () => {
  ElMessage.info('查看详细数据')
}

const handleRecommendation = (recommendation: any) => {
  ElMessage.info(`执行建议: ${recommendation.title}`)
}

watch(trendPeriod, () => {
  updateTrendsChart()
})

onMounted(() => {
  nextTick(() => {
    updateTrendsChart()
  })
})
</script>

<style lang="scss" scoped>
.personal-data-stats {
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
  
  .stats-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
}

.data-overview {
  margin-bottom: var(--spacing-lg);
  
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-lg);
    
    .overview-card {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .card-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
      }
      
      .card-content {
        flex: 1;
        
        .card-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: 2px;
        }
        
        .card-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .card-trend {
        display: flex;
        align-items: center;
        gap: 2px;
        font-size: var(--font-xs);
        
        &.positive {
          color: var(--success-500);
        }
        
        &.negative {
          color: var(--error-500);
        }
      }
      
      .card-info {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
      
      &.total-records .card-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
      }
      
      &.data-types .card-icon {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
      }
      
      &.data-quality .card-icon {
        background: linear-gradient(135deg, #ffa726, #ff9800);
      }
      
      &.storage-used .card-icon {
        background: linear-gradient(135deg, #9c27b0, #673ab7);
      }
    }
  }
}

.data-categories {
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
  
  .categories-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
    
    .category-card {
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-light);
      
      .category-header {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        margin-bottom: var(--spacing-md);
        
        .category-icon {
          width: 32px;
          height: 32px;
          border-radius: var(--radius-sm);
          background: var(--primary-500);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 14px;
        }
        
        .category-info {
          .category-name {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 2px;
          }
          
          .category-count {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
      
      .category-stats {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
        margin-bottom: var(--spacing-sm);
        
        .stat-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .stat-label {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
          
          .stat-value {
            font-size: var(--font-xs);
            font-weight: 500;
            color: var(--text-primary);
          }
        }
      }
      
      .category-progress {
        .progress-bar {
          width: 100%;
          height: 4px;
          background: var(--bg-card);
          border-radius: var(--radius-full);
          overflow: hidden;
          
          .progress-fill {
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
      }
    }
  }
}

.data-trends {
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

.data-quality-analysis {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .quality-header {
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
    
    .quality-score {
      text-align: right;
      
      .score-text {
        font-size: var(--font-sm);
        font-weight: 600;
        font-family: var(--font-tech);
        display: block;
        margin-bottom: 2px;
      }
      
      .score-level {
        font-size: var(--font-xs);
      }
      
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
  
  .quality-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .metric-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .metric-info {
        flex: 1;
        
        .metric-name {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .metric-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .metric-score {
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
          min-width: 30px;
        }
      }
      
      .metric-status {
        min-width: 60px;
      }
    }
  }
}

.data-recommendations {
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
    gap: var(--spacing-md);
    
    .recommendation-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .rec-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
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
          margin-bottom: var(--spacing-xs);
        }
        
        .rec-impact {
          font-size: var(--font-xs);
          color: var(--primary-500);
          font-weight: 500;
        }
      }
      
      .rec-action {
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

@media (max-width: 1024px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .categories-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>