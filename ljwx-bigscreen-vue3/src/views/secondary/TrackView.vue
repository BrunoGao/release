<template>
  <div class="track-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.7"
      :particle-count="80"
      :enable-grid="true"
      :enable-pulse="false"
      :enable-data-flow="true"
    />
    
    <!-- 页面头部 -->
    <div class="view-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ArrowLeftIcon />
          <span>返回个人大屏</span>
        </button>
        <div class="page-title">
          <h1>轨迹追踪中心</h1>
          <p class="page-subtitle">实时位置监控与轨迹分析系统</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="track-stats">
          <div class="stat-item">
            <span class="stat-label">在线用户</span>
            <span class="stat-value online">{{ onlineUsers }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">今日轨迹</span>
            <span class="stat-value">{{ todayTracks }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">覆盖区域</span>
            <span class="stat-value">{{ coverageAreas }}</span>
          </div>
        </div>
        <button class="action-btn" @click="exportTrackData">
          <DocumentArrowDownIcon />
          导出数据
        </button>
      </div>
    </div>
    
    <!-- 轨迹追踪主体 -->
    <div class="track-content">
      <!-- 地图和控制面板 -->
      <div class="map-section">
        <div class="map-container">
          <!-- 地图控制面板 -->
          <div class="map-controls">
            <div class="control-group">
              <label>时间范围:</label>
              <select v-model="selectedTimeRange" @change="updateTrackData">
                <option value="today">今天</option>
                <option value="yesterday">昨天</option>
                <option value="week">本周</option>
                <option value="month">本月</option>
              </select>
            </div>
            <div class="control-group">
              <label>用户筛选:</label>
              <select v-model="selectedUser" @change="filterUserTracks">
                <option value="all">全部用户</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ user.name }}
                </option>
              </select>
            </div>
            <div class="control-group">
              <button class="control-btn" @click="toggleRealtime" :class="{ active: isRealtime }">
                <component :is="isRealtime ? PauseIcon : PlayIcon" />
                {{ isRealtime ? '暂停实时' : '开启实时' }}
              </button>
              <button class="control-btn" @click="refreshTracks">
                <RefreshIcon :class="{ spinning: isRefreshing }" />
                刷新
              </button>
            </div>
          </div>
          
          <!-- 地图区域 -->
          <div class="map-area">
            <TrackMapComponent 
              :tracks="filteredTracks"
              :center="mapCenter"
              :zoom="mapZoom"
              :realtime="isRealtime"
              @marker-click="selectTrackPoint"
            />
          </div>
          
          <!-- 地图图例 -->
          <div class="map-legend">
            <div class="legend-item">
              <div class="legend-color online"></div>
              <span>在线用户</span>
            </div>
            <div class="legend-item">
              <div class="legend-color offline"></div>
              <span>离线用户</span>
            </div>
            <div class="legend-item">
              <div class="legend-color track-line"></div>
              <span>行走轨迹</span>
            </div>
            <div class="legend-item">
              <div class="legend-color danger-zone"></div>
              <span>危险区域</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 轨迹分析面板 -->
      <div class="analysis-section">
        <div class="section-header">
          <h3>轨迹分析</h3>
          <div class="analysis-tabs">
            <button 
              v-for="tab in analysisTabs"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              <component :is="tab.icon" class="tab-icon" />
              {{ tab.label }}
            </button>
          </div>
        </div>
        
        <div class="analysis-content">
          <!-- 用户列表 -->
          <div v-if="activeTab === 'users'" class="tab-content">
            <div class="user-list">
              <div class="list-header">
                <div class="search-box">
                  <MagnifyingGlassIcon class="search-icon" />
                  <input 
                    v-model="searchQuery" 
                    type="text" 
                    placeholder="搜索用户..."
                    class="search-input"
                  />
                </div>
              </div>
              <div class="user-items">
                <div 
                  v-for="user in filteredUsers"
                  :key="user.id"
                  class="user-item"
                  :class="{ active: user.id === selectedUser, online: user.online }"
                  @click="selectUser(user)"
                >
                  <div class="user-avatar">
                    <UserIcon />
                    <div class="status-dot" :class="{ online: user.online }"></div>
                  </div>
                  <div class="user-info">
                    <div class="user-name">{{ user.name }}</div>
                    <div class="user-department">{{ user.department }}</div>
                    <div class="user-location">{{ user.lastLocation }}</div>
                  </div>
                  <div class="user-stats">
                    <div class="stat-item">
                      <span class="stat-label">距离</span>
                      <span class="stat-value">{{ user.todayDistance }}km</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">时长</span>
                      <span class="stat-value">{{ user.todayDuration }}h</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 热力图 -->
          <div v-if="activeTab === 'heatmap'" class="tab-content">
            <div class="heatmap-controls">
              <div class="control-row">
                <label>热力图类型:</label>
                <select v-model="heatmapType">
                  <option value="density">人员密度</option>
                  <option value="duration">停留时长</option>
                  <option value="frequency">访问频次</option>
                </select>
              </div>
              <div class="control-row">
                <label>强度:</label>
                <input 
                  type="range" 
                  v-model="heatmapIntensity" 
                  min="0.1" 
                  max="2" 
                  step="0.1"
                  class="intensity-slider"
                />
                <span class="intensity-value">{{ heatmapIntensity }}</span>
              </div>
            </div>
            <div class="heatmap-display">
              <HeatmapChart 
                :data="heatmapData"
                :type="heatmapType"
                :intensity="heatmapIntensity"
              />
            </div>
          </div>
          
          <!-- 统计报告 -->
          <div v-if="activeTab === 'statistics'" class="tab-content">
            <div class="statistics-grid">
              <div class="stat-card">
                <div class="stat-header">
                  <h4>活动统计</h4>
                  <CalendarIcon class="stat-icon" />
                </div>
                <div class="stat-metrics">
                  <div class="metric">
                    <span class="metric-label">总行走距离</span>
                    <span class="metric-value">{{ totalDistance }}km</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">平均停留时间</span>
                    <span class="metric-value">{{ avgStayTime }}分钟</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">最远距离</span>
                    <span class="metric-value">{{ maxDistance }}km</span>
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-header">
                  <h4>区域分布</h4>
                  <MapIcon class="stat-icon" />
                </div>
                <div class="area-list">
                  <div 
                    v-for="area in areaDistribution"
                    :key="area.name"
                    class="area-item"
                  >
                    <span class="area-name">{{ area.name }}</span>
                    <div class="area-bar">
                      <div 
                        class="area-fill"
                        :style="{ width: (area.percentage) + '%' }"
                      ></div>
                    </div>
                    <span class="area-percentage">{{ area.percentage }}%</span>
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-header">
                  <h4>时间分析</h4>
                  <ClockIcon class="stat-icon" />
                </div>
                <div class="time-chart">
                  <TimeDistributionChart :data="timeDistribution" />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 轨迹详情 -->
          <div v-if="activeTab === 'details'" class="tab-content">
            <div class="track-details" v-if="selectedTrackPoint">
              <div class="detail-header">
                <h4>轨迹点详情</h4>
                <button class="close-btn" @click="selectedTrackPoint = null">
                  <XMarkIcon />
                </button>
              </div>
              <div class="detail-content">
                <div class="detail-item">
                  <span class="detail-label">用户:</span>
                  <span class="detail-value">{{ selectedTrackPoint.userName }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">位置:</span>
                  <span class="detail-value">{{ selectedTrackPoint.location }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">坐标:</span>
                  <span class="detail-value">
                    {{ selectedTrackPoint.latitude }}, {{ selectedTrackPoint.longitude }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">时间:</span>
                  <span class="detail-value">{{ formatTime(selectedTrackPoint.timestamp) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">精度:</span>
                  <span class="detail-value">{{ selectedTrackPoint.accuracy }}m</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">速度:</span>
                  <span class="detail-value">{{ selectedTrackPoint.speed }}km/h</span>
                </div>
              </div>
            </div>
            <div v-else class="no-selection">
              <MapPinIcon class="no-selection-icon" />
              <p>请在地图上点击轨迹点查看详情</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 全局提示 -->
    <GlobalToast ref="toast" />
  </div>
</template>

<script setup lang="ts">
import { 
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  PlayIcon,
  PauseIcon,
  RefreshIcon,
  MagnifyingGlassIcon,
  UserIcon,
  CalendarIcon,
  MapIcon,
  ClockIcon,
  XMarkIcon,
  MapPinIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import TrackMapComponent from '@/components/track/TrackMapComponent.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import TimeDistributionChart from '@/components/charts/TimeDistributionChart.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { useTrackStore } from '@/stores/track'
import { useRouter } from 'vue-router'

// Store and router
const trackStore = useTrackStore()
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const selectedTimeRange = ref('today')
const selectedUser = ref('all')
const isRealtime = ref(false)
const isRefreshing = ref(false)
const activeTab = ref('users')
const searchQuery = ref('')
const heatmapType = ref('density')
const heatmapIntensity = ref(1.0)
const selectedTrackPoint = ref(null)

// 地图配置
const mapCenter = ref({ lat: 39.9042, lng: 116.4074 }) // 北京
const mapZoom = ref(12)

// 分析标签配置
const analysisTabs = [
  { key: 'users', label: '用户列表', icon: UserIcon },
  { key: 'heatmap', label: '热力图', icon: MapIcon },
  { key: 'statistics', label: '统计报告', icon: CalendarIcon },
  { key: 'details', label: '轨迹详情', icon: MapPinIcon }
]

// 模拟用户数据
const users = ref([
  {
    id: 'user_001',
    name: '张三',
    department: '技术部',
    online: true,
    lastLocation: '办公楼A座2层',
    todayDistance: 3.2,
    todayDuration: 6.5,
    coordinates: { lat: 39.9052, lng: 116.4084 }
  },
  {
    id: 'user_002',
    name: '李四',
    department: '市场部',
    online: true,
    lastLocation: '办公楼B座1层',
    todayDistance: 2.8,
    todayDuration: 5.2,
    coordinates: { lat: 39.9032, lng: 116.4064 }
  },
  {
    id: 'user_003',
    name: '王五',
    department: '财务部',
    online: false,
    lastLocation: '办公楼C座3层',
    todayDistance: 1.5,
    todayDuration: 3.8,
    coordinates: { lat: 39.9062, lng: 116.4054 }
  }
])

// 模拟轨迹数据
const tracks = ref([
  {
    id: 'track_001',
    userId: 'user_001',
    userName: '张三',
    points: Array.from({ length: 20 }, (_, i) => ({
      latitude: 39.9052 + (Math.random() - 0.5) * 0.01,
      longitude: 116.4084 + (Math.random() - 0.5) * 0.01,
      timestamp: new Date(Date.now() - i * 30 * 60000),
      accuracy: 5 + Math.random() * 10,
      speed: Math.random() * 5,
      location: `位置点${i + 1}`
    }))
  }
])

// 计算属性
const onlineUsers = computed(() => users.value.filter(u => u.online).length)
const todayTracks = computed(() => tracks.value.length)
const coverageAreas = computed(() => 8)

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  return users.value.filter(user => 
    user.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    user.department.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const filteredTracks = computed(() => {
  if (selectedUser.value === 'all') return tracks.value
  return tracks.value.filter(track => track.userId === selectedUser.value)
})

const heatmapData = computed(() => {
  // 模拟热力图数据
  return Array.from({ length: 50 }, (_, i) => ({
    lat: 39.9042 + (Math.random() - 0.5) * 0.02,
    lng: 116.4074 + (Math.random() - 0.5) * 0.02,
    intensity: Math.random()
  }))
})

const totalDistance = computed(() => '125.6')
const avgStayTime = computed(() => '18.5')
const maxDistance = computed(() => '8.3')

const areaDistribution = computed(() => [
  { name: '办公区域', percentage: 45 },
  { name: '休息区域', percentage: 25 },
  { name: '会议区域', percentage: 15 },
  { name: '公共区域', percentage: 15 }
])

const timeDistribution = computed(() => 
  Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    count: Math.floor(Math.random() * 50) + 10
  }))
)

// 方法
const goBack = () => {
  router.push('/dashboard/personal')
}

const updateTrackData = () => {
  toast.value?.info(`已切换到${selectedTimeRange.value}数据`)
}

const filterUserTracks = () => {
  if (selectedUser.value !== 'all') {
    const user = users.value.find(u => u.id === selectedUser.value)
    if (user) {
      mapCenter.value = user.coordinates
      mapZoom.value = 15
    }
  } else {
    mapCenter.value = { lat: 39.9042, lng: 116.4074 }
    mapZoom.value = 12
  }
}

const toggleRealtime = () => {
  isRealtime.value = !isRealtime.value
  if (isRealtime.value) {
    toast.value?.success('已开启实时追踪')
  } else {
    toast.value?.info('已暂停实时追踪')
  }
}

const refreshTracks = async () => {
  isRefreshing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    toast.value?.success('轨迹数据已刷新')
  } finally {
    isRefreshing.value = false
  }
}

const selectUser = (user: any) => {
  selectedUser.value = user.id
  filterUserTracks()
}

const selectTrackPoint = (point: any) => {
  selectedTrackPoint.value = point
  activeTab.value = 'details'
}

const exportTrackData = () => {
  toast.value?.info('轨迹数据导出功能开发中')
}

const formatTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  console.log('轨迹追踪页面已加载')
})
</script>

<style lang="scss" scoped>
.track-view {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// ========== 页面头部 ==========
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
  z-index: 10;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

.page-title {
  h1 {
    font-size: var(--font-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }
  
  .page-subtitle {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin: 0;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.track-stats {
  display: flex;
  gap: var(--spacing-lg);
  
  .stat-item {
    text-align: center;
    
    .stat-label {
      display: block;
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-value {
      display: block;
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
      
      &.online {
        color: var(--success);
      }
    }
  }
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--primary-500);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    background: var(--primary-600);
    transform: translateY(-1px);
  }
}

// ========== 主体内容 ==========
.track-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

// ========== 地图区域 ==========
.map-section {
  flex: 2;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-right: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
}

.map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-secondary);
  
  .control-group {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      white-space: nowrap;
    }
    
    select {
      padding: var(--spacing-xs) var(--spacing-sm);
      border: 1px solid var(--border-secondary);
      border-radius: var(--radius-sm);
      background: var(--bg-tertiary);
      color: var(--text-primary);
      
      &:focus {
        outline: none;
        border-color: var(--primary-500);
      }
    }
  }
  
  .control-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-sm);
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
    
    .spinning {
      animation: spin 1s linear infinite;
    }
  }
}

