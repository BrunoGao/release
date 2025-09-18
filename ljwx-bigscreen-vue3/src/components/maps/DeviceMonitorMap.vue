<template>
  <div class="device-monitor-map">
    <div class="map-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Location />
        </el-icon>
        <h3 class="map-title">{{ title }}</h3>
      </div>
      
      <div class="map-controls">
        <el-select v-model="selectedLayer" size="small">
          <el-option label="设备分布" value="devices" />
          <el-option label="信号强度" value="signal" />
          <el-option label="在线状态" value="status" />
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
          <p class="placeholder-text">设备分布地图</p>
          <p class="placeholder-note">实际项目中可集成百度地图、高德地图等地图服务</p>
          
          <!-- 模拟设备分布 -->
          <div class="mock-devices">
            <div 
              v-for="device in mockDevices" 
              :key="device.id"
              class="device-point"
              :class="device.status"
              :style="{ left: device.x + '%', top: device.y + '%' }"
              @click="selectDevice(device)"
            >
              <div class="device-marker">
                <el-icon>
                  <component :is="getDeviceIcon(device.type)" />
                </el-icon>
              </div>
              <div class="device-info" v-if="selectedDeviceId === device.id">
                <div class="info-header">{{ device.name }}</div>
                <div class="info-details">
                  <div>类型: {{ device.type }}</div>
                  <div>状态: {{ getStatusText(device.status) }}</div>
                  <div>信号: {{ device.signal }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 设备统计 -->
    <div class="device-stats">
      <div class="stats-grid">
        <div class="stat-item online">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.online }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </div>
        
        <div class="stat-item offline">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.offline }}</div>
            <div class="stat-label">离线设备</div>
          </div>
        </div>
        
        <div class="stat-item alert">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.alert }}</div>
            <div class="stat-label">异常设备</div>
          </div>
        </div>
        
        <div class="stat-item total">
          <div class="stat-icon">
            <el-icon><DataBoard /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ getTotalDevices() }}</div>
            <div class="stat-label">设备总数</div>
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
  CircleCheck, 
  CircleClose, 
  Warning, 
  DataBoard,
  Monitor,
  Cpu,
  Camera
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '设备监控地图',
  height: '500px'
})

const mapContainer = ref<HTMLElement>()
const selectedLayer = ref('devices')
const selectedDeviceId = ref<string | null>(null)

// 设备统计数据
const deviceStats = reactive({
  online: 45,
  offline: 8,
  alert: 3,
})

// 模拟设备数据
const mockDevices = ref([
  {
    id: 'device_001',
    name: '心率监测器-A1',
    type: '心率监测器',
    status: 'online',
    signal: 95,
    x: 25,
    y: 30
  },
  {
    id: 'device_002',
    name: '血氧仪-B2',
    type: '血氧监测器',
    status: 'online',
    signal: 88,
    x: 45,
    y: 25
  },
  {
    id: 'device_003',
    name: '血压计-C3',
    type: '血压计',
    status: 'offline',
    signal: 0,
    x: 65,
    y: 40
  },
  {
    id: 'device_004',
    name: '体温计-D4',
    type: '体温计',
    status: 'alert',
    signal: 45,
    x: 35,
    y: 60
  },
  {
    id: 'device_005',
    name: '智能手环-E5',
    type: '智能手环',
    status: 'online',
    signal: 92,
    x: 75,
    y: 20
  },
  {
    id: 'device_006',
    name: '心率监测器-F6',
    type: '心率监测器',
    status: 'online',
    signal: 78,
    x: 20,
    y: 70
  }
])

const centerMap = () => {
  ElMessage.info('地图已定位到中心位置')
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

const selectDevice = (device: any) => {
  selectedDeviceId.value = selectedDeviceId.value === device.id ? null : device.id
  ElMessage.info(`选择设备: ${device.name}`)
}

const getDeviceIcon = (type: string) => {
  const iconMap = {
    '心率监测器': Monitor,
    '血氧监测器': Cpu,
    '血压计': Monitor,
    '体温计': Camera,
    '智能手环': Monitor
  }
  return iconMap[type as keyof typeof iconMap] || Monitor
}

const getStatusText = (status: string) => {
  const textMap = {
    online: '在线',
    offline: '离线',
    alert: '异常'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getTotalDevices = () => {
  return deviceStats.online + deviceStats.offline + deviceStats.alert
}

onMounted(() => {
  console.log('设备监控地图已挂载')
})
</script>

<style lang="scss" scoped>
.device-monitor-map {
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
    
    .mock-devices {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      
      .device-point {
        position: absolute;
        cursor: pointer;
        transform: translate(-50%, -50%);
        
        .device-marker {
          width: 24px;
          height: 24px;
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 12px;
          border: 2px solid white;
          transition: all 0.3s ease;
          
          &:hover {
            transform: scale(1.2);
          }
        }
        
        .device-info {
          position: absolute;
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: var(--bg-card);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm);
          min-width: 150px;
          margin-top: var(--spacing-xs);
          z-index: 10;
          
          .info-header {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: var(--spacing-xs);
          }
          
          .info-details {
            font-size: var(--font-xs);
            color: var(--text-secondary);
            
            div {
              margin-bottom: 2px;
            }
          }
        }
        
        &.online .device-marker {
          background: var(--success-500);
          box-shadow: 0 0 20px rgba(102, 187, 106, 0.5);
        }
        
        &.offline .device-marker {
          background: var(--text-secondary);
          box-shadow: 0 0 20px rgba(156, 163, 175, 0.5);
        }
        
        &.alert .device-marker {
          background: var(--error-500);
          box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
          animation: pulse 2s infinite;
        }
      }
    }
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(255, 107, 107, 0.8);
  }
  100% {
    box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
  }
}

.device-stats {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-light);
  
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
      
      &.online .stat-icon {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
      }
      
      &.offline .stat-icon {
        background: linear-gradient(135deg, #9e9e9e, #757575);
      }
      
      &.alert .stat-icon {
        background: linear-gradient(135deg, #ff6b6b, #f44336);
      }
      
      &.total .stat-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
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
  }
}
</style>