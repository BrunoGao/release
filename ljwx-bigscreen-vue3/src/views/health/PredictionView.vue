<template>
  <div class="prediction-view">
    <div class="view-header">
      <h2 class="view-title">健康预测分析</h2>
      <div class="header-actions">
        <el-select v-model="predictionType" size="small" placeholder="选择预测类型">
          <el-option label="综合健康趋势" value="overall" />
          <el-option label="疾病风险预测" value="disease" />
          <el-option label="运动表现预测" value="performance" />
          <el-option label="睡眠质量预测" value="sleep" />
        </el-select>
        <el-button size="small" @click="generatePrediction">
          <el-icon><Magic /></el-icon>
          重新预测
        </el-button>
      </div>
    </div>

    <div class="prediction-overview">
      <div class="prediction-card overall-trend">
        <div class="card-header">
          <el-icon><TrendUp /></el-icon>
          <h3>整体趋势预测</h3>
        </div>
        <div class="trend-chart" ref="trendChartRef"></div>
        <div class="trend-summary">
          <div class="summary-item">
            <span class="label">预测趋势:</span>
            <span class="value positive">持续改善</span>
          </div>
          <div class="summary-item">
            <span class="label">置信度:</span>
            <span class="value">{{ overallConfidence }}%</span>
          </div>
        </div>
      </div>

      <div class="prediction-card risk-assessment">
        <div class="card-header">
          <el-icon><Warning /></el-icon>
          <h3>风险评估</h3>
        </div>
        <div class="risk-levels">
          <div class="risk-item" v-for="risk in riskAssessment" :key="risk.type">
            <div class="risk-header">
              <span class="risk-name">{{ risk.name }}</span>
              <el-tag :type="getRiskTagType(risk.level)" size="small">
                {{ getRiskLevelText(risk.level) }}
              </el-tag>
            </div>
            <div class="risk-bar">
              <div 
                class="risk-fill" 
                :style="{ width: risk.probability + '%' }"
                :class="getRiskClass(risk.level)"
              ></div>
            </div>
            <div class="risk-probability">{{ risk.probability }}% 概率</div>
          </div>
        </div>
      </div>
    </div>

    <div class="prediction-details">
      <div class="details-card prediction-model">
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <h4>预测模型分析</h4>
        </div>
        <div class="model-metrics">
          <div class="metric-item">
            <div class="metric-label">模型准确率</div>
            <div class="metric-value">{{ modelAccuracy }}%</div>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: modelAccuracy + '%' }"></div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">数据完整度</div>
            <div class="metric-value">{{ dataCompleteness }}%</div>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: dataCompleteness + '%' }"></div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">预测可靠性</div>
            <div class="metric-value">{{ predictionReliability }}%</div>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: predictionReliability + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="details-card key-factors">
        <div class="card-header">
          <el-icon><Key /></el-icon>
          <h4>关键影响因素</h4>
        </div>
        <div class="factors-list">
          <div class="factor-item" v-for="factor in keyFactors" :key="factor.name">
            <div class="factor-icon">
              <el-icon><component :is="factor.icon" /></el-icon>
            </div>
            <div class="factor-content">
              <div class="factor-name">{{ factor.name }}</div>
              <div class="factor-impact" :class="factor.trend">
                {{ getImpactText(factor.impact) }}
              </div>
            </div>
            <div class="factor-weight">{{ factor.weight }}%</div>
          </div>
        </div>
      </div>
    </div>

    <div class="prediction-recommendations">
      <div class="recommendations-header">
        <h4>预测性建议</h4>
        <el-tag type="info" size="small">基于AI分析</el-tag>
      </div>
      <div class="recommendations-grid">
        <div class="recommendation-item" v-for="rec in predictions" :key="rec.id">
          <div class="rec-timeline">
            <div class="timeline-point" :class="rec.urgency"></div>
            <div class="timeline-period">{{ rec.timeframe }}</div>
          </div>
          <div class="rec-content">
            <div class="rec-title">{{ rec.title }}</div>
            <div class="rec-description">{{ rec.description }}</div>
            <div class="rec-impact">
              <span class="impact-label">预期效果:</span>
              <span class="impact-value">{{ rec.expectedOutcome }}</span>
            </div>
          </div>
          <div class="rec-confidence">
            <div class="confidence-label">准确度</div>
            <div class="confidence-value">{{ rec.confidence }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  TrendUp, 
  Warning, 
  DataAnalysis, 
  Key,
  Magic,
  Monitor,
  Timer,
  Cpu,
  Setting
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

const predictionType = ref('overall')
const trendChartRef = ref<HTMLElement>()

const overallConfidence = ref(87)
const modelAccuracy = ref(92)
const dataCompleteness = ref(95)
const predictionReliability = ref(89)

const riskAssessment = ref([
  {
    type: 'cardiovascular',
    name: '心血管疾病',
    level: 'low',
    probability: 15
  },
  {
    type: 'diabetes',
    name: '糖尿病',
    level: 'medium',
    probability: 35
  },
  {
    type: 'hypertension',
    name: '高血压',
    level: 'low',
    probability: 22
  },
  {
    type: 'obesity',
    name: '肥胖',
    level: 'high',
    probability: 68
  }
])

const keyFactors = ref([
  {
    name: '运动频率',
    icon: Timer,
    impact: 85,
    weight: 28,
    trend: 'positive'
  },
  {
    name: '饮食习惯',
    icon: Monitor,
    impact: 72,
    weight: 25,
    trend: 'neutral'
  },
  {
    name: '睡眠质量',
    icon: Cpu,
    impact: 91,
    weight: 22,
    trend: 'positive'
  },
  {
    name: '压力水平',
    icon: Setting,
    impact: 45,
    weight: 18,
    trend: 'negative'
  }
])

const predictions = ref([
  {
    id: 1,
    timeframe: '1周内',
    urgency: 'immediate',
    title: '增强心血管锻炼',
    description: '建议每天进行30分钟中等强度心血管运动',
    expectedOutcome: '降低心血管疾病风险15%',
    confidence: 92
  },
  {
    id: 2,
    timeframe: '1个月内',
    urgency: 'soon',
    title: '调整饮食结构',
    description: '减少高糖食物摄入，增加蔬菜和蛋白质比例',
    expectedOutcome: '改善代谢指标20%',
    confidence: 88
  },
  {
    id: 3,
    timeframe: '3个月内',
    urgency: 'planned',
    title: '建立睡眠规律',
    description: '保持固定的睡眠时间，提高睡眠质量',
    expectedOutcome: '整体健康评分提升12%',
    confidence: 85
  }
])

const getRiskTagType = (level: string) => {
  const typeMap = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return typeMap[level as keyof typeof typeMap] || 'info'
}

const getRiskLevelText = (level: string) => {
  const textMap = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return textMap[level as keyof typeof textMap] || '未知'
}

const getRiskClass = (level: string) => {
  const classMap = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return classMap[level as keyof typeof classMap] || 'info'
}

const getImpactText = (impact: number) => {
  if (impact >= 80) return '高度影响'
  if (impact >= 60) return '中度影响'
  if (impact >= 40) return '轻度影响'
  return '微弱影响'
}

const updateTrendChart = () => {
  if (!trendChartRef.value) return
  
  const chart = echarts.init(trendChartRef.value, 'health-tech')
  
  // 生成预测数据
  const dates = []
  const actualData = []
  const predictedData = []
  
  // 历史数据 (30天)
  for (let i = 29; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    actualData.push(70 + Math.random() * 20)
    predictedData.push(null)
  }
  
  // 预测数据 (30天)
  for (let i = 1; i <= 30; i++) {
    const date = new Date(Date.now() + i * 24 * 60 * 60 * 1000)
    dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    actualData.push(null)
    predictedData.push(75 + Math.random() * 15 + i * 0.2) // 上升趋势
  }
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['历史数据', '预测趋势'],
      textStyle: {
        color: '#999'
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        color: '#999',
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#999'
      }
    },
    series: [
      {
        name: '历史数据',
        type: 'line',
        data: actualData,
        smooth: true,
        lineStyle: {
          color: '#42a5f5',
          width: 2
        }
      },
      {
        name: '预测趋势',
        type: 'line',
        data: predictedData,
        smooth: true,
        lineStyle: {
          color: '#66bb6a',
          width: 2,
          type: 'dashed'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(102, 187, 106, 0.3)' },
              { offset: 1, color: 'rgba(102, 187, 106, 0.1)' }
            ]
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
  
  const resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)
  
  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    chart.dispose()
  })
}

