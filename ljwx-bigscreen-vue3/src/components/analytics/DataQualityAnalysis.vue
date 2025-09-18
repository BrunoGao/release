<template>
  <div class="data-quality-analysis">
    <div class="analysis-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <DataAnalysis />
        </el-icon>
        <h3 class="analysis-title">数据质量分析</h3>
        <el-tag 
          :type="getQualityScoreType(overallQuality.overall)" 
          class="quality-tag"
        >
          {{ getQualityLevel(overallQuality.overall) }}
        </el-tag>
      </div>
      
      <div class="header-actions">
        <el-button-group>
          <el-button 
            type="primary" 
            size="small"
            @click="refreshAnalysis"
            :loading="isLoading"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button 
            size="small"
            @click="exportReport"
          >
            <el-icon><Download /></el-icon>
            导出
          </el-button>
          <el-dropdown @command="handleTimeRangeChange">
            <el-button size="small">
              {{ currentTimeRange.label }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="hour">最近1小时</el-dropdown-item>
                <el-dropdown-item command="day">最近1天</el-dropdown-item>
                <el-dropdown-item command="week">最近1周</el-dropdown-item>
                <el-dropdown-item command="month">最近1月</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-button-group>
      </div>
    </div>

    <!-- 总体质量概览 -->
    <div class="quality-overview">
      <div class="overview-chart">
        <div class="chart-container" ref="qualityGaugeRef">
          <!-- ECharts 总体质量仪表盘 -->
        </div>
      </div>
      
      <div class="overview-details">
        <div class="quality-metrics">
          <div 
            v-for="(value, key) in overallQuality" 
            :key="key"
            class="metric-item"
            :class="getMetricClass(value)"
          >
            <div class="metric-header">
              <span class="metric-name">{{ getMetricName(key) }}</span>
              <span class="metric-value">{{ value }}%</span>
            </div>
            <div class="metric-bar">
              <div 
                class="metric-fill" 
                :style="{ 
                  width: `${value}%`,
                  backgroundColor: getQualityColor(value)
                }"
              />
            </div>
            <div class="metric-status">
              <el-icon>
                <component :is="getMetricIcon(value)" />
              </el-icon>
              <span>{{ getQualityStatus(value) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据源质量分析 -->
    <div class="data-sources-analysis">
      <div class="section-header">
        <h4>数据源质量</h4>
        <div class="sources-filter">
          <el-select 
            v-model="selectedDataSource" 
            size="small" 
            placeholder="选择数据源"
            @change="onDataSourceChange"
          >
            <el-option label="全部数据源" value="all" />
            <el-option label="心率监测" value="heart_rate" />
            <el-option label="血氧监测" value="blood_oxygen" />
            <el-option label="血压监测" value="blood_pressure" />
            <el-option label="体温监测" value="temperature" />
            <el-option label="运动数据" value="exercise" />
            <el-option label="睡眠数据" value="sleep" />
          </el-select>
        </div>
      </div>
      
      <div class="sources-grid">
        <div 
          v-for="source in filteredDataSources" 
          :key="source.id"
          class="source-card"
          :class="getSourceStatusClass(source.quality.overall)"
        >
          <div class="source-header">
            <div class="source-info">
              <el-icon class="source-icon">
                <component :is="getSourceIcon(source.type)" />
              </el-icon>
              <div>
                <h5 class="source-name">{{ source.name }}</h5>
                <span class="source-type">{{ getSourceTypeLabel(source.type) }}</span>
              </div>
            </div>
            <div class="source-score">
              <span class="score-number">{{ source.quality.overall }}</span>
              <span class="score-unit">%</span>
            </div>
          </div>
          
          <div class="source-metrics">
            <div class="mini-metrics">
              <div class="mini-metric">
                <span class="mini-label">完整性</span>
                <div class="mini-progress">
                  <div 
                    class="mini-fill" 
                    :style="{ 
                      width: `${source.quality.completeness}%`,
                      backgroundColor: getQualityColor(source.quality.completeness)
                    }"
                  />
                </div>
                <span class="mini-value">{{ source.quality.completeness }}%</span>
              </div>
              <div class="mini-metric">
                <span class="mini-label">准确性</span>
                <div class="mini-progress">
                  <div 
                    class="mini-fill" 
                    :style="{ 
                      width: `${source.quality.accuracy}%`,
                      backgroundColor: getQualityColor(source.quality.accuracy)
                    }"
                  />
                </div>
                <span class="mini-value">{{ source.quality.accuracy }}%</span>
              </div>
              <div class="mini-metric">
                <span class="mini-label">及时性</span>
                <div class="mini-progress">
                  <div 
                    class="mini-fill" 
                    :style="{ 
                      width: `${source.quality.timeliness}%`,
                      backgroundColor: getQualityColor(source.quality.timeliness)
                    }"
                  />
                </div>
                <span class="mini-value">{{ source.quality.timeliness }}%</span>
              </div>
            </div>
          </div>
          
          <div class="source-status">
            <el-tag 
              :type="getQualityScoreType(source.quality.overall)" 
              size="small"
            >
              {{ getQualityLevel(source.quality.overall) }}
            </el-tag>
            <span class="last-update">
              更新于 {{ formatTime(source.lastUpdate) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 质量趋势分析 -->
    <div class="quality-trends">
      <div class="section-header">
        <h4>质量趋势</h4>
        <div class="trend-controls">
          <el-radio-group 
            v-model="trendMetric" 
            size="small"
            @change="updateTrendChart"
          >
            <el-radio-button label="overall">总体</el-radio-button>
            <el-radio-button label="completeness">完整性</el-radio-button>
            <el-radio-button label="accuracy">准确性</el-radio-button>
            <el-radio-button label="timeliness">及时性</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <div class="trend-chart-container" ref="trendChartRef">
        <!-- ECharts 趋势图 -->
      </div>
    </div>

    <!-- 问题识别和建议 -->
    <div class="issues-recommendations">
      <div class="issues-section">
        <div class="section-header">
          <h4>
            <el-icon class="section-icon warning">
              <Warning />
            </el-icon>
            发现的问题
          </h4>
        </div>
        
        <div class="issues-list">
          <div 
            v-for="issue in qualityIssues" 
            :key="issue.id"
            class="issue-item"
            :class="issue.severity"
          >
            <div class="issue-indicator">
              <el-icon>
                <component :is="getIssueIcon(issue.severity)" />
              </el-icon>
            </div>
            <div class="issue-content">
              <h5 class="issue-title">{{ issue.title }}</h5>
              <p class="issue-description">{{ issue.description }}</p>
              <div class="issue-impact">
                影响范围: {{ issue.affectedSources.join(', ') }}
              </div>
            </div>
            <div class="issue-actions">
              <el-button 
                size="small" 
                type="primary" 
                @click="resolveIssue(issue)"
              >
                处理
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="recommendations-section">
        <div class="section-header">
          <h4>
            <el-icon class="section-icon success">
              <Lightbulb />
            </el-icon>
            优化建议
          </h4>
        </div>
        
        <div class="recommendations-list">
          <div 
            v-for="recommendation in qualityRecommendations" 
            :key="recommendation.id"
            class="recommendation-item"
          >
            <div class="recommendation-priority">
              <el-tag 
                :type="getPriorityType(recommendation.priority)" 
                size="small"
              >
                {{ recommendation.priority }}
              </el-tag>
            </div>
            <div class="recommendation-content">
              <h5 class="recommendation-title">{{ recommendation.title }}</h5>
              <p class="recommendation-description">{{ recommendation.description }}</p>
              <div class="recommendation-benefit">
                预期提升: {{ recommendation.expectedImprovement }}%
              </div>
            </div>
            <div class="recommendation-actions">
              <el-button 
                size="small" 
                @click="implementRecommendation(recommendation)"
              >
                采纳
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
  DataAnalysis, 
  Refresh, 
  Download, 
  ArrowDown,
  Warning,
  Lightbulb,
  CircleCheck,
  InfoFilled,
  Heart,
  Activity,
  Stopwatch,
  TrendCharts
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'
import type { DataQuality } from '@/types/health'

interface DataSource {
  id: string
  name: string
  type: string
  quality: DataQuality
  lastUpdate: Date
  status: 'active' | 'inactive' | 'error'
  dataCount: number
}

interface QualityIssue {
  id: string
  title: string
  description: string
  severity: 'high' | 'medium' | 'low'
  affectedSources: string[]
  suggestedAction: string
}

interface QualityRecommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  expectedImprovement: number
  effort: 'low' | 'medium' | 'high'
}

// 响应式数据
const isLoading = ref(false)
const selectedDataSource = ref('all')
const trendMetric = ref<keyof DataQuality>('overall')

// 时间范围
const currentTimeRange = ref({
  value: 'day',
  label: '最近1天'
})

// 总体质量数据
const overallQuality = reactive<DataQuality>({
  completeness: 87,
  accuracy: 94,
  timeliness: 92,
  consistency: 89,
  overall: 90,
  lastUpdated: new Date()
})

// 数据源质量
const dataSources = ref<DataSource[]>([
  {
    id: 'heart_rate_001',
    name: '心率监测设备',
    type: 'heart_rate',
    quality: {
      completeness: 95,
      accuracy: 98,
      timeliness: 96,
      consistency: 93,
      overall: 95,
      lastUpdated: new Date()
    },
    lastUpdate: new Date(Date.now() - 300000),
    status: 'active',
    dataCount: 1240
  },
  {
    id: 'blood_oxygen_001',
    name: '血氧监测设备',
    type: 'blood_oxygen',
    quality: {
      completeness: 82,
      accuracy: 90,
      timeliness: 88,
      consistency: 85,
      overall: 86,
      lastUpdated: new Date()
    },
    lastUpdate: new Date(Date.now() - 600000),
    status: 'active',
    dataCount: 980
  },
  {
    id: 'sleep_001',
    name: '睡眠监测系统',
    type: 'sleep',
    quality: {
      completeness: 78,
      accuracy: 85,
      timeliness: 75,
      consistency: 80,
      overall: 79,
      lastUpdated: new Date()
    },
    lastUpdate: new Date(Date.now() - 900000),
    status: 'error',
    dataCount: 450
  }
])

// 质量问题
const qualityIssues = ref<QualityIssue[]>([
  {
    id: 'issue_001',
    title: '睡眠数据缺失',
    description: '过去48小时内有30%的睡眠数据缺失，影响睡眠质量评估准确性',
    severity: 'high',
    affectedSources: ['睡眠监测系统'],
    suggestedAction: '检查设备连接状态并重新同步数据'
  },
  {
    id: 'issue_002',
    title: '数据时间戳不一致',
    description: '部分设备的时间戳存在偏差，可能影响数据关联分析',
    severity: 'medium',
    affectedSources: ['心率监测设备', '血氧监测设备'],
    suggestedAction: '统一设备时间同步机制'
  }
])

// 优化建议
const qualityRecommendations = ref<QualityRecommendation[]>([
  {
    id: 'rec_001',
    title: '实施数据验证规则',
    description: '为关键健康指标设置数据范围验证，自动识别异常数据',
    priority: 'high',
    expectedImprovement: 15,
    effort: 'medium'
  },
  {
    id: 'rec_002',
    title: '优化数据收集频率',
    description: '根据指标重要性调整数据收集频率，提高关键数据的完整性',
    priority: 'medium',
    expectedImprovement: 8,
    effort: 'low'
  }
])

// 模板引用
const qualityGaugeRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()

// 计算属性
const filteredDataSources = computed(() => {
  if (selectedDataSource.value === 'all') {
    return dataSources.value
  }
  return dataSources.value.filter(source => source.type === selectedDataSource.value)
})

// 方法
const refreshAnalysis = async () => {
  isLoading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 更新数据
    overallQuality.overall = Math.floor(Math.random() * 20) + 80
    overallQuality.lastUpdated = new Date()
    
    ElMessage.success('数据质量分析已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    isLoading.value = false
  }
}

const exportReport = () => {
  ElMessage.success('质量报告导出完成')
}

const handleTimeRangeChange = (command: string) => {
  const timeRangeMap = {
    hour: '最近1小时',
    day: '最近1天',
    week: '最近1周',
    month: '最近1月'
  }
  
  currentTimeRange.value = {
    value: command,
    label: timeRangeMap[command as keyof typeof timeRangeMap]
  }
  
  updateTrendChart()
}

const onDataSourceChange = () => {
  // 数据源筛选变化处理
  console.log('数据源筛选变化:', selectedDataSource.value)
}

const resolveIssue = (issue: QualityIssue) => {
  ElMessage.success(`正在处理问题: ${issue.title}`)
}

const implementRecommendation = (recommendation: QualityRecommendation) => {
  ElMessage.success(`已采纳建议: ${recommendation.title}`)
}

// 工具方法
const getQualityLevel = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  return '较差'
}

