<template>
  <div class="activity-dashboard">
    <div class="dashboard-header">
      <h4 class="dashboard-title">活动仪表板</h4>
      <div class="dashboard-controls">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          size="small"
          @change="updateData"
        />
        <el-button size="small" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 今日活动概览 -->
    <div class="activity-overview">
      <div class="overview-card main-metrics">
        <div class="card-header">
          <h5>今日主要指标</h5>
          <div class="completion-rate" :class="`rate-${getCompletionLevel(dailyCompletion)}`">
            {{ dailyCompletion }}% 完成度
          </div>
        </div>
        
        <div class="metrics-grid">
          <div 
            v-for="metric in mainMetrics" 
            :key="metric.key"
            class="metric-item"
          >
            <div class="metric-icon" :style="{ color: metric.color }">
              <el-icon><component :is="metric.icon" /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">
                <span class="value-number">{{ metric.current }}</span>
                <span class="value-unit">{{ metric.unit }}</span>
              </div>
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-progress">
                <el-progress 
                  :percentage="metric.progress" 
                  :color="metric.color"
                  :show-text="false"
                  :stroke-width="4"
                />
              </div>
              <div class="metric-target">目标: {{ metric.target }}{{ metric.unit }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-card activity-ring">
        <div class="card-header">
          <h5>活动环</h5>
          <div class="ring-date">{{ formatDate(selectedDate) }}</div>
        </div>
        
        <div class="ring-container">
          <div class="activity-rings">
            <svg class="rings-svg" viewBox="0 0 200 200">
              <!-- 移动环 -->
              <circle
                cx="100"
                cy="100"
                r="85"
                fill="none"
                stroke="rgba(255, 107, 107, 0.2)"
                stroke-width="8"
              />
              <circle
                cx="100"
                cy="100"
                r="85"
                fill="none"
                stroke="#ff6b6b"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="`${activityRings.move.progress * 534.07 / 100} 534.07`"
                transform="rotate(-90 100 100)"
                class="ring-progress"
              />
              
              <!-- 锻炼环 -->
              <circle
                cx="100"
                cy="100"
                r="70"
                fill="none"
                stroke="rgba(0, 255, 157, 0.2)"
                stroke-width="8"
              />
              <circle
                cx="100"
                cy="100"
                r="70"
                fill="none"
                stroke="#00ff9d"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="`${activityRings.exercise.progress * 439.82 / 100} 439.82`"
                transform="rotate(-90 100 100)"
                class="ring-progress"
              />
              
              <!-- 站立环 -->
              <circle
                cx="100"
                cy="100"
                r="55"
                fill="none"
                stroke="rgba(64, 158, 255, 0.2)"
                stroke-width="8"
              />
              <circle
                cx="100"
                cy="100"
                r="55"
                fill="none"
                stroke="#409eff"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="`${activityRings.stand.progress * 345.58 / 100} 345.58`"
                transform="rotate(-90 100 100)"
                class="ring-progress"
              />
            </svg>
            
            <div class="rings-center">
              <div class="center-time">{{ currentTime }}</div>
              <div class="center-date">{{ formatShortDate(selectedDate) }}</div>
            </div>
          </div>
          
          <div class="rings-legend">
            <div 
              v-for="ring in activityRings" 
              :key="ring.type"
              class="legend-item"
            >
              <div class="legend-color" :style="{ background: ring.color }"></div>
              <div class="legend-info">
                <div class="legend-label">{{ ring.label }}</div>
                <div class="legend-value">{{ ring.current }}/{{ ring.target }}{{ ring.unit }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 活动趋势分析 -->
    <div class="activity-trends">
      <div class="trends-header">
        <h5>活动趋势</h5>
        <el-radio-group v-model="trendsTimeRange" size="small">
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="year">本年</el-radio-button>
        </el-radio-group>
      </div>
      <div class="trends-chart" ref="trendsChartRef"></div>
    </div>

    <!-- 活动热力图 -->
    <div class="activity-heatmap">
      <div class="heatmap-header">
        <h5>活动热力图</h5>
        <div class="heatmap-legend">
          <span class="legend-label">活动强度:</span>
          <div class="legend-scale">
            <div class="scale-item" v-for="(level, index) in heatmapLevels" :key="index">
              <div class="scale-color" :style="{ background: level.color }"></div>
              <span class="scale-label">{{ level.label }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="heatmap-content">
        <div class="heatmap-grid">
          <div class="grid-header">
            <div class="time-labels">
              <div v-for="hour in 24" :key="hour" class="time-label">
                {{ (hour - 1).toString().padStart(2, '0') }}
              </div>
            </div>
          </div>
          <div class="grid-body">
            <div v-for="(day, dayIndex) in heatmapData" :key="dayIndex" class="grid-row">
              <div class="day-label">{{ day.name }}</div>
              <div class="hour-cells">
                <div 
                  v-for="(cell, hourIndex) in day.hours" 
                  :key="hourIndex"
                  class="hour-cell"
                  :style="{ background: getHeatmapColor(cell.intensity) }"
                  :title="`${day.name} ${hourIndex}:00 - 活动强度: ${cell.intensity}`"
                  @click="showHourDetail(dayIndex, hourIndex, cell)"
                >
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 活动建议 -->
    <div class="activity-suggestions">
      <h5>智能建议</h5>
      <div class="suggestions-grid">
        <div 
          v-for="suggestion in activitySuggestions" 
          :key="suggestion.id"
          class="suggestion-card"
          :class="`suggestion-${suggestion.priority}`"
        >
          <div class="suggestion-icon">
            <el-icon><component :is="suggestion.icon" /></el-icon>
          </div>
          <div class="suggestion-content">
            <div class="suggestion-title">{{ suggestion.title }}</div>
            <div class="suggestion-desc">{{ suggestion.description }}</div>
            <div class="suggestion-benefit">{{ suggestion.benefit }}</div>
          </div>
          <div class="suggestion-actions">
            <el-button size="small" type="primary" @click="applySuggestion(suggestion.id)">
              采纳
            </el-button>
            <el-button size="small" text @click="dismissSuggestion(suggestion.id)">
              忽略
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 活动记录 -->
    <div class="activity-records">
      <div class="records-header">
        <h5>今日活动记录</h5>
        <el-button size="small" @click="showAddModal = true">
          <el-icon><Plus /></el-icon>
          添加活动
        </el-button>
      </div>
      
      <div class="records-timeline">
        <div 
          v-for="record in todayRecords" 
          :key="record.id"
          class="record-item"
        >
          <div class="record-time">{{ formatTime(record.startTime) }}</div>
          <div class="record-content">
            <div class="record-type" :style="{ color: record.color }">
              <el-icon><component :is="record.icon" /></el-icon>
              <span>{{ record.type }}</span>
            </div>
            <div class="record-details">
              <div class="record-duration">时长: {{ record.duration }}分钟</div>
              <div class="record-calories">消耗: {{ record.calories }}千卡</div>
              <div class="record-description">{{ record.description }}</div>
            </div>
          </div>
          <div class="record-actions">
            <el-button size="small" text @click="editRecord(record)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" text @click="deleteRecord(record.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加活动模态框 -->
    <el-dialog 
      v-model="showAddModal" 
      title="添加活动记录"
      width="500px"
    >
      <el-form :model="activityForm" label-width="80px">
        <el-form-item label="活动类型">
          <el-select v-model="activityForm.type" placeholder="选择活动类型">
            <el-option label="跑步" value="running" />
            <el-option label="走路" value="walking" />
            <el-option label="骑行" value="cycling" />
            <el-option label="游泳" value="swimming" />
            <el-option label="健身" value="fitness" />
            <el-option label="瑜伽" value="yoga" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-picker 
            v-model="activityForm.startTime" 
            format="HH:mm"
            placeholder="选择开始时间"
          />
        </el-form-item>
        <el-form-item label="持续时间">
          <el-input-number 
            v-model="activityForm.duration" 
            :min="1" 
            :max="600"
          />
          <span style="margin-left: 8px;">分钟</span>
        </el-form-item>
        <el-form-item label="消耗卡路里">
          <el-input-number 
            v-model="activityForm.calories" 
            :min="0" 
            :max="2000"
          />
          <span style="margin-left: 8px;">千卡</span>
        </el-form-item>
        <el-form-item label="活动描述">
          <el-input 
            v-model="activityForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="描述你的活动详情"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddModal = false">取消</el-button>
        <el-button type="primary" @click="saveActivity">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { 
  Refresh, Plus, Edit, Delete,
  Walking, Timer, TrendingUp, InfoFilled, Warning, CircleCheck
} from '@element-plus/icons-vue'
import { echarts } from '@/plugins/echarts'

interface MainMetric {
  key: string
  label: string
  current: number
  target: number
  unit: string
  progress: number
  color: string
  icon: any
}

interface ActivityRing {
  type: string
  label: string
  current: number
  target: number
  unit: string
  progress: number
  color: string
}

interface ActivityRecord {
  id: string
  type: string
  startTime: number
  duration: number
  calories: number
  description: string
  color: string
  icon: any
}

interface ActivitySuggestion {
  id: string
  title: string
  description: string
  benefit: string
  priority: 'high' | 'medium' | 'low'
  icon: any
}

interface HeatmapCell {
  intensity: number
  activities: string[]
}

interface HeatmapDay {
  name: string
  hours: HeatmapCell[]
}

// 响应式数据
const selectedDate = ref(new Date())
const trendsTimeRange = ref('week')
const showAddModal = ref(false)
const trendsChartRef = ref<HTMLElement>()
const currentTime = ref('')

// 今日完成度
const dailyCompletion = ref(78)

// 主要指标
const mainMetrics = ref<MainMetric[]>([
  {
    key: 'steps',
    label: '步数',
    current: 8756,
    target: 10000,
    unit: '步',
    progress: 87.6,
    color: '#67c23a',
    icon: Walking
  },
  {
    key: 'calories',
    label: '卡路里',
    current: 245,
    target: 300,
    unit: '千卡',
    progress: 81.7,
    color: '#ff6b6b',
    icon: TrendingUp
  },
  {
    key: 'exercise_time',
    label: '锻炼时长',
    current: 35,
    target: 60,
    unit: '分钟',
    progress: 58.3,
    color: '#409eff',
    icon: Timer
  }
])

// 活动环数据
const activityRings = ref<Record<string, ActivityRing>>({
  move: {
    type: 'move',
    label: '移动',
    current: 245,
    target: 300,
    unit: '千卡',
    progress: 81.7,
    color: '#ff6b6b'
  },
  exercise: {
    type: 'exercise',
    label: '锻炼',
    current: 35,
    target: 60,
    unit: '分钟',
    progress: 58.3,
    color: '#00ff9d'
  },
  stand: {
    type: 'stand',
    label: '站立',
    current: 9,
    target: 12,
    unit: '小时',
    progress: 75,
    color: '#409eff'
  }
})

// 热力图数据
const heatmapLevels = [
  { label: '无', color: '#f5f5f5' },
  { label: '低', color: '#c6e48b' },
  { label: '中', color: '#7bc96f' },
  { label: '高', color: '#239a3b' },
  { label: '极高', color: '#196127' }
]

const heatmapData = ref<HeatmapDay[]>([
  {
    name: '周一',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周二',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周三',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周四',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周五',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周六',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  },
  {
    name: '周日',
    hours: Array.from({ length: 24 }, (_, i) => ({
      intensity: Math.floor(Math.random() * 5),
      activities: []
    }))
  }
])

// 活动建议
const activitySuggestions = ref<ActivitySuggestion[]>([
  {
    id: '1',
    title: '增加步行',
    description: '距离目标还差1244步，建议在下午增加10分钟步行',
    benefit: '完成今日步数目标',
    priority: 'high',
    icon: Walking
  },
  {
    id: '2',
    title: '站立提醒',
    description: '已坐立超过2小时，建议起身活动5分钟',
    benefit: '改善血液循环，缓解疲劳',
    priority: 'medium',
    icon: TrendingUp
  },
  {
    id: '3',
    title: '补充锻炼',
    description: '今日锻炼时间较少，建议进行25分钟中等强度运动',
    benefit: '达成锻炼目标，提升心肺功能',
    priority: 'high',
    icon: Timer
  }
])

// 今日活动记录
const todayRecords = ref<ActivityRecord[]>([
  {
    id: '1',
    type: '晨跑',
    startTime: Date.now() - 18000000, // 5小时前
    duration: 30,
    calories: 180,
    description: '在公园进行30分钟慢跑，感觉良好',
    color: '#67c23a',
    icon: Walking
  },
  {
    id: '2',
    type: '步行',
    startTime: Date.now() - 7200000, // 2小时前
    duration: 15,
    calories: 45,
    description: '午餐后散步',
    color: '#409eff',
    icon: Walking
  }
])

// 活动表单
const activityForm = ref({
  type: '',
  startTime: null,
  duration: 30,
  calories: 0,
  description: ''
})

// 工具方法
const getCompletionLevel = (completion: number) => {
  if (completion >= 90) return 'excellent'
  if (completion >= 70) return 'good'
  if (completion >= 50) return 'fair'
  return 'poor'
}

const formatDate = (date: Date) => {
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

const formatShortDate = (date: Date) => {
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const getHeatmapColor = (intensity: number) => {
  return heatmapLevels[intensity]?.color || heatmapLevels[0].color
}

// 生成趋势数据
const generateTrendsData = () => {
  const data = {
    dates: [] as string[],
    steps: [] as number[],
    calories: [] as number[],
    exerciseTime: [] as number[]
  }
  
  const days = trendsTimeRange.value === 'week' ? 7 : 
               trendsTimeRange.value === 'month' ? 30 : 365
  const now = new Date()
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 86400000)
    
    if (trendsTimeRange.value === 'year') {
      data.dates.push(`${date.getMonth() + 1}月`)
    } else {
      data.dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
    }
    
    // 生成模拟数据
    data.steps.push(Math.round(Math.random() * 5000 + 5000)) // 5000-10000
    data.calories.push(Math.round(Math.random() * 200 + 150)) // 150-350
    data.exerciseTime.push(Math.round(Math.random() * 60 + 20)) // 20-80
  }
  
  return data
}

// 更新趋势图表
const updateTrendsChart = () => {
  if (!trendsChartRef.value) return
  
  const chart = echarts.init(trendsChartRef.value, 'health-tech')
  const data = generateTrendsData()
  
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
      }
    },
    legend: {
      data: ['步数', '卡路里', '锻炼时长'],
      textStyle: {
        color: '#999'
      }
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: {
        color: '#999'
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '步数',
        position: 'left',
        axisLabel: {
          color: '#999',
          formatter: '{value}'
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      {
        type: 'value',
        name: '卡路里/分钟',
        position: 'right',
        axisLabel: {
          color: '#999',
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '步数',
        type: 'line',
        data: data.steps,
        lineStyle: { color: '#67c23a' },
        itemStyle: { color: '#67c23a' },
        smooth: true
      },
      {
        name: '卡路里',
        type: 'line',
        yAxisIndex: 1,
        data: data.calories,
        lineStyle: { color: '#ff6b6b' },
        itemStyle: { color: '#ff6b6b' },
        smooth: true
      },
      {
        name: '锻炼时长',
        type: 'bar',
        yAxisIndex: 1,
        data: data.exerciseTime,
        itemStyle: { color: '#409eff' },
        barWidth: '30%'
      }
    ]
  }
  
  chart.setOption(option)
}

// 更新当前时间
const updateCurrentTime = () => {
  const now = new Date()
  currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

// 事件处理
const updateData = () => {
  // 根据选择的日期更新数据
}

const refreshData = () => {
  // 刷新数据
  mainMetrics.value.forEach(metric => {
    const variation = Math.random() * 0.1 + 0.95
    metric.current = Math.round(metric.current * variation)
    metric.progress = Math.min(100, (metric.current / metric.target) * 100)
  })
  
  updateTrendsChart()
}

const showHourDetail = (dayIndex: number, hourIndex: number, cell: HeatmapCell) => {
  // 显示小时详情
  console.log('Hour detail:', dayIndex, hourIndex, cell)
}

const applySuggestion = (id: string) => {
  const index = activitySuggestions.value.findIndex(s => s.id === id)
  if (index > -1) {
    activitySuggestions.value.splice(index, 1)
  }
}

const dismissSuggestion = (id: string) => {
  const index = activitySuggestions.value.findIndex(s => s.id === id)
  if (index > -1) {
    activitySuggestions.value.splice(index, 1)
  }
}

const saveActivity = () => {
  const activity: ActivityRecord = {
    id: Date.now().toString(),
    type: activityForm.value.type,
    startTime: Date.now(), // 简化处理
    duration: activityForm.value.duration,
    calories: activityForm.value.calories,
    description: activityForm.value.description,
    color: '#67c23a',
    icon: Walking
  }
  
  todayRecords.value.unshift(activity)
  
  // 重置表单
  activityForm.value = {
    type: '',
    startTime: null,
    duration: 30,
    calories: 0,
    description: ''
  }
  
  showAddModal.value = false
}

const editRecord = (record: ActivityRecord) => {
  // 编辑记录
  console.log('Edit record:', record)
}

const deleteRecord = (id: string) => {
  const index = todayRecords.value.findIndex(r => r.id === id)
  if (index > -1) {
    todayRecords.value.splice(index, 1)
  }
}

// 监听时间范围变化
watch(trendsTimeRange, () => {
  updateTrendsChart()
})

// 生命周期
onMounted(() => {
  updateCurrentTime()
  setInterval(updateCurrentTime, 60000) // 每分钟更新一次
  
  nextTick(() => {
    updateTrendsChart()
  })
})
</script>

<style lang="scss" scoped>
.activity-dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow-y: auto;
  gap: var(--spacing-lg);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .dashboard-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .dashboard-controls {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.activity-overview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-lg);
  
  .overview-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    border: 1px solid var(--border-light);
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
      
      h5 {
        font-size: var(--font-base);
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
      }
      
      .completion-rate {
        font-size: var(--font-sm);
        font-weight: 600;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        
        &.rate-excellent {
          background: rgba(103, 194, 58, 0.2);
          color: var(--success);
        }
        
        &.rate-good {
          background: rgba(64, 158, 255, 0.2);
          color: var(--info);
        }
        
        &.rate-fair {
          background: rgba(255, 167, 38, 0.2);
          color: var(--warning);
        }
        
        &.rate-poor {
          background: rgba(255, 107, 107, 0.2);
          color: var(--error);
        }
      }
      
      .ring-date {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
  }
  
  .main-metrics {
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--spacing-lg);
      
      .metric-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        
        .metric-icon {
          width: 48px;
          height: 48px;
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.1);
          font-size: var(--font-xl);
        }
        
        .metric-content {
          flex: 1;
          
          .metric-value {
            font-size: var(--font-xl);
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--spacing-xs);
            
            .value-unit {
              font-size: var(--font-sm);
              color: var(--text-secondary);
              margin-left: var(--spacing-xs);
            }
          }
          
          .metric-label {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            margin-bottom: var(--spacing-sm);
          }
          
          .metric-progress {
            margin-bottom: var(--spacing-xs);
          }
          
          .metric-target {
            font-size: var(--font-xs);
            color: var(--text-tertiary);
          }
        }
      }
    }
  }
  
  .activity-ring {
    .ring-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-lg);
      
      .activity-rings {
        position: relative;
        width: 200px;
        height: 200px;
        
        .rings-svg {
          width: 100%;
          height: 100%;
          
          .ring-progress {
            transition: stroke-dasharray 0.5s ease;
          }
        }
        
        .rings-center {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          
          .center-time {
            font-size: var(--font-xl);
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--spacing-xs);
          }
          
          .center-date {
            font-size: var(--font-sm);
            color: var(--text-secondary);
          }
        }
      }
      
      .rings-legend {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        width: 100%;
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          
          .legend-color {
            width: 12px;
            height: 12px;
            border-radius: var(--radius-full);
          }
          
          .legend-info {
            flex: 1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            
            .legend-label {
              font-size: var(--font-sm);
              color: var(--text-secondary);
            }
            
            .legend-value {
              font-size: var(--font-sm);
              font-weight: 600;
              color: var(--text-primary);
            }
          }
        }
      }
    }
  }
}

