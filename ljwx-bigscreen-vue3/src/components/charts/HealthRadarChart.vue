<template>
  <div class="health-radar-chart">
    <div class="chart-header">
      <h4 class="chart-title">{{ title }}</h4>
      <div class="chart-controls">
        <el-select 
          v-model="selectedUser" 
          size="small" 
          style="width: 120px"
          @change="updateChart"
        >
          <el-option label="当前用户" value="current" />
          <el-option label="平均水平" value="average" />
          <el-option label="优秀水平" value="excellent" />
        </el-select>
      </div>
    </div>
    
    <div class="chart-container" ref="chartRef">
      <!-- ECharts 健康雷达图 -->
    </div>
    
    <div class="health-scores">
      <div class="score-grid">
        <div 
          v-for="(score, key) in healthScores" 
          :key="key"
          class="score-item"
          :class="getScoreClass(score)"
        >
          <div class="score-icon">
            <el-icon>
              <component :is="getScoreIcon(key)" />
            </el-icon>
          </div>
          <div class="score-content">
            <div class="score-name">{{ getScoreName(key) }}</div>
            <div class="score-value">{{ score }}</div>
            <div class="score-trend">
              <el-icon>
                <component :is="getTrendIcon(getScoreTrend(score))" />
              </el-icon>
              <span>{{ getTrendText(getScoreTrend(score)) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Heart, 
  TrendCharts, 
  Timer, 
  Sunny,
  Activity,
  Monitor,
  TrendingUp,
  TrendingDown,
  Minus
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface Props {
  title?: string
  height?: string
  userId?: string
  healthData?: Record<string, number>
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康指标雷达图',
  height: '500px',
  userId: '',
  healthData: () => ({})
})

// 响应式数据
const chartRef = ref<HTMLElement>()
const selectedUser = ref('current')

// 健康评分数据
const healthScores = reactive({
  cardiovascular: 85,  // 心血管健康
  respiratory: 90,     // 呼吸系统
  metabolic: 78,       // 代谢健康
  mental: 82,          // 心理健康
  physical: 88,        // 身体素质
  immunity: 86         // 免疫系统
})

// 生成图表数据
const generateRadarData = () => {
  const indicators = [
    { name: '心血管', max: 100 },
    { name: '呼吸系统', max: 100 },
    { name: '代谢健康', max: 100 },
    { name: '心理健康', max: 100 },
    { name: '身体素质', max: 100 },
    { name: '免疫系统', max: 100 }
  ]

  const data = []
  
  switch (selectedUser.value) {
    case 'current':
      data.push({
        value: Object.values(healthScores),
        name: '当前用户',
        itemStyle: {
          color: '#00ff9d'
        },
        areaStyle: {
          color: 'rgba(0, 255, 157, 0.2)'
        }
      })
      break
      
    case 'average':
      data.push({
        value: [75, 78, 72, 76, 74, 77],
        name: '平均水平',
        itemStyle: {
          color: '#42a5f5'
        },
        areaStyle: {
          color: 'rgba(66, 165, 245, 0.2)'
        }
      })
      break
      
    case 'excellent':
      data.push({
        value: [95, 96, 94, 93, 95, 92],
        name: '优秀水平',
        itemStyle: {
          color: '#66bb6a'
        },
        areaStyle: {
          color: 'rgba(102, 187, 106, 0.2)'
        }
      })
      break
  }
  
  return { indicators, data }
}

const updateChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value, 'health-tech')
  const { indicators, data } = generateRadarData()
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const { data, value } = params
        let html = `<div style="margin-bottom: 5px; font-weight: bold;">${data.name}</div>`
        
        indicators.forEach((indicator, index) => {
          html += `
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span>${indicator.name}:</span>
              <span style="font-weight: bold; color: ${data.itemStyle.color};">${value[index]}</span>
            </div>
          `
        })
        
        return html
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      textStyle: {
        color: '#fff'
      }
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      radius: '70%',
      center: ['50%', '45%'],
      startAngle: 90,
      splitNumber: 4,
      name: {
        textStyle: {
          color: '#fff',
          fontSize: 12,
          fontWeight: 'bold'
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.2)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(0, 255, 157, 0.05)',
            'rgba(0, 255, 157, 0.02)'
          ]
        }
      }
    },
    series: [{
      name: '健康指标',
      type: 'radar',
      data: data,
      lineStyle: {
        width: 3
      },
      symbol: 'circle',
      symbolSize: 8
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
const getScoreName = (key: string) => {
  const nameMap = {
    cardiovascular: '心血管',
    respiratory: '呼吸系统',
    metabolic: '代谢健康',
    mental: '心理健康',
    physical: '身体素质',
    immunity: '免疫系统'
  }
  return nameMap[key as keyof typeof nameMap] || key
}

const getScoreIcon = (key: string) => {
  const iconMap = {
    cardiovascular: Heart,
    respiratory: Activity,
    metabolic: TrendCharts,
    mental: Sunny,
    physical: Monitor,
    immunity: Timer
  }
  return iconMap[key as keyof typeof iconMap] || Heart
}

const getScoreClass = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
}

const getScoreTrend = (score: number) => {
  // 模拟趋势，实际应该基于历史数据
  const random = Math.random()
  if (random > 0.6) return 'up'
  if (random < 0.4) return 'down'
  return 'stable'
}

const getTrendIcon = (trend: string) => {
  const iconMap = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus
  }
  return iconMap[trend as keyof typeof iconMap] || Minus
}

