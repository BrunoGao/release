<template>
  <div class="personal-device-panel">
    <div class="panel-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Monitor />
        </el-icon>
        <h3 class="panel-title">{{ title }}</h3>
      </div>
      
      <div class="panel-controls">
        <el-button-group size="small">
          <el-button @click="scanDevices">
            <el-icon><Search /></el-icon>
            扫描设备
          </el-button>
          <el-button @click="addDevice">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
          <el-button @click="syncAllDevices">
            <el-icon><Refresh /></el-icon>
            全部同步
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 设备状态概览 -->
    <div class="device-overview">
      <div class="overview-stats">
        <div class="stat-card online">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.online }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </div>
        
        <div class="stat-card offline">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.offline }}</div>
            <div class="stat-label">离线设备</div>
          </div>
        </div>
        
        <div class="stat-card syncing">
          <div class="stat-icon">
            <el-icon><Refresh /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ deviceStats.syncing }}</div>
            <div class="stat-label">同步中</div>
          </div>
        </div>
        
        <div class="stat-card total">
          <div class="stat-icon">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ getTotalDevices() }}</div>
            <div class="stat-label">设备总数</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 设备列表 -->
    <div class="device-list">
      <div class="list-header">
        <h4>我的设备</h4>
        <div class="list-filters">
          <el-select v-model="statusFilter" size="small" placeholder="状态筛选">
            <el-option label="全部" value="all" />
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="同步中" value="syncing" />
          </el-select>
          <el-select v-model="typeFilter" size="small" placeholder="类型筛选">
            <el-option label="全部" value="all" />
            <el-option label="智能手环" value="smartband" />
            <el-option label="智能手表" value="smartwatch" />
            <el-option label="健康秤" value="scale" />
            <el-option label="血压计" value="bloodpressure" />
            <el-option label="体温计" value="thermometer" />
          </el-select>
        </div>
      </div>
      
      <div class="device-grid">
        <div 
          v-for="device in filteredDevices" 
          :key="device.id"
          class="device-card"
          :class="device.status"
          @click="selectDevice(device)"
        >
          <div class="device-header">
            <div class="device-icon">
              <el-icon>
                <component :is="getDeviceIcon(device.type)" />
              </el-icon>
            </div>
            <div class="device-status" :class="device.status">
              <span class="status-indicator"></span>
              <span class="status-text">{{ getStatusText(device.status) }}</span>
            </div>
          </div>
          
          <div class="device-info">
            <div class="device-name">{{ device.name }}</div>
            <div class="device-model">{{ device.model }}</div>
            <div class="device-type">{{ getTypeText(device.type) }}</div>
          </div>
          
          <div class="device-metrics">
            <div class="metric-item">
              <span class="metric-label">电量</span>
              <div class="battery-indicator">
                <div 
                  class="battery-fill" 
                  :style="{ width: device.battery + '%' }"
                  :class="getBatteryClass(device.battery)"
                ></div>
                <span class="battery-text">{{ device.battery }}%</span>
              </div>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">信号</span>
              <div class="signal-strength">
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
            <el-button 
              size="small" 
              type="primary" 
              :disabled="device.status === 'offline'"
              @click.stop="syncDevice(device)"
            >
              同步数据
            </el-button>
            <el-dropdown trigger="click" @click.stop>
              <el-button size="small" type="text">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="viewDeviceDetails(device)">查看详情</el-dropdown-item>
                  <el-dropdown-item @click="configureDevice(device)">设备配置</el-dropdown-item>
                  <el-dropdown-item @click="resetDevice(device)" divided>重置设备</el-dropdown-item>
                  <el-dropdown-item @click="removeDevice(device)" divided>移除设备</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据同步记录 -->
    <div class="sync-history">
      <div class="history-header">
        <h4>同步记录</h4>
        <el-button size="small" type="text" @click="viewAllHistory">
          查看全部
        </el-button>
      </div>
      
      <div class="history-list">
        <div 
          v-for="record in syncHistory" 
          :key="record.id"
          class="history-item"
          :class="record.status"
        >
          <div class="history-icon">
            <el-icon>
              <component :is="getHistoryIcon(record.status)" />
            </el-icon>
          </div>
          <div class="history-content">
            <div class="history-title">{{ record.deviceName }} 数据同步</div>
            <div class="history-details">
              <span class="sync-type">{{ record.dataType }}</span>
              <span class="sync-count">{{ record.dataCount }} 条记录</span>
              <span class="sync-time">{{ formatTime(record.timestamp) }}</span>
            </div>
          </div>
          <div class="history-status">
            <el-tag :type="getStatusTagType(record.status)" size="small">
              {{ getHistoryStatusText(record.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 设备提醒 -->
    <div class="device-alerts">
      <div class="alerts-header">
        <h4>设备提醒</h4>
        <el-badge :value="alertCount" :max="99">
          <el-button size="small" type="text" @click="viewAllAlerts">
            查看全部
          </el-button>
        </el-badge>
      </div>
      
      <div class="alerts-list">
        <div 
          v-for="alert in deviceAlerts" 
          :key="alert.id"
          class="alert-item"
          :class="alert.level"
        >
          <el-icon class="alert-icon">
            <component :is="getAlertIcon(alert.level)" />
          </el-icon>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-description">{{ alert.description }}</div>
          </div>
          <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
          <div class="alert-action">
            <el-button size="small" type="text" @click="handleAlert(alert)">
              处理
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Monitor, 
  Search, 
  Plus, 
  Refresh, 
  CircleCheck, 
  CircleClose,
  Collection,
  MoreFilled,
  Warning,
  InfoFilled,
  CircleCheckFilled,
  Camera,
  Cpu
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '个人设备面板',
  userId: ''
})

const statusFilter = ref('all')
const typeFilter = ref('all')

// 设备统计
const deviceStats = reactive({
  online: 4,
  offline: 1,
  syncing: 1,
})

// 设备列表
const personalDevices = ref([
  {
    id: 1,
    name: 'Apple Watch Series 8',
    model: 'MNUV3CH/A',
    type: 'smartwatch',
    status: 'online',
    battery: 78,
    signal: 95,
    lastSync: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    id: 2,
    name: '小米手环 7',
    model: 'XMSH15HM',
    type: 'smartband',
    status: 'online',
    battery: 45,
    signal: 88,
    lastSync: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: 3,
    name: '华为智能体脂秤',
    model: 'AH100',
    type: 'scale',
    status: 'syncing',
    battery: 89,
    signal: 72,
    lastSync: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 4,
    name: '欧姆龙血压计',
    model: 'HEM-7136',
    type: 'bloodpressure',
    status: 'online',
    battery: 92,
    signal: 85,
    lastSync: new Date(Date.now() - 30 * 60 * 1000)
  },
  {
    id: 5,
    name: '博朗体温计',
    model: 'IRT6520',
    type: 'thermometer',
    status: 'offline',
    battery: 15,
    signal: 0,
    lastSync: new Date(Date.now() - 6 * 60 * 60 * 1000)
  },
  {
    id: 6,
    name: 'Fitbit Charge 5',
    model: 'FB421',
    type: 'smartband',
    status: 'online',
    battery: 63,
    signal: 91,
    lastSync: new Date(Date.now() - 8 * 60 * 1000)
  }
])

// 同步记录
const syncHistory = ref([
  {
    id: 1,
    deviceName: 'Apple Watch Series 8',
    dataType: '健康数据',
    dataCount: 1248,
    status: 'success',
    timestamp: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    id: 2,
    deviceName: '小米手环 7',
    dataType: '运动数据',
    dataCount: 856,
    status: 'success',
    timestamp: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: 3,
    deviceName: '华为智能体脂秤',
    dataType: '体重数据',
    dataCount: 1,
    status: 'syncing',
    timestamp: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 4,
    deviceName: '博朗体温计',
    dataType: '体温数据',
    dataCount: 0,
    status: 'failed',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000)
  }
])

