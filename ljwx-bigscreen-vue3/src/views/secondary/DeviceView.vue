<template>
  <div class="device-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.6"
      :particle-count="60"
      :enable-grid="false"
      :enable-pulse="true"
      :enable-data-flow="true"
    />
    
    <!-- 页面头部 -->
    <div class="view-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ArrowLeftIcon />
          <span>返回主大屏</span>
        </button>
        <div class="page-title">
          <h1>设备监控中心</h1>
          <p class="page-subtitle">实时设备状态监控与管理</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="device-summary">
          <div class="summary-item">
            <span class="summary-label">在线设备</span>
            <span class="summary-value online">{{ onlineDevices }}/{{ totalDevices }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">数据同步率</span>
            <span class="summary-value">{{ syncRate }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 设备监控主体 -->
    <div class="device-content">
      <!-- 设备状态概览 -->
      <div class="content-section">
        <div class="section-header">
          <h3>设备状态概览</h3>
          <div class="section-actions">
            <button class="action-btn" @click="refreshDevices">
              <RefreshIcon :class="{ spinning: isRefreshing }" />
              刷新
            </button>
            <button class="action-btn" @click="showAddDevice">
              <PlusIcon />
              添加设备
            </button>
          </div>
        </div>
        
        <div class="device-grid">
          <div 
            v-for="device in devices" 
            :key="device.id"
            class="device-card"
            :class="getDeviceStatusClass(device.status)"
            @click="selectDevice(device)"
          >
            <div class="device-header">
              <div class="device-icon">
                <component :is="getDeviceIcon(device.type)" />
              </div>
              <div class="device-status" :class="device.status">
                <div class="status-indicator"></div>
                <span class="status-text">{{ getStatusText(device.status) }}</span>
              </div>
            </div>
            
            <div class="device-info">
              <h4 class="device-name">{{ device.name }}</h4>
              <p class="device-type">{{ getDeviceTypeName(device.type) }}</p>
              <p class="device-location">{{ device.location }}</p>
            </div>
            
            <div class="device-metrics">
              <div class="metric-item">
                <span class="metric-label">电池</span>
                <div class="battery-indicator" :class="getBatteryClass(device.battery)">
                  <div class="battery-fill" :style="{ width: device.battery + '%' }"></div>
                  <span class="battery-text">{{ device.battery }}%</span>
                </div>
              </div>
              <div class="metric-item">
                <span class="metric-label">信号</span>
                <div class="signal-bars">
                  <div 
                    v-for="i in 4" 
                    :key="i"
                    class="signal-bar"
                    :class="{ active: i <= Math.ceil(device.signal / 25) }"
                  ></div>
                  <span class="signal-text">{{ device.signal }}%</span>
                </div>
              </div>
              <div class="metric-item">
                <span class="metric-label">最后同步</span>
                <span class="sync-time">{{ formatSyncTime(device.lastSync) }}</span>
              </div>
            </div>
            
            <div class="device-actions">
              <button 
                class="device-action-btn"
                @click.stop="syncDevice(device.id)"
                :disabled="device.status === 'offline'"
              >
                <SyncIcon />
              </button>
              <button 
                class="device-action-btn"
                @click.stop="configDevice(device.id)"
              >
                <CogIcon />
              </button>
              <button 
                class="device-action-btn danger"
                @click.stop="removeDevice(device.id)"
              >
                <TrashIcon />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 设备详情面板 -->
      <div class="content-section" v-if="selectedDevice">
        <div class="section-header">
          <h3>设备详情 - {{ selectedDevice.name }}</h3>
          <button class="close-btn" @click="selectedDevice = null">
            <XMarkIcon />
          </button>
        </div>
        
        <div class="device-detail">
          <div class="detail-tabs">
            <button 
              v-for="tab in detailTabs"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
          </div>
          
          <div class="detail-content">
            <!-- 实时数据 -->
            <div v-if="activeTab === 'realtime'" class="tab-content">
              <div class="realtime-metrics">
                <div 
                  v-for="metric in selectedDevice.metrics"
                  :key="metric.name"
                  class="metric-card"
                >
                  <div class="metric-header">
                    <span class="metric-name">{{ metric.name }}</span>
                    <span class="metric-unit">{{ metric.unit }}</span>
                  </div>
                  <div class="metric-value">{{ metric.value }}</div>
                  <div class="metric-chart">
                    <MiniTrendChart 
                      :data="metric.history" 
                      :color="metric.color"
                      :height="60"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 历史数据 -->
            <div v-if="activeTab === 'history'" class="tab-content">
              <div class="history-chart">
                <DeviceHistoryChart 
                  :device-id="selectedDevice.id"
                  :time-range="historyTimeRange"
                />
              </div>
            </div>
            
            <!-- 设备配置 -->
            <div v-if="activeTab === 'config'" class="tab-content">
              <DeviceConfigPanel :device="selectedDevice" />
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
  RefreshIcon,
  PlusIcon,
  SyncIcon,
  CogIcon,
  TrashIcon,
  XMarkIcon,
  MonitorIcon,
  DevicePhoneMobileIcon,
  HeartIcon,
  ThermometerIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import MiniTrendChart from '@/components/charts/MiniTrendChart.vue'
import DeviceHistoryChart from '@/components/charts/DeviceHistoryChart.vue'
import DeviceConfigPanel from '@/components/device/DeviceConfigPanel.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { useDeviceStore } from '@/stores/device'
import { useRouter } from 'vue-router'

// Store and router
const deviceStore = useDeviceStore()
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const isRefreshing = ref(false)
const selectedDevice = ref(null)
const activeTab = ref('realtime')
const historyTimeRange = ref('24h')

// 详情面板标签
const detailTabs = [
  { key: 'realtime', label: '实时数据' },
  { key: 'history', label: '历史数据' },
  { key: 'config', label: '设备配置' }
]

// 模拟设备数据
const devices = ref([
  {
    id: 'device_001',
    name: '智能手环-001',
    type: 'wearable',
    status: 'online',
    location: '1号楼-2层-办公区',
    battery: 85,
    signal: 92,
    lastSync: new Date(Date.now() - 5 * 60000), // 5分钟前
    metrics: [
      {
        name: '心率',
        value: '72',
        unit: 'BPM',
        color: '#ff6b6b',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 70 + Math.random() * 10
        }))
      },
      {
        name: '步数',
        value: '8,456',
        unit: '步',
        color: '#4ecdc4',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 8000 + Math.random() * 1000
        }))
      }
    ]
  },
  {
    id: 'device_002',
    name: '温度传感器-002',
    type: 'sensor',
    status: 'online',
    location: '1号楼-3层-会议室',
    battery: 78,
    signal: 88,
    lastSync: new Date(Date.now() - 2 * 60000),
    metrics: [
      {
        name: '温度',
        value: '23.5',
        unit: '°C',
        color: '#ffa726',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 23 + Math.random() * 2
        }))
      },
      {
        name: '湿度',
        value: '45',
        unit: '%',
        color: '#42a5f5',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 40 + Math.random() * 10
        }))
      }
    ]
  },
  {
    id: 'device_003',
    name: '血压监护仪-003',
    type: 'medical',
    status: 'warning',
    location: '2号楼-1层-医务室',
    battery: 12,
    signal: 76,
    lastSync: new Date(Date.now() - 15 * 60000),
    metrics: [
      {
        name: '收缩压',
        value: '125',
        unit: 'mmHg',
        color: '#9c27b0',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 120 + Math.random() * 10
        }))
      },
      {
        name: '舒张压',
        value: '82',
        unit: 'mmHg',
        color: '#673ab7',
        history: Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000),
          value: 80 + Math.random() * 5
        }))
      }
    ]
  },
  {
    id: 'device_004',
    name: '智能手机-004',
    type: 'mobile',
    status: 'offline',
    location: '3号楼-2层-研发区',
    battery: 0,
    signal: 0,
    lastSync: new Date(Date.now() - 120 * 60000),
    metrics: []
  }
])

