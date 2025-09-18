<template>
  <div class="vital-signs-panel">
    <div class="panel-header">
      <h3 class="panel-title">实时生命体征</h3>
      <div class="refresh-indicator" :class="{ active: isRefreshing }">
        <RefreshIcon class="refresh-icon" />
        <span class="refresh-text">{{ lastUpdateText }}</span>
      </div>
    </div>
    
    <div class="vital-signs-grid">
      <!-- 心率 -->
      <div class="vital-sign-item" :class="getStatusClass(heartRate.quality)">
        <div class="sign-header">
          <div class="sign-icon heart-rate">
            <HeartIcon />
          </div>
          <div class="sign-label">心率</div>
          <div class="sign-status" :class="getTrendClass(heartRate.trend)">
            <component :is="getTrendIcon(heartRate.trend)" class="trend-icon" />
          </div>
        </div>
        
        <div class="sign-value">
          <span class="value-number">{{ heartRate.current }}</span>
          <span class="value-unit">BPM</span>
        </div>
        
        <div class="sign-range">
          正常范围: {{ heartRate.range.min }}-{{ heartRate.range.max }}
        </div>
        
        <div class="sign-chart">
          <MiniTrendChart 
            :data="heartRateHistory" 
            :color="getSignColor('heartRate')"
            :height="40"
          />
        </div>
      </div>
      
      <!-- 血氧 -->
      <div class="vital-sign-item" :class="getStatusClass(bloodOxygen.quality)">
        <div class="sign-header">
          <div class="sign-icon blood-oxygen">
            <WaterDropIcon />
          </div>
          <div class="sign-label">血氧</div>
          <div class="sign-status" :class="getTrendClass(bloodOxygen.trend)">
            <component :is="getTrendIcon(bloodOxygen.trend)" class="trend-icon" />
          </div>
        </div>
        
        <div class="sign-value">
          <span class="value-number">{{ bloodOxygen.current }}</span>
          <span class="value-unit">%</span>
        </div>
        
        <div class="sign-range">
          正常范围: {{ bloodOxygen.range.min }}-{{ bloodOxygen.range.max }}%
        </div>
        
        <div class="sign-chart">
          <MiniTrendChart 
            :data="bloodOxygenHistory" 
            :color="getSignColor('bloodOxygen')"
            :height="40"
          />
        </div>
      </div>
      
      <!-- 血压 -->
      <div class="vital-sign-item" :class="getStatusClass(bloodPressure.quality)">
        <div class="sign-header">
          <div class="sign-icon blood-pressure">
            <ActivityIcon />
          </div>
          <div class="sign-label">血压</div>
          <div class="sign-status" :class="getTrendClass(bloodPressure.trend)">
            <component :is="getTrendIcon(bloodPressure.trend)" class="trend-icon" />
          </div>
        </div>
        
        <div class="sign-value">
          <span class="value-number">{{ bloodPressure.systolic }}</span>
          <span class="value-separator">/</span>
          <span class="value-number">{{ bloodPressure.diastolic }}</span>
          <span class="value-unit">mmHg</span>
        </div>
        
        <div class="sign-range">
          理想血压: &lt;120/80 mmHg
        </div>
        
        <div class="sign-chart">
          <MiniTrendChart 
            :data="bloodPressureHistory" 
            :color="getSignColor('bloodPressure')"
            :height="40"
            :is-dual="true"
          />
        </div>
      </div>
      
      <!-- 体温 -->
      <div class="vital-sign-item" :class="getStatusClass(temperature.quality)">
        <div class="sign-header">
          <div class="sign-icon temperature">
            <ThermometerIcon />
          </div>
          <div class="sign-label">体温</div>
          <div class="sign-status" :class="getTrendClass(temperature.trend)">
            <component :is="getTrendIcon(temperature.trend)" class="trend-icon" />
          </div>
        </div>
        
        <div class="sign-value">
          <span class="value-number">{{ temperature.current }}</span>
          <span class="value-unit">°C</span>
        </div>
        
        <div class="sign-range">
          正常范围: {{ temperature.range.min }}-{{ temperature.range.max }}°C
        </div>
        
        <div class="sign-chart">
          <MiniTrendChart 
            :data="temperatureHistory" 
            :color="getSignColor('temperature')"
            :height="40"
          />
        </div>
      </div>
    </div>
    
    <!-- 整体状态摘要 -->
    <div class="status-summary">
      <div class="summary-item">
        <span class="summary-label">整体状态</span>
        <span class="summary-value" :class="overallStatusClass">
          {{ overallStatusText }}
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">异常指标</span>
        <span class="summary-value">
          {{ abnormalCount }}/{{ totalCount }}
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">最后更新</span>
        <span class="summary-value">
          {{ formatTime(lastUpdateTime) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  RefreshIcon,
  HeartIcon,
  WaterDropIcon,
  ActivityIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon
} from '@element-plus/icons-vue'
import MiniTrendChart from '@/components/charts/MiniTrendChart.vue'
import type { VitalSigns, VitalSignReading, BloodPressureReading } from '@/types/health'

// 自定义体温图标组件
const ThermometerIcon = {
  name: 'ThermometerIcon',
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0zM12 4a1 1 0 0 1 1 1v8.26a3 3 0 1 1-2 0V5a1 1 0 0 1 1-1z"/>
    </svg>
  `
}

interface Props {
  heartRate: VitalSignReading
  bloodOxygen: VitalSignReading
  bloodPressure: BloodPressureReading
  temperature: VitalSignReading
}

const props = defineProps<Props>()

// 组件状态
const isRefreshing = ref(false)
const lastUpdateTime = ref(new Date())

// 生成模拟历史数据
const generateHistory = (current: number, count = 20) => {
  return Array.from({ length: count }, (_, i) => ({
    timestamp: new Date(Date.now() - (count - i) * 60000),
    value: current + (Math.random() - 0.5) * 10
  }))
}

// 历史数据
const heartRateHistory = computed(() => generateHistory(props.heartRate.current))
const bloodOxygenHistory = computed(() => generateHistory(props.bloodOxygen.current))
const temperatureHistory = computed(() => generateHistory(props.temperature.current))
const bloodPressureHistory = computed(() => generateHistory(props.bloodPressure.systolic))

// 计算属性
const lastUpdateText = computed(() => {
  const now = new Date()
  const diff = now.getTime() - lastUpdateTime.value.getTime()
  const seconds = Math.floor(diff / 1000)
  
  if (seconds < 60) return `${seconds}秒前更新`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前更新`
  return `${Math.floor(seconds / 3600)}小时前更新`
})

