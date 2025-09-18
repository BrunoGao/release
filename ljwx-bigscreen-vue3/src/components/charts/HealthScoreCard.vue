<template>
  <div class="health-score-card">
    <div class="card-header">
      <div class="title-section">
        <h3 class="card-title">{{ title }}</h3>
        <div class="trend-indicator" :class="trendClass">
          <component :is="trendIcon" class="trend-icon" />
          <span class="trend-text">{{ trendText }}</span>
        </div>
      </div>
      <div class="score-badge" :class="scoreLevel.level">
        {{ scoreLevel.text }}
      </div>
    </div>
    
    <div class="score-display">
      <!-- 主评分圆环 -->
      <div class="score-gauge" ref="gaugeContainer">
        <!-- ECharts 仪表盘将渲染在这里 -->
      </div>
      
      <!-- 评分详情 -->
      <div class="score-details">
        <div class="main-score">
          <span class="score-number">{{ animatedScore }}</span>
          <span class="score-suffix">分</span>
        </div>
        <div class="score-description">
          <span class="score-label">健康指数</span>
          <span class="score-change" :class="trendClass">
            {{ trendChange }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- 关键指标 -->
    <div class="key-indicators">
      <div 
        v-for="(indicator, key) in keyIndicators" 
        :key="key"
        class="indicator-item"
      >
        <div class="indicator-header">
          <span class="indicator-name">{{ getIndicatorName(key) }}</span>
          <span class="indicator-value">{{ indicator }}%</span>
        </div>
        <div class="indicator-bar">
          <div 
            class="indicator-fill" 
            :style="{ 
              width: `${indicator}%`,
              backgroundColor: getIndicatorColor(indicator)
            }"
          />
        </div>
      </div>
    </div>
    
    <!-- 改进建议和成就 -->
    <div class="insights-section">
      <div class="improvement-areas" v-if="improvementAreas.length > 0">
        <div class="section-header">
          <ExclamationTriangleIcon class="section-icon warning" />
          <span class="section-title">需要改进</span>
        </div>
        <div class="insight-list">
          <div 
            v-for="area in improvementAreas.slice(0, 2)" 
            :key="area"
            class="insight-item improvement"
          >
            {{ area }}
          </div>
        </div>
      </div>
      
      <div class="achievements" v-if="achievements.length > 0">
        <div class="section-header">
          <CheckCircleIcon class="section-icon success" />
          <span class="section-title">健康成就</span>
        </div>
        <div class="insight-list">
          <div 
            v-for="achievement in achievements.slice(0, 2)" 
            :key="achievement"
            class="insight-item achievement"
          >
            {{ achievement }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  TrendingUpIcon, 
  TrendingDownIcon, 
  MinusIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  score: number
  trend: 'up' | 'down' | 'stable'
  title?: string
  keyIndicators?: Record<string, number>
  improvementAreas?: string[]
  achievements?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康评分',
  keyIndicators: () => ({
    cardiovascular: 85,
    respiratory: 90,
    metabolic: 78,
    mental: 82,
    physical: 88
  }),
  improvementAreas: () => ['睡眠质量', '运动量'],
  achievements: () => ['心率稳定', '血氧正常']
})

// 模板引用
const gaugeContainer = ref<HTMLElement>()

// 动画评分
const animatedScore = ref(0)

// 计算属性
const scoreLevel = computed(() => {
  if (props.score >= 90) return { level: 'excellent', color: '#00ff9d', text: '优秀' }
  if (props.score >= 80) return { level: 'good', color: '#66bb6a', text: '良好' }
  if (props.score >= 70) return { level: 'fair', color: '#ffa726', text: '一般' }
  return { level: 'poor', color: '#ff6b6b', text: '较差' }
})

const trendClass = computed(() => ({
  'trend-up': props.trend === 'up',
  'trend-down': props.trend === 'down',
  'trend-stable': props.trend === 'stable'
}))

const trendIcon = computed(() => {
  switch (props.trend) {
    case 'up': return TrendingUpIcon
    case 'down': return TrendingDownIcon
    default: return MinusIcon
  }
})

const trendText = computed(() => {
  switch (props.trend) {
    case 'up': return '上升'
    case 'down': return '下降'
    default: return '稳定'
  }
})

const trendChange = computed(() => {
  const change = Math.floor(Math.random() * 5) + 1 // 模拟变化值
  switch (props.trend) {
    case 'up': return `+${change}`
    case 'down': return `-${change}`
    default: return '0'
  }
})

// 方法
const getIndicatorName = (key: string) => {
  const names: Record<string, string> = {
    cardiovascular: '心血管',
    respiratory: '呼吸系统',
    metabolic: '代谢健康',
    mental: '心理健康',
    physical: '身体健康'
  }
  return names[key] || key
}

const getIndicatorColor = (value: number) => {
  if (value >= 90) return '#00ff9d'
  if (value >= 80) return '#66bb6a'
  if (value >= 70) return '#ffa726'
  return '#ff6b6b'
}