// 设备提醒
const deviceAlerts = ref([
  {
    id: 1,
    level: 'warning',
    title: '设备电量不足',
    description: '小米手环 7 电量仅剩45%，建议及时充电',
    timestamp: new Date(Date.now() - 30 * 60 * 1000)
  },
  {
    id: 2,
    level: 'error',
    title: '设备离线',
    description: '博朗体温计已离线超过6小时，请检查设备连接',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000)
  },
  {
    id: 3,
    level: 'critical',
    title: '设备电量严重不足',
    description: '博朗体温计电量仅剩15%，可能影响正常使用',
    timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000)
  }
])

const alertCount = computed(() => deviceAlerts.value.length)

const filteredDevices = computed(() => {
  let devices = personalDevices.value
  
  if (statusFilter.value !== 'all') {
    devices = devices.filter(device => device.status === statusFilter.value)
  }
  
  if (typeFilter.value !== 'all') {
    devices = devices.filter(device => device.type === typeFilter.value)
  }
  
  return devices
})

// 工具方法
const getTotalDevices = () => {
  return deviceStats.online + deviceStats.offline + deviceStats.syncing
}

const getDeviceIcon = (type: string) => {
  const iconMap = {
    smartwatch: Monitor,
    smartband: Monitor,
    scale: Cpu,
    bloodpressure: Monitor,
    thermometer: Camera
  }
  return iconMap[type as keyof typeof iconMap] || Monitor
}