const getTrendText = (trend: string) => {
  const textMap = {
    up: '上升',
    down: '下降',
    stable: '稳定'
  }
  return textMap[trend as keyof typeof textMap] || '稳定'
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(() => props.healthData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    Object.assign(healthScores, newData)
    updateChart()
  }
}, { deep: true })
</script>

<style lang="scss" scoped>
.health-radar-chart {
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
}

.chart-container {
  flex: 1;
  min-height: 300px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.health-scores {
  margin-top: var(--spacing-lg);
  
  .score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-md);
    
    .score-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
      }
      
      .score-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
      }
      
      .score-content {
        flex: 1;
        min-width: 0;
        
        .score-name {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: 2px;
        }
        
        .score-value {
          font-size: var(--font-lg);
          font-weight: 700;
          font-family: var(--font-tech);
          margin-bottom: 2px;
        }
        
        .score-trend {
          display: flex;
          align-items: center;
          gap: 2px;
          font-size: var(--font-xs);
          
          .el-icon {
            font-size: 12px;
          }
        }
      }
      
      &.excellent {
        border-color: var(--success-300);
        
        .score-icon {
          background: linear-gradient(135deg, var(--success-500), var(--success-600));
          color: white;
        }
        
        .score-value {
          color: var(--success-500);
        }
        
        .score-trend {
          color: var(--success-500);
        }
      }
      
      &.good {
        border-color: var(--primary-300);
        
        .score-icon {
          background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
          color: white;
        }
        
        .score-value {
          color: var(--primary-500);
        }
        
        .score-trend {
          color: var(--primary-500);
        }
      }
      
      &.fair {
        border-color: var(--warning-300);
        
        .score-icon {
          background: linear-gradient(135deg, var(--warning-500), var(--warning-600));
          color: white;
        }
        
        .score-value {
          color: var(--warning-500);
        }
        
        .score-trend {
          color: var(--warning-500);
        }
      }
      
      &.poor {
        border-color: var(--error-300);
        
        .score-icon {
          background: linear-gradient(135deg, var(--error-500), var(--error-600));
          color: white;
        }
        
        .score-value {
          color: var(--error-500);
        }
        
        .score-trend {
          color: var(--error-500);
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .score-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .score-grid {
    grid-template-columns: 1fr;
  }
}
</style>