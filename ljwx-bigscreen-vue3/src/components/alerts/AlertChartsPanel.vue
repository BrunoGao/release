<template>
  <div class="alert-charts-panel">
    <!-- 告警统计概览 -->
    <div class="alert-overview">
      <div class="alert-stats">
        <div class="stat-item critical">
          <span class="stat-value">{{ alertStats.critical }}</span>
          <span class="stat-label">严重</span>
        </div>
        <div class="stat-item high">
          <span class="stat-value">{{ alertStats.high }}</span>
          <span class="stat-label">重要</span>
        </div>
        <div class="stat-item medium">
          <span class="stat-value">{{ alertStats.medium }}</span>
          <span class="stat-label">一般</span>
        </div>
        <div class="stat-item low">
          <span class="stat-value">{{ alertStats.low }}</span>
          <span class="stat-label">轻微</span>
        </div>
      </div>
      
      <div class="alert-status">
        <div class="status-badge" :class="overallStatusClass">
          {{ overallStatusText }}
        </div>
        <div class="status-info">
          <span>处理率: {{ handleRate }}%</span>
          <span>待处理: {{ alertStats.pending }}</span>
        </div>
      </div>
    </div>
    
    <!-- 四个图表网格 -->
    <div class="alert-charts-grid">
      <!-- 告警类型分布 - 环形图 -->
      <div class="chart-item">
        <div class="chart-header">
          <span class="chart-title">告警类型分布</span>
          <div class="chart-legend">
            <div v-for="item in alertTypes" :key="item.name" class="legend-item">
              <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
              <span class="legend-text">{{ item.name }}</span>
              <span class="legend-value">{{ item.count }}</span>
            </div>
          </div>
        </div>
        <div ref="typeChartRef" class="chart-container" id="alertTypeChart"></div>
      </div>
      
      <!-- 严重程度分析 - 柱状图 -->
      <div class="chart-item">
        <div class="chart-header">
          <span class="chart-title">严重程度分析</span>
          <div class="severity-stats">
            <span class="severity-trend">较上周 {{ severityTrend > 0 ? '+' : '' }}{{ severityTrend }}%</span>
          </div>
        </div>
        <div ref="severityChartRef" class="chart-container" id="alertLevelChart"></div>
      </div>
      
      <!-- 处理状态仪表盘 -->
      <div class="chart-item">
        <div class="chart-header">
          <span class="chart-title">处理状态</span>
          <div class="gauge-info">
            <span class="gauge-rate">{{ handleRate }}%</span>
            <span class="gauge-label">处理率</span>
          </div>
        </div>
        <div ref="statusChartRef" class="chart-container" id="alertStatusChart"></div>
      </div>
      
      <!-- 24小时趋势 - 折线图 -->
      <div class="chart-item">
        <div class="chart-header">
          <span class="chart-title">24小时趋势</span>
          <div class="trend-stats">
            <span class="peak-time">高峰: {{ peakTime }}</span>
            <span class="trend-direction" :class="trendDirection">{{ trendText }}</span>
          </div>
        </div>
        <div ref="trendChartRef" class="chart-container" id="alertTrendChart"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// Props
interface AlertData {
  critical: number
  high: number
  medium: number
  low: number
  pending: number
  resolved: number
  types: Array<{
    name: string
    count: number
    color: string
  }>
  hourlyData: Array<{
    hour: string
    count: number
  }>
}

interface Props {
  data?: AlertData
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 30000
})

// Emits
const emit = defineEmits<{
  chartClick: [data: any]
  refresh: []
}>()

// Refs
const typeChartRef = ref<HTMLElement>()
const severityChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()

// 图表实例
let typeChart: echarts.ECharts | null = null
let severityChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// 模拟数据
const defaultData: AlertData = {
  critical: 3,
  high: 12,
  medium: 28,
  low: 45,
  pending: 30,
  resolved: 58,
  types: [
    { name: 'WEAR_DEVICE_OFFLINE', count: 34, color: '#ff4444' },
    { name: 'HEALTH_ABNORMAL', count: 25, color: '#ff6600' },
    { name: 'LOCATION_TIMEOUT', count: 18, color: '#ffbb00' },
    { name: 'BATTERY_LOW', count: 11, color: '#00ff9d' }
  ],
  hourlyData: Array.from({ length: 24 }, (_, i) => ({
    hour: String(i).padStart(2, '0') + ':00',
    count: Math.floor(Math.random() * 20) + 5
  }))
}

