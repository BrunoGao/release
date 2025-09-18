<template>
  <div class="correlation-matrix">
    <div class="matrix-header">
      <h4 class="matrix-title">{{ title }}</h4>
      <div class="correlation-legend">
        <span class="legend-label">负相关</span>
        <div class="legend-bar negative"></div>
        <span class="legend-value">-1</span>
        <div class="legend-bar neutral"></div>
        <span class="legend-value">0</span>
        <div class="legend-bar positive"></div>
        <span class="legend-value">1</span>
        <span class="legend-label">正相关</span>
      </div>
    </div>
    
    <div class="matrix-container" ref="matrixRef">
      <!-- ECharts 相关性矩阵图 -->
    </div>
    
    <div class="matrix-insights">
      <div class="insight-item strong-positive">
        <div class="insight-header">
          <span class="insight-color"></span>
          <span class="insight-label">强正相关</span>
        </div>
        <div class="insight-pairs">
          <span>心率 - 血氧 (相关系数</span>
          <span>0.82</span>
        </div>
      </div>
      
      <div class="insight-item strong-negative">
        <div class="insight-header">
          <span class="insight-color"></span>
          <span class="insight-label">强负相关</span>
        </div>
        <div class="insight-pairs">
          <span>压力 - 睡眠质量</span>
          <span>-0.76</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  data?: Array<{
    indicator1: string
    indicator2: string
    correlation: number
  }>
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康指标相关性分析',
  data: () => []
})

const matrixRef = ref<HTMLElement>()

const correlationData = [
  ['心率', '血氧', 0.82],
  ['心率', '体温', 0.45],
  ['心率', '血压', 0.68],
  ['心率', '压力', 0.71],
  ['心率', '睡眠', -0.34],
  ['血氧', '体温', 0.23],
  ['血氧', '血压', 0.56],
  ['血氧', '压力', -0.42],
  ['血氧', '睡眠', 0.38],
  ['体温', '血压', 0.31],
  ['体温', '压力', 0.29],
  ['体温', '睡眠', -0.18],
  ['血压', '压力', 0.63],
  ['血压', '睡眠', -0.47],
  ['压力', '睡眠', -0.76]
]

const indicators = ['心率', '血氧', '体温', '血压', '压力', '睡眠']

const initChart = () => {
  if (!matrixRef.value) return
  
  const chart = echarts.init(matrixRef.value, 'health-tech')
  
  // 构建矩阵数据
  const matrixData = []
  for (let i = 0; i < indicators.length; i++) {
    for (let j = 0; j < indicators.length; j++) {
      if (i === j) {
        matrixData.push([i, j, 1])
      } else {
        const correlation = correlationData.find(item => 
          (item[0] === indicators[i] && item[1] === indicators[j]) ||
          (item[0] === indicators[j] && item[1] === indicators[i])
        )
        matrixData.push([i, j, correlation ? correlation[2] : 0])
      }
    }
  }
  
  const option = {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const xLabel = indicators[params.data[0]]
        const yLabel = indicators[params.data[1]]
        const value = params.data[2].toFixed(2)
        return `${xLabel} - ${yLabel}: ${value}`
      }
    },
    grid: {
      height: '80%',
      top: '10%',
      left: '15%',
      right: '5%'
    },
    xAxis: {
      type: 'category',
      data: indicators,
      splitArea: {
        show: true
      },
      axisLabel: {
        color: '#999',
        fontSize: 12
      }
    },
    yAxis: {
      type: 'category',
      data: indicators,
      splitArea: {
        show: true
      },
      axisLabel: {
        color: '#999',
        fontSize: 12
      }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#1e88e5', '#ffffff', '#e53935']
      },
      textStyle: {
        color: '#999'
      }
    },
    series: [{
      name: '相关系数',
      type: 'heatmap',
      data: matrixData,
      label: {
        show: true,
        formatter: (params: any) => params.data[2].toFixed(2),
        color: '#333',
        fontSize: 10
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  chart.setOption(option)
  
  const resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    chart.dispose()
  })
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})
</script>

<style lang="scss" scoped>
.correlation-matrix {
  width: 100%;
  height: 100%;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .matrix-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .correlation-legend {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    
    .legend-label {
      font-size: var(--font-xs);
      color: var(--text-secondary);
    }
    
    .legend-bar {
      width: 20px;
      height: 8px;
      border-radius: var(--radius-sm);
      
      &.negative {
        background: linear-gradient(90deg, #1e88e5, #42a5f5);
      }
      
      &.neutral {
        background: #ffffff;
        border: 1px solid var(--border-light);
      }
      
      &.positive {
        background: linear-gradient(90deg, #ff5722, #e53935);
      }
    }
    
    .legend-value {
      font-size: var(--font-xs);
      color: var(--text-secondary);
      font-family: var(--font-tech);
    }
  }
}

.matrix-container {
  flex: 1;
  min-height: 300px;
}

.matrix-insights {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  
  .insight-item {
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    
    .insight-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-sm);
      
      .insight-color {
        width: 12px;
        height: 12px;
        border-radius: var(--radius-sm);
      }
      
      .insight-label {
        font-size: var(--font-sm);
        font-weight: 600;
        color: var(--text-primary);
      }
    }
    
    .insight-pairs {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--font-sm);
      color: var(--text-secondary);
      
      span:last-child {
        font-family: var(--font-tech);
        font-weight: 600;
        color: var(--text-primary);
      }
    }
    
    &.strong-positive .insight-color {
      background: var(--error-500);
    }
    
    &.strong-negative .insight-color {
      background: var(--primary-500);
    }
  }
}

@media (max-width: 768px) {
  .matrix-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .matrix-insights {
    grid-template-columns: 1fr;
  }
}
</style>