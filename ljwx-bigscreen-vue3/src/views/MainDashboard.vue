<template>
  <div class="main-dashboard">
    <!-- 顶部标题栏 -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="company-logo">
          <div class="logo-icon">🏥</div>
          <span class="company-name">{{ COMPANY_NAME }}</span>
        </div>
      </div>
      
      <div class="header-center">
        <h1 class="dashboard-title">智能健康数据分析平台</h1>
      </div>
      
      <div class="header-right">
        <div class="current-time">{{ currentTime }}</div>
        <div class="system-status" :class="systemStatusClass">
          <div class="status-indicator"></div>
          <span>{{ systemStatusText }}</span>
        </div>
      </div>
    </header>
    
    <!-- 主要内容区域 - 三列布局 -->
    <div class="dashboard-container">
      <!-- 左侧面板 -->
      <div class="side-container left-side">
        <!-- 实时统计面板 -->
        <div class="panel stats-panel">
          <div class="panel-header">
            <span>实时统计</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showStatsDetail">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <!-- 统计卡片 -->
            <div class="stats-cards">
              <div class="stat-card health-card">
                <div class="stat-icon">💓</div>
                <div class="stat-info">
                  <div class="stat-value-container">
                    <span class="stat-value" id="healthValue">{{ realTimeStats.healthCount }}</span>
                    <span class="stat-unit">人</span>
                  </div>
                  <div class="stat-trend" id="healthTrend">{{ realTimeStats.healthTrend }}</div>
                </div>
                <div class="stat-label">健康人员</div>
              </div>
              
              <div class="stat-card alert-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-info">
                  <div class="stat-value-container">
                    <span class="stat-value" id="alertValue">{{ realTimeStats.alertCount }}</span>
                    <span class="stat-unit">条</span>
                  </div>
                  <div class="stat-trend" id="alertTrend">{{ realTimeStats.alertTrend }}</div>
                </div>
                <div class="stat-label">预警信息</div>
              </div>
              
              <div class="stat-card device-card">
                <div class="stat-icon">⌚</div>
                <div class="stat-info">
                  <div class="stat-value-container">
                    <span class="stat-value" id="deviceValue">{{ realTimeStats.deviceCount }}</span>
                    <span class="stat-unit">台</span>
                  </div>
                  <div class="stat-trend" id="deviceTrend">{{ realTimeStats.deviceTrend }}</div>
                </div>
                <div class="stat-label">在线设备</div>
              </div>
              
              <div class="stat-card message-card">
                <div class="stat-icon">📨</div>
                <div class="stat-info">
                  <div class="stat-value-container">
                    <span class="stat-value" id="messageValue">{{ realTimeStats.messageCount }}</span>
                    <span class="stat-unit">条</span>
                  </div>
                  <div class="stat-trend" id="messageTrend">{{ realTimeStats.messageTrend }}</div>
                </div>
                <div class="stat-label">系统消息</div>
              </div>
            </div>
            
            <!-- 系统状态指示器 -->
            <div class="system-status-panel" id="systemStatus">
              <div class="status-indicator" :class="systemStatusClass" id="statusIndicator"></div>
              <span class="status-text">{{ systemStatusText }}</span>
            </div>
          </div>
        </div>
        
        <!-- 人员管理面板 -->
        <div class="panel personnel-panel">
          <div class="panel-header">
            <span>人员管理</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showPersonnelDetail">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <!-- 人员统计概览 -->
            <div class="personnel-overview">
              <div class="overview-row">
                <div class="overview-item">
                  <div class="overview-value" id="totalUsers">{{ personnelStats.totalUsers }}</div>
                  <div class="overview-label">总人数</div>
                </div>
                <div class="overview-item">
                  <div class="overview-value" id="totalBindDevices">{{ personnelStats.totalBindDevices }}</div>
                  <div class="overview-label">绑定设备</div>
                </div>
                <div class="overview-item">
                  <div class="overview-value" id="onlineRate">{{ personnelStats.onlineRate }}%</div>
                  <div class="overview-label">在线率</div>
                </div>
              </div>
              
              <div class="overview-row">
                <div class="overview-item mini">
                  <div class="overview-value mini" id="activeOrgCount">{{ personnelStats.activeOrgCount }}</div>
                  <div class="overview-label mini">活跃组织</div>
                </div>
                <div class="overview-item mini">
                  <div class="overview-value mini" id="onlineUsers">{{ personnelStats.onlineUsers }}</div>
                  <div class="overview-label mini">在线用户</div>
                </div>
                <div class="overview-item mini">
                  <div class="overview-value mini" id="boundDevices">{{ personnelStats.boundDevices }}</div>
                  <div class="overview-label mini">绑定数</div>
                </div>
                <div class="overview-item mini">
                  <div class="overview-value mini" id="alertUsers">{{ personnelStats.alertUsers }}</div>
                  <div class="overview-label mini">预警用户</div>
                </div>
              </div>
            </div>
            
            <!-- 部门分布图表 -->
            <div class="charts-container">
              <div class="chart-wrapper" id="departmentDistribution">
                <div class="chart-title">部门分布</div>
              </div>
              <div class="chart-wrapper" id="userStatusChart">
                <div class="chart-title">用户状态</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 告警信息面板 -->
        <div class="panel alert-panel">
          <div class="panel-header">
            <span>告警信息</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showAlertDetail">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <AlertChartsPanel 
              :data="alertChartsData"
              @chart-click="handleAlertChartClick"
              @refresh="refreshAlertData"
            />
          </div>
        </div>
      </div>
      
      <!-- 中间地图区域 -->
      <div class="center-container">
        <!-- 健康预测卡片 -->
        <div class="health-cards-container">
          <div class="health-card prediction-card" id="healthPredictionCard">
            <div class="health-card-header">
              <div class="health-card-title">健康预测</div>
              <div class="health-card-count" id="predictionCount">3</div>
            </div>
            <div class="health-card-content">
              <div class="health-loading" id="predictionLoading" v-if="loadingPrediction">
                <div class="loading-spinner"></div>
                <span>加载预测数据...</span>
              </div>
              <div id="predictionItems" v-else>
                <div v-for="item in healthPredictions" :key="item.id" class="prediction-item">
                  <span class="prediction-risk" :class="item.riskLevel">{{ item.risk }}</span>
                  <span class="prediction-desc">{{ item.description }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="health-card score-card" id="healthScoreCard">
            <div class="health-card-header">
              <div class="health-card-title">健康评分</div>
              <div class="health-score-compact">
                <div class="score-number-compact" id="compactHealthScore">{{ healthScore.score }}</div>
                <div class="score-unit">分</div>
              </div>
              <div class="score-status-compact" id="compactHealthStatus">{{ healthScore.status }}</div>
            </div>
          </div>
          
          <div class="health-card recommendation-card" id="healthRecommendationCard">
            <div class="health-card-header">
              <div class="health-card-title">健康建议</div>
              <div class="health-card-count" id="recommendationCount">{{ healthRecommendations.length }}</div>
            </div>
            <div class="health-card-content">
              <div class="health-loading" id="recommendationLoading" v-if="loadingRecommendations">
                <div class="loading-spinner"></div>
                <span>生成建议中...</span>
              </div>
              <div id="recommendationItems" v-else>
                <div v-for="item in healthRecommendations" :key="item.id" class="recommendation-item">
                  <span class="recommendation-type" :class="item.type">{{ item.category }}</span>
                  <span class="recommendation-text">{{ item.content }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 地图容器 -->
        <div class="map-container" id="map-container">
          <AmapComponent
            container-id="mainMapCanvas"
            :center="mapCenter"
            :zoom="17"
            :pitch="45"
            :view3D="true"
            :show-controls="true"
            :geo-data="mapGeoData"
            @map-ready="handleMapReady"
            @marker-click="handleMarkerClick"
            @map-click="handleMapClick"
            @error="handleMapError"
          />
        </div>
        
        <!-- 消息面板 -->
        <div class="message-panel">
          <div class="message-card-header">
            <div class="message-card-title">系统消息</div>
            <div class="message-card-count" id="messageCount">{{ systemMessages.length }}</div>
          </div>
          <div class="message-card-content" id="messageCardContent">
            <div class="health-loading" id="messageLoading" v-if="loadingMessages">
              <div class="loading-spinner"></div>
              <span>加载消息...</span>
            </div>
            <div id="messageItems" v-else>
              <div v-for="message in systemMessages" :key="message.id" class="message-item">
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                <div class="message-content" :class="message.type">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧面板 -->
      <div class="side-container right-side">
        <!-- 手表管理面板 -->
        <div class="panel device-panel">
          <div class="panel-header">
            <span>手表管理</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showDeviceDetail">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <div id="statsChart" class="chart-container"></div>
          </div>
        </div>
        
        <!-- 健康数据分析面板 -->
        <div class="panel health-analysis-panel">
          <div class="panel-header">
            <span>健康数据分析</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showHealthAnalysisDetail">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <div id="trendChart" class="chart-container"></div>
          </div>
        </div>
        
        <!-- 健康评分面板 -->
        <div class="panel health-score-panel">
          <div class="panel-header">
            <span>综合健康评分</span>
            <div class="panel-controls">
              <button class="detail-btn" @click="showScoreDetails">详情 →</button>
            </div>
          </div>
          <div class="panel-content">
            <HealthScoreRadar
              :data="healthScoreData"
              :auto-refresh="true"
              :show-suggestions="true"
              @dimension-click="handleDimensionClick"
              @suggestion-click="handleSuggestionClick"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 全局提示信息 -->
    <GlobalToast ref="toast" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import AmapComponent from '@/components/maps/AmapComponent.vue'
import AlertChartsPanel from '@/components/alerts/AlertChartsPanel.vue'
import HealthScoreRadar from '@/components/charts/HealthScoreRadar.vue'
import { useSystemStore } from '@/stores/system'
import { useHealthStore } from '@/stores/health'
import { useDeviceStore } from '@/stores/device'
import { useAlertStore } from '@/stores/alert'

// 环境变量
const COMPANY_NAME = ref('LJWX')

// Store实例
const systemStore = useSystemStore()
const healthStore = useHealthStore()
const deviceStore = useDeviceStore()
const alertStore = useAlertStore()

const toast = ref<InstanceType<typeof GlobalToast>>()

// 页面状态
const currentTime = ref('')
const loadingPrediction = ref(false)
const loadingRecommendations = ref(false)
const loadingMessages = ref(false)

// 地图配置
const mapCenter = ref<[number, number]>([116.397428, 39.90923]) // 北京
const mapGeoData = ref([
  {
    id: 'device_001',
    position: [116.397428, 39.90923] as [number, number],
    level: 'healthy' as const,
    title: '设备001 - 正常运行',
    content: '心率正常，步数达标',
    data: { deviceId: '001', status: 'online', batteryLevel: 85 }
  },
  {
    id: 'device_002', 
    position: [116.407428, 39.91923] as [number, number],
    level: 'warning' as const,
    title: '设备002 - 需要关注',
    content: '心率偏高，建议休息',
    data: { deviceId: '002', status: 'warning', batteryLevel: 45 }
  },
  {
    id: 'device_003',
    position: [116.387428, 39.89923] as [number, number],
    level: 'critical' as const,
    title: '设备003 - 紧急状况',
    content: '设备离线，无法联系',
    data: { deviceId: '003', status: 'offline', batteryLevel: 0 }
  }
])

// 告警图表数据
const alertChartsData = ref({
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
})

// 健康评分数据
const healthScoreData = ref({
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
})

// 实时统计数据
const realTimeStats = ref({
  healthCount: 0,
  healthTrend: '+0%',
  alertCount: 0,
  alertTrend: '+0%',
  deviceCount: 0,
  deviceTrend: '+0%',
  messageCount: 0,
  messageTrend: '+0%'
})

// 人员统计数据
const personnelStats = ref({
  totalUsers: 0,
  totalBindDevices: 0,
  onlineRate: 0,
  activeOrgCount: 0,
  onlineUsers: 0,
  boundDevices: 0,
  alertUsers: 0
})

// 健康相关数据
const healthScore = ref({
  score: 0,
  status: '正在计算...'
})

const overallHealthScore = ref({
  score: 0,
  status: '良好状态'
})

const healthPredictions = ref([
  { id: 1, risk: '低风险', riskLevel: 'low', description: '心血管健康良好' },
  { id: 2, risk: '中风险', riskLevel: 'medium', description: '需要注意血压变化' },
  { id: 3, risk: '高风险', riskLevel: 'high', description: '建议立即体检' }
])

const healthRecommendations = ref([
  { id: 1, category: '运动', type: 'exercise', content: '建议每日步行8000步' },
  { id: 2, category: '饮食', type: 'diet', content: '减少高盐食物摄入' },
  { id: 3, category: '睡眠', type: 'sleep', content: '保持规律作息时间' }
])

const systemMessages = ref([
  { id: 1, timestamp: Date.now() - 300000, type: 'info', content: '系统自动备份完成' },
  { id: 2, timestamp: Date.now() - 600000, type: 'warning', content: '检测到3个设备离线' },
  { id: 3, timestamp: Date.now() - 900000, type: 'success', content: '健康数据同步成功' }
])

// 计算属性
const systemStatusClass = computed(() => {
  // 根据系统状态返回相应的CSS类
  return 'normal' // 'normal', 'warning', 'error'
})

const systemStatusText = computed(() => {
  return '系统正常运行'
})

// 方法
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 地图事件处理
const handleMapReady = (map: any) => {
  console.log('地图初始化完成', map)
}

const handleMarkerClick = (data: any) => {
  console.log('标点点击', data)
  toast.value?.info(`查看设备 ${data.id} 详情`)
}

const handleMapClick = (position: [number, number]) => {
  console.log('地图点击', position)
}

const handleMapError = (error: string) => {
  console.error('地图错误', error)
  toast.value?.error('地图加载失败')
}

// 告警图表事件处理
const handleAlertChartClick = (data: any) => {
  console.log('告警图表点击', data)
  toast.value?.info(`查看${data.type}详情`)
}

const refreshAlertData = () => {
  console.log('刷新告警数据')
  // 这里可以调用API刷新数据
}

// 健康评分事件处理
const handleDimensionClick = (dimension: any) => {
  console.log('维度点击', dimension)
  toast.value?.info(`查看${dimension.label}详细数据`)
}

const handleSuggestionClick = (suggestion: any) => {
  console.log('建议点击', suggestion)
  toast.value?.info(`执行建议: ${suggestion.title}`)
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 详情页面跳转
const showStatsDetail = () => {
  console.log('显示统计详情')
}

const showPersonnelDetail = () => {
  console.log('显示人员详情')
}

const showAlertDetail = () => {
  console.log('显示告警详情')
}

const showDeviceDetail = () => {
  console.log('显示设备详情')
}

const showHealthAnalysisDetail = () => {
  console.log('显示健康分析详情')
}

const showScoreDetails = () => {
  console.log('显示健康评分详情')
}

// 数据初始化
const initializeData = async () => {
  try {
    // 初始化实时统计
    realTimeStats.value = {
      healthCount: 1234,
      healthTrend: '+5.2%',
      alertCount: 23,
      alertTrend: '-1.8%',
      deviceCount: 456,
      deviceTrend: '+2.1%',
      messageCount: 12,
      messageTrend: '+0.5%'
    }
    
    // 初始化人员统计
    personnelStats.value = {
      totalUsers: 1256,
      totalBindDevices: 456,
      onlineRate: 87.5,
      activeOrgCount: 15,
      onlineUsers: 1099,
      boundDevices: 456,
      alertUsers: 23
    }
    
    // 初始化健康评分
    healthScore.value = {
      score: 94.5,
      status: '良好状态'
    }
    
    overallHealthScore.value = {
      score: 94.5,
      status: '良好状态'
    }
    
    // 初始化图表
    await initializeCharts()
    
  } catch (error) {
    console.error('数据初始化失败:', error)
    toast.value?.error('数据初始化失败')
  }
}

// 图表初始化 (后续会实现ECharts)
const initializeCharts = async () => {
  // TODO: 实现ECharts图表初始化
  // - 部门分布饼图
  // - 用户状态柱状图  
  // - 告警信息四个图表
  // - 设备统计图表
  // - 健康趋势图表
  // - 健康评分雷达图
  console.log('初始化图表...')
}

// 数据刷新方法
const refreshMapData = () => {
  // 模拟数据更新
  const newData = [...mapGeoData.value]
  newData.forEach(item => {
    // 随机更新设备状态
    if (Math.random() > 0.7) {
      const levels = ['healthy', 'warning', 'critical'] as const
      item.level = levels[Math.floor(Math.random() * levels.length)]
    }
  })
  mapGeoData.value = newData
}

const refreshHealthScore = () => {
  // 模拟健康评分数据更新
  const newData = { ...healthScoreData.value }
  newData.dimensions.forEach(dimension => {
    dimension.value += (Math.random() - 0.5) * 2
    dimension.value = Math.max(0, Math.min(100, dimension.value))
  })
  newData.totalScore = newData.dimensions.reduce((sum, d) => sum + d.value, 0) / newData.dimensions.length
  healthScoreData.value = newData
}

const refreshAllData = () => {
  refreshMapData()
  refreshHealthScore()
  console.log('所有数据已刷新')
  toast.value?.success('数据刷新完成')
}

// 生命周期
onMounted(async () => {
  // 更新时间
  updateTime()
  const timeInterval = setInterval(updateTime, 1000)
  
  // 初始化数据
  await initializeData()
  
  // 启动数据刷新定时器
  const refreshInterval = setInterval(refreshAllData, 30000) // 30秒刷新一次
  
  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
  
  // 清理定时器
  onUnmounted(() => {
    clearInterval(timeInterval)
  })
})
</script>

<style lang="scss" scoped>
.main-dashboard {
  width: 100vw;
  height: 100vh;
  background: #001529;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  overflow: hidden;
  position: relative;
}

// ========== 顶部标题栏 ==========
.dashboard-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: rgba(0, 21, 41, 0.9);
  border-bottom: 2px solid rgba(0, 228, 255, 0.3);
  position: relative;
  z-index: 100;
}

.header-left {
  .company-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo-icon {
      font-size: 32px;
    }
    
    .company-name {
      font-size: 24px;
      font-weight: 700;
      color: #00e4ff;
      text-shadow: 0 0 15px rgba(0, 228, 255, 0.5);
    }
  }
}

.header-center {
  .dashboard-title {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
    margin: 0;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  
  .current-time {
    font-size: 18px;
    font-weight: 600;
    color: #00ff9d;
    font-family: 'Monaco', 'Menlo', monospace;
  }
  
  .system-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 20px;
    background: rgba(0, 255, 157, 0.1);
    
    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #00ff9d;
      animation: pulse 2s ease-in-out infinite;
      
      &.warning {
        background: #ffbb00;
      }
      
      &.error {
        background: #ff4444;
      }
    }
    
    span {
      font-size: 14px;
      color: #00ff9d;
    }
  }
}