const getQualityScoreType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 80) return ''
  if (score >= 70) return 'warning'
  return 'danger'
}

const getQualityColor = (score: number) => {
  if (score >= 90) return '#00ff9d'
  if (score >= 80) return '#66bb6a'
  if (score >= 70) return '#ffa726'
  return '#ff6b6b'
}

const getQualityStatus = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '需改进'
  return '问题较多'
}

const getMetricName = (key: string) => {
  const nameMap = {
    completeness: '完整性',
    accuracy: '准确性',
    timeliness: '及时性',
    consistency: '一致性',
    overall: '总体质量'
  }
  return nameMap[key as keyof typeof nameMap] || key
}

const getMetricClass = (value: number) => {
  if (value >= 90) return 'excellent'
  if (value >= 80) return 'good'
  if (value >= 70) return 'fair'
  return 'poor'
}

const getMetricIcon = (value: number) => {
  if (value >= 90) return CircleCheck
  if (value >= 70) return InfoFilled
  return Warning
}

const getSourceIcon = (type: string) => {
  const iconMap = {
    heart_rate: Heart,
    blood_oxygen: Activity,
    sleep: Stopwatch,
    exercise: TrendCharts
  }
  return iconMap[type as keyof typeof iconMap] || DataAnalysis
}

const getSourceTypeLabel = (type: string) => {
  const labelMap = {
    heart_rate: '心率监测',
    blood_oxygen: '血氧监测',
    blood_pressure: '血压监测',
    temperature: '体温监测',
    exercise: '运动数据',
    sleep: '睡眠数据'
  }
  return labelMap[type as keyof typeof labelMap] || type
}

