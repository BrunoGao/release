<template>
  <div class="blood-pressure-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="pressure-status" :class="getPressureStatusClass(currentReading)">
        <div class="pressure-values">
          <span class="systolic">{{ currentReading.systolic }}</span>
          <span class="separator">/</span>
          <span class="diastolic">{{ currentReading.diastolic }}</span>
          <span class="unit">mmHg</span>
        </div>
        <div class="pressure-label">{{ getPressureLabel(currentReading) }}</div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 血压趋势图 -->
    </div>
    
    <div class="pressure-ranges">
      <div class="range-item normal">
        <span class="range-color"></span>
        <span class="range-label">正常</span>
        <span class="range-value">&lt;120/80</span>
      </div>
      <div class="range-item elevated">
        <span class="range-color"></span>
        <span class="range-label">偏高</span>
        <span class="range-value">120-129/&lt;80</span>
      </div>
      <div class="range-item stage1">
        <span class="range-color"></span>
        <span class="range-label">高血压1期</span>
        <span class="range-value">130-139/80-89</span>
      </div>
      <div class="range-item stage2">
        <span class="range-color"></span>
        <span class="range-label">高血压2期</span>
        <span class="range-value">&ge;140/90</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { echarts } from '@/plugins/echarts'
import type { BloodPressureReading } from '@/types/health'

interface Props {
  title?: string
  height?: string
  readings?: BloodPressureReading[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '血压监测',
  height: '400px',
  readings: () => []
})

// 响应式数据
const chartRef = ref<HTMLElement>()

// 当前血压读数
const currentReading = reactive<BloodPressureReading>({
  systolic: 120,
  diastolic: 80,
  trend: 'stable',
  timestamp: new Date(),
  quality: 'good'
})