// ========== 主要内容区域 - 三列布局 ==========
.dashboard-container {
  display: grid;
  grid-template-columns: 22% 1fr 22%;
  grid-gap: 16px;
  padding: 0 16px 8px 16px;
  height: calc(100vh - 104px);
  max-height: calc(100vh - 104px);
  overflow: hidden;
  align-items: end;
}

// ========== 面板通用样式 ==========
.panel {
  background: rgba(0, 21, 41, 0.7);
  border: 1px solid rgba(0, 228, 255, 0.2);
  border-radius: 4px;
  padding: 10px;
  margin: 0;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(0, 228, 255, 0.6);
    box-shadow: 0 4px 15px rgba(0, 228, 255, 0.2);
  }
}

.panel-header {
  color: #00e4ff;
  font-size: 16px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 998;
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.detail-btn {
  background: transparent;
  border: 1px solid rgba(0, 228, 255, 0.3);
  color: #00e4ff;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(0, 228, 255, 0.1);
    border-color: #00e4ff;
  }
}

// ========== 侧边栏容器 ==========
.side-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  overflow: hidden;
}

// 左侧面板高度分配
.left-side .panel:nth-child(1) {
  height: 35%;
  min-height: 180px;
  max-height: 300px;
}

.left-side .panel:nth-child(2) {
  height: 28%;
  min-height: 200px;
  max-height: 280px;
}