const generatePrediction = () => {
  // 重新生成预测逻辑
}

onMounted(() => {
  nextTick(() => {
    updateTrendChart()
  })
})
</script>

<style lang="scss" scoped>
.prediction-view {
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  min-height: 100vh;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  
  .view-title {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }
}

.prediction-overview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.prediction-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .card-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    
    .el-icon {
      color: var(--primary-500);
      font-size: 18px;
    }
    
    h3 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  &.overall-trend {
    .trend-chart {
      height: 200px;
      margin-bottom: var(--spacing-lg);
    }
    
    .trend-summary {
      display: flex;
      justify-content: space-between;
      
      .summary-item {
        .label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-right: var(--spacing-xs);
        }
        
        .value {
          font-size: var(--font-sm);
          font-weight: 600;
          
          &.positive {
            color: var(--success-500);
          }
        }
      }
    }
  }
  
  &.risk-assessment {
    .risk-levels {
      .risk-item {
        margin-bottom: var(--spacing-md);
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .risk-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-xs);
          
          .risk-name {
            font-size: var(--font-sm);
            color: var(--text-primary);
          }
        }
        
        .risk-bar {
          width: 100%;
          height: 6px;
          background: var(--bg-secondary);
          border-radius: var(--radius-full);
          overflow: hidden;
          margin-bottom: var(--spacing-xs);
          
          .risk-fill {
            height: 100%;
            border-radius: var(--radius-full);
            transition: width 0.3s ease;
            
            &.success {
              background: var(--success-500);
            }
            
            &.warning {
              background: var(--warning-500);
            }
            
            &.danger {
              background: var(--error-500);
            }
          }
        }
        
        .risk-probability {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.prediction-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.details-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .card-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    
    .el-icon {
      color: var(--primary-500);
      font-size: 16px;
    }
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  &.prediction-model {
    .model-metrics {
      .metric-item {
        margin-bottom: var(--spacing-md);
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .metric-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .metric-value {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .metric-bar {
          width: 100%;
          height: 4px;
          background: var(--bg-secondary);
          border-radius: var(--radius-full);
          overflow: hidden;
          
          .metric-fill {
            height: 100%;
            background: var(--primary-500);
            border-radius: var(--radius-full);
            transition: width 0.3s ease;
          }
        }
      }
    }
  }
  
  &.key-factors {
    .factors-list {
      .factor-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-sm);
        margin-bottom: var(--spacing-sm);
        background: var(--bg-elevated);
        border-radius: var(--radius-md);
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .factor-icon {
          width: 28px;
          height: 28px;
          border-radius: var(--radius-sm);
          background: var(--primary-500);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 14px;
          flex-shrink: 0;
        }
        
        .factor-content {
          flex: 1;
          
          .factor-name {
            font-size: var(--font-sm);
            color: var(--text-primary);
            margin-bottom: 2px;
          }
          
          .factor-impact {
            font-size: var(--font-xs);
            
            &.positive {
              color: var(--success-500);
            }
            
            &.negative {
              color: var(--error-500);
            }
            
            &.neutral {
              color: var(--warning-500);
            }
          }
        }
        
        .factor-weight {
          font-size: var(--font-xs);
          font-weight: 600;
          color: var(--text-primary);
        }
      }
    }
  }
}

.prediction-recommendations {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .recommendations-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .recommendations-grid {
    .recommendation-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      margin-bottom: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .rec-timeline {
        display: flex;
        flex-direction: column;
        align-items: center;
        
        .timeline-point {
          width: 12px;
          height: 12px;
          border-radius: var(--radius-full);
          margin-bottom: var(--spacing-xs);
          
          &.immediate {
            background: var(--error-500);
          }
          
          &.soon {
            background: var(--warning-500);
          }
          
          &.planned {
            background: var(--success-500);
          }
        }
        
        .timeline-period {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          text-align: center;
        }
      }
      
      .rec-content {
        flex: 1;
        
        .rec-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .rec-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
        }
        
        .rec-impact {
          .impact-label {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
          
          .impact-value {
            font-size: var(--font-xs);
            color: var(--primary-500);
            font-weight: 500;
          }
        }
      }
      
      .rec-confidence {
        text-align: center;
        
        .confidence-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .confidence-value {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .prediction-overview,
  .prediction-details {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
}
</style>