// 生成模拟数据
const generateChartData = () => {
  const data = {
    xAxis: [] as string[],
    systolic: [] as number[],
    diastolic: [] as number[]
  }
  
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 3600000) // 每小时
    data.xAxis.push(date.getHours() + ':00')
    
    // 模拟血压数据
    const baseSystolic = 120 + Math.sin(i * 0.5) * 10
    const baseDiastolic = 80 + Math.sin(i * 0.3) * 5
    
    data.systolic.push(Math.floor(baseSystolic + Math.random() * 10 - 5))
    data.diastolic.push(Math.floor(baseDiastolic + Math.random() * 6 - 3))
  }
  
  // 更新当前读数
  currentReading.systolic = data.systolic[data.systolic.length - 1]
  currentReading.diastolic = data.diastolic[data.diastolic.length - 1]
  currentReading.timestamp = new Date()
  
  return data
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const data = generateChartData()
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const systolic = params.find((p: any) => p.seriesName === '收缩压')
        const diastolic = params.find((p: any) => p.seriesName === '舒张压')
        
        return `
          <div style="margin-bottom: 5px;">时间: ${params[0].axisValue}</div>
          <div style="margin-bottom: 2px;">
            <span style="color: #ff6b6b;">收缩压: ${systolic.value} mmHg</span>
          </div>
          <div>
            <span style="color: #42a5f5;">舒张压: ${diastolic.value} mmHg</span>
          </div>
          <div style="margin-top: 5px; color: #999;">
            ${getPressureLabel({ systolic: systolic.value, diastolic: diastolic.value })}
          </div>
        `
      }
    },
    legend: {
      show: false
    },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLabel: {
        color: '#999',
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#333'
        }
      }
    },
    yAxis: {
      type: 'value',
      min: 60,
      max: 160,
      axisLabel: {
        color: '#999',
        fontSize: 12,
        formatter: '{value} mmHg'
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    },
    series: [
      {
        name: '收缩压',
        type: 'line',
        data: data.systolic,
        lineStyle: {
          color: '#ff6b6b',
          width: 3
        },
        itemStyle: {
          color: '#ff6b6b',
          borderWidth: 2,
          borderColor: '#fff'
        },
        symbol: 'circle',
        symbolSize: 8,
        smooth: true,
        markLine: {
          silent: true,
          lineStyle: {
            color: '#ff6b6b',
            type: 'dashed',
            opacity: 0.5
          },
          data: [
            { yAxis: 140, label: { formatter: '高血压线 (140)' } }
          ]
        }
      },
      {
        name: '舒张压',
        type: 'line',
        data: data.diastolic,
        lineStyle: {
          color: '#42a5f5',
          width: 3
        },
        itemStyle: {
          color: '#42a5f5',
          borderWidth: 2,
          borderColor: '#fff'
        },
        symbol: 'circle',
        symbolSize: 8,
        smooth: true,
        markLine: {
          silent: true,
          lineStyle: {
            color: '#42a5f5',
            type: 'dashed',
            opacity: 0.5
          },
          data: [
            { yAxis: 90, label: { formatter: '高血压线 (90)' } }
          ]
        }
      }
    ]
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
const getPressureLabel = (reading: any) => {
  const { systolic, diastolic } = reading
  
  if (systolic >= 180 || diastolic >= 120) return '高血压危象'
  if (systolic >= 140 || diastolic >= 90) return '高血压2期'
  if (systolic >= 130 || diastolic >= 80) return '高血压1期'
  if (systolic >= 120 && diastolic < 80) return '血压偏高'
  return '正常血压'
}

const getPressureStatusClass = (reading: BloodPressureReading) => {
  const { systolic, diastolic } = reading
  
  if (systolic >= 180 || diastolic >= 120) return 'crisis'
  if (systolic >= 140 || diastolic >= 90) return 'stage2'
  if (systolic >= 130 || diastolic >= 80) return 'stage1'
  if (systolic >= 120 && diastolic < 80) return 'elevated'
  return 'normal'
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.readings, () => {
  updateChart()
}, { deep: true })
</script>

<style lang="scss" scoped>
.blood-pressure-chart {
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
  
  .pressure-status {
    text-align: right;
    
    .pressure-values {
      display: flex;
      align-items: baseline;
      gap: 2px;
      margin-bottom: var(--spacing-xs);
      
      .systolic {
        font-size: var(--font-xl);
        font-weight: 700;
        font-family: var(--font-tech);
      }
      
      .separator {
        font-size: var(--font-lg);
        color: var(--text-secondary);
      }
      
      .diastolic {
        font-size: var(--font-xl);
        font-weight: 700;
        font-family: var(--font-tech);
      }
      
      .unit {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-left: var(--spacing-xs);
      }
    }
    
    .pressure-label {
      font-size: var(--font-sm);
      font-weight: 600;
      padding: 2px 8px;
      border-radius: var(--radius-sm);
    }
    
    &.normal {
      .pressure-values .systolic,
      .pressure-values .diastolic {
        color: var(--success-500);
      }
      .pressure-label {
        background: rgba(102, 187, 106, 0.2);
        color: var(--success-500);
      }
    }
    
    &.elevated {
      .pressure-values .systolic,
      .pressure-values .diastolic {
        color: var(--warning-500);
      }
      .pressure-label {
        background: rgba(255, 167, 38, 0.2);
        color: var(--warning-500);
      }
    }
    
    &.stage1 {
      .pressure-values .systolic,
      .pressure-values .diastolic {
        color: var(--error-500);
      }
      .pressure-label {
        background: rgba(255, 107, 107, 0.2);
        color: var(--error-500);
      }
    }
    
    &.stage2 {
      .pressure-values .systolic,
      .pressure-values .diastolic {
        color: #d32f2f;
      }
      .pressure-label {
        background: rgba(211, 47, 47, 0.2);
        color: #d32f2f;
      }
    }
    
    &.crisis {
      .pressure-values .systolic,
      .pressure-values .diastolic {
        color: #b71c1c;
        animation: pulse 2s ease-in-out infinite;
      }
      .pressure-label {
        background: rgba(183, 28, 28, 0.2);
        color: #b71c1c;
        animation: pulse 2s ease-in-out infinite;
      }
    }
  }
}

.chart-container {
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.pressure-ranges {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  
  .range-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--bg-elevated);
    border-radius: var(--radius-sm);
    font-size: var(--font-xs);
    
    .range-color {
      width: 8px;
      height: 8px;
      border-radius: var(--radius-full);
      flex-shrink: 0;
    }
    
    .range-label {
      color: var(--text-secondary);
      flex: 1;
    }
    
    .range-value {
      color: var(--text-primary);
      font-weight: 600;
      font-family: var(--font-mono);
    }
    
    &.normal .range-color {
      background: var(--success-500);
    }
    
    &.elevated .range-color {
      background: var(--warning-500);
    }
    
    &.stage1 .range-color {
      background: var(--error-500);
    }
    
    &.stage2 .range-color {
      background: #d32f2f;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .pressure-ranges {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>