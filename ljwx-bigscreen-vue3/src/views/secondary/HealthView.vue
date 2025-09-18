<template>
  <div class="health-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.8"
      :particle-count="100"
      :enable-grid="true"
      :enable-pulse="false"
      :enable-data-flow="true"
    />
    
    <!-- 页面头部 -->
    <div class="view-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ArrowLeftIcon />
          <span>返回个人大屏</span>
        </button>
        <div class="page-title">
          <h1>健康数据中心</h1>
          <p class="page-subtitle">深度健康数据分析与可视化</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="time-selector">
          <select v-model="selectedTimeRange" @change="loadHealthData">
            <option value="1d">今天</option>
            <option value="7d">近7天</option>
            <option value="30d">近30天</option>
            <option value="90d">近3个月</option>
          </select>
        </div>
        <button class="export-btn" @click="exportHealthData">
          <DocumentArrowDownIcon />
          导出数据
        </button>
      </div>
    </div>
    
    <!-- 健康数据主体 -->
    <div class="health-content">
      <!-- 健康概览卡片 -->
      <div class="overview-section">
        <div class="overview-cards">
          <div class="overview-card">
            <div class="card-icon heart-rate">
              <HeartIcon />
            </div>
            <div class="card-content">
              <div class="card-label">平均心率</div>
              <div class="card-value">{{ healthMetrics.avgHeartRate }} <span class="unit">BPM</span></div>
              <div class="card-trend" :class="getTrendClass(healthMetrics.heartRateTrend)">
                <component :is="getTrendIcon(healthMetrics.heartRateTrend)" />
                {{ healthMetrics.heartRateChange }}%
              </div>
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-icon blood-oxygen">
              <WaterDropIcon />
            </div>
            <div class="card-content">
              <div class="card-label">血氧饱和度</div>
              <div class="card-value">{{ healthMetrics.avgBloodOxygen }} <span class="unit">%</span></div>
              <div class="card-trend" :class="getTrendClass(healthMetrics.bloodOxygenTrend)">
                <component :is="getTrendIcon(healthMetrics.bloodOxygenTrend)" />
                {{ healthMetrics.bloodOxygenChange }}%
              </div>
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-icon blood-pressure">
              <ActivityIcon />
            </div>
            <div class="card-content">
              <div class="card-label">血压</div>
              <div class="card-value">{{ healthMetrics.avgBloodPressure }} <span class="unit">mmHg</span></div>
              <div class="card-trend" :class="getTrendClass(healthMetrics.bloodPressureTrend)">
                <component :is="getTrendIcon(healthMetrics.bloodPressureTrend)" />
                {{ healthMetrics.bloodPressureChange }}%
              </div>
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-icon sleep">
              <MoonIcon />
            </div>
            <div class="card-content">
              <div class="card-label">睡眠质量</div>
              <div class="card-value">{{ healthMetrics.sleepScore }} <span class="unit">分</span></div>
              <div class="card-trend" :class="getTrendClass(healthMetrics.sleepTrend)">
                <component :is="getTrendIcon(healthMetrics.sleepTrend)" />
                {{ healthMetrics.sleepChange }}%
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 详细图表区域 -->
      <div class="charts-section">
        <div class="chart-tabs">
          <button 
            v-for="tab in chartTabs"
            :key="tab.key"
            class="chart-tab"
            :class="{ active: activeChart === tab.key }"
            @click="activeChart = tab.key"
          >
            <component :is="tab.icon" class="tab-icon" />
            {{ tab.label }}
          </button>
        </div>
        
        <div class="chart-container">
          <!-- 心率图表 -->
          <div v-if="activeChart === 'heartRate'" class="chart-content">
            <div class="chart-header">
              <h3>心率变化趋势</h3>
              <div class="chart-controls">
                <button class="control-btn" @click="toggleChartType('line')">
                  <ChartLineIcon />
                </button>
                <button class="control-btn" @click="toggleChartType('area')">
                  <ChartAreaIcon />
                </button>
              </div>
            </div>
            <div class="chart-wrapper">
              <HealthTrendChart 
                :data="heartRateData"
                :type="chartType"
                :color="'#ff6b6b'"
                :unit="'BPM'"
                :normal-range="{ min: 60, max: 100 }"
              />
            </div>
          </div>
          
          <!-- 血氧图表 -->
          <div v-if="activeChart === 'bloodOxygen'" class="chart-content">
            <div class="chart-header">
              <h3>血氧饱和度趋势</h3>
            </div>
            <div class="chart-wrapper">
              <HealthTrendChart 
                :data="bloodOxygenData"
                :type="chartType"
                :color="'#4ecdc4'"
                :unit="'%'"
                :normal-range="{ min: 95, max: 100 }"
              />
            </div>
          </div>
          
          <!-- 血压图表 -->
          <div v-if="activeChart === 'bloodPressure'" class="chart-content">
            <div class="chart-header">
              <h3>血压变化趋势</h3>
            </div>
            <div class="chart-wrapper">
              <BloodPressureChart 
                :data="bloodPressureData"
                :time-range="selectedTimeRange"
              />
            </div>
          </div>
          
          <!-- 睡眠图表 -->
          <div v-if="activeChart === 'sleep'" class="chart-content">
            <div class="chart-header">
              <h3>睡眠质量分析</h3>
            </div>
            <div class="chart-wrapper">
              <SleepAnalysisChart 
                :data="sleepData"
                :time-range="selectedTimeRange"
              />
            </div>
          </div>
          
          <!-- 综合分析 -->
          <div v-if="activeChart === 'comprehensive'" class="chart-content">
            <div class="chart-header">
              <h3>综合健康分析</h3>
            </div>
            <div class="comprehensive-analysis">
              <div class="analysis-grid">
                <div class="analysis-item">
                  <h4>健康评分</h4>
                  <HealthScoreChart :score="healthMetrics.overallScore" />
                </div>
                <div class="analysis-item">
                  <h4>健康雷达</h4>
                  <HealthRadarChart :data="radarData" />
                </div>
                <div class="analysis-item correlation">
                  <h4>指标关联性</h4>
                  <CorrelationMatrix :data="correlationData" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 健康洞察与建议 -->
      <div class="insights-section">
        <div class="section-header">
          <h3>健康洞察</h3>
          <button class="refresh-insights" @click="refreshInsights">
            <RefreshIcon :class="{ spinning: isRefreshingInsights }" />
            刷新分析
          </button>
        </div>
        
        <div class="insights-grid">
          <div class="insight-card warning" v-if="healthInsights.warnings.length > 0">
            <div class="insight-header">
              <ExclamationTriangleIcon class="insight-icon" />
              <h4>需要关注</h4>
            </div>
            <ul class="insight-list">
              <li v-for="warning in healthInsights.warnings" :key="warning">
                {{ warning }}
              </li>
            </ul>
          </div>
          
          <div class="insight-card positive" v-if="healthInsights.positives.length > 0">
            <div class="insight-header">
              <CheckCircleIcon class="insight-icon" />
              <h4>良好表现</h4>
            </div>
            <ul class="insight-list">
              <li v-for="positive in healthInsights.positives" :key="positive">
                {{ positive }}
              </li>
            </ul>
          </div>
          
          <div class="insight-card recommendation">
            <div class="insight-header">
              <LightBulbIcon class="insight-icon" />
              <h4>健康建议</h4>
            </div>
            <ul class="insight-list">
              <li v-for="recommendation in healthInsights.recommendations" :key="recommendation">
                {{ recommendation }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 全局提示 -->
    <GlobalToast ref="toast" />
  </div>
</template>

<script setup lang="ts">
import { 
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  HeartIcon,
  WaterDropIcon,
  ActivityIcon,
  MoonIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon,
  RefreshIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import HealthTrendChart from '@/components/charts/HealthTrendChart.vue'
import BloodPressureChart from '@/components/charts/BloodPressureChart.vue'
import SleepAnalysisChart from '@/components/charts/SleepAnalysisChart.vue'
import HealthScoreChart from '@/components/charts/HealthScoreChart.vue'
import HealthRadarChart from '@/components/charts/HealthRadarChart.vue'
import CorrelationMatrix from '@/components/charts/CorrelationMatrix.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { usePersonalStore } from '@/stores/personal'
import { useRouter } from 'vue-router'

// 自定义图标组件
const ChartLineIcon = {
  name: 'ChartLineIcon',
  template: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 3l18 0 0 18-18 0z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 12l2-4 4 8 2-6" fill="none" stroke="currentColor" stroke-width="2"/></svg>`
}

const ChartAreaIcon = {
  name: 'ChartAreaIcon',
  template: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 21l18 0 0-18-18 0z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 12l2-4 4 8 2-6 0 9-8 0z" fill="currentColor" fill-opacity="0.3"/></svg>`
}

// Store and router
const personalStore = usePersonalStore()
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const selectedTimeRange = ref('7d')
const activeChart = ref('heartRate')
const chartType = ref('line')
const isRefreshingInsights = ref(false)

// 图表标签配置
const chartTabs = [
  { key: 'heartRate', label: '心率', icon: HeartIcon },
  { key: 'bloodOxygen', label: '血氧', icon: WaterDropIcon },
  { key: 'bloodPressure', label: '血压', icon: ActivityIcon },
  { key: 'sleep', label: '睡眠', icon: MoonIcon },
  { key: 'comprehensive', label: '综合分析', icon: ChartLineIcon }
]

// 模拟健康指标数据
const healthMetrics = ref({
  avgHeartRate: 72,
  heartRateTrend: 'stable',
  heartRateChange: 2.1,
  avgBloodOxygen: 98,
  bloodOxygenTrend: 'up',
  bloodOxygenChange: 0.8,
  avgBloodPressure: '120/80',
  bloodPressureTrend: 'down',
  bloodPressureChange: -1.2,
  sleepScore: 82,
  sleepTrend: 'up',
  sleepChange: 5.3,
  overallScore: 85
})

// 生成模拟数据
const generateTimeSeriesData = (baseValue: number, variance: number, days: number) => {
  const now = new Date()
  const pointsPerDay = selectedTimeRange.value === '1d' ? 24 : 
                      selectedTimeRange.value === '7d' ? 7 * 4 : 
                      selectedTimeRange.value === '30d' ? 30 : 90
  
  return Array.from({ length: pointsPerDay }, (_, i) => {
    const timestamp = new Date(now.getTime() - (pointsPerDay - i) * (24 * 60 * 60 * 1000) / (pointsPerDay / days))
    const value = baseValue + Math.sin(i * 0.1) * variance + (Math.random() - 0.5) * variance * 0.5
    return { timestamp, value }
  })
}

// 计算属性
const heartRateData = computed(() => generateTimeSeriesData(72, 10, parseInt(selectedTimeRange.value)))
const bloodOxygenData = computed(() => generateTimeSeriesData(98, 2, parseInt(selectedTimeRange.value)))
const bloodPressureData = computed(() => {
  const systolicData = generateTimeSeriesData(120, 8, parseInt(selectedTimeRange.value))
  const diastolicData = generateTimeSeriesData(80, 6, parseInt(selectedTimeRange.value))
  
  return systolicData.map((item, index) => ({
    timestamp: item.timestamp,
    systolic: item.value,
    diastolic: diastolicData[index]?.value || 80
  }))
})

const sleepData = computed(() => generateTimeSeriesData(7.5, 1.5, parseInt(selectedTimeRange.value)))

const radarData = computed(() => ([
  { indicator: '心血管', value: 85 },
  { indicator: '呼吸系统', value: 92 },
  { indicator: '代谢', value: 78 },
  { indicator: '免疫力', value: 88 },
  { indicator: '神经系统', value: 82 },
  { indicator: '内分泌', value: 75 }
]))

const correlationData = computed(() => ([
  { metric1: '心率', metric2: '血压', correlation: 0.65 },
  { metric1: '睡眠', metric2: '心率', correlation: -0.42 },
  { metric1: '运动', metric2: '睡眠', correlation: 0.73 },
  { metric1: '压力', metric2: '血压', correlation: 0.58 }
]))

const healthInsights = computed(() => ({
  warnings: [
    '近期心率偏高，建议增加休息时间',
    '睡眠时间不规律，影响恢复质量'
  ],
  positives: [
    '血氧饱和度保持在优秀水平',
    '血压控制良好，继续保持'
  ],
  recommendations: [
    '建议每天进行30分钟中等强度运动',
    '保持规律作息，晚上10点前入睡',
    '增加深呼吸练习，有助于降低心率',
    '定期监测血压，建立健康档案'
  ]
}))

// 方法
const goBack = () => {
  router.push('/dashboard/personal')
}

const getTrendClass = (trend: string) => {
  return `trend-${trend}`
}

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return TrendingUpIcon
    case 'down': return TrendingDownIcon
    default: return MinusIcon
  }
}