// 状态计算
const alertStats = computed(() => props.data || defaultData)

const totalAlerts = computed(() => 
  alertStats.value.critical + alertStats.value.high + 
  alertStats.value.medium + alertStats.value.low
)

const handleRate = computed(() => 
  totalAlerts.value > 0 
    ? Math.round((alertStats.value.resolved / (alertStats.value.resolved + alertStats.value.pending)) * 100)
    : 0
)

const overallStatusClass = computed(() => {
  if (alertStats.value.critical > 0) return 'critical'
  if (alertStats.value.high > 5) return 'high'
  if (alertStats.value.medium > 20) return 'medium'
  return 'normal'
})

const overallStatusText = computed(() => {
  const statusMap = {
    critical: '⚠️ 严重告警',
    high: '⚡ 重要告警',
    medium: '📊 一般告警',
    normal: '✅ 状态正常'
  }
  return statusMap[overallStatusClass.value as keyof typeof statusMap]
})

const alertTypes = computed(() => alertStats.value.types)

const severityTrend = ref(-12.5)
const peakTime = ref('14:30')
const trendDirection = ref('up')
const trendText = ref('上升趋势')

// 初始化告警类型分布图
const initTypeChart = () => {
  if (!typeChartRef.value) return

  typeChart = echarts.init(typeChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
      backgroundColor: 'rgba(0, 21, 41, 0.9)',
      borderColor: 'rgba(0, 228, 255, 0.5)',
      textStyle: { color: '#fff' }
    },
    legend: {
      show: false
    },
    series: [
      {
        name: '告警类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#001529',
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\\n{d}%',
          fontSize: 10,
          color: '#8cc8ff'
        },
        labelLine: {
          show: true,
          lineStyle: {
            color: '#8cc8ff'
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 228, 255, 0.5)'
          }
        },
        data: alertTypes.value.map(item => ({
          value: item.count,
          name: item.name,
          itemStyle: { color: item.color }
        })),
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: (idx: number) => Math.random() * 200
      }
    ]
  }
  
  typeChart.setOption(option)
  
  // 点击事件
  typeChart.on('click', (params) => {
    emit('chartClick', { type: 'alertType', data: params })
  })
}

// 初始化严重程度分析图
const initSeverityChart = () => {
  if (!severityChartRef.value) return

  severityChart = echarts.init(severityChartRef.value)
  
  const severityData = [
    { name: '严重', value: alertStats.value.critical, color: '#ff4444' },
    { name: '重要', value: alertStats.value.high, color: '#ff6600' },
    { name: '一般', value: alertStats.value.medium, color: '#ffbb00' },
    { name: '轻微', value: alertStats.value.low, color: '#00ff9d' }
  ]
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0, 21, 41, 0.9)',
      borderColor: 'rgba(0, 228, 255, 0.5)',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '15%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: severityData.map(item => item.name),
      axisLine: {
        lineStyle: { color: 'rgba(0, 228, 255, 0.3)' }
      },
      axisLabel: {
        color: '#8cc8ff',
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: { color: 'rgba(0, 228, 255, 0.3)' }
      },
      axisLabel: {
        color: '#8cc8ff',
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 228, 255, 0.1)'
        }
      }
    },
    series: [
      {
        name: '告警数量',
        type: 'bar',
        data: severityData.map(item => ({
          value: item.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: item.color },
              { offset: 1, color: item.color + '66' }
            ])
          }
        })),
        barWidth: '60%',
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 228, 255, 0.5)'
          }
        },
        animationDelay: (idx: number) => idx * 100
      }
    ]
  }
  
  severityChart.setOption(option)
  
  severityChart.on('click', (params) => {
    emit('chartClick', { type: 'severity', data: params })
  })
}