const abnormalCount = computed(() => {
  const signs = [props.heartRate, props.bloodOxygen, props.bloodPressure, props.temperature]
  return signs.filter(sign => sign.quality === 'poor' || sign.quality === 'fair').length
})

const totalCount = computed(() => 4)

const overallStatusClass = computed(() => {
  if (abnormalCount.value === 0) return 'status-excellent'
  if (abnormalCount.value <= 1) return 'status-good'
  if (abnormalCount.value <= 2) return 'status-warning'
  return 'status-critical'
})

const overallStatusText = computed(() => {
  if (abnormalCount.value === 0) return '优秀'
  if (abnormalCount.value <= 1) return '良好'
  if (abnormalCount.value <= 2) return '注意'
  return '异常'
})

// 方法
const getStatusClass = (quality: string) => {
  return `quality-${quality}`
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

const getSignColor = (signType: string) => {
  const colors = {
    heartRate: '#ff6b6b',
    bloodOxygen: '#4ecdc4',
    bloodPressure: '#45b7d1',
    temperature: '#ffa726'
  }
  return colors[signType as keyof typeof colors] || '#00ff9d'
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 自动刷新
const startAutoRefresh = () => {
  isRefreshing.value = true
  setTimeout(() => {
    lastUpdateTime.value = new Date()
    isRefreshing.value = false
  }, 1000)
}

// 定期刷新
onMounted(() => {
  const interval = setInterval(() => {
    startAutoRefresh()
  }, 30000) // 30秒刷新一次
  
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style lang="scss" scoped>
.vital-signs-panel {
  height: 100%;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

// ========== 面板头部 ==========
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .panel-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .refresh-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--font-sm);
    color: var(--text-secondary);
    
    .refresh-icon {
      width: 14px;
      height: 14px;
      transition: transform var(--duration-fast);
    }
    
    &.active .refresh-icon {
      animation: spin 1s linear infinite;
    }
  }
}

// ========== 生命体征网格 ==========
.vital-signs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  flex: 1;
  margin-bottom: var(--spacing-lg);
}

.vital-sign-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  transition: all var(--duration-normal);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--border-tertiary);
    transition: background var(--duration-normal);
  }
  
  &:hover {
    border-color: var(--primary-500);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }
  
  &.quality-excellent::before {
    background: var(--success);
  }
  
  &.quality-good::before {
    background: var(--info);
  }
  
  &.quality-fair::before {
    background: var(--warning);
  }
  
  &.quality-poor::before {
    background: var(--error);
  }
}

.sign-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
  
  .sign-icon {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    
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
    
    &.temperature {
      background: rgba(255, 167, 38, 0.2);
      color: #ffa726;
    }
  }
  
  .sign-label {
    flex: 1;
    font-size: var(--font-md);
    font-weight: 500;
    color: var(--text-primary);
    margin-left: var(--spacing-sm);
  }
  
  .sign-status {
    .trend-icon {
      width: 16px;
      height: 16px;
    }
    
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

.sign-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  
  .value-number {
    font-size: var(--font-2xl);
    font-weight: 700;
    color: var(--text-primary);
    font-family: var(--font-tech);
  }
  
  .value-separator {
    font-size: var(--font-xl);
    color: var(--text-secondary);
    font-weight: 500;
  }
  
  .value-unit {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }
}

.sign-range {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-sm);
}

.sign-chart {
  height: 40px;
  margin-top: var(--spacing-sm);
}

// ========== 状态摘要 ==========
.status-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-tertiary);
  
  .summary-item {
    text-align: center;
    
    .summary-label {
      display: block;
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .summary-value {
      display: block;
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
      
      &.status-excellent {
        color: var(--success);
      }
      
      &.status-good {
        color: var(--info);
      }
      
      &.status-warning {
        color: var(--warning);
      }
      
      &.status-critical {
        color: var(--error);
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
@media (max-width: 768px) {
  .vital-signs-grid {
    grid-template-columns: 1fr;
  }
  
  .status-summary {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .sign-value .value-number {
    font-size: var(--font-xl);
  }
}

@media (prefers-reduced-motion: reduce) {
  .vital-sign-item,
  .refresh-icon {
    transition: none;
    animation: none;
  }
}
</style>