const loadHealthData = () => {
  // 这里可以根据时间范围加载不同的数据
  toast.value?.info(`已切换到${selectedTimeRange.value}数据视图`)
}

const toggleChartType = (type: string) => {
  chartType.value = type
}

const exportHealthData = () => {
  toast.value?.info('健康数据导出功能开发中')
}

const refreshInsights = async () => {
  isRefreshingInsights.value = true
  try {
    // 模拟刷新
    await new Promise(resolve => setTimeout(resolve, 1500))
    toast.value?.success('健康洞察已更新')
  } finally {
    isRefreshingInsights.value = false
  }
}

// 生命周期
onMounted(() => {
  console.log('健康数据页面已加载')
  loadHealthData()
})
</script>

<style lang="scss" scoped>
.health-view {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// ========== 页面头部 ==========
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
  z-index: 10;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

.page-title {
  h1 {
    font-size: var(--font-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }
  
  .page-subtitle {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin: 0;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  
  .time-selector select {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    
    &:focus {
      outline: none;
      border-color: var(--primary-500);
    }
  }
  
  .export-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

// ========== 主体内容 ==========
.health-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

// ========== 概览卡片 ==========
.overview-section {
  .overview-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: var(--spacing-lg);
  }
}

.overview-card {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all var(--duration-normal);
  backdrop-filter: blur(10px);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-500);
  }
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  
  &.heart-rate {
    background: rgba(255, 107, 107, 0.2);
    color: #ff6b6b;
  }
  
  &.blood-oxygen {
    background: rgba(78, 205, 196, 0.2);
    color: #4ecdc4;
  }
  
  &.blood-pressure {
    background: rgba(69, 183, 209, 0.2);
    color: #45b7d1;
  }
  
  &.sleep {
    background: rgba(156, 39, 176, 0.2);
    color: #9c27b0;
  }
}

.card-content {
  flex: 1;
  
  .card-label {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }
  
  .card-value {
    font-size: var(--font-xl);
    font-weight: 700;
    color: var(--text-primary);
    font-family: var(--font-tech);
    margin-bottom: var(--spacing-xs);
    
    .unit {
      font-size: var(--font-sm);
      font-weight: 500;
      color: var(--text-secondary);
    }
  }
  
  .card-trend {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--font-sm);
    font-weight: 500;
    
    &.trend-up {
      color: var(--success);
    }
    
    &.trend-down {
      color: var(--error);
    }
    
    &.trend-stable {
      color: var(--text-secondary);
    }
  }
}

