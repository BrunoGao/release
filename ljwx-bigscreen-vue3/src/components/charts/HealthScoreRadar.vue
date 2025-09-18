<template>
  <div class="health-score-radar">
    <!-- 评分显示区域 -->
    <div class="score-display">
      <div class="score-info">
        <div class="score-title">综合健康评分</div>
        <div class="score-main">
          <div class="score-number" :class="scoreClass">{{ totalScore }}</div>
          <div class="score-unit">分</div>
        </div>
        <div class="score-status" :class="statusClass">{{ statusText }}</div>
        <div class="score-trend">
          <span class="trend-icon" :class="trendClass">{{ trendIcon }}</span>
          <span class="trend-text">较上周{{ trendText }}</span>
        </div>
      </div>
    </div>
    
    <!-- 雷达图容器 -->
    <div class="radar-container">
      <div ref="radarChartRef" class="radar-chart" id="healthScoreChart"></div>
      
      <!-- 维度详细信息 -->
      <div class="dimensions-info">
        <div 
          v-for="(dimension, index) in dimensions" 
          :key="dimension.name"
          class="dimension-item"
          :class="{ active: activeDimension === index }"
          @mouseenter="highlightDimension(index)"
          @mouseleave="highlightDimension(-1)"
        >
          <div class="dimension-icon" :style="{ color: dimension.color }">
            {{ dimension.icon }}
          </div>
          <div class="dimension-info">
            <div class="dimension-name">{{ dimension.label }}</div>
            <div class="dimension-value">
              <span class="value" :style="{ color: dimension.color }">{{ dimension.value }}</span>
              <span class="unit">{{ dimension.unit }}</span>
            </div>
            <div class="dimension-status" :class="dimension.status">
              {{ getStatusText(dimension.status) }}
            </div>
          </div>
          <div class="dimension-trend" :class="dimension.trend">
            {{ dimension.trendValue }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 健康建议 -->
    <div class="health-suggestions" v-if="suggestions.length">
      <div class="suggestions-title">健康建议</div>
      <div class="suggestions-list">
        <div 
          v-for="suggestion in suggestions" 
          :key="suggestion.id"
          class="suggestion-item"
          :class="suggestion.priority"
        >
          <div class="suggestion-icon">{{ suggestion.icon }}</div>
          <div class="suggestion-content">
            <div class="suggestion-title">{{ suggestion.title }}</div>
            <div class="suggestion-desc">{{ suggestion.description }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// Props
interface HealthDimension {
  name: string
  label: string
  value: number
  max: number
  unit: string
  icon: string
  color: string
  status: 'excellent' | 'good' | 'normal' | 'attention' | 'warning'
  trend: 'up' | 'down' | 'stable'
  trendValue: string
}

interface HealthSuggestion {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  icon: string
}

interface Props {
  data?: {
    dimensions: HealthDimension[]
    totalScore: number
    trend: number
    suggestions: HealthSuggestion[]
  }
  autoRefresh?: boolean
  showSuggestions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  showSuggestions: true
})

// Emits
const emit = defineEmits<{
  dimensionClick: [dimension: HealthDimension]
  suggestionClick: [suggestion: HealthSuggestion]
}>()

// Refs
const radarChartRef = ref<HTMLElement>()
const activeDimension = ref(-1)

// 图表实例
let radarChart: echarts.ECharts | null = null

// 默认数据
const defaultData = {
  totalScore: 94.5,
  trend: 2.3,
  dimensions: [
    {
      name: 'heartRate',
      label: '心率',
      value: 85.2,
      max: 100,
      unit: '分',
      icon: '💓',
      color: '#ff4757',
      status: 'good' as const,
      trend: 'stable' as const,
      trendValue: '+0.2%'
    },
    {
      name: 'bloodOxygen',
      label: '血氧',
      value: 98.1,
      max: 100,
      unit: '分',
      icon: '🫁',
      color: '#00d2d3',
      status: 'excellent' as const,
      trend: 'up' as const,
      trendValue: '+1.5%'
    },
    {
      name: 'temperature',
      label: '体温',
      value: 92.8,
      max: 100,
      unit: '分',
      icon: '🌡️',
      color: '#ff6348',
      status: 'good' as const,
      trend: 'stable' as const,
      trendValue: '0%'
    },
    {
      name: 'steps',
      label: '步数',
      value: 81.1,
      max: 100,
      unit: '分',
      icon: '👟',
      color: '#2ed573',
      status: 'normal' as const,
      trend: 'down' as const,
      trendValue: '-2.1%'
    },
    {
      name: 'calories',
      label: '卡路里',
      value: 88.6,
      max: 100,
      unit: '分',
      icon: '🔥',
      color: '#ffa726',
      status: 'good' as const,
      trend: 'up' as const,
      trendValue: '+3.2%'
    },
    {
      name: 'systolicPressure',
      label: '收缩压',
      value: 89.3,
      max: 100,
      unit: '分',
      icon: '💉',
      color: '#a55eea',
      status: 'good' as const,
      trend: 'stable' as const,
      trendValue: '+0.5%'
    },
    {
      name: 'diastolicPressure',
      label: '舒张压',
      value: 91.7,
      max: 100,
      unit: '分',
      icon: '🩸',
      color: '#26de81',
      status: 'good' as const,
      trend: 'up' as const,
      trendValue: '+1.8%'
    },
    {
      name: 'stress',
      label: '压力',
      value: 76.4,
      max: 100,
      unit: '分',
      icon: '🧠',
      color: '#fd79a8',
      status: 'attention' as const,
      trend: 'down' as const,
      trendValue: '-5.3%'
    }
  ],
  suggestions: [
    {
      id: '1',
      title: '适度运动',
      description: '建议每日步数达到8000步以上',
      priority: 'medium' as const,
      icon: '🏃‍♂️'
    },
    {
      id: '2',
      title: '压力管理',
      description: '建议进行冥想或深呼吸练习',
      priority: 'high' as const,
      icon: '🧘‍♀️'
    },
    {
      id: '3',
      title: '规律作息',
      description: '保持良好的睡眠质量',
      priority: 'low' as const,
      icon: '😴'
    }
  ]
}

// 计算属性
const healthData = computed(() => props.data || defaultData)
const dimensions = computed(() => healthData.value.dimensions)
const totalScore = computed(() => healthData.value.totalScore)
const suggestions = computed(() => healthData.value.suggestions)

const scoreClass = computed(() => {
  const score = totalScore.value
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'normal'
  if (score >= 60) return 'attention'
  return 'warning'
})

const statusClass = computed(() => scoreClass.value)

const statusText = computed(() => {
  const statusMap = {
    excellent: '优秀状态',
    good: '良好状态',
    normal: '正常状态',
    attention: '需要关注',
    warning: '需要改善'
  }
  return statusMap[scoreClass.value]
})

const trendClass = computed(() => {
  const trend = healthData.value.trend
  if (trend > 1) return 'up'
  if (trend < -1) return 'down'
  return 'stable'
})

const trendIcon = computed(() => {
  const iconMap = {
    up: '↗️',
    down: '↘️',
    stable: '➡️'
  }
  return iconMap[trendClass.value]
})

const trendText = computed(() => {
  const trend = healthData.value.trend
  const abs = Math.abs(trend)
  if (trend > 0) return `上升${abs.toFixed(1)}%`
  if (trend < 0) return `下降${abs.toFixed(1)}%`
  return '保持稳定'
})

// 方法
const getStatusText = (status: string) => {
  const statusMap = {
    excellent: '优秀',
    good: '良好',
    normal: '正常',
    attention: '关注',
    warning: '警告'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const highlightDimension = (index: number) => {
  activeDimension.value = index
  
  if (radarChart && index >= 0) {
    // 高亮显示对应的维度
    radarChart.dispatchAction({
      type: 'highlight',
      seriesIndex: 0,
      dataIndex: index
    })
  } else if (radarChart) {
    // 取消高亮
    radarChart.dispatchAction({
      type: 'downplay',
      seriesIndex: 0
    })
  }
}

// 初始化雷达图
const initRadarChart = async () => {
  if (!radarChartRef.value) return

  await nextTick()

  radarChart = echarts.init(radarChartRef.value)

  const indicator = dimensions.value.map(d => ({
    name: d.label,
    max: d.max,
    color: d.color
  }))

  const data = dimensions.value.map(d => d.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 21, 41, 0.9)',
      borderColor: 'rgba(0, 228, 255, 0.5)',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        const dimension = dimensions.value[params.dataIndex]
        return `
          <div style="padding: 8px;">
            <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px;">
              ${dimension.icon} ${dimension.label}
            </div>
            <div style="font-size: 16px; color: ${dimension.color}; font-weight: 700;">
              ${dimension.value} ${dimension.unit}
            </div>
            <div style="font-size: 12px; margin-top: 4px;">
              状态: ${getStatusText(dimension.status)}
            </div>
            <div style="font-size: 12px; color: #8cc8ff;">
              趋势: ${dimension.trendValue}
            </div>
          </div>
        `
      }
    },
    legend: {
      show: false
    },
    radar: {
      indicator,
      center: ['50%', '50%'],
      radius: '70%',
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#8cc8ff',
        fontSize: 11,
        fontWeight: 600
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 228, 255, 0.2)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 228, 255, 0.1)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(0, 228, 255, 0.02)',
            'rgba(0, 228, 255, 0.04)',
            'rgba(0, 228, 255, 0.06)',
            'rgba(0, 228, 255, 0.08)'
          ]
        }
      }
    },
    series: [
      {
        name: '健康评分',
        type: 'radar',
        symbol: 'circle',
        symbolSize: 6,
        data: [
          {
            value: data,
            name: '当前评分',
            lineStyle: {
              color: '#00e4ff',
              width: 2
            },
            itemStyle: {
              color: '#00e4ff',
              borderColor: '#00e4ff',
              borderWidth: 2
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(0, 228, 255, 0.3)' },
                { offset: 1, color: 'rgba(0, 228, 255, 0.05)' }
              ])
            },
            emphasis: {
              lineStyle: {
                width: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(0, 228, 255, 0.8)'
              },
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 228, 255, 0.8)'
              }
            }
          }
        ],
        animationDuration: 1000,
        animationEasing: 'cubicOut'
      }
    ]
  }

  radarChart.setOption(option)

  // 点击事件
  radarChart.on('click', (params) => {
    if (params.dataIndex !== undefined) {
      const dimension = dimensions.value[params.dataIndex]
      emit('dimensionClick', dimension)
    }
  })

  // 鼠标悬停事件
  radarChart.on('mouseover', (params) => {
    if (params.dataIndex !== undefined) {
      activeDimension.value = params.dataIndex
    }
  })

  radarChart.on('mouseout', () => {
    activeDimension.value = -1
  })
}