const getSourceStatusClass = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
}

const getIssueIcon = (severity: string) => {
  const iconMap = {
    high: Warning,
    medium: InfoFilled,
    low: InfoFilled
  }
  return iconMap[severity as keyof typeof iconMap] || InfoFilled
}

const getPriorityType = (priority: string) => {
  const typeMap = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return typeMap[priority as keyof typeof typeMap] || 'info'
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return timestamp.toLocaleDateString()
}

// 图表初始化
const initQualityGauge = () => {
  if (!qualityGaugeRef.value) return
  
  const chart = echarts.init(qualityGaugeRef.value, 'health-tech')
  
  const option = {
    series: [{
      type: 'gauge',
      min: 0,
      max: 100,
      radius: '80%',
      axisLine: {
        lineStyle: {
          width: 10,
          color: [
            [0.7, '#ff6b6b'],
            [0.8, '#ffa726'],
            [0.9, '#66bb6a'],
            [1, '#00ff9d']
          ]
        }
      },
      pointer: {
        itemStyle: {
          color: '#00e4ff'
        }
      },
      detail: {
        valueAnimation: true,
        fontSize: 24,
        fontWeight: 'bold',
        color: '#00ff9d',
        formatter: '{value}%'
      },
      data: [{
        value: overallQuality.overall,
        name: '数据质量'
      }]
    }]
  }
  
  chart.setOption(option)
  
  // 响应式调整
  const resizeChart = () => chart.resize()
  window.addEventListener('resize', resizeChart)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chart.dispose()
  })
}