// 初始化处理状态仪表盘
const initStatusChart = () => {
  if (!statusChartRef.value) return

  statusChart = echarts.init(statusChartRef.value)
  
  const option = {
    tooltip: {
      formatter: '{a} <br/>{b} : {c}%',
      backgroundColor: 'rgba(0, 21, 41, 0.9)',
      borderColor: 'rgba(0, 228, 255, 0.5)',
      textStyle: { color: '#fff' }
    },
    series: [
      {
        name: '处理率',
        type: 'gauge',
        center: ['50%', '60%'],
        radius: '70%',
        min: 0,
        max: 100,
        splitNumber: 10,
        progress: {
          show: true,
          width: 12,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#ff4444' },
              { offset: 0.5, color: '#ffbb00' },
              { offset: 1, color: '#00ff9d' }
            ])
          }
        },
        pointer: {
          show: true,
          length: '75%',
          width: 4,
          itemStyle: {
            color: '#00e4ff'
          }
        },
        axisLine: {
          lineStyle: {
            width: 12,
            color: [
              [0.3, '#ff4444'],
              [0.7, '#ffbb00'],
              [1, '#00ff9d']
            ]
          }
        },
        axisTick: {
          distance: -20,
          length: 5,
          lineStyle: {
            color: '#8cc8ff'
          }
        },
        splitLine: {
          distance: -20,
          length: 8,
          lineStyle: {
            color: '#8cc8ff'
          }
        },
        axisLabel: {
          distance: -35,
          color: '#8cc8ff',
          fontSize: 10
        },
        anchor: {
          show: true,
          showAbove: true,
          size: 8,
          itemStyle: {
            color: '#00e4ff'
          }
        },
        title: {
          show: false
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: '#00e4ff',
          fontSize: 16,
          offsetCenter: [0, '80%']
        },
        data: [
          {
            value: handleRate.value,
            name: '处理率'
          }
        ]
      }
    ]
  }
  
  statusChart.setOption(option)
  
  statusChart.on('click', (params) => {
    emit('chartClick', { type: 'status', data: params })
  })
}

// 初始化24小时趋势图
const initTrendChart = () => {
  if (!trendChartRef.value) return

  trendChart = echarts.init(trendChartRef.value)
  
  const hourlyData = alertStats.value.hourlyData
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 21, 41, 0.9)',
      borderColor: 'rgba(0, 228, 255, 0.5)',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '10%',
      top: '15%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: hourlyData.map(item => item.hour),
      axisLine: {
        lineStyle: { color: 'rgba(0, 228, 255, 0.3)' }
      },
      axisLabel: {
        color: '#8cc8ff',
        fontSize: 9,
        interval: 3
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: { color: 'rgba(0, 228, 255, 0.3)' }
      },
      axisLabel: {
        color: '#8cc8ff',
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 228, 255, 0.1)'
        }
      }
    },
    series: [
      {
        name: '告警数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        data: hourlyData.map(item => item.count),
        lineStyle: {
          color: '#00e4ff',
          width: 2
        },
        itemStyle: {
          color: '#00e4ff'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 228, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 228, 255, 0.05)' }
          ])
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 228, 255, 0.8)'
          }
        }
      }
    ]
  }
  
  trendChart.setOption(option)
  
  trendChart.on('click', (params) => {
    emit('chartClick', { type: 'trend', data: params })
  })
}

// 初始化所有图表
const initCharts = async () => {
  await nextTick()
  
  setTimeout(() => {
    initTypeChart()
    initSeverityChart()
    initStatusChart()
    initTrendChart()
  }, 100)
}

// 更新图表数据
const updateCharts = () => {
  if (typeChart) {
    typeChart.setOption({
      series: [{
        data: alertTypes.value.map(item => ({
          value: item.count,
          name: item.name,
          itemStyle: { color: item.color }
        }))
      }]
    })
  }
  
  if (severityChart) {
    const severityData = [
      { name: '严重', value: alertStats.value.critical, color: '#ff4444' },
      { name: '重要', value: alertStats.value.high, color: '#ff6600' },
      { name: '一般', value: alertStats.value.medium, color: '#ffbb00' },
      { name: '轻微', value: alertStats.value.low, color: '#00ff9d' }
    ]
    
    severityChart.setOption({
      xAxis: {
        data: severityData.map(item => item.name)
      },
      series: [{
        data: severityData.map(item => ({
          value: item.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: item.color },
              { offset: 1, color: item.color + '66' }
            ])
          }
        }))
      }]
    })
  }
  
  if (statusChart) {
    statusChart.setOption({
      series: [{
        data: [{
          value: handleRate.value,
          name: '处理率'
        }]
      }]
    })
  }
  
  if (trendChart) {
    const hourlyData = alertStats.value.hourlyData
    trendChart.setOption({
      xAxis: {
        data: hourlyData.map(item => item.hour)
      },
      series: [{
        data: hourlyData.map(item => item.count)
      }]
    })
  }
}