const getStatusText = (status: string) => {
  const textMap = {
    online: '在线',
    offline: '离线',
    syncing: '同步中'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getTypeText = (type: string) => {
  const textMap = {
    smartwatch: '智能手表',
    smartband: '智能手环',
    scale: '智能秤',
    bloodpressure: '血压计',
    thermometer: '体温计'
  }
  return textMap[type as keyof typeof textMap] || '未知设备'
}

const getBatteryClass = (battery: number) => {
  if (battery > 50) return 'high'
  if (battery > 20) return 'medium'
  return 'low'
}

const formatSyncTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return time.toLocaleDateString('zh-CN')
}

const formatTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return time.toLocaleDateString('zh-CN')
}

const getHistoryIcon = (status: string) => {
  const iconMap = {
    success: CircleCheckFilled,
    failed: Warning,
    syncing: Refresh
  }
  return iconMap[status as keyof typeof iconMap] || InfoFilled
}

const getStatusTagType = (status: string) => {
  const typeMap = {
    success: 'success',
    failed: 'danger',
    syncing: 'warning'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getHistoryStatusText = (status: string) => {
  const textMap = {
    success: '成功',
    failed: '失败',
    syncing: '同步中'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getAlertIcon = (level: string) => {
  const iconMap = {
    info: InfoFilled,
    warning: Warning,
    error: CircleClose,
    critical: Warning
  }
  return iconMap[level as keyof typeof iconMap] || InfoFilled
}

// 事件处理
const scanDevices = () => {
  ElMessage.info('开始扫描设备...')
}

const addDevice = () => {
  ElMessage.info('打开添加设备向导')
}

const syncAllDevices = () => {
  ElMessage.info('开始同步所有设备...')
}

const selectDevice = (device: any) => {
  console.log('Selected device:', device)
}

const syncDevice = (device: any) => {
  ElMessage.info(`同步设备: ${device.name}`)
}

const viewDeviceDetails = (device: any) => {
  ElMessage.info(`查看设备详情: ${device.name}`)
}

const configureDevice = (device: any) => {
  ElMessage.info(`配置设备: ${device.name}`)
}

const resetDevice = (device: any) => {
  ElMessage.warning(`重置设备: ${device.name}`)
}

const removeDevice = (device: any) => {
  ElMessage.error(`移除设备: ${device.name}`)
}

const viewAllHistory = () => {
  ElMessage.info('查看所有同步记录')
}

const viewAllAlerts = () => {
  ElMessage.info('查看所有设备提醒')
}

const handleAlert = (alert: any) => {
  ElMessage.info(`处理提醒: ${alert.title}`)
}

onMounted(() => {
  console.log('Personal Device Panel mounted')
})
</script>

<style lang="scss" scoped>
.personal-device-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .panel-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.device-overview {
  margin-bottom: var(--spacing-lg);
  
  .overview-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-lg);
    
    .stat-card {
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
      
      &.syncing .stat-icon {
        background: linear-gradient(135deg, #ffa726, #ff9800);
      }
      
      &.total .stat-icon {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
      }
    }
  }
}

.device-list {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .list-header {
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
    
    .list-filters {
      display: flex;
      gap: var(--spacing-sm);
    }
  }
  
  .device-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
    
    .device-card {
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-light);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: var(--bg-card);
        transform: translateY(-2px);
      }
      
      .device-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-sm);
        
        .device-icon {
          width: 32px;
          height: 32px;
          border-radius: var(--radius-sm);
          background: var(--primary-500);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 16px;
        }
        
        .device-status {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          font-size: var(--font-xs);
          
          .status-indicator {
            width: 6px;
            height: 6px;
            border-radius: var(--radius-full);
          }
          
          &.online {
            color: var(--success-500);
            
            .status-indicator {
              background: var(--success-500);
            }
          }
          
          &.offline {
            color: var(--text-secondary);
            
            .status-indicator {
              background: var(--text-secondary);
            }
          }
          
          &.syncing {
            color: var(--warning-500);
            
            .status-indicator {
              background: var(--warning-500);
              animation: pulse 2s infinite;
            }
          }
        }
      }
      
      .device-info {
        margin-bottom: var(--spacing-md);
        
        .device-name {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .device-model {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: 2px;
        }
        
        .device-type {
          font-size: var(--font-xs);
          color: var(--primary-500);
        }
      }
      
      .device-metrics {
        margin-bottom: var(--spacing-md);
        
        .metric-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-xs);
          
          .metric-label {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
          
          .battery-indicator {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            
            .battery-fill {
              width: 30px;
              height: 4px;
              border-radius: var(--radius-full);
              position: relative;
              
              &.high {
                background: var(--success-500);
              }
              
              &.medium {
                background: var(--warning-500);
              }
              
              &.low {
                background: var(--error-500);
              }
            }
            
            .battery-text {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-family: var(--font-tech);
            }
          }
          
          .signal-strength {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            
            .signal-bar {
              width: 3px;
              height: 8px;
              background: var(--bg-card);
              border-radius: var(--radius-full);
              
              &:nth-child(1) { height: 4px; }
              &:nth-child(2) { height: 6px; }
              &:nth-child(3) { height: 8px; }
              &:nth-child(4) { height: 10px; }
              
              &.active {
                background: var(--success-500);
              }
            }
            
            .signal-text {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-family: var(--font-tech);
            }
          }
          
          .sync-time {
            font-size: var(--font-xs);
            color: var(--text-primary);
          }
        }
      }
      
      .device-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.offline {
        opacity: 0.7;
        
        .device-icon {
          background: var(--text-secondary);
        }
      }
      
      &.syncing {
        .device-icon {
          background: var(--warning-500);
          animation: pulse 2s infinite;
        }
      }
    }
  }
}