const updateTrendChart = () => {
  if (!trendChartRef.value) return
  
  const chart = echarts.init(trendChartRef.value, 'health-tech')
  
  // 生成模拟趋势数据
  const xData = []
  const yData = []
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 3600000) // 每小时
    xData.push(time.getHours() + ':00')
    yData.push(Math.floor(Math.random() * 20) + 80) // 80-100之间的随机值
  }
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: {
        color: '#999'
      }
    },
    yAxis: {
      type: 'value',
      min: 60,
      max: 100,
      axisLabel: {
        color: '#999',
        formatter: '{value}%'
      }
    },
    series: [{
      data: yData,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#00ff9d',
        width: 3
      },
      itemStyle: {
        color: '#00ff9d'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(0, 255, 157, 0.3)'
          }, {
            offset: 1,
            color: 'rgba(0, 255, 157, 0.05)'
          }]
        }
      }
    }]
  }
  
  chart.setOption(option)
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initQualityGauge()
    updateTrendChart()
  })
})
</script>

<style lang="scss" scoped>
.data-quality-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

// ========== 分析头部 ==========
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(0, 255, 157, 0.02) 100%);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .analysis-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .quality-tag {
      margin-left: var(--spacing-sm);
    }
  }
}

// ========== 质量概览 ==========
.quality-overview {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .overview-chart {
    .chart-container {
      width: 200px;
      height: 200px;
    }
  }
  
  .overview-details {
    flex: 1;
    
    .quality-metrics {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
      
      .metric-item {
        padding: var(--spacing-md);
        background: var(--bg-elevated);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-light);
        
        .metric-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-sm);
          
          .metric-name {
            font-weight: 600;
            color: var(--text-primary);
          }
          
          .metric-value {
            font-size: var(--font-lg);
            font-weight: 700;
            color: var(--primary-500);
            font-family: var(--font-tech);
          }
        }
        
        .metric-bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-full);
          overflow: hidden;
          margin-bottom: var(--spacing-sm);
          
          .metric-fill {
            height: 100%;
            border-radius: var(--radius-full);
            transition: width 1s ease;
          }
        }
        
        .metric-status {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
}