// 更新图表数据
const updateChart = () => {
  if (!radarChart) return

  const indicator = dimensions.value.map(d => ({
    name: d.label,
    max: d.max,
    color: d.color
  }))

  const data = dimensions.value.map(d => d.value)

  radarChart.setOption({
    radar: {
      indicator
    },
    series: [{
      data: [{
        value: data,
        name: '当前评分'
      }]
    }]
  })
}

// 响应式处理
const handleResize = () => {
  radarChart?.resize()
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 暴露方法
defineExpose({
  updateChart,
  handleResize
})

// 生命周期
onMounted(() => {
  initRadarChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
})
</script>

<style lang="scss" scoped>
.health-score-radar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

// ========== 评分显示区域 ==========
.score-display {
  background: rgba(0, 21, 41, 0.4);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.score-info {
  .score-title {
    font-size: 12px;
    color: #8cc8ff;
    margin-bottom: 8px;
  }
  
  .score-main {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
    margin-bottom: 6px;
    
    .score-number {
      font-size: 36px;
      font-weight: 700;
      line-height: 1;
      
      &.excellent {
        color: #00ff9d;
      }
      
      &.good {
        color: #00e4ff;
      }
      
      &.normal {
        color: #ffbb00;
      }
      
      &.attention {
        color: #ff6600;
      }
      
      &.warning {
        color: #ff4444;
      }
    }
    
    .score-unit {
      font-size: 14px;
      color: #8cc8ff;
    }
  }
  
  .score-status {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
    
    &.excellent {
      color: #00ff9d;
    }
    
    &.good {
      color: #00e4ff;
    }
    
    &.normal {
      color: #ffbb00;
    }
    
    &.attention {
      color: #ff6600;
    }
    
    &.warning {
      color: #ff4444;
    }
  }
  
  .score-trend {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    font-size: 11px;
    color: #8cc8ff;
    
    .trend-icon {
      &.up {
        color: #00ff9d;
      }
      
      &.down {
        color: #ff6600;
      }
      
      &.stable {
        color: #ffbb00;
      }
    }
  }
}

// ========== 雷达图容器 ==========
.radar-container {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 200px;
}

.radar-chart {
  flex: 2;
  min-height: 200px;
}

// ========== 维度信息 ==========
.dimensions-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 240px;
  overflow-y: auto;
}

.dimension-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover,
  &.active {
    background: rgba(0, 228, 255, 0.1);
    border: 1px solid rgba(0, 228, 255, 0.3);
  }
  
  .dimension-icon {
    font-size: 16px;
    width: 20px;
    text-align: center;
  }
  
  .dimension-info {
    flex: 1;
    min-width: 0;
    
    .dimension-name {
      font-size: 11px;
      color: #8cc8ff;
      margin-bottom: 2px;
    }
    
    .dimension-value {
      display: flex;
      align-items: baseline;
      gap: 2px;
      margin-bottom: 2px;
      
      .value {
        font-size: 14px;
        font-weight: 600;
      }
      
      .unit {
        font-size: 10px;
        color: #8cc8ff;
      }
    }
    
    .dimension-status {
      font-size: 9px;
      padding: 1px 4px;
      border-radius: 8px;
      
      &.excellent {
        background: rgba(0, 255, 157, 0.2);
        color: #00ff9d;
      }
      
      &.good {
        background: rgba(0, 228, 255, 0.2);
        color: #00e4ff;
      }
      
      &.normal {
        background: rgba(255, 187, 0, 0.2);
        color: #ffbb00;
      }
      
      &.attention {
        background: rgba(255, 102, 0, 0.2);
        color: #ff6600;
      }
      
      &.warning {
        background: rgba(255, 68, 68, 0.2);
        color: #ff4444;
      }
    }
  }
  
  .dimension-trend {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 8px;
    min-width: 32px;
    text-align: center;
    
    &.up {
      background: rgba(0, 255, 157, 0.2);
      color: #00ff9d;
    }
    
    &.down {
      background: rgba(255, 102, 0, 0.2);
      color: #ff6600;
    }
    
    &.stable {
      background: rgba(255, 187, 0, 0.2);
      color: #ffbb00;
    }
  }
}