// 初始化图表
const initGaugeChart = () => {
  if (!gaugeContainer.value) return
  
  const chart = echarts.init(gaugeContainer.value, 'health-tech')
  
  const option = {
    series: [{
      type: 'gauge',
      min: 0,
      max: 100,
      radius: '90%',
      startAngle: 225,
      endAngle: -45,
      axisLine: {
        lineStyle: {
          width: 12,
          color: [
            [0.2, '#ff6b6b'],
            [0.4, '#ffa726'],
            [0.6, '#66bb6a'],
            [0.8, '#42a5f5'],
            [1, '#00ff9d']
          ]
        }
      },
      pointer: {
        itemStyle: {
          color: '#00e4ff',
          shadowColor: 'rgba(0, 228, 255, 0.5)',
          shadowBlur: 10
        },
        width: 8,
        length: '70%'
      },
      axisTick: {
        distance: -15,
        length: 8,
        lineStyle: {
          color: '#fff',
          width: 2
        }
      },
      splitLine: {
        distance: -20,
        length: 15,
        lineStyle: {
          color: '#fff',
          width: 3
        }
      },
      axisLabel: {
        color: '#fff',
        distance: 25,
        fontSize: 12
      },
      detail: {
        show: false
      },
      data: [{
        value: props.score,
        name: '健康评分'
      }]
    }]
  }
  
  chart.setOption(option)
  
  // 响应式调整
  const resizeChart = () => chart.resize()
  window.addEventListener('resize', resizeChart)
  
  // 清理函数
  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chart.dispose()
  })
  
  return chart
}

// 动画效果
const animateScore = () => {
  const target = props.score
  const duration = 1500
  const startTime = Date.now()
  
  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    // 使用 easing 函数
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedScore.value = Math.floor(target * eased)
    
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initGaugeChart()
    animateScore()
  })
})

// 监听 score 变化
watch(() => props.score, (newScore) => {
  animateScore()
})
</script>

<style lang="scss" scoped>
.health-score-card {
  height: 100%;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(0, 255, 157, 0.05) 100%);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary-500), var(--tech-500));
  }
}

// ========== 卡片头部 ==========
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);
}

.title-section {
  .card-title {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-sm);
  
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

.score-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-sm);
  font-weight: 600;
  
  &.excellent {
    background: rgba(0, 255, 157, 0.2);
    color: var(--primary-500);
    border: 1px solid var(--primary-500);
  }
  
  &.good {
    background: rgba(102, 187, 106, 0.2);
    color: #66bb6a;
    border: 1px solid #66bb6a;
  }
  
  &.fair {
    background: rgba(255, 167, 38, 0.2);
    color: var(--warning);
    border: 1px solid var(--warning);
  }
  
  &.poor {
    background: rgba(255, 107, 107, 0.2);
    color: var(--error);
    border: 1px solid var(--error);
  }
}

// ========== 评分显示 ==========
.score-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  flex: 1;
  min-height: 200px;
}

.score-gauge {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.score-details {
  flex: 1;
  
  .main-score {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-md);
    
    .score-number {
      font-size: 3.5rem;
      font-weight: 700;
      color: var(--primary-500);
      font-family: var(--font-tech);
      text-shadow: 0 0 20px rgba(0, 255, 157, 0.5);
    }
    
    .score-suffix {
      font-size: var(--font-xl);
      color: var(--text-secondary);
      font-weight: 500;
    }
  }
  
  .score-description {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .score-label {
      font-size: var(--font-md);
      color: var(--text-secondary);
    }
    
    .score-change {
      font-size: var(--font-md);
      font-weight: 600;
      
      &.trend-up {
        color: var(--success);
        &::before { content: '↗ '; }
      }
      
      &.trend-down {
        color: var(--error);
        &::before { content: '↘ '; }
      }
      
      &.trend-stable {
        color: var(--text-secondary);
        &::before { content: '→ '; }
      }
    }
  }
}

// ========== 关键指标 ==========
.key-indicators {
  margin-bottom: var(--spacing-lg);
  
  .indicator-item {
    margin-bottom: var(--spacing-md);
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .indicator-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
    
    .indicator-name {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
    
    .indicator-value {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
    }
  }
  
  .indicator-bar {
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-full);
    overflow: hidden;
    
    .indicator-fill {
      height: 100%;
      border-radius: var(--radius-full);
      transition: width 1s ease-out;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 20px;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
        animation: shimmer 2s ease-in-out infinite;
      }
    }
  }
}

// ========== 洞察部分 ==========
.insights-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  
  .section-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-sm);
    
    .section-icon {
      width: 16px;
      height: 16px;
      
      &.warning {
        color: var(--warning);
      }
      
      &.success {
        color: var(--success);
      }
    }
    
    .section-title {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .insight-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .insight-item {
    font-size: var(--font-xs);
    padding: var(--spacing-xs);
    border-radius: var(--radius-sm);
    position: relative;
    
    &.improvement {
      background: rgba(255, 167, 38, 0.1);
      color: var(--warning);
      border-left: 3px solid var(--warning);
    }
    
    &.achievement {
      background: rgba(0, 255, 157, 0.1);
      color: var(--success);
      border-left: 3px solid var(--success);
    }
  }
}

// ========== 动画 ==========
@keyframes shimmer {
  0% {
    transform: translateX(-20px);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateX(20px);
    opacity: 0;
  }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .score-display {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-lg);
  }
  
  .insights-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .health-score-card {
    padding: var(--spacing-md);
  }
  
  .card-header {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .score-gauge {
    width: 150px;
    height: 150px;
  }
  
  .main-score .score-number {
    font-size: 2.5rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .indicator-fill,
  .shimmer {
    transition: none;
    animation: none;
  }
}
</style>