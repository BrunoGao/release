<template>
  <div class="environmental-monitor">
    <div class="monitor-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Sunny />
        </el-icon>
        <h3 class="monitor-title">{{ title }}</h3>
      </div>
      
      <div class="env-status" :class="getEnvironmentStatus()">
        <span class="status-indicator"></span>
        <span class="status-text">{{ getStatusText() }}</span>
      </div>
    </div>
    
    <!-- 环境指标网格 -->
    <div class="env-metrics-grid">
      <div class="metric-card temperature">
        <div class="metric-header">
          <el-icon><Sunny /></el-icon>
          <span>环境温度</span>
        </div>
        <div class="metric-value">{{ envData.temperature }}°C</div>
        <div class="metric-range">
          <span class="range-text">正常范围: 18-26°C</span>
          <div class="range-indicator" :class="getTempClass(envData.temperature)"></div>
        </div>
      </div>
      
      <div class="metric-card humidity">
        <div class="metric-header">
          <el-icon><Drizzling /></el-icon>
          <span>相对湿度</span>
        </div>
        <div class="metric-value">{{ envData.humidity }}%</div>
        <div class="metric-range">
          <span class="range-text">正常范围: 40-70%</span>
          <div class="range-indicator" :class="getHumidityClass(envData.humidity)"></div>
        </div>
      </div>
      
      <div class="metric-card airQuality">
        <div class="metric-header">
          <el-icon><WindPower /></el-icon>
          <span>空气质量</span>
        </div>
        <div class="metric-value">{{ envData.airQuality }}</div>
        <div class="metric-status" :class="getAirQualityClass(envData.airQuality)">
          {{ getAirQualityText(envData.airQuality) }}
        </div>
      </div>
      
      <div class="metric-card noise">
        <div class="metric-header">
          <el-icon><Headphones /></el-icon>
          <span>噪音水平</span>
        </div>
        <div class="metric-value">{{ envData.noise }}dB</div>
        <div class="metric-range">
          <span class="range-text">安静环境: &lt;50dB</span>
          <div class="range-indicator" :class="getNoiseClass(envData.noise)"></div>
        </div>
      </div>
      
      <div class="metric-card light">
        <div class="metric-header">
          <el-icon><Sunrise /></el-icon>
          <span>光照强度</span>
        </div>
        <div class="metric-value">{{ envData.light }} lux</div>
        <div class="metric-range">
          <span class="range-text">适宜: 300-750 lux</span>
          <div class="range-indicator" :class="getLightClass(envData.light)"></div>
        </div>
      </div>
      
      <div class="metric-card co2">
        <div class="metric-header">
          <el-icon><Platform /></el-icon>
          <span>CO₂浓度</span>
        </div>
        <div class="metric-value">{{ envData.co2 }} ppm</div>
        <div class="metric-range">
          <span class="range-text">良好: &lt;1000 ppm</span>
          <div class="range-indicator" :class="getCo2Class(envData.co2)"></div>
        </div>
      </div>
    </div>
    
    <!-- 环境趋势图表 -->
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 环境数据趋势图 -->
    </div>
    
    <!-- 环境建议 -->
    <div class="env-recommendations">
      <div class="recommendations-header">
        <h4>环境建议</h4>
        <el-tag :type="getRecommendationLevel()" size="small">
          {{ getRecommendationLevelText() }}
        </el-tag>
      </div>
      
      <div class="recommendations-list">
        <div 
          v-for="recommendation in environmentRecommendations" 
          :key="recommendation.id"
          class="recommendation-item"
          :class="recommendation.priority"
        >
          <el-icon class="rec-icon">
            <component :is="getRecommendationIcon(recommendation.type)" />
          </el-icon>
          <div class="rec-content">
            <div class="rec-title">{{ recommendation.title }}</div>
            <div class="rec-desc">{{ recommendation.description }}</div>
          </div>
          <div class="rec-action">
            <el-button size="small" type="text">
              {{ recommendation.action }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Sunny, 
  Drizzling, 
  WindPower, 
  Headphones, 
  Sunrise, 
  Platform,
  Setting,
  Warning,
  InfoFilled,
  TrendCharts
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '环境监控',
  height: '700px',
  autoRefresh: true,
  refreshInterval: 10000
})