.map-area {
  flex: 1;
  background: var(--bg-tertiary);
  position: relative;
}

.map-legend {
  position: absolute;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  backdrop-filter: blur(10px);
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
    font-size: var(--font-sm);
    color: var(--text-secondary);
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .legend-color {
    width: 16px;
    height: 4px;
    border-radius: var(--radius-sm);
    
    &.online { background: var(--success); }
    &.offline { background: var(--error); }
    &.track-line { background: var(--primary-500); }
    &.danger-zone { background: var(--warning); }
  }
}

// ========== 分析面板 ==========
.analysis-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
  
  h3 {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.analysis-tabs {
  display: flex;
  gap: var(--spacing-xs);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  .tab-icon {
    width: 16px;
    height: 16px;
  }
  
  &:hover {
    color: var(--text-primary);
  }
  
  &.active {
    background: var(--primary-500);
    color: white;
    border-color: var(--primary-500);
  }
}

.analysis-content {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  padding: var(--spacing-lg);
  height: 100%;
}

// ========== 用户列表 ==========
.user-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  margin-bottom: var(--spacing-lg);
}

.search-box {
  position: relative;
  
  .search-icon {
    position: absolute;
    left: var(--spacing-sm);
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: var(--text-tertiary);
  }
  
  .search-input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) var(--spacing-xl);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:focus {
      outline: none;
      border-color: var(--primary-500);
    }
    
    &::placeholder {
      color: var(--text-tertiary);
    }
  }
}