.left-side .panel:nth-child(3) {
  flex: 1;
  min-height: 250px;
  overflow: hidden;
}

// 右侧面板高度分配
.right-side .panel:nth-child(1) {
  height: 26%;
  min-height: 200px;
  max-height: 250px;
}

.right-side .panel:nth-child(2) {
  height: 32%;
  min-height: 200px;
  max-height: 300px;
}

.right-side .panel:nth-child(3) {
  flex: 1;
  min-height: 250px;
  overflow: hidden;
}

// ========== 统计卡片样式 ==========
.stats-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 15px;
}

.stat-card {
  background: rgba(0, 228, 255, 0.1);
  border-radius: 4px;
  padding: 8px;
  position: relative;
  overflow: hidden;
  
  .stat-icon {
    font-size: 20px;
    margin-bottom: 4px;
  }
  
  .stat-value-container {
    display: flex;
    align-items: baseline;
    gap: 2px;
    
    .stat-value {
      font-size: 20px;
      font-weight: 700;
      color: #00e4ff;
    }
    
    .stat-unit {
      font-size: 12px;
      color: #8cc8ff;
    }
  }
  
  .stat-trend {
    font-size: 11px;
    color: #00ff9d;
    margin-top: 2px;
  }
  
  .stat-label {
    font-size: 11px;
    color: #8cc8ff;
    margin-top: 4px;
  }
}

