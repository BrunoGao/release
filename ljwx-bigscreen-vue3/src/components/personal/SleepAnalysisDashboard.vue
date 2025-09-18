<template>
  <div class="sleep-analysis-dashboard">
    <div class="dashboard-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Clock />
        </el-icon>
        <h3 class="dashboard-title">{{ title }}</h3>
      </div>
      
      <div class="dashboard-controls">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          size="small"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
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
            <div class="score-label">睡眠质量</div>
            <div class="score-level" :class="getSleepScoreLevel()">
              {{ getSleepScoreText() }}
            </div>
            <div class="score-date">{{ formatDate(selectedDate) }}</div>
          </div>
        </div>
      </div>
      
      <div class="overview-card sleep-duration">
        <div class="card-header">
          <el-icon><Timer /></el-icon>
          <span>睡眠时长</span>
        </div>
        <div class="duration-display">
          <div class="duration-value">{{ sleepData.duration }}h</div>
          <div class="duration-breakdown">
            <div class="breakdown-item">
              <span class="breakdown-label">入睡时间</span>
              <span class="breakdown-value">{{ sleepData.bedtime }}</span>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">起床时间</span>
              <span class="breakdown-value">{{ sleepData.wakeTime }}</span>
            </div>
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
      
      <div class="overview-card sleep-disturbances">
        <div class="card-header">
          <el-icon><Warning /></el-icon>
          <span>睡眠干扰</span>
        </div>
        <div class="disturbances-display">
          <div class="disturbances-count">{{ sleepData.disturbances }}</div>
          <div class="disturbances-label">次数</div>
          <div class="disturbances-duration">
            平均时长: {{ sleepData.disturbanceDuration }}分钟
          </div>
        </div>
      </div>
    </div>
    
    <!-- 睡眠阶段分析 -->
    <div class="sleep-stages">
      <div class="stages-header">
        <h4>睡眠阶段分析</h4>
        <div class="stages-legend">
          <div class="legend-item deep">
            <div class="legend-color"></div>
            <span>深度睡眠</span>
          </div>
          <div class="legend-item light">
            <div class="legend-color"></div>
            <span>浅度睡眠</span>
          </div>
          <div class="legend-item rem">
            <div class="legend-color"></div>
            <span>REM睡眠</span>
          </div>
          <div class="legend-item awake">
            <div class="legend-color"></div>
            <span>清醒</span>
          </div>
        </div>
      </div>
      
      <div class="stages-content">
        <div class="stages-chart" ref="stagesChartRef"></div>
        <div class="stages-details">
          <div 
            v-for="stage in sleepStages" 
            :key="stage.name"
            class="stage-item"
            :class="stage.type"
          >
            <div class="stage-info">
              <div class="stage-name">{{ stage.name }}</div>
              <div class="stage-percentage">{{ stage.percentage }}%</div>
            </div>
            <div class="stage-duration">{{ stage.duration }}h</div>
            <div class="stage-quality" :class="stage.quality">
              {{ getQualityText(stage.quality) }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 睡眠时间线 -->
    <div class="sleep-timeline">
      <div class="timeline-header">
        <h4>睡眠时间线</h4>
        <div class="timeline-controls">
          <el-radio-group v-model="timelineView" size="small">
            <el-radio-button label="detailed">详细</el-radio-button>
            <el-radio-button label="summary">概览</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <div class="timeline-chart" ref="timelineChartRef"></div>
    </div>
    
    <!-- 睡眠指标分析 -->
    <div class="sleep-metrics">
      <div class="metrics-header">
        <h4>关键指标</h4>
      </div>
      
      <div class="metrics-grid">
        <div 
          v-for="metric in sleepMetrics" 
          :key="metric.name"
          class="metric-card"
          :class="metric.status"
        >
          <div class="metric-icon">
            <el-icon>
              <component :is="getMetricIcon(metric.type)" />
            </el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-name">{{ metric.name }}</div>
            <div class="metric-value">{{ metric.value }} {{ metric.unit }}</div>
            <div class="metric-comparison">
              <span class="comparison-label">vs 平均值:</span>
              <span class="comparison-value" :class="metric.trend">
                {{ metric.comparison }}
              </span>
            </div>
          </div>
          <div class="metric-status">
            <el-tag :type="getMetricTagType(metric.status)" size="small">
              {{ getMetricStatusText(metric.status) }}
            </el-tag>
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
            <div class="rec-benefit">预期改善: {{ recommendation.expectedBenefit }}</div>
          </div>
          <div class="rec-action">
            <el-button size="small" type="primary" @click="applyRecommendation(recommendation)">
              应用建议
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 睡眠环境数据 -->
    <div class="sleep-environment">
      <div class="environment-header">
        <h4>睡眠环境</h4>
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
            <span class="range-text">理想: {{ factor.idealRange }}</span>
            <div class="range-indicator" :class="factor.status"></div>
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
  Warning,
  Setting,
  Sunny,
  Drizzling,
  WindPower,
  Headphones,
  Monitor,
  CircleCheck,
  Guide
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '睡眠分析仪表板',
  userId: ''
})

