<template>
  <div class="sleep-quality-analysis">
    <div class="analysis-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Clock />
        </el-icon>
        <h3 class="analysis-title">{{ title }}</h3>
      </div>
      
      <div class="analysis-controls">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="onDateChange"
        />
        <el-button-group size="small">
          <el-button @click="generateReport">
            <el-icon><Document /></el-icon>
            生成报告
          </el-button>
          <el-button @click="exportData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 睡眠质量概览 -->
    <div class="sleep-overview">
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
                :stroke="getSleepScoreColor()"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${sleepData.qualityScore} 100`"
                transform="rotate(-90 21 21)"
              />
            </svg>
            <div class="score-text">{{ sleepData.qualityScore }}</div>
          </div>
          <div class="score-info">
            <div class="score-label">睡眠质量评分</div>
            <div class="score-level" :class="getSleepScoreLevel()">
              {{ getSleepScoreText() }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="overview-card sleep-duration">
        <div class="card-header">
          <el-icon><Timer /></el-icon>
          <span>平均睡眠时长</span>
        </div>
        <div class="duration-display">
          <div class="duration-value">{{ sleepData.averageDuration }}h</div>
          <div class="duration-target">目标: 8h</div>
          <div class="duration-trend" :class="sleepData.durationTrend">
            <el-icon>
              <component :is="getTrendIcon(sleepData.durationTrend)" />
            </el-icon>
            <span>{{ getTrendText(sleepData.durationTrend) }}</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card sleep-efficiency">
        <div class="card-header">
          <el-icon><TrendUp /></el-icon>
          <span>睡眠效率</span>
        </div>
        <div class="efficiency-display">
          <div class="efficiency-meter">
            <div 
              class="efficiency-fill" 
              :style="{ width: sleepData.efficiency + '%' }"
              :class="getEfficiencyClass()"
            ></div>
          </div>
          <div class="efficiency-value">{{ sleepData.efficiency }}%</div>
          <div class="efficiency-description">{{ getEfficiencyDescription() }}</div>
        </div>
      </div>
      
      <div class="overview-card sleep-stages">
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>睡眠阶段</span>
        </div>
        <div class="stages-chart" ref="stagesChartRef"></div>
      </div>
    </div>
    
    <!-- 睡眠趋势图表 -->
    <div class="sleep-trends">
      <div class="trends-header">
        <h4>睡眠趋势分析</h4>
        <el-radio-group v-model="trendPeriod" size="small">
          <el-radio-button label="week">近7天</el-radio-button>
          <el-radio-button label="month">近30天</el-radio-button>
          <el-radio-button label="quarter">近3个月</el-radio-button>
        </el-radio-group>
      </div>
      <div class="chart-container" ref="trendsChartRef"></div>
    </div>
    
    <!-- 睡眠模式分析 -->
    <div class="sleep-patterns">
      <div class="patterns-header">
        <h4>睡眠模式分析</h4>
      </div>
      
      <div class="patterns-grid">
        <div class="pattern-card bedtime">
          <div class="pattern-icon">
            <el-icon><Sunset /></el-icon>
          </div>
          <div class="pattern-content">
            <div class="pattern-title">就寝时间</div>
            <div class="pattern-stats">
              <div class="stat-item">
                <span class="stat-label">平均时间</span>
                <span class="stat-value">{{ sleepPatterns.averageBedtime }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">最早</span>
                <span class="stat-value">{{ sleepPatterns.earliestBedtime }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">最晚</span>
                <span class="stat-value">{{ sleepPatterns.latestBedtime }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="pattern-card waketime">
          <div class="pattern-icon">
            <el-icon><Sunrise /></el-icon>
          </div>
          <div class="pattern-content">
            <div class="pattern-title">起床时间</div>
            <div class="pattern-stats">
              <div class="stat-item">
                <span class="stat-label">平均时间</span>
                <span class="stat-value">{{ sleepPatterns.averageWakeTime }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">最早</span>
                <span class="stat-value">{{ sleepPatterns.earliestWakeTime }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">最晚</span>
                <span class="stat-value">{{ sleepPatterns.latestWakeTime }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="pattern-card consistency">
          <div class="pattern-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="pattern-content">
            <div class="pattern-title">睡眠规律性</div>
            <div class="pattern-score">
              <div class="score-ring">
                <div class="ring-progress" :style="{ '--progress': sleepPatterns.consistency + '%' }">
                  <span class="score-value">{{ sleepPatterns.consistency }}%</span>
                </div>
              </div>
              <div class="score-description">{{ getConsistencyDescription() }}</div>
            </div>
          </div>
        </div>
        
        <div class="pattern-card disturbances">
          <div class="pattern-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="pattern-content">
            <div class="pattern-title">睡眠干扰</div>
            <div class="pattern-stats">
              <div class="stat-item">
                <span class="stat-label">平均次数</span>
                <span class="stat-value">{{ sleepPatterns.averageDisturbances }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">主要原因</span>
                <span class="stat-value">{{ sleepPatterns.mainCause }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">持续时间</span>
                <span class="stat-value">{{ sleepPatterns.disturbanceDuration }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 睡眠建议 -->
    <div class="sleep-recommendations">
      <div class="recommendations-header">
        <h4>睡眠改善建议</h4>
        <el-tag :type="getRecommendationLevel()" size="small">
          {{ getRecommendationText() }}
        </el-tag>
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in sleepRecommendations" 
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
            <el-tag :type="getPriorityType(recommendation.priority)" size="small">
              {{ getPriorityText(recommendation.priority) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 睡眠环境监测 -->
    <div class="sleep-environment">
      <div class="environment-header">
        <h4>睡眠环境监测</h4>
        <el-button size="small" @click="calibrateEnvironment">
          <el-icon><Setting /></el-icon>
          环境校准
        </el-button>
      </div>
      
      <div class="environment-grid">
        <div 
          v-for="factor in environmentFactors" 
          :key="factor.name"
          class="factor-card"
          :class="factor.status"
        >
          <div class="factor-header">
            <el-icon>
              <component :is="getEnvironmentIcon(factor.type)" />
            </el-icon>
            <span class="factor-name">{{ factor.name }}</span>
          </div>
          <div class="factor-value">{{ factor.value }} {{ factor.unit }}</div>
          <div class="factor-range">
            <span class="range-text">理想范围: {{ factor.idealRange }}</span>
            <div class="range-indicator" :class="factor.status"></div>
          </div>
          <div class="factor-impact">
            影响程度: {{ factor.impact }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Clock, 
  Document, 
  Download, 
  Timer, 
  TrendUp,
  TrendDown,
  Minus,
  DataAnalysis,
  Sunset,
  Sunrise,
  CircleCheck,
  Warning,
  Setting,
  Sunny,
  Drizzling,
  WindPower,
  Headphones
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '睡眠质量分析',
  userId: ''
})

const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
  new Date()
])
const trendPeriod = ref('month')
const trendsChartRef = ref<HTMLElement>()
const stagesChartRef = ref<HTMLElement>()

// 睡眠数据
const sleepData = reactive({
  qualityScore: 82,
  averageDuration: 7.2,
  durationTrend: 'stable', // up, down, stable
  efficiency: 89
})

// 睡眠模式
const sleepPatterns = reactive({
  averageBedtime: '22:45',
  earliestBedtime: '21:30',
  latestBedtime: '00:15',
  averageWakeTime: '06:30',
  earliestWakeTime: '05:45',
  latestWakeTime: '07:30',
  consistency: 75,
  averageDisturbances: 2.3,
  mainCause: '噪音干扰',
  disturbanceDuration: '15分钟'
})

// 睡眠建议
const sleepRecommendations = ref([
  {
    id: 1,
    type: 'schedule',
    priority: 'high',
    title: '规律作息时间',
    description: '建议保持固定的就寝和起床时间，提高睡眠规律性',
    actions: ['设置提醒', '制定计划']
  },
  {
    id: 2,
    type: 'environment',
    priority: 'medium',
    title: '优化睡眠环境',
    description: '降低卧室噪音，调节合适的温度和湿度',
    actions: ['检查环境', '调整设置']
  },
  {
    id: 3,
    type: 'habit',
    priority: 'low',
    title: '睡前习惯调整',
    description: '建立良好的睡前例行程序，避免蓝光暴露',
    actions: ['查看建议', '设置提醒']
  }
])

// 环境因子
const environmentFactors = ref([
  {
    name: '温度',
    type: 'temperature',
    value: 23.5,
    unit: '°C',
    idealRange: '18-22°C',
    status: 'warning',
    impact: '中等'
  },
  {
    name: '湿度',
    type: 'humidity',
    value: 45,
    unit: '%',
    idealRange: '40-60%',
    status: 'normal',
    impact: '轻微'
  },
  {
    name: '噪音',
    type: 'noise',
    value: 35,
    unit: 'dB',
    idealRange: '<30dB',
    status: 'warning',
    impact: '较高'
  },
  {
    name: '光照',
    type: 'light',
    value: 5,
    unit: 'lux',
    idealRange: '<10lux',
    status: 'normal',
    impact: '轻微'
  }
])

const updateTrendsChart = () => {
  if (!trendsChartRef.value) return
  
  const chart = echarts.init(trendsChartRef.value, 'health-tech')
  
  // 生成趋势数据
  const days = trendPeriod.value === 'week' ? 7 : trendPeriod.value === 'month' ? 30 : 90
  const timeData = []
  const durationData = []
  const qualityData = []
  const efficiencyData = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    timeData.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    durationData.push(6 + Math.random() * 3) // 6-9小时
    qualityData.push(70 + Math.random() * 25) // 70-95分
    efficiencyData.push(80 + Math.random() * 15) // 80-95%
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
      data: ['睡眠时长', '质量评分', '睡眠效率'],
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
        name: '时长(小时)/评分',
        position: 'left',
        axisLabel: {
          color: '#999'
        }
      },
      {
        type: 'value',
        name: '效率(%)',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '睡眠时长',
        type: 'line',
        yAxisIndex: 0,
        data: durationData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
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
              { offset: 0, color: 'rgba(66, 165, 245, 0.3)' },
              { offset: 1, color: 'rgba(66, 165, 245, 0.1)' }
            ]
          }
        }
      },
      {
        name: '质量评分',
        type: 'line',
        yAxisIndex: 0,
        data: qualityData,
        smooth: true,
        lineStyle: {
          color: '#66bb6a',
          width: 2
        }
      },
      {
        name: '睡眠效率',
        type: 'line',
        yAxisIndex: 1,
        data: efficiencyData,
        smooth: true,
        lineStyle: {
          color: '#ffa726',
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

const updateStagesChart = () => {
  if (!stagesChartRef.value) return
  
  const chart = echarts.init(stagesChartRef.value, 'health-tech')
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: [
          { value: 15, name: '深度睡眠', itemStyle: { color: '#2196f3' } },
          { value: 50, name: '浅度睡眠', itemStyle: { color: '#42a5f5' } },
          { value: 20, name: 'REM睡眠', itemStyle: { color: '#66bb6a' } },
          { value: 15, name: '清醒', itemStyle: { color: '#ffa726' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: false
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 工具方法
const getSleepScoreColor = () => {
  if (sleepData.qualityScore >= 85) return 'var(--success-500)'
  if (sleepData.qualityScore >= 70) return 'var(--primary-500)'
  if (sleepData.qualityScore >= 60) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getSleepScoreLevel = () => {
  if (sleepData.qualityScore >= 85) return 'excellent'
  if (sleepData.qualityScore >= 70) return 'good'
  if (sleepData.qualityScore >= 60) return 'fair'
  return 'poor'
}

const getSleepScoreText = () => {
  if (sleepData.qualityScore >= 85) return '睡眠优质'
  if (sleepData.qualityScore >= 70) return '睡眠良好'
  if (sleepData.qualityScore >= 60) return '睡眠一般'
  return '睡眠较差'
}

const getTrendIcon = (trend: string) => {
  const iconMap = {
    up: TrendUp,
    down: TrendDown,
    stable: Minus
  }
  return iconMap[trend as keyof typeof iconMap] || Minus
}

const getTrendText = (trend: string) => {
  const textMap = {
    up: '时长增加',
    down: '时长减少',
    stable: '时长稳定'
  }
  return textMap[trend as keyof typeof textMap] || '时长稳定'
}

const getEfficiencyClass = () => {
  if (sleepData.efficiency >= 90) return 'excellent'
  if (sleepData.efficiency >= 80) return 'good'
  if (sleepData.efficiency >= 70) return 'fair'
  return 'poor'
}

const getEfficiencyDescription = () => {
  if (sleepData.efficiency >= 90) return '效率优秀'
  if (sleepData.efficiency >= 80) return '效率良好'
  if (sleepData.efficiency >= 70) return '效率一般'
  return '效率较低'
}

const getConsistencyDescription = () => {
  if (sleepPatterns.consistency >= 80) return '作息规律'
  if (sleepPatterns.consistency >= 60) return '基本规律'
  return '作息不规律'
}

const getRecommendationLevel = () => {
  const hasHighPriority = sleepRecommendations.value.some(r => r.priority === 'high')
  if (hasHighPriority) return 'warning'
  const hasMediumPriority = sleepRecommendations.value.some(r => r.priority === 'medium')
  if (hasMediumPriority) return 'primary'
  return 'success'
}

const getRecommendationText = () => {
  const hasHighPriority = sleepRecommendations.value.some(r => r.priority === 'high')
  if (hasHighPriority) return '需要改善'
  const hasMediumPriority = sleepRecommendations.value.some(r => r.priority === 'medium')
  if (hasMediumPriority) return '建议优化'
  return '状态良好'
}

const getRecommendationIcon = (type: string) => {
  const iconMap = {
    schedule: Clock,
    environment: Setting,
    habit: CircleCheck
  }
  return iconMap[type as keyof typeof iconMap] || Setting
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

const getEnvironmentIcon = (type: string) => {
  const iconMap = {
    temperature: Sunny,
    humidity: Drizzling,
    noise: Headphones,
    light: Sunny
  }
  return iconMap[type as keyof typeof iconMap] || Setting
}

// 事件处理
const onDateChange = (range: [Date, Date]) => {
  console.log('Date range changed:', range)
}

const generateReport = () => {
  ElMessage.info('生成睡眠质量报告')
}

const exportData = () => {
  ElMessage.info('导出睡眠数据')
}

const handleRecommendationAction = (recommendation: any, action: string) => {
  ElMessage.info(`执行建议: ${recommendation.title} - ${action}`)
}

const calibrateEnvironment = () => {
  ElMessage.info('开始环境校准')
}

watch(trendPeriod, () => {
  updateTrendsChart()
})

onMounted(() => {
  nextTick(() => {
    updateTrendsChart()
    updateStagesChart()
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
  overflow: hidden;
}

.analysis-header {
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
    
    .analysis-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .analysis-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
}

.sleep-overview {
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
    
    &.sleep-duration {
      text-align: center;
      
      .duration-display {
        .duration-value {
          font-size: var(--font-xl);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: var(--spacing-xs);
        }
        
        .duration-target {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .duration-trend {
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
    
    &.sleep-efficiency {
      .efficiency-display {
        .efficiency-meter {
          width: 100%;
          height: 8px;
          background: var(--bg-secondary);
          border-radius: var(--radius-full);
          overflow: hidden;
          margin-bottom: var(--spacing-sm);
          
          .efficiency-fill {
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
        
        .efficiency-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          text-align: center;
          margin-bottom: var(--spacing-xs);
        }
        
        .efficiency-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          text-align: center;
        }
      }
    }
    
    &.sleep-stages {
      .stages-chart {
        height: 120px;
      }
    }
  }
}

.sleep-trends {
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

.sleep-patterns {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .patterns-header {
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .patterns-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
    
    .pattern-card {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .pattern-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        flex-shrink: 0;
      }
      
      .pattern-content {
        flex: 1;
        
        .pattern-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-sm);
        }
        
        .pattern-stats {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-xs);
          
          .stat-item {
            display: flex;
            justify-content: space-between;
            
            .stat-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
            
            .stat-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 500;
            }
          }
        }
        
        .pattern-score {
          text-align: center;
          
          .score-ring {
            margin: 0 auto var(--spacing-sm) auto;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: conic-gradient(var(--primary-500) calc(var(--progress) * 1%), var(--bg-card) 0%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            
            &::before {
              content: '';
              position: absolute;
              width: 70%;
              height: 70%;
              background: var(--bg-secondary);
              border-radius: 50%;
            }
            
            .score-value {
              position: relative;
              z-index: 1;
              font-size: var(--font-sm);
              font-weight: 700;
              color: var(--text-primary);
              font-family: var(--font-tech);
            }
          }
          
          .score-description {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
    }
  }
}

.sleep-recommendations {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
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
        border-radius: var(--radius-sm);
        background: var(--primary-500);
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

.sleep-environment {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .environment-header {
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
  
  .environment-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-md);
    
    .factor-card {
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      text-align: center;
      
      .factor-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--spacing-xs);
        margin-bottom: var(--spacing-sm);
        color: var(--primary-500);
        font-size: var(--font-sm);
        font-weight: 600;
      }
      
      .factor-value {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
        margin-bottom: var(--spacing-sm);
      }
      
      .factor-range {
        margin-bottom: var(--spacing-sm);
        
        .range-text {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          display: block;
          margin-bottom: var(--spacing-xs);
        }
        
        .range-indicator {
          width: 8px;
          height: 8px;
          border-radius: var(--radius-full);
          margin: 0 auto;
          
          &.normal {
            background: var(--success-500);
          }
          
          &.warning {
            background: var(--warning-500);
          }
          
          &.critical {
            background: var(--error-500);
          }
        }
      }
      
      .factor-impact {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
      
      &.warning {
        border-left: 3px solid var(--warning-500);
      }
      
      &.critical {
        border-left: 3px solid var(--error-500);
      }
    }
  }
}

@media (max-width: 1024px) {
  .sleep-overview {
    grid-template-columns: 1fr 1fr;
  }
  
  .patterns-grid,
  .environment-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .analysis-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .sleep-overview {
    grid-template-columns: 1fr;
  }
  
  .patterns-grid,
  .environment-grid {
    grid-template-columns: 1fr;
  }
}
</style>