// ========== 人员管理面板样式 ==========
.personnel-overview {
  margin-bottom: 15px;
}

.overview-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.overview-item {
  text-align: center;
  
  .overview-value {
    font-size: 18px;
    font-weight: bold;
    color: #00e4ff;
    
    &.mini {
      font-size: 14px;
    }
  }
  
  .overview-label {
    font-size: 11px;
    color: #8cc8ff;
    margin-top: 2px;
    
    &.mini {
      font-size: 10px;
    }
  }
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  flex: 1;
}

.chart-wrapper {
  background: rgba(0, 21, 41, 0.4);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 6px;
  position: relative;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(0, 228, 255, 0.6);
    box-shadow: 0 4px 15px rgba(0, 228, 255, 0.2);
  }
  
  .chart-title {
    position: absolute;
    top: 8px;
    left: 8px;
    font-size: 12px;
    color: #8cc8ff;
    z-index: 10;
  }
}

// ========== 中间区域样式 ==========
.center-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  height: 100%;
}

.health-cards-container {
  display: flex;
  gap: 10px;
  height: auto;
  min-height: 80px;
}

.health-card {
  flex: 1;
  background: rgba(0, 21, 41, 0.7);
  border: 1px solid rgba(0, 228, 255, 0.2);
  border-radius: 4px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  
  .health-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    
    .health-card-title {
      font-size: 12px;
      color: #00e4ff;
    }
    
    .health-card-count {
      font-size: 14px;
      font-weight: 700;
      color: #00ff9d;
    }
  }
  
  .health-score-compact {
    display: flex;
    align-items: baseline;
    gap: 2px;
    
    .score-number-compact {
      font-size: 16px;
      font-weight: 700;
      color: #00e4ff;
    }
    
    .score-unit {
      font-size: 10px;
      color: #8cc8ff;
    }
  }
  
  .score-status-compact {
    font-size: 10px;
    color: #00ff9d;
  }
}