// ========== 图表区域 ==========
.charts-section {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  backdrop-filter: blur(10px);
  flex: 1;
}

.chart-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-secondary);
  overflow-x: auto;
}

.chart-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  
  .tab-icon {
    width: 16px;
    height: 16px;
  }
  
  &:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.05);
  }
  
  &.active {
    color: var(--primary-500);
    border-bottom-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

.chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  h3 {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .chart-controls {
    display: flex;
    gap: var(--spacing-sm);
  }
  
  .control-btn {
    width: 32px;
    height: 32px;
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

.chart-wrapper {
  flex: 1;
  min-height: 300px;
}

.comprehensive-analysis {
  .analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-lg);
  }
  
  .analysis-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-md) 0;
    }
    
    &.correlation {
      grid-column: 1 / -1;
    }
  }
}

// ========== 洞察区域 ==========
.insights-section {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  backdrop-filter: blur(10px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  h3 {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .refresh-insights {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    .spinning {
      animation: spin 1s linear infinite;
    }
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.insight-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
  }
  
  &.warning::before {
    background: var(--warning);
  }
  
  &.positive::before {
    background: var(--success);
  }
  
  &.recommendation::before {
    background: var(--info);
  }
  
  .insight-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    
    .insight-icon {
      width: 20px;
      height: 20px;
    }
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .insight-list {
    list-style: none;
    padding: 0;
    margin: 0;
    
    li {
      padding: var(--spacing-sm) 0;
      border-bottom: 1px solid var(--border-tertiary);
      font-size: var(--font-sm);
      color: var(--text-secondary);
      
      &:last-child {
        border-bottom: none;
      }
    }
  }
}

// ========== 动画 ==========
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .overview-cards {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .chart-tabs {
    flex-wrap: wrap;
  }
  
  .insights-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .overview-card,
  .chart-tab,
  .control-btn {
    transition: none;
  }
  
  .spinning {
    animation: none;
  }
}
</style>