const selectedDate = ref(new Date().toISOString().split('T')[0])
const timelineView = ref('detailed')
const stagesChartRef = ref<HTMLElement>()
const timelineChartRef = ref<HTMLElement>()

// 睡眠数据
const sleepData = reactive({
  qualityScore: 82,
  duration: 7.2,
  bedtime: '22:45',
  wakeTime: '06:30',
  efficiency: 89,
  disturbances: 3,
  disturbanceDuration: 12
})

// 睡眠阶段
const sleepStages = ref([
  {
    name: '深度睡眠',
    type: 'deep',
    percentage: 18,
    duration: 1.3,
    quality: 'good'
  },
  {
    name: '浅度睡眠',
    type: 'light',
    percentage: 52,
    duration: 3.7,
    quality: 'normal'
  },
  {
    name: 'REM睡眠',
    type: 'rem',
    percentage: 22,
    duration: 1.6,
    quality: 'good'
  },
  {
    name: '清醒',
    type: 'awake',
    percentage: 8,
    duration: 0.6,
    quality: 'normal'
  }
])

// 睡眠指标
const sleepMetrics = ref([
  {
    name: '入睡时间',
    type: 'onset',
    value: 8,
    unit: '分钟',
    comparison: '-2分钟',
    trend: 'better',
    status: 'good'
  },
  {
    name: '深睡比例',
    type: 'deep',
    value: 18,
    unit: '%',
    comparison: '+3%',
    trend: 'better',
    status: 'normal'
  },
  {
    name: '心率变化',
    type: 'heartRate',
    value: 52,
    unit: 'bpm',
    comparison: '正常',
    trend: 'stable',
    status: 'good'
  },
  {
    name: '体动次数',
    type: 'movement',
    value: 15,
    unit: '次',
    comparison: '+5次',
    trend: 'worse',
    status: 'warning'
  }
])

// 睡眠建议
const sleepRecommendations = ref([
  {
    id: 1,
    type: 'schedule',
    priority: 'medium',
    title: '优化就寝时间',
    description: '建议将就寝时间提前15分钟，有助于获得更充足的深度睡眠',
    expectedBenefit: '深睡时长增加20%'
  },
  {
    id: 2,
    type: 'environment',
    priority: 'low',
    title: '调节室内温度',
    description: '降低卧室温度1-2度，创造更适宜的睡眠环境',
    expectedBenefit: '睡眠效率提升5%'
  },
  {
    id: 3,
    type: 'habit',
    priority: 'high',
    title: '减少睡前屏幕时间',
    description: '睡前1小时避免使用电子设备，有助于更快入睡',
    expectedBenefit: '入睡时间缩短30%'
  }
])

// 环境因子
const environmentFactors = ref([
  {
    name: '温度',
    type: 'temperature',
    value: 22.5,
    unit: '°C',
    idealRange: '18-22°C',
    status: 'warning'
  },
  {
    name: '湿度',
    type: 'humidity',
    value: 55,
    unit: '%',
    idealRange: '40-60%',
    status: 'normal'
  },
  {
    name: '噪音',
    type: 'noise',
    value: 32,
    unit: 'dB',
    idealRange: '<30dB',
    status: 'warning'
  },
  {
    name: '光照',
    type: 'light',
    value: 2,
    unit: 'lux',
    idealRange: '<5lux',
    status: 'good'
  }
])