.user-items {
  flex: 1;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    background: var(--bg-secondary);
    border-color: var(--primary-500);
  }
  
  &.active {
    background: rgba(0, 255, 157, 0.1);
    border-color: var(--primary-500);
  }
}

.user-avatar {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  
  .status-dot {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--error);
    border: 2px solid var(--bg-card);
    
    &.online {
      background: var(--success);
    }
  }
}

.user-info {
  flex: 1;
  
  .user-name {
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }
  
  .user-department,
  .user-location {
    font-size: var(--font-xs);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }
}

.user-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  
  .stat-item {
    display: flex;
    justify-content: space-between;
    gap: var(--spacing-sm);
    
    .stat-label {
      font-size: var(--font-xs);
      color: var(--text-tertiary);
    }
    
    .stat-value {
      font-size: var(--font-xs);
      color: var(--text-primary);
      font-family: var(--font-tech);
    }
  }
}

// ========== 热力图 ==========
.heatmap-controls {
  margin-bottom: var(--spacing-lg);
  
  .control-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
    
    label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      min-width: 80px;
    }
    
    select {
      padding: var(--spacing-xs) var(--spacing-sm);
      border: 1px solid var(--border-secondary);
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      color: var(--text-primary);
    }
  }
  
  .intensity-slider {
    flex: 1;
    margin-right: var(--spacing-sm);
  }
  
  .intensity-value {
    font-size: var(--font-sm);
    color: var(--text-primary);
    font-family: var(--font-tech);
    min-width: 30px;
  }
}

