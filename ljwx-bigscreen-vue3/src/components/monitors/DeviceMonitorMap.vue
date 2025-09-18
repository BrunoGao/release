<template>
  <div class="device-monitor-map">
    <div class="map-header">
      <h4 class="map-title">设备监控地图</h4>
      <div class="map-controls">
        <el-radio-group v-model="viewMode" size="small" @change="updateView">
          <el-radio-button label="status">设备状态</el-radio-button>
          <el-radio-button label="health">健康分布</el-radio-button>
          <el-radio-button label="alerts">告警分布</el-radio-button>
        </el-radio-group>
        <el-button size="small" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 地图统计概览 -->
    <div class="map-overview">
      <div class="overview-stats">
        <div class="stat-item" v-for="stat in overviewStats" :key="stat.key">
          <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
            <el-icon><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
      
      <div class="view-legend">
        <div class="legend-title">图例</div>
        <div class="legend-items">
          <div 
            v-for="legend in currentLegend" 
            :key="legend.type"
            class="legend-item"
          >
            <div class="legend-indicator" :style="{ background: legend.color }"></div>
            <span class="legend-text">{{ legend.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 地图主体 -->
    <div class="map-container">
      <div class="map-canvas" ref="mapCanvasRef">
        <!-- 模拟地图背景 -->
        <div class="map-background">
          <div class="grid-lines"></div>
          
          <!-- 区域划分 -->
          <div class="map-regions">
            <div 
              v-for="region in mapRegions" 
              :key="region.id"
              class="map-region"
              :style="{ 
                left: region.x + '%', 
                top: region.y + '%',
                width: region.width + '%',
                height: region.height + '%'
              }"
            >
              <div class="region-label">{{ region.name }}</div>
            </div>
          </div>
          
          <!-- 设备点位 -->
          <div class="device-markers">
            <div 
              v-for="device in devices" 
              :key="device.id"
              class="device-marker"
              :class="getDeviceClass(device)"
              :style="{ left: device.x + '%', top: device.y + '%' }"
              @click="selectDevice(device)"
              @mouseenter="showDeviceTooltip(device, $event)"
              @mouseleave="hideDeviceTooltip"
            >
              <div class="marker-icon">
                <el-icon><component :is="getDeviceIcon(device.type)" /></el-icon>
              </div>
              <div class="marker-pulse" v-if="device.status === 'alert'"></div>
            </div>
          </div>
          
          <!-- 连接线 -->
          <svg class="connection-lines" v-if="showConnections">
            <line 
              v-for="connection in connections" 
              :key="connection.id"
              :x1="connection.x1 + '%'" 
              :y1="connection.y1 + '%'"
              :x2="connection.x2 + '%'" 
              :y2="connection.y2 + '%'"
              :class="`connection-${connection.strength}`"
            />
          </svg>
        </div>
      </div>
      
      <!-- 地图缩放控制 -->
      <div class="map-zoom-controls">
        <el-button-group>
          <el-button size="small" @click="zoomIn">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button size="small" @click="zoomOut">
            <el-icon><Minus /></el-icon>
          </el-button>
          <el-button size="small" @click="resetZoom">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 设备详情面板 -->
    <div v-if="selectedDevice" class="device-detail-panel">
      <div class="panel-header">
        <div class="device-info">
          <div class="device-icon" :style="{ color: getDeviceStatusColor(selectedDevice.status) }">
            <el-icon><component :is="getDeviceIcon(selectedDevice.type)" /></el-icon>
          </div>
          <div class="device-basic">
            <div class="device-name">{{ selectedDevice.name }}</div>
            <div class="device-type">{{ selectedDevice.type }}</div>
          </div>
        </div>
        <el-button size="small" text @click="selectedDevice = null">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      
      <div class="panel-content">
        <div class="device-status">
          <div class="status-item">
            <span class="status-label">状态:</span>
            <span class="status-value" :class="`status-${selectedDevice.status}`">
              {{ getStatusText(selectedDevice.status) }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">位置:</span>
            <span class="status-value">{{ selectedDevice.location }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">最后更新:</span>
            <span class="status-value">{{ formatTime(selectedDevice.lastUpdate) }}</span>
          </div>
        </div>
        
        <div class="device-metrics" v-if="selectedDevice.metrics">
          <div class="metrics-title">设备指标</div>
          <div class="metrics-list">
            <div 
              v-for="metric in selectedDevice.metrics" 
              :key="metric.name"
              class="metric-item"
            >
              <div class="metric-name">{{ metric.name }}</div>
              <div class="metric-value">{{ metric.value }}{{ metric.unit }}</div>
              <div class="metric-status" :class="`status-${metric.status}`">
                {{ getStatusText(metric.status) }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="device-actions">
          <el-button size="small" type="primary" @click="configDevice(selectedDevice)">
            设备配置
          </el-button>
          <el-button size="small" @click="viewDeviceHistory(selectedDevice)">
            历史数据
          </el-button>
          <el-button 
            size="small" 
            :type="selectedDevice.status === 'offline' ? 'success' : 'warning'"
            @click="toggleDevice(selectedDevice)"
          >
            {{ selectedDevice.status === 'offline' ? '启用' : '禁用' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 设备悬浮提示 -->
    <div 
      v-if="tooltipVisible" 
      class="device-tooltip" 
      :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }"
    >
      <div class="tooltip-header">{{ tooltipDevice?.name }}</div>
      <div class="tooltip-content">
        <div>类型: {{ tooltipDevice?.type }}</div>
        <div>状态: {{ getStatusText(tooltipDevice?.status) }}</div>
        <div v-if="tooltipDevice?.healthScore">
          健康评分: {{ tooltipDevice.healthScore }}分
        </div>
      </div>
    </div>

    <!-- 批量操作工具栏 -->
    <div v-if="selectedDevices.length > 0" class="batch-toolbar">
      <div class="toolbar-info">
        已选择 {{ selectedDevices.length }} 个设备
      </div>
      <div class="toolbar-actions">
        <el-button size="small" @click="batchConfig">批量配置</el-button>
        <el-button size="small" @click="batchUpdate">批量更新</el-button>
        <el-button size="small" type="danger" @click="batchDisable">批量禁用</el-button>
        <el-button size="small" text @click="clearSelection">清除选择</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Refresh, Plus, Minus, FullScreen, Close,
  Monitor, Camera, Wifi, Warning, CircleCheck, CircleClose
} from '@element-plus/icons-vue'

interface Device {
  id: string
  name: string
  type: string
  x: number
  y: number
  status: 'online' | 'offline' | 'alert' | 'maintenance'
  location: string
  lastUpdate: number
  healthScore?: number
  alertCount?: number
  metrics?: DeviceMetric[]
}

interface DeviceMetric {
  name: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'error'
}

interface MapRegion {
  id: string
  name: string
  x: number
  y: number
  width: number
  height: number
}

interface Connection {
  id: string
  x1: number
  y1: number
  x2: number
  y2: number
  strength: 'strong' | 'medium' | 'weak'
}

interface OverviewStat {
  key: string
  label: string
  value: number | string
  color: string
  icon: any
}

interface LegendItem {
  type: string
  label: string
  color: string
}

// 响应式数据
const viewMode = ref('status')
const selectedDevice = ref<Device | null>(null)
const selectedDevices = ref<string[]>([])
const showConnections = ref(false)
const zoomLevel = ref(1)
const mapCanvasRef = ref<HTMLElement>()

// 悬浮提示
const tooltipVisible = ref(false)
const tooltipDevice = ref<Device | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })

// 概览统计
const overviewStats = ref<OverviewStat[]>([
  {
    key: 'total',
    label: '总设备数',
    value: 24,
    color: '#409eff',
    icon: Monitor
  },
  {
    key: 'online',
    label: '在线设备',
    value: 18,
    color: '#67c23a',
    icon: CircleCheck
  },
  {
    key: 'offline',
    label: '离线设备',
    value: 3,
    color: '#909399',
    icon: CircleClose
  },
  {
    key: 'alerts',
    label: '告警设备',
    value: 3,
    color: '#ff6b6b',
    icon: Warning
  }
])

// 地图区域
const mapRegions: MapRegion[] = [
  { id: 'office-a', name: '办公区A', x: 10, y: 15, width: 35, height: 30 },
  { id: 'office-b', name: '办公区B', x: 55, y: 15, width: 35, height: 30 },
  { id: 'meeting', name: '会议室', x: 10, y: 55, width: 25, height: 20 },
  { id: 'server', name: '机房', x: 45, y: 55, width: 20, height: 20 },
  { id: 'lobby', name: '大厅', x: 75, y: 55, width: 15, height: 35 }
]

// 设备数据
const devices = ref<Device[]>([
  {
    id: 'dev-001',
    name: '健康监测器-001',
    type: 'health_monitor',
    x: 15,
    y: 25,
    status: 'online',
    location: '办公区A',
    lastUpdate: Date.now() - 300000,
    healthScore: 85,
    metrics: [
      { name: '心率', value: 72, unit: 'bpm', status: 'normal' },
      { name: '血氧', value: 98, unit: '%', status: 'normal' }
    ]
  },
  {
    id: 'dev-002',
    name: '环境传感器-002',
    type: 'environment',
    x: 25,
    y: 35,
    status: 'alert',
    location: '办公区A',
    lastUpdate: Date.now() - 120000,
    alertCount: 2,
    metrics: [
      { name: '温度', value: 28, unit: '°C', status: 'warning' },
      { name: '湿度', value: 65, unit: '%', status: 'normal' }
    ]
  },
  {
    id: 'dev-003',
    name: '摄像头-003',
    type: 'camera',
    x: 35,
    y: 20,
    status: 'online',
    location: '办公区A',
    lastUpdate: Date.now() - 60000
  },
  {
    id: 'dev-004',
    name: '健康监测器-004',
    type: 'health_monitor',
    x: 60,
    y: 30,
    status: 'online',
    location: '办公区B',
    lastUpdate: Date.now() - 180000,
    healthScore: 92
  },
  {
    id: 'dev-005',
    name: 'WiFi接入点-005',
    type: 'network',
    x: 70,
    y: 25,
    status: 'offline',
    location: '办公区B',
    lastUpdate: Date.now() - 3600000
  },
  {
    id: 'dev-006',
    name: '服务器-006',
    type: 'server',
    x: 55,
    y: 65,
    status: 'alert',
    location: '机房',
    lastUpdate: Date.now() - 900000,
    alertCount: 1,
    metrics: [
      { name: 'CPU', value: 85, unit: '%', status: 'warning' },
      { name: '内存', value: 78, unit: '%', status: 'normal' }
    ]
  }
])

// 连接线
const connections: Connection[] = [
  { id: 'conn-1', x1: 15, y1: 25, x2: 25, y2: 35, strength: 'strong' },
  { id: 'conn-2', x1: 25, y1: 35, x2: 35, y2: 20, strength: 'medium' },
  { id: 'conn-3', x1: 60, y1: 30, x2: 70, y2: 25, strength: 'weak' },
  { id: 'conn-4', x1: 70, y1: 25, x2: 55, y2: 65, strength: 'medium' }
]

// 计算属性
const currentLegend = computed((): LegendItem[] => {
  switch (viewMode.value) {
    case 'status':
      return [
        { type: 'online', label: '在线', color: '#67c23a' },
        { type: 'offline', label: '离线', color: '#909399' },
        { type: 'alert', label: '告警', color: '#ff6b6b' },
        { type: 'maintenance', label: '维护', color: '#ffa726' }
      ]
    case 'health':
      return [
        { type: 'excellent', label: '优秀(90+)', color: '#67c23a' },
        { type: 'good', label: '良好(70-89)', color: '#409eff' },
        { type: 'fair', label: '一般(50-69)', color: '#ffa726' },
        { type: 'poor', label: '较差(<50)', color: '#ff6b6b' }
      ]
    case 'alerts':
      return [
        { type: 'no-alert', label: '无告警', color: '#67c23a' },
        { type: 'low-alert', label: '低级告警', color: '#ffa726' },
        { type: 'high-alert', label: '高级告警', color: '#ff6b6b' }
      ]
    default:
      return []
  }
})

// 工具方法
const getDeviceClass = (device: Device) => {
  const baseClass = 'device-marker'
  
  switch (viewMode.value) {
    case 'status':
      return `${baseClass} marker-${device.status}`
    case 'health':
      if (!device.healthScore) return `${baseClass} marker-no-data`
      if (device.healthScore >= 90) return `${baseClass} marker-excellent`
      if (device.healthScore >= 70) return `${baseClass} marker-good`
      if (device.healthScore >= 50) return `${baseClass} marker-fair`
      return `${baseClass} marker-poor`
    case 'alerts':
      if (!device.alertCount || device.alertCount === 0) return `${baseClass} marker-no-alert`
      if (device.alertCount <= 2) return `${baseClass} marker-low-alert`
      return `${baseClass} marker-high-alert`
    default:
      return baseClass
  }
}

const getDeviceIcon = (type: string) => {
  switch (type) {
    case 'health_monitor':
      return Monitor
    case 'camera':
      return Camera
    case 'network':
      return Wifi
    case 'environment':
      return Monitor
    case 'server':
      return Monitor
    default:
      return Monitor
  }
}

const getDeviceStatusColor = (status: string) => {
  switch (status) {
    case 'online':
      return '#67c23a'
    case 'offline':
      return '#909399'
    case 'alert':
      return '#ff6b6b'
    case 'maintenance':
      return '#ffa726'
    default:
      return '#409eff'
  }
}

const getStatusText = (status: string) => {
  const statusMap = {
    online: '在线',
    offline: '离线',
    alert: '告警',
    maintenance: '维护',
    normal: '正常',
    warning: '警告',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const formatTime = (timestamp: number) => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

// 事件处理
const updateView = () => {
  // 更新视图模式
}

const refreshData = () => {
  // 刷新设备数据
  devices.value.forEach(device => {
    device.lastUpdate = Date.now() - Math.random() * 3600000
  })
}

const selectDevice = (device: Device) => {
  selectedDevice.value = device
}

const showDeviceTooltip = (device: Device, event: MouseEvent) => {
  tooltipDevice.value = device
  tooltipPosition.value = {
    x: event.clientX + 10,
    y: event.clientY - 50
  }
  tooltipVisible.value = true
}

const hideDeviceTooltip = () => {
  tooltipVisible.value = false
  tooltipDevice.value = null
}

const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value + 0.2, 3)
  if (mapCanvasRef.value) {
    mapCanvasRef.value.style.transform = `scale(${zoomLevel.value})`
  }
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.5)
  if (mapCanvasRef.value) {
    mapCanvasRef.value.style.transform = `scale(${zoomLevel.value})`
  }
}

const resetZoom = () => {
  zoomLevel.value = 1
  if (mapCanvasRef.value) {
    mapCanvasRef.value.style.transform = 'scale(1)'
  }
}

const configDevice = (device: Device) => {
  // 设备配置逻辑
  console.log('配置设备:', device.name)
}

const viewDeviceHistory = (device: Device) => {
  // 查看设备历史数据
  console.log('查看历史:', device.name)
}

const toggleDevice = (device: Device) => {
  // 切换设备状态
  device.status = device.status === 'offline' ? 'online' : 'offline'
}

const batchConfig = () => {
  console.log('批量配置设备')
}

const batchUpdate = () => {
  console.log('批量更新设备')
}

const batchDisable = () => {
  console.log('批量禁用设备')
}

const clearSelection = () => {
  selectedDevices.value = []
}

// 生命周期
onMounted(() => {
  // 初始化地图
})
</script>

<style lang="scss" scoped>
.device-monitor-map {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .map-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .map-controls {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.map-overview {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overview-stats {
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
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--font-lg);
      }
      
      .stat-content {
        .stat-value {
          font-size: var(--font-xl);
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .stat-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
  
  .view-legend {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    min-width: 200px;
    
    .legend-title {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: var(--spacing-sm);
    }
    
    .legend-items {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        
        .legend-indicator {
          width: 12px;
          height: 12px;
          border-radius: var(--radius-full);
        }
        
        .legend-text {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.map-container {
  position: relative;
  flex: 1;
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  overflow: hidden;
  
  .map-canvas {
    width: 100%;
    height: 100%;
    position: relative;
    transform-origin: center;
    transition: transform var(--duration-normal);
  }
  
  .map-background {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a2332 0%, #2a3441 100%);
    position: relative;
    
    .grid-lines {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-image: 
        linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
      background-size: 50px 50px;
    }
  }
  
  .map-regions {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    
    .map-region {
      position: absolute;
      border: 2px dashed rgba(0, 255, 157, 0.3);
      border-radius: var(--radius-md);
      background: rgba(0, 255, 157, 0.05);
      
      .region-label {
        position: absolute;
        top: 8px;
        left: 8px;
        font-size: var(--font-sm);
        color: var(--primary-500);
        font-weight: 600;
      }
    }
  }
  
  .device-markers {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    
    .device-marker {
      position: absolute;
      width: 32px;
      height: 32px;
      border-radius: var(--radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transform: translate(-50%, -50%);
      transition: all var(--duration-normal);
      font-size: var(--font-base);
      border: 2px solid transparent;
      
      &:hover {
        transform: translate(-50%, -50%) scale(1.2);
        z-index: 10;
      }
      
      .marker-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
      }
      
      .marker-pulse {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: var(--radius-full);
        animation: pulse 2s infinite;
      }
      
      // 状态模式样式
      &.marker-online {
        background: #67c23a;
      }
      
      &.marker-offline {
        background: #909399;
      }
      
      &.marker-alert {
        background: #ff6b6b;
        
        .marker-pulse {
          border: 2px solid #ff6b6b;
        }
      }
      
      &.marker-maintenance {
        background: #ffa726;
      }
      
      // 健康模式样式
      &.marker-excellent {
        background: #67c23a;
      }
      
      &.marker-good {
        background: #409eff;
      }
      
      &.marker-fair {
        background: #ffa726;
      }
      
      &.marker-poor {
        background: #ff6b6b;
      }
      
      &.marker-no-data {
        background: #909399;
      }
      
      // 告警模式样式
      &.marker-no-alert {
        background: #67c23a;
      }
      
      &.marker-low-alert {
        background: #ffa726;
      }
      
      &.marker-high-alert {
        background: #ff6b6b;
      }
    }
  }
  
  .connection-lines {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    
    line {
      stroke-width: 2;
      opacity: 0.6;
      
      &.connection-strong {
        stroke: #67c23a;
      }
      
      &.connection-medium {
        stroke: #ffa726;
      }
      
      &.connection-weak {
        stroke: #ff6b6b;
        stroke-dasharray: 5,5;
      }
    }
  }
}

.map-zoom-controls {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  z-index: 20;
}

.device-detail-panel {
  position: absolute;
  top: var(--spacing-md);
  left: var(--spacing-md);
  width: 300px;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 30;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-light);
    
    .device-info {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      
      .device-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.1);
        font-size: var(--font-lg);
      }
      
      .device-basic {
        .device-name {
          font-size: var(--font-base);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .device-type {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
      }
    }
  }
  
  .panel-content {
    padding: var(--spacing-md);
    
    .device-status {
      margin-bottom: var(--spacing-md);
      
      .status-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: var(--spacing-sm);
        
        .status-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
        
        .status-value {
          font-size: var(--font-sm);
          color: var(--text-primary);
          
          &.status-online {
            color: var(--success);
          }
          
          &.status-offline {
            color: var(--text-tertiary);
          }
          
          &.status-alert {
            color: var(--error);
          }
        }
      }
    }
    
    .device-metrics {
      margin-bottom: var(--spacing-md);
      
      .metrics-title {
        font-size: var(--font-sm);
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-sm);
      }
      
      .metrics-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        
        .metric-item {
          display: grid;
          grid-template-columns: 1fr auto auto;
          gap: var(--spacing-sm);
          align-items: center;
          font-size: var(--font-sm);
          
          .metric-name {
            color: var(--text-secondary);
          }
          
          .metric-value {
            color: var(--text-primary);
            font-weight: 600;
          }
          
          .metric-status {
            font-size: var(--font-xs);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            
            &.status-normal {
              background: rgba(103, 194, 58, 0.2);
              color: var(--success);
            }
            
            &.status-warning {
              background: rgba(255, 167, 38, 0.2);
              color: var(--warning);
            }
            
            &.status-error {
              background: rgba(255, 107, 107, 0.2);
              color: var(--error);
            }
          }
        }
      }
    }
    
    .device-actions {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }
  }
}

.device-tooltip {
  position: fixed;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
  box-shadow: var(--shadow-md);
  z-index: 40;
  pointer-events: none;
  
  .tooltip-header {
    font-size: var(--font-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }
  
  .tooltip-content {
    font-size: var(--font-xs);
    color: var(--text-secondary);
    
    div {
      margin-bottom: 2px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.batch-toolbar {
  position: absolute;
  bottom: var(--spacing-md);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 30;
  
  .toolbar-info {
    font-size: var(--font-sm);
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .toolbar-actions {
    display: flex;
    gap: var(--spacing-sm);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0.5;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

@media (max-width: 1024px) {
  .map-overview {
    grid-template-columns: 1fr;
    
    .overview-stats {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  .device-detail-panel {
    width: 250px;
  }
}

@media (max-width: 768px) {
  .map-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .overview-stats {
    grid-template-columns: 1fr !important;
  }
  
  .device-detail-panel {
    position: relative;
    width: 100%;
    margin-top: var(--spacing-md);
  }
  
  .batch-toolbar {
    position: relative;
    left: auto;
    transform: none;
    margin-top: var(--spacing-md);
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
</style>