.activity-trends {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-light);
  
  .trends-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .trends-chart {
    height: 300px;
  }
}

.activity-heatmap {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-light);
  
  .heatmap-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .heatmap-legend {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      
      .legend-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
      
      .legend-scale {
        display: flex;
        gap: var(--spacing-sm);
        
        .scale-item {
          display: flex;
          align-items: center;
          gap: 4px;
          
          .scale-color {
            width: 12px;
            height: 12px;
            border-radius: var(--radius-xs);
          }
          
          .scale-label {
            font-size: var(--font-xs);
            color: var(--text-tertiary);
          }
        }
      }
    }
  }
  
  .heatmap-content {
    .heatmap-grid {
      .grid-header {
        .time-labels {
          display: grid;
          grid-template-columns: 60px repeat(24, 1fr);
          gap: 2px;
          margin-bottom: 4px;
          
          .time-label {
            font-size: var(--font-xs);
            color: var(--text-tertiary);
            text-align: center;
            
            &:nth-child(odd) {
              display: none;
            }
          }
        }
      }
      
      .grid-body {
        display: flex;
        flex-direction: column;
        gap: 2px;
        
        .grid-row {
          display: grid;
          grid-template-columns: 60px 1fr;
          gap: var(--spacing-sm);
          align-items: center;
          
          .day-label {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            text-align: right;
          }
          
          .hour-cells {
            display: grid;
            grid-template-columns: repeat(24, 1fr);
            gap: 2px;
            
            .hour-cell {
              width: 20px;
              height: 20px;
              border-radius: var(--radius-xs);
              cursor: pointer;
              transition: all var(--duration-fast);
              
              &:hover {
                transform: scale(1.1);
                border: 1px solid var(--primary-500);
              }
            }
          }
        }
      }
    }
  }
}

