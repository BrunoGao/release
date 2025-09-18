<template>
  <div class="track-map-component">
    <div class="map-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Location />
        </el-icon>
        <h3 class="map-title">轨迹地图</h3>
      </div>
      
      <div class="map-controls">
        <el-select v-model="selectedTimeRange" size="small" @change="updateTrackData">
          <el-option label="今日轨迹" value="today" />
          <el-option label="昨日轨迹" value="yesterday" />
          <el-option label="本周轨迹" value="week" />
          <el-option label="本月轨迹" value="month" />
        </el-select>
        
        <el-button-group>
          <el-button size="small" @click="centerMap">
            <el-icon><Aim /></el-icon>
            定位
          </el-button>
          <el-button size="small" @click="fullScreen">
            <el-icon><FullScreen /></el-icon>
            全屏
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 地图容器 -->
    <div class="map-container" ref="mapContainer">
      <div class="map-placeholder">
        <div class="placeholder-content">
          <el-icon class="placeholder-icon">
            <Location />
          </el-icon>
          <p class="placeholder-text">地图组件占位</p>
          <p class="placeholder-note">实际项目中可集成百度地图、高德地图或其他地图服务</p>
          
          <!-- 模拟轨迹点 -->
          <div class="mock-track">
            <div class="track-point start">起点</div>
            <div class="track-line"></div>
            <div class="track-point middle">途经点</div>
            <div class="track-line"></div>
            <div class="track-point end">终点</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 轨迹统计 -->
    <div class="track-stats">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trackStats.duration }}</div>
            <div class="stat-label">运动时长</div>
          </div>
        </div>
        
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><Position /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trackStats.distance }}</div>
            <div class="stat-label">运动距离</div>
          </div>
        </div>
        
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trackStats.avgSpeed }}</div>
            <div class="stat-label">平均速度</div>
          </div>
        </div>
        
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trackStats.calories }}</div>
            <div class="stat-label">消耗卡路里</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 轨迹详情 -->
    <div class="track-details">
      <div class="details-header">
        <h4>轨迹详情</h4>
        <el-button type="text" @click="showAllTracks">
          查看全部 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <div class="track-list">
        <div 
          v-for="track in recentTracks" 
          :key="track.id"
          class="track-item"
          @click="selectTrack(track)"
        >
          <div class="track-icon">
            <el-icon>
              <component :is="getTrackTypeIcon(track.type)" />
            </el-icon>
          </div>
          <div class="track-info">
            <div class="track-name">{{ track.name }}</div>
            <div class="track-meta">
              <span class="track-date">{{ formatDate(track.date) }}</span>
              <span class="track-distance">{{ track.distance }}km</span>
            </div>
          </div>
          <div class="track-status">
            <el-tag :type="getTrackStatusType(track.status)" size="small">
              {{ getTrackStatusText(track.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Location, 
  Aim, 
  FullScreen, 
  Timer,
  Position,
  TrendCharts,
  Lightning,
  ArrowRight,
  Walking,
  Bicycle,
  CaretRight
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface TrackPoint {
  lat: number
  lng: number
  timestamp: Date
  altitude?: number
  speed?: number
}

interface Track {
  id: string
  name: string
  type: 'walking' | 'running' | 'cycling' | 'other'
  date: Date
  distance: number
  duration: number
  status: 'completed' | 'paused' | 'recording'
  points: TrackPoint[]
}

interface Props {
  userId?: string
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  userId: '',
  height: '500px'
})

// 响应式数据
const mapContainer = ref<HTMLElement>()
const selectedTimeRange = ref('today')

// 轨迹统计数据
const trackStats = reactive({
  duration: '1小时32分',
  distance: '8.5公里',
  avgSpeed: '5.5km/h',
  calories: '520卡'
})

// 最近轨迹记录
const recentTracks = ref<Track[]>([
  {
    id: 'track_001',
    name: '晨跑轨迹',
    type: 'running',
    date: new Date(),
    distance: 5.2,
    duration: 35,
    status: 'completed',
    points: []
  },
  {
    id: 'track_002',
    name: '骑行锻炼',
    type: 'cycling',
    date: new Date(Date.now() - 86400000),
    distance: 12.8,
    duration: 45,
    status: 'completed',
    points: []
  },
  {
    id: 'track_003',
    name: '散步轨迹',
    type: 'walking',
    date: new Date(Date.now() - 172800000),
    distance: 3.1,
    duration: 28,
    status: 'completed',
    points: []
  }
])

// 方法
const updateTrackData = () => {
  console.log('更新轨迹数据:', selectedTimeRange.value)
  // 根据时间范围更新轨迹数据
  ElMessage.success(`已切换到${getTimeRangeLabel()}的轨迹数据`)
}

const centerMap = () => {
  ElMessage.info('地图已定位到当前位置')
}

const fullScreen = () => {
  if (!document.fullscreenElement) {
    mapContainer.value?.requestFullscreen()
    ElMessage.info('已进入全屏模式')
  } else {
    document.exitFullscreen()
    ElMessage.info('已退出全屏模式')
  }
}

const selectTrack = (track: Track) => {
  ElMessage.info(`已选择轨迹: ${track.name}`)
  // 在地图上显示选中的轨迹
}

const showAllTracks = () => {
  ElMessage.info('跳转到轨迹历史页面')
  // 路由跳转到轨迹列表页面
}

// 工具方法
const getTimeRangeLabel = () => {
  const labelMap = {
    today: '今日',
    yesterday: '昨日',
    week: '本周',
    month: '本月'
  }
  return labelMap[selectedTimeRange.value as keyof typeof labelMap]
}

const getTrackTypeIcon = (type: string) => {
  const iconMap = {
    walking: Walking,
    running: CaretRight,
    cycling: Bicycle,
    other: Position
  }
  return iconMap[type as keyof typeof iconMap] || Position
}

const getTrackStatusType = (status: string) => {
  const typeMap = {
    completed: 'success',
    paused: 'warning',
    recording: 'primary'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getTrackStatusText = (status: string) => {
  const textMap = {
    completed: '已完成',
    paused: '已暂停',
    recording: '记录中'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const formatDate = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString()
}

// 生命周期
onMounted(() => {
  // 初始化地图组件
  console.log('地图组件已挂载')
})
</script>

<style lang="scss" scoped>
.track-map-component {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .map-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .map-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
}

.map-container {
  flex: 1;
  position: relative;
  min-height: 300px;
  
  .map-placeholder {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: 
        radial-gradient(circle at 20% 50%, rgba(0, 255, 157, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(66, 165, 245, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(255, 167, 38, 0.1) 0%, transparent 50%);
    }
    
    .placeholder-content {
      text-align: center;
      z-index: 1;
      
      .placeholder-icon {
        font-size: 64px;
        color: var(--primary-500);
        margin-bottom: var(--spacing-lg);
        opacity: 0.8;
      }
      
      .placeholder-text {
        font-size: var(--font-xl);
        color: var(--text-primary);
        margin-bottom: var(--spacing-sm);
      }
      
      .placeholder-note {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-xl);
      }
    }
    
    .mock-track {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-md);
      margin-top: var(--spacing-lg);
      
      .track-point {
        padding: var(--spacing-xs) var(--spacing-sm);
        background: var(--bg-elevated);
        border: 2px solid var(--primary-500);
        border-radius: var(--radius-full);
        color: var(--text-primary);
        font-size: var(--font-xs);
        font-weight: 600;
        white-space: nowrap;
        z-index: 2;
        
        &.start {
          border-color: var(--success-500);
          background: linear-gradient(135deg, var(--success-500), var(--success-600));
          color: white;
        }
        
        &.end {
          border-color: var(--error-500);
          background: linear-gradient(135deg, var(--error-500), var(--error-600));
          color: white;
        }
      }
      
      .track-line {
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
        border-radius: var(--radius-full);
        position: relative;
        
        &::before {
          content: '';
          position: absolute;
          top: 50%;
          right: -6px;
          transform: translateY(-50%);
          width: 0;
          height: 0;
          border-left: 6px solid var(--primary-500);
          border-top: 4px solid transparent;
          border-bottom: 4px solid transparent;
        }
      }
    }
  }
}

.track-stats {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-lg);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      
      .stat-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
      }
      
      .stat-content {
        .stat-value {
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
          margin-bottom: 2px;
        }
        
        .stat-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.track-details {
  padding: var(--spacing-lg);
  
  .details-header {
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
  
  .track-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .track-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-elevated);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateX(4px);
        border-color: var(--primary-300);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }
      
      .track-icon {
        width: 36px;
        height: 36px;
        background: var(--bg-secondary);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary-500);
        font-size: 16px;
      }
      
      .track-info {
        flex: 1;
        
        .track-name {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .track-meta {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          font-size: var(--font-xs);
          color: var(--text-secondary);
          
          .track-distance {
            font-weight: 600;
            color: var(--primary-500);
          }
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .map-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .track-item {
    .track-info .track-meta {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-xs);
    }
  }
}
</style>