const updateStagesChart = () => {
  if (!stagesChartRef.value) return
  
  const chart = echarts.init(stagesChartRef.value, 'health-tech')
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: sleepStages.value.map(stage => ({
          value: stage.percentage,
          name: stage.name,
          itemStyle: {
            color: getStageColor(stage.type)
          }
        })),
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

const updateTimelineChart = () => {
  if (!timelineChartRef.value) return
  
  const chart = echarts.init(timelineChartRef.value, 'health-tech')
  
  // 生成24小时睡眠时间线数据
  const timeData = []
  const sleepStateData = []
  
  for (let i = 0; i < 24; i++) {
    const hour = i.toString().padStart(2, '0') + ':00'
    timeData.push(hour)
    
    // 模拟睡眠状态: 0-清醒, 1-浅睡, 2-深睡, 3-REM
    let state = 0 // 默认清醒
    if (i >= 23 || i < 6) { // 23:00-06:00 睡眠时间
      if (i === 23 || i === 0 || i === 5) {
        state = 1 // 浅睡
      } else if (i >= 1 && i <= 2) {
        state = 2 // 深睡
      } else if (i >= 3 && i <= 4) {
        state = 3 // REM
      } else {
        state = 1 // 浅睡
      }
    }
    sleepStateData.push(state)
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
      formatter: (params: any) => {
        const stateMap = ['清醒', '浅睡', '深睡', 'REM']
        return `${params[0].axisValue}: ${stateMap[params[0].value]}`
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
      show: false,
      min: 0,
      max: 3
    },
    series: [
      {
        data: sleepStateData,
        type: 'line',
        step: 'end',
        lineStyle: {
          width: 4
        },
        itemStyle: {
          color: (params: any) => {
            const colors = ['#9e9e9e', '#42a5f5', '#2196f3', '#66bb6a']
            return colors[params.value]
          }
        },
        areaStyle: {
          color: (params: any) => {
            const colors = [
              'rgba(158, 158, 158, 0.3)',
              'rgba(66, 165, 245, 0.3)',
              'rgba(33, 150, 243, 0.3)',
              'rgba(102, 187, 106, 0.3)'
            ]
            return colors[params.value] || colors[0]
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 工具方法
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

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
  if (sleepData.qualityScore >= 85) return '优秀'
  if (sleepData.qualityScore >= 70) return '良好'
  if (sleepData.qualityScore >= 60) return '一般'
  return '较差'
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

const getStageColor = (type: string) => {
  const colorMap = {
    deep: '#2196f3',
    light: '#42a5f5',
    rem: '#66bb6a',
    awake: '#ffa726'
  }
  return colorMap[type as keyof typeof colorMap] || '#999'
}

const getQualityText = (quality: string) => {
  const textMap = {
    excellent: '优秀',
    good: '良好',
    normal: '正常',
    poor: '较差'
  }
  return textMap[quality as keyof typeof textMap] || '正常'
}

const getMetricIcon = (type: string) => {
  const iconMap = {
    onset: Timer,
    deep: Monitor,
    heartRate: TrendUp,
    movement: Warning
  }
  return iconMap[type as keyof typeof iconMap] || Monitor
}

const getMetricTagType = (status: string) => {
  const typeMap = {
    excellent: 'success',
    good: 'success',
    normal: 'primary',
    warning: 'warning',
    poor: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getMetricStatusText = (status: string) => {
  const textMap = {
    excellent: '优秀',
    good: '良好',
    normal: '正常',
    warning: '注意',
    poor: '较差'
  }
  return textMap[status as keyof typeof textMap] || '正常'
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
  return iconMap[type as keyof typeof iconMap] || Guide
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
const onDateChange = (date: string) => {
  console.log('Date changed:', date)
}

const generateReport = () => {
  ElMessage.info('生成睡眠报告')
}

const exportData = () => {
  ElMessage.info('导出睡眠数据')
}

const applyRecommendation = (recommendation: any) => {
  ElMessage.success(`应用建议: ${recommendation.title}`)
}

const calibrateEnvironment = () => {
  ElMessage.info('开始环境校准')
}

watch([timelineView, selectedDate], () => {
  nextTick(() => {
    updateTimelineChart()
  })
})

onMounted(() => {
  nextTick(() => {
    updateStagesChart()
    updateTimelineChart()
  })
})
</script>

<style lang="scss" scoped>
.sleep-analysis-dashboard {
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
  
  .dashboard-controls {
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
            margin-bottom: 4px;
            
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
          
          .score-date {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
    }
    
    &.sleep-duration {
      .duration-display {
        .duration-value {
          font-size: var(--font-xl);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          text-align: center;
          margin-bottom: var(--spacing-sm);
        }
        
        .duration-breakdown {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-xs);
          
          .breakdown-item {
            display: flex;
            justify-content: space-between;
            
            .breakdown-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
            
            .breakdown-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 500;
            }
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
    
    &.sleep-disturbances {
      text-align: center;
      
      .disturbances-display {
        .disturbances-count {
          font-size: var(--font-xl);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: var(--spacing-xs);
        }
        
        .disturbances-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .disturbances-duration {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.sleep-stages {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .stages-header {
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
    
    .stages-legend {
      display: flex;
      gap: var(--spacing-md);
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-size: var(--font-xs);
        color: var(--text-secondary);
        
        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: var(--radius-sm);
        }
        
        &.deep .legend-color {
          background: #2196f3;
        }
        
        &.light .legend-color {
          background: #42a5f5;
        }
        
        &.rem .legend-color {
          background: #66bb6a;
        }
        
        &.awake .legend-color {
          background: #ffa726;
        }
      }
    }
  }
  
  .stages-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-lg);
    
    .stages-chart {
      height: 200px;
    }
    
    .stages-details {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
      
      .stage-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-sm);
        background: var(--bg-secondary);
        border-radius: var(--radius-sm);
        
        .stage-info {
          flex: 1;
          
          .stage-name {
            font-size: var(--font-sm);
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 2px;
          }
          
          .stage-percentage {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
        
        .stage-duration {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          font-family: var(--font-tech);
          min-width: 50px;
          text-align: center;
        }
        
        .stage-quality {
          font-size: var(--font-xs);
          padding: 2px 6px;
          border-radius: var(--radius-sm);
          min-width: 40px;
          text-align: center;
          
          &.excellent {
            background: rgba(102, 187, 106, 0.2);
            color: var(--success-500);
          }
          
          &.good {
            background: rgba(66, 165, 245, 0.2);
            color: var(--primary-500);
          }
          
          &.normal {
            background: rgba(158, 158, 158, 0.2);
            color: var(--text-secondary);
          }
          
          &.poor {
            background: rgba(255, 107, 107, 0.2);
            color: var(--error-500);
          }
        }
      }
    }
  }
}

.sleep-timeline {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .timeline-header {
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
  
  .timeline-chart {
    height: 150px;
  }
}

.sleep-metrics {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .metrics-header {
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-md);
    
    .metric-card {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .metric-icon {
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
      
      .metric-content {
        flex: 1;
        
        .metric-name {
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
        
        .metric-comparison {
          font-size: var(--font-xs);
          
          .comparison-label {
            color: var(--text-secondary);
          }
          
          .comparison-value {
            font-weight: 500;
            margin-left: 4px;
            
            &.better {
              color: var(--success-500);
            }
            
            &.worse {
              color: var(--error-500);
            }
            
            &.stable {
              color: var(--text-secondary);
            }
          }
        }
      }
      
      .metric-status {
        .el-tag {
          font-size: var(--font-xs);
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
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
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
          margin-bottom: var(--spacing-xs);
        }
        
        .rec-benefit {
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
          
          &.good {
            background: var(--success-500);
          }
          
          &.normal {
            background: var(--primary-500);
          }
          
          &.warning {
            background: var(--warning-500);
          }
          
          &.critical {
            background: var(--error-500);
          }
        }
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
  
  .stages-content {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid,
  .environment-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .sleep-overview {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid,
  .environment-grid {
    grid-template-columns: 1fr;
  }
}
</style>