.heatmap-display {
  height: 400px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
}

// ========== 统计报告 ==========
.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  .stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .stat-icon {
      width: 20px;
      height: 20px;
      color: var(--primary-500);
    }
  }
  
  .stat-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .metric-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
    
    .metric-value {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
    }
  }
}

.area-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.area-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  
  .area-name {
    font-size: var(--font-sm);
    color: var(--text-primary);
    min-width: 80px;
  }
  
  .area-bar {
    flex: 1;
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
    
    .area-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary-500), var(--tech-500));
      transition: width var(--duration-normal);
    }
  }
  
  .area-percentage {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    font-family: var(--font-tech);
    min-width: 40px;
    text-align: right;
  }
}

.time-chart {
  height: 200px;
}

// ========== 轨迹详情 ==========
.track-details {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-tertiary);
  
  h4 {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: var(--error);
    color: white;
  }
}

.detail-content {
  padding: var(--spacing-lg);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  
  .detail-label {
    font-size: var(--font-sm);
    color: var(--text-secondary);
  }
  
  .detail-value {
    font-size: var(--font-sm);
    color: var(--text-primary);
    font-family: var(--font-tech);
  }
}

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  
  .no-selection-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--spacing-md);
  }
  
  p {
    margin: 0;
    font-size: var(--font-sm);
  }
}

// ========== 动画 ==========
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .track-content {
    flex-direction: column;
  }
  
  .map-section {
    flex: 1;
    min-height: 400px;
    border-right: none;
    border-bottom: 1px solid var(--border-primary);
  }
  
  .analysis-section {
    flex: 1;
    min-height: 400px;
  }
  
  .statistics-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .track-stats {
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }
  
  .map-controls {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
    
    .control-group {
      justify-content: space-between;
    }
  }
  
  .analysis-tabs {
    flex-wrap: wrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .user-item,
  .control-btn,
  .tab-btn {
    transition: none;
  }
  
  .spinning {
    animation: none;
  }
}
</style>