<template>
  <div class="severity-pie-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="total-count">
        <span class="count-label">总计</span>
        <span class="count-value">{{ totalCount }}</span>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 严重程度饼图 -->
    </div>
    
    <div class="severity-legend">
      <div 
        v-for="item in severityData" 
        :key="item.name"
        class="legend-item"
        :class="item.level"
      >
        <div class="legend-indicator">
          <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
          <span class="legend-name">{{ item.name }}</span>
        </div>
        <div class="legend-stats">
          <span class="legend-count">{{ item.value }}</span>
          <span class="legend-percent">{{ getPercentage(item.value) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'

interface SeverityData {
  name: string
  value: number
  color: string
  level: string
}

interface Props {
  title?: string
  height?: string
  data?: SeverityData[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '预警严重程度分布',
  height: '400px',
  data: () => []
})

// 响应式数据
const chartRef = ref<HTMLElement>()

// 默认严重程度数据
const severityData = ref<SeverityData[]>([
  {
    name: '严重预警',
    value: 12,
    color: '#ff6b6b',
    level: 'critical'
  },
  {
    name: '高优先级',
    value: 28,
    color: '#ffa726', 
    level: 'high'
  },
  {
    name: '中等预警',
    value: 45,
    color: '#42a5f5',
    level: 'medium'
  },
  {
    name: '低级预警',
    value: 23,
    color: '#66bb6a',
    level: 'low'
  }
])

// 计算属性
const totalCount = computed(() => {
  return severityData.value.reduce((sum, item) => sum + item.value, 0)
})

// 生成图表
const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `
          <div style="margin-bottom: 5px; font-weight: bold;">${params.name}</div>
          <div style="margin-bottom: 2px;">数量: ${params.value}</div>
          <div>占比: ${params.percent}%</div>
        `
      }
    },
    legend: {
      show: false
    },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      label: {
        show: false
      },
      labelLine: {
        show: false
      },
      emphasis: {
        scale: true,
        scaleSize: 5,
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      data: severityData.value.map(item => ({
        name: item.name,
        value: item.value,
        itemStyle: {
          color: item.color,
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        }
      }))
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

// 工具方法
const getPercentage = (value: number) => {
  if (totalCount.value === 0) return 0
  return Math.round((value / totalCount.value) * 100)
}

// 生命周期
onMounted(() => {
  // 如果有传入数据则使用传入数据
  if (props.data && props.data.length > 0) {
    severityData.value = props.data
  }
  
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.data, (newData) => {
  if (newData && newData.length > 0) {
    severityData.value = newData
    updateChart()
  }
}, { deep: true })
</script>

<style lang="scss" scoped>
.severity-pie-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .chart-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .total-count {
    text-align: right;
    
    .count-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      display: block;
      margin-bottom: 2px;
    }
    
    .count-value {
      font-size: var(--font-xl);
      font-weight: 700;
      color: var(--primary-500);
      font-family: var(--font-tech);
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 250px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.severity-legend {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  
  .legend-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateX(4px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .legend-indicator {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      
      .legend-color {
        width: 12px;
        height: 12px;
        border-radius: var(--radius-full);
        flex-shrink: 0;
      }
      
      .legend-name {
        font-size: var(--font-sm);
        color: var(--text-primary);
        font-weight: 500;
      }
    }
    
    .legend-stats {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      
      .legend-count {
        font-size: var(--font-md);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
      }
      
      .legend-percent {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        background: var(--bg-secondary);
        padding: 2px 6px;
        border-radius: var(--radius-sm);
      }
    }
    
    &.critical {
      border-left: 4px solid #ff6b6b;
      
      &:hover {
        border-color: #ff6b6b;
        background: rgba(255, 107, 107, 0.05);
      }
    }
    
    &.high {
      border-left: 4px solid #ffa726;
      
      &:hover {
        border-color: #ffa726;
        background: rgba(255, 167, 38, 0.05);
      }
    }
    
    &.medium {
      border-left: 4px solid #42a5f5;
      
      &:hover {
        border-color: #42a5f5;
        background: rgba(66, 165, 245, 0.05);
      }
    }
    
    &.low {
      border-left: 4px solid #66bb6a;
      
      &:hover {
        border-color: #66bb6a;
        background: rgba(102, 187, 106, 0.05);
      }
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
    
    .total-count {
      text-align: left;
    }
  }
  
  .severity-legend {
    .legend-item {
      .legend-stats {
        flex-direction: column;
        gap: var(--spacing-xs);
        text-align: right;
      }
    }
  }
}
</style>