// ========== 地图容器 ==========
.map-container {
  flex: 1;
  background: rgba(0, 21, 41, 0.7);
  border: 1px solid rgba(0, 228, 255, 0.2);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 15px;
  min-height: 350px;
  max-height: 450px;
  position: relative;
}

.filter-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  
  .filter-toggle {
    width: 32px;
    height: 32px;
    background: rgba(0, 21, 41, 0.9);
    border: 1px solid rgba(0, 228, 255, 0.3);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: #00e4ff;
      background: rgba(0, 228, 255, 0.1);
    }
  }
  
  .filter-content {
    position: absolute;
    top: 40px;
    right: 0;
    background: rgba(0, 21, 41, 0.95);
    border: 1px solid rgba(0, 228, 255, 0.3);
    border-radius: 4px;
    padding: 10px;
    min-width: 160px;
    
    .filter-select {
      width: 100%;
      padding: 4px 8px;
      border: 1px solid rgba(0, 228, 255, 0.3);
      border-radius: 3px;
      background: rgba(0, 21, 41, 0.9);
      color: #fff;
      font-size: 12px;
      margin-bottom: 6px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      &:focus {
        outline: none;
        border-color: #00e4ff;
      }
    }
  }
}

.map-canvas {
  width: 100%;
  height: calc(100% - 20px);
  border-radius: 4px;
  overflow: hidden;
}