// ========== 健康建议 ==========
.health-suggestions {
  background: rgba(0, 21, 41, 0.4);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 6px;
  padding: 8px;
  max-height: 120px;
}

.suggestions-title {
  font-size: 12px;
  color: #00e4ff;
  font-weight: 600;
  margin-bottom: 6px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(0, 228, 255, 0.1);
  }
  
  &.high {
    border-left: 3px solid #ff4444;
  }
  
  &.medium {
    border-left: 3px solid #ffbb00;
  }
  
  &.low {
    border-left: 3px solid #00ff9d;
  }
  
  .suggestion-icon {
    font-size: 14px;
  }
  
  .suggestion-content {
    flex: 1;
    min-width: 0;
    
    .suggestion-title {
      font-size: 11px;
      color: #00e4ff;
      font-weight: 600;
      margin-bottom: 1px;
    }
    
    .suggestion-desc {
      font-size: 9px;
      color: #8cc8ff;
      line-height: 1.2;
    }
  }
}

// ========== 滚动条美化 ==========
.dimensions-info::-webkit-scrollbar {
  width: 4px;
}

.dimensions-info::-webkit-scrollbar-track {
  background: rgba(0, 228, 255, 0.1);
  border-radius: 2px;
}

.dimensions-info::-webkit-scrollbar-thumb {
  background: rgba(0, 228, 255, 0.3);
  border-radius: 2px;
}

.dimensions-info::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 228, 255, 0.5);
}

// ========== 响应式设计 ==========
@media (max-width: 768px) {
  .radar-container {
    flex-direction: column;
  }
  
  .radar-chart {
    height: 200px;
  }
  
  .dimensions-info {
    max-height: 150px;
  }
  
  .health-suggestions {
    max-height: 100px;
  }
}
</style>