// 计算属性
const onlineDevices = computed(() => devices.value.filter(d => d.status === 'online').length)
const totalDevices = computed(() => devices.value.length)
const syncRate = computed(() => {
  const onlineCount = onlineDevices.value
  return totalDevices.value > 0 ? Math.round((onlineCount / totalDevices.value) * 100) : 0
})

// 方法
const goBack = () => {
  router.push('/dashboard/main')
}

const getDeviceIcon = (type: string) => {
  const icons = {
    wearable: HeartIcon,
    sensor: ThermometerIcon,
    medical: MonitorIcon,
    mobile: DevicePhoneMobileIcon
  }
  return icons[type as keyof typeof icons] || MonitorIcon
}

const getDeviceStatusClass = (status: string) => {
  return `device-status-${status}`
}

const getStatusText = (status: string) => {
  const statusMap = {
    online: '在线',
    offline: '离线',
    warning: '警告',
    error: '错误'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const getDeviceTypeName = (type: string) => {
  const typeMap = {
    wearable: '可穿戴设备',
    sensor: '传感器',
    medical: '医疗设备',
    mobile: '移动设备'
  }
  return typeMap[type as keyof typeof typeMap] || type
}

const getBatteryClass = (battery: number) => {
  if (battery > 50) return 'battery-good'
  if (battery > 20) return 'battery-medium'
  return 'battery-low'
}

const formatSyncTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  return `${hours}小时前`
}

const selectDevice = (device: any) => {
  selectedDevice.value = device
  activeTab.value = 'realtime'
}

const refreshDevices = async () => {
  isRefreshing.value = true
  try {
    // 模拟刷新
    await new Promise(resolve => setTimeout(resolve, 1000))
    toast.value?.success('设备状态已刷新')
  } finally {
    isRefreshing.value = false
  }
}

const showAddDevice = () => {
  toast.value?.info('添加设备功能开发中')
}

const syncDevice = async (deviceId: string) => {
  try {
    await deviceStore.syncDevice(deviceId)
    toast.value?.success('设备同步成功')
  } catch (error) {
    toast.value?.error('设备同步失败')
  }
}

const configDevice = (deviceId: string) => {
  const device = devices.value.find(d => d.id === deviceId)
  if (device) {
    selectedDevice.value = device
    activeTab.value = 'config'
  }
}

const removeDevice = (deviceId: string) => {
  toast.value?.warning('确认删除设备？')
  // 这里可以添加确认对话框
}

// 生命周期
onMounted(() => {
  // 可以在这里加载设备数据
  console.log('设备监控页面已加载')
})
</script>

<style lang="scss" scoped>
.device-view {
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
  .device-summary {
    display: flex;
    gap: var(--spacing-lg);
  }
  
  .summary-item {
    text-align: center;
    
    .summary-label {
      display: block;
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .summary-value {
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

// ========== 主体内容 ==========
.device-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.content-section {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
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

.section-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  font-size: var(--font-sm);
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
  
  .spinning {
    animation: spin 1s linear infinite;
  }
}

// ========== 设备网格 ==========
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
}

.device-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: all var(--duration-normal);
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    transition: background var(--duration-normal);
  }
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-500);
  }
  
  &.device-status-online::before {
    background: var(--success);
  }
  
  &.device-status-warning::before {
    background: var(--warning);
  }
  
  &.device-status-offline::before {
    background: var(--error);
  }
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(0, 255, 157, 0.2);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.device-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }
  
  .status-text {
    font-size: var(--font-xs);
    font-weight: 500;
  }
  
  &.online {
    color: var(--success);
    .status-indicator { background: var(--success); }
  }
  
  &.warning {
    color: var(--warning);
    .status-indicator { background: var(--warning); }
  }
  
  &.offline {
    color: var(--error);
    .status-indicator { background: var(--error); animation: none; }
  }
}