// 响应式处理
const handleResize = () => {
  typeChart?.resize()
  severityChart?.resize()
  statusChart?.resize()
  trendChart?.resize()
}

// 自动刷新
let refreshTimer: number | null = null

const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = window.setInterval(() => {
      emit('refresh')
    }, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听数据变化
watch(() => props.data, (newData) => {
  if (newData) {
    updateCharts()
  }
}, { deep: true })

// 暴露方法
defineExpose({
  initCharts,
  updateCharts,
  handleResize
})

// 生命周期
onMounted(() => {
  initCharts()
  startAutoRefresh()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  
  // 销毁图表实例
  typeChart?.dispose()
  severityChart?.dispose()
  statusChart?.dispose()
  trendChart?.dispose()
})
</script>

<style lang="scss" scoped>
.alert-charts-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

// ========== 告警概览 ==========
.alert-overview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  min-width: 40px;
  
  .stat-value {
    font-size: 16px;
    font-weight: 700;
    line-height: 1;
  }
  
  .stat-label {
    font-size: 10px;
    margin-top: 2px;
    opacity: 0.8;
  }
  
  &.critical {
    background: rgba(255, 68, 68, 0.15);
    color: #ff4444;
  }
  
  &.high {
    background: rgba(255, 102, 0, 0.15);
    color: #ff6600;
  }
  
  &.medium {
    background: rgba(255, 187, 0, 0.15);
    color: #ffbb00;
  }
  
  &.low {
    background: rgba(0, 255, 157, 0.15);
    color: #00ff9d;
  }
}

.alert-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  
  &.critical {
    background: rgba(255, 68, 68, 0.2);
    color: #ff4444;
    animation: pulse 2s ease-in-out infinite;
  }
  
  &.high {
    background: rgba(255, 102, 0, 0.2);
    color: #ff6600;
  }
  
  &.medium {
    background: rgba(255, 187, 0, 0.2);
    color: #ffbb00;
  }
  
  &.normal {
    background: rgba(0, 255, 157, 0.2);
    color: #00ff9d;
  }
}

.status-info {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #8cc8ff;
  
  span {
    white-space: nowrap;
  }
}

// ========== 图表网格 ==========
.alert-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 8px;
  flex: 1;
  min-height: 250px;
  overflow: hidden;
}

.chart-item {
  background: rgba(0, 21, 41, 0.4);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 6px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(0, 228, 255, 0.6);
    box-shadow: 0 4px 15px rgba(0, 228, 255, 0.2);
  }
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
  min-height: 20px;
}

.chart-title {
  font-size: 11px;
  color: #00e4ff;
  font-weight: 600;
}

.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 9px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-text {
  color: #8cc8ff;
  font-size: 8px;
}

.legend-value {
  color: #00e4ff;
  font-weight: 600;
  font-size: 8px;
}

.severity-stats,
.trend-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.severity-trend,
.peak-time {
  font-size: 9px;
  color: #8cc8ff;
}

.trend-direction {
  font-size: 9px;
  font-weight: 600;
  
  &.up {
    color: #ff6600;
  }
  
  &.down {
    color: #00ff9d;
  }
  
  &.stable {
    color: #ffbb00;
  }
}

.gauge-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.gauge-rate {
  font-size: 14px;
  font-weight: 700;
  color: #00e4ff;
}

.gauge-label {
  font-size: 9px;
  color: #8cc8ff;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 110px;
  max-height: 200px;
}

// ========== 动画 ==========
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

// ========== 响应式设计 ==========
@media (max-width: 1200px) {
  .alert-charts-grid {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
  }
  
  .chart-container {
    min-height: 80px;
    max-height: 120px;
  }
}

@media (max-width: 768px) {
  .alert-stats {
    gap: 6px;
  }
  
  .stat-item {
    padding: 4px 6px;
    min-width: 32px;
    
    .stat-value {
      font-size: 14px;
    }
    
    .stat-label {
      font-size: 9px;
    }
  }
  
  .chart-container {
    min-height: 60px;
    max-height: 100px;
  }
}
</style>