const chartRef = ref<HTMLElement>()

// 环境数据
const envData = reactive({
  temperature: 22.5,
  humidity: 55,
  airQuality: 85,
  noise: 42,
  light: 450,
  co2: 680
})

// 环境建议
const environmentRecommendations = ref([
  {
    id: 1,
    type: 'temperature',
    priority: 'normal',
    title: '温度适宜',
    description: '当前温度处于舒适范围内，有利于健康状态',
    action: '保持'
  },
  {
    id: 2,
    type: 'humidity',
    priority: 'normal',
    title: '湿度正常',
    description: '相对湿度适中，空气不会过于干燥或潮湿',
    action: '保持'
  },
  {
    id: 3,
    type: 'light',
    priority: 'suggestion',
    title: '建议调节光照',
    description: '当前光照强度适中，可根据活动需要微调',
    action: '调节'
  }
])

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  
  // 生成最近24小时的环境数据
  const timeData = []
  const tempData = []
  const humidityData = []
  const airQualityData = []
  const noiseData = []
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(Date.now() - i * 3600000)
    timeData.push(time.getHours().toString().padStart(2, '0') + ':00')
    tempData.push(20 + Math.random() * 8)
    humidityData.push(45 + Math.random() * 30)
    airQualityData.push(70 + Math.random() * 25)
    noiseData.push(35 + Math.random() * 25)
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
      data: ['温度(°C)', '湿度(%)', '空气质量', '噪音(dB)'],
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
        name: '温度/湿度/空气质量',
        position: 'left',
        axisLabel: {
          color: '#999'
        }
      },
      {
        type: 'value',
        name: '噪音(dB)',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}dB'
        }
      }
    ],
    series: [
      {
        name: '温度(°C)',
        type: 'line',
        yAxisIndex: 0,
        data: tempData,
        smooth: true,
        lineStyle: {
          color: '#ff6b6b',
          width: 2
        }
      },
      {
        name: '湿度(%)',
        type: 'line',
        yAxisIndex: 0,
        data: humidityData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        }
      },
      {
        name: '空气质量',
        type: 'line',
        yAxisIndex: 0,
        data: airQualityData,
        smooth: true,
        lineStyle: {
          color: '#66bb6a',
          width: 2
        }
      },
      {
        name: '噪音(dB)',
        type: 'line',
        yAxisIndex: 1,
        data: noiseData,
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

// 工具方法
const getEnvironmentStatus = () => {
  let issueCount = 0
  
  if (envData.temperature < 18 || envData.temperature > 26) issueCount++
  if (envData.humidity < 40 || envData.humidity > 70) issueCount++
  if (envData.airQuality < 50) issueCount++
  if (envData.noise > 60) issueCount++
  if (envData.co2 > 1000) issueCount++
  
  if (issueCount >= 3) return 'critical'
  if (issueCount >= 1) return 'warning'
  return 'normal'
}

const getStatusText = () => {
  const status = getEnvironmentStatus()
  const textMap = {
    normal: '环境良好',
    warning: '需要关注',
    critical: '环境异常'
  }
  return textMap[status]
}

const getTempClass = (value: number) => {
  if (value >= 18 && value <= 26) return 'normal'
  if ((value >= 16 && value < 18) || (value > 26 && value <= 28)) return 'warning'
  return 'critical'
}

const getHumidityClass = (value: number) => {
  if (value >= 40 && value <= 70) return 'normal'
  if ((value >= 30 && value < 40) || (value > 70 && value <= 80)) return 'warning'
  return 'critical'
}

const getAirQualityClass = (value: number) => {
  if (value >= 80) return 'excellent'
  if (value >= 60) return 'good'
  if (value >= 40) return 'fair'
  return 'poor'
}

const getAirQualityText = (value: number) => {
  if (value >= 80) return '优秀'
  if (value >= 60) return '良好'
  if (value >= 40) return '一般'
  return '较差'
}

const getNoiseClass = (value: number) => {
  if (value <= 50) return 'normal'
  if (value <= 70) return 'warning'
  return 'critical'
}

const getLightClass = (value: number) => {
  if (value >= 300 && value <= 750) return 'normal'
  if ((value >= 200 && value < 300) || (value > 750 && value <= 1000)) return 'warning'
  return 'critical'
}

const getCo2Class = (value: number) => {
  if (value <= 1000) return 'normal'
  if (value <= 1500) return 'warning'
  return 'critical'
}

const getRecommendationLevel = () => {
  const status = getEnvironmentStatus()
  const levelMap = {
    normal: 'success',
    warning: 'warning',
    critical: 'danger'
  }
  return levelMap[status]
}

const getRecommendationLevelText = () => {
  const status = getEnvironmentStatus()
  const textMap = {
    normal: '环境优良',
    warning: '需要改善',
    critical: '立即处理'
  }
  return textMap[status]
}

const getRecommendationIcon = (type: string) => {
  const iconMap = {
    temperature: Sunny,
    humidity: Drizzling,
    airQuality: WindPower,
    noise: Headphones,
    light: Sunrise,
    co2: Platform,
    general: Setting
  }
  return iconMap[type as keyof typeof iconMap] || Setting
}

// 自动刷新
let refreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  if (!props.autoRefresh) return
  
  refreshTimer = setInterval(() => {
    // 模拟环境数据更新
    envData.temperature = 20 + Math.random() * 8
    envData.humidity = 45 + Math.random() * 30
    envData.airQuality = 70 + Math.random() * 25
    envData.noise = 35 + Math.random() * 25
    envData.light = 350 + Math.random() * 400
    envData.co2 = 600 + Math.random() * 300
    
    updateChart()
  }, props.refreshInterval)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  nextTick(() => {
    updateChart()
    startAutoRefresh()
  })
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.environmental-monitor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.monitor-header {
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
    
    .monitor-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .env-status {
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
    
    &.normal {
      background: rgba(102, 187, 106, 0.1);
      color: var(--success-500);
      
      .status-indicator {
        background: var(--success-500);
      }
    }
    
    &.warning {
      background: rgba(255, 167, 38, 0.1);
      color: var(--warning-500);
      
      .status-indicator {
        background: var(--warning-500);
      }
    }
    
    &.critical {
      background: rgba(255, 107, 107, 0.1);
      color: var(--error-500);
      
      .status-indicator {
        background: var(--error-500);
      }
    }
  }
}

.env-metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .metric-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    
    .metric-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-sm);
      
      .el-icon {
        color: var(--primary-500);
        font-size: 16px;
      }
      
      span {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
    
    .metric-value {
      font-size: var(--font-xl);
      font-weight: 700;
      color: var(--text-primary);
      font-family: var(--font-tech);
      margin-bottom: var(--spacing-sm);
    }
    
    .metric-range {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .range-text {
        font-size: var(--font-xs);
        color: var(--text-secondary);
      }
      
      .range-indicator {
        width: 12px;
        height: 12px;
        border-radius: var(--radius-full);
        
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
    
    .metric-status {
      font-size: var(--font-xs);
      font-weight: 500;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      
      &.excellent {
        background: rgba(102, 187, 106, 0.2);
        color: var(--success-500);
      }
      
      &.good {
        background: rgba(0, 255, 157, 0.2);
        color: var(--primary-500);
      }
      
      &.fair {
        background: rgba(255, 167, 38, 0.2);
        color: var(--warning-500);
      }
      
      &.poor {
        background: rgba(255, 107, 107, 0.2);
        color: var(--error-500);
      }
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 200px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.env-recommendations {
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
    gap: var(--spacing-sm);
    
    .recommendation-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      
      .rec-icon {
        color: var(--primary-500);
        font-size: 16px;
      }
      
      .rec-content {
        flex: 1;
        
        .rec-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .rec-desc {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .rec-action {
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.suggestion {
        border-left: 3px solid var(--primary-500);
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
  .env-metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .env-metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>