.sync-history {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .history-header {
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
  }
  
  .history-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    
    .history-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .history-icon {
        width: 24px;
        height: 24px;
        border-radius: var(--radius-full);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        
        &.success {
          background: var(--success-500);
          color: white;
        }
        
        &.failed {
          background: var(--error-500);
          color: white;
        }
        
        &.syncing {
          background: var(--warning-500);
          color: white;
        }
      }
      
      .history-content {
        flex: 1;
        
        .history-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .history-details {
          display: flex;
          gap: var(--spacing-sm);
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .history-status {
        .el-tag {
          font-size: var(--font-xs);
        }
      }
    }
  }
}

.device-alerts {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .alerts-header {
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
  }
  
  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    
    .alert-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .alert-icon {
        width: 24px;
        height: 24px;
        border-radius: var(--radius-full);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        
        &.info {
          background: var(--info-500);
          color: white;
        }
        
        &.warning {
          background: var(--warning-500);
          color: white;
        }
        
        &.error {
          background: var(--error-500);
          color: white;
        }
        
        &.critical {
          background: var(--error-500);
          color: white;
          animation: pulse 2s infinite;
        }
      }
      
      .alert-content {
        flex: 1;
        
        .alert-title {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .alert-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .alert-time {
        font-size: var(--font-xs);
        color: var(--text-secondary);
        margin-right: var(--spacing-sm);
      }
      
      .alert-action {
        .el-button {
          font-size: var(--font-xs);
        }
      }
      
      &.warning {
        border-left: 3px solid var(--warning-500);
      }
      
      &.error {
        border-left: 3px solid var(--error-500);
      }
      
      &.critical {
        border-left: 3px solid var(--error-500);
        background: rgba(255, 107, 107, 0.1);
      }
    }
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 1024px) {
  .overview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .device-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .overview-stats {
    grid-template-columns: 1fr;
  }
  
  .device-grid {
    grid-template-columns: 1fr;
  }
  
  .list-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
}
</style>