// ========== 数据源分析 ==========
.data-sources-analysis {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .section-header {
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
  
  .sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: var(--spacing-lg);
    
    .source-card {
      padding: var(--spacing-lg);
      background: var(--bg-elevated);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-light);
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
      }
      
      .source-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: var(--spacing-lg);
        
        .source-info {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          
          .source-icon {
            width: 40px;
            height: 40px;
            background: var(--primary-500);
            color: white;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
          }
          
          .source-name {
            font-size: var(--font-md);
            font-weight: 600;
            color: var(--text-primary);
            margin: 0 0 var(--spacing-xs) 0;
          }
          
          .source-type {
            font-size: var(--font-sm);
            color: var(--text-secondary);
          }
        }
        
        .source-score {
          text-align: right;
          
          .score-number {
            font-size: var(--font-xxl);
            font-weight: 700;
            color: var(--primary-500);
            font-family: var(--font-tech);
          }
          
          .score-unit {
            font-size: var(--font-md);
            color: var(--text-secondary);
          }
        }
      }
      
      .source-metrics {
        margin-bottom: var(--spacing-md);
        
        .mini-metrics {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
          
          .mini-metric {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            
            .mini-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
              width: 60px;
              flex-shrink: 0;
            }
            
            .mini-progress {
              flex: 1;
              height: 6px;
              background: rgba(255, 255, 255, 0.1);
              border-radius: var(--radius-full);
              overflow: hidden;
              
              .mini-fill {
                height: 100%;
                border-radius: var(--radius-full);
                transition: width 0.8s ease;
              }
            }
            
            .mini-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 600;
              font-family: var(--font-tech);
              width: 35px;
              text-align: right;
            }
          }
        }
      }
      
      .source-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .last-update {
          font-size: var(--font-xs);
          color: var(--text-muted);
        }
      }
      
      &.excellent {
        border-color: var(--success-300);
        
        .source-header .source-icon {
          background: linear-gradient(135deg, var(--success-500), var(--success-600));
        }
      }
      
      &.good {
        border-color: var(--primary-300);
      }
      
      &.fair {
        border-color: var(--warning-300);
        
        .source-header .source-icon {
          background: linear-gradient(135deg, var(--warning-500), var(--warning-600));
        }
      }
      
      &.poor {
        border-color: var(--error-300);
        
        .source-header .source-icon {
          background: linear-gradient(135deg, var(--error-500), var(--error-600));
        }
      }
    }
  }
}

// ========== 质量趋势 ==========
.quality-trends {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .section-header {
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
  
  .trend-chart-container {
    height: 300px;
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
  }
}

// ========== 问题和建议 ==========
.issues-recommendations {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  overflow-y: auto;
  
  .issues-section,
  .recommendations-section {
    .section-header {
      margin-bottom: var(--spacing-lg);
      
      h4 {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-size: var(--font-md);
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        
        .section-icon {
          font-size: 18px;
          
          &.warning {
            color: var(--warning-500);
          }
          
          &.success {
            color: var(--success-500);
          }
        }
      }
    }
  }
  
  .issues-list,
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .issue-item,
  .recommendation-item {
    display: flex;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--primary-300);
      transform: translateX(4px);
    }
  }
  
  .issue-indicator,
  .recommendation-priority {
    flex-shrink: 0;
    display: flex;
    align-items: flex-start;
    padding-top: var(--spacing-xs);
  }
  
  .issue-content,
  .recommendation-content {
    flex: 1;
    
    .issue-title,
    .recommendation-title {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-xs) 0;
    }
    
    .issue-description,
    .recommendation-description {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      line-height: 1.4;
      margin-bottom: var(--spacing-sm);
    }
    
    .issue-impact,
    .recommendation-benefit {
      font-size: var(--font-xs);
      color: var(--text-muted);
      font-style: italic;
    }
  }
  
  .issue-actions,
  .recommendation-actions {
    display: flex;
    align-items: flex-start;
    padding-top: var(--spacing-xs);
  }
  
  .issue-item {
    &.high {
      border-left: 4px solid var(--error-500);
    }
    
    &.medium {
      border-left: 4px solid var(--warning-500);
    }
    
    &.low {
      border-left: 4px solid var(--info-500);
    }
  }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .quality-overview {
    flex-direction: column;
    
    .overview-chart .chart-container {
      width: 150px;
      height: 150px;
      margin: 0 auto;
    }
  }
  
  .sources-grid {
    grid-template-columns: 1fr;
  }
  
  .issues-recommendations {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analysis-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .data-quality-analysis {
    .section-header {
      flex-direction: column;
      gap: var(--spacing-sm);
      align-items: stretch;
    }
  }
}
</style>