// ========== 消息面板 ==========
.message-panel {
  background: rgba(0, 21, 41, 0.7);
  border: 1px solid rgba(0, 228, 255, 0.2);
  border-radius: 4px;
  padding: 8px;
  height: auto;
  min-height: 100px;
  
  .message-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    
    .message-card-title {
      font-size: 12px;
      color: #00e4ff;
    }
    
    .message-card-count {
      font-size: 14px;
      font-weight: 700;
      color: #00ff9d;
    }
  }
  
  .message-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    border-bottom: 1px solid rgba(0, 228, 255, 0.1);
    font-size: 11px;
    
    &:last-child {
      border-bottom: none;
    }
    
    .message-time {
      color: #8cc8ff;
    }
    
    .message-content {
      color: #fff;
      
      &.warning {
        color: #ffbb00;
      }
      
      &.error {
        color: #ff4444;
      }
      
      &.success {
        color: #00ff9d;
      }
    }
  }
}

// ========== 图表容器 ==========
.chart-container {
  position: relative;
  flex: 1;
  width: 100%;
  height: calc(100% - 40px);
  min-height: 120px;
}

// ========== 健康评分面板 ==========
.score-display {
  margin-bottom: 15px;
  text-align: center;
  
  .score-info {
    .score-title {
      font-size: 12px;
      color: #8cc8ff;
      margin-bottom: 8px;
    }
    
    .score-number {
      font-size: 36px;
      font-weight: 700;
      color: #00e4ff;
      margin-bottom: 4px;
    }
    
    .score-status {
      font-size: 14px;
      color: #00ff9d;
    }
  }
}

// ========== 加载状态 ==========
.health-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  font-size: 11px;
  color: #8cc8ff;
  
  .loading-spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(0, 228, 255, 0.3);
    border-top: 2px solid #00e4ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

// ========== 动画 ==========
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1920px) {
  .dashboard-container {
    grid-template-columns: 20% 1fr 20%;
  }
}

@media (max-width: 1440px) {
  .dashboard-container {
    grid-template-columns: 25% 1fr 25%;
  }
}

@media (max-width: 1024px) {
  .dashboard-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
  
  .side-container {
    flex-direction: row;
    height: auto;
  }
  
  .center-container {
    order: 2;
  }
}

// ========== 滚动条美化 ==========
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 228, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 228, 255, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 228, 255, 0.5);
}
</style>