.device-info {
  margin-bottom: var(--spacing-md);
  
  .device-name {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }
  
  .device-type,
  .device-location {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-xs) 0;
  }
}

.device-metrics {
  margin-bottom: var(--spacing-md);
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  
  .metric-label {
    font-size: var(--font-xs);
    color: var(--text-secondary);
  }
}

.battery-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  
  .battery-fill {
    width: 60px;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    position: relative;
    overflow: hidden;
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      background: inherit;
      border-radius: inherit;
      transition: width var(--duration-normal);
    }
  }
  
  .battery-text {
    font-size: var(--font-xs);
    font-family: var(--font-tech);
  }
  
  &.battery-good .battery-fill::after { background: var(--success); }
  &.battery-medium .battery-fill::after { background: var(--warning); }
  &.battery-low .battery-fill::after { background: var(--error); }
}

.signal-bars {
  display: flex;
  align-items: end;
  gap: 2px;
  
  .signal-bar {
    width: 3px;
    background: var(--border-tertiary);
    border-radius: 1px;
    transition: background var(--duration-fast);
    
    &:nth-child(1) { height: 4px; }
    &:nth-child(2) { height: 6px; }
    &:nth-child(3) { height: 8px; }
    &:nth-child(4) { height: 10px; }
    
    &.active {
      background: var(--primary-500);
    }
  }
  
  .signal-text {
    font-size: var(--font-xs);
    font-family: var(--font-tech);
    margin-left: var(--spacing-xs);
  }
}

.sync-time {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.device-actions {
  display: flex;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-tertiary);
}

.device-action-btn {
  flex: 1;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-tertiary);
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover:not(:disabled) {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
  
  &.danger:hover {
    color: var(--error);
    border-color: var(--error);
    background: rgba(255, 107, 107, 0.1);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// ========== 设备详情 ==========
.device-detail {
  .detail-tabs {
    display: flex;
    border-bottom: 1px solid var(--border-secondary);
  }
  
  .tab-btn {
    padding: var(--spacing-md) var(--spacing-lg);
    border: none;
    background: none;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    border-bottom: 2px solid transparent;
    
    &:hover {
      color: var(--text-primary);
    }
    
    &.active {
      color: var(--primary-500);
      border-bottom-color: var(--primary-500);
    }
  }
  
  .detail-content {
    padding: var(--spacing-lg);
  }
}

.realtime-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}

.metric-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  
  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
    
    .metric-name {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
    
    .metric-unit {
      font-size: var(--font-xs);
      color: var(--text-tertiary);
    }
  }
  
  .metric-value {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text-primary);
    font-family: var(--font-tech);
    margin-bottom: var(--spacing-sm);
  }
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: var(--error);
    color: white;
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
@media (max-width: 1024px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-md);
  }
  
  .header-right .device-summary {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }
  
  .device-grid {
    grid-template-columns: 1fr;
  }
  
  .realtime-metrics {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .device-card,
  .action-btn,
  .device-action-btn {
    transition: none;
  }
  
  .status-indicator,
  .spinning {
    animation: none;
  }
}
</style>