.activity-suggestions {
  h5 {
    font-size: var(--font-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg);
  }
  
  .suggestions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-md);
    
    .suggestion-card {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      border-left: 4px solid;
      
      &.suggestion-high {
        border-left-color: var(--error);
      }
      
      &.suggestion-medium {
        border-left-color: var(--warning);
      }
      
      &.suggestion-low {
        border-left-color: var(--info);
      }
      
      .suggestion-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(103, 194, 58, 0.1);
        color: var(--success);
        font-size: var(--font-lg);
        flex-shrink: 0;
      }
      
      .suggestion-content {
        flex: 1;
        
        .suggestion-title {
          font-size: var(--font-base);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .suggestion-desc {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .suggestion-benefit {
          font-size: var(--font-sm);
          color: var(--success);
          font-style: italic;
        }
      }
      
      .suggestion-actions {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        flex-shrink: 0;
      }
    }
  }
}

.activity-records {
  .records-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    
    h5 {
      font-size: var(--font-base);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .records-timeline {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .record-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .record-time {
        font-size: var(--font-sm);
        color: var(--text-tertiary);
        min-width: 60px;
      }
      
      .record-content {
        flex: 1;
        
        .record-type {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          font-size: var(--font-sm);
          font-weight: 600;
          margin-bottom: var(--spacing-xs);
        }
        
        .record-details {
          display: flex;
          gap: var(--spacing-md);
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .record-description {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
      
      .record-actions {
        display: flex;
        gap: var(--spacing-xs);
        flex-shrink: 0;
      }
    }
  }
}

@media (max-width: 1024px) {
  .activity-overview {
    grid-template-columns: 1fr;
    
    .main-metrics .metrics-grid {
      grid-template-columns: 1fr;
    }
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .trends-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .heatmap-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .suggestions-grid {
    grid-template-columns: 1fr;
  }
}
</style>