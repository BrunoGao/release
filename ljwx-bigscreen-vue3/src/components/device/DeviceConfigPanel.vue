<template>
  <div class="device-config-panel">
    <div class="panel-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Monitor />
        </el-icon>
        <h3 class="panel-title">设备配置管理</h3>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" size="small" @click="addDevice">
          <el-icon><Plus /></el-icon>
          添加设备
        </el-button>
        <el-button size="small" @click="refreshDevices" :loading="isLoading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 设备列表 -->
    <div class="device-list">
      <div 
        v-for="device in devices" 
        :key="device.id"
        class="device-card"
        :class="{ 
          active: device.status === 'active',
          inactive: device.status === 'inactive',
          error: device.status === 'error'
        }"
      >
        <div class="device-header">
          <div class="device-info">
            <div class="device-name">{{ device.name }}</div>
            <div class="device-type">{{ device.type }} - {{ device.model }}</div>
          </div>
          <div class="device-status">
            <el-tag 
              :type="getStatusType(device.status)" 
              size="small"
            >
              {{ getStatusText(device.status) }}
            </el-tag>
          </div>
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
            <span class="metric-label">最后同步</span>
            <span class="metric-value">{{ formatLastSync(device.lastSync) }}</span>
          </div>
          
          <div class="metric-item">
            <span class="metric-label">数据质量</span>
            <div class="quality-indicator" :class="getQualityClass(device.dataQuality)">
              <span>{{ device.dataQuality }}%</span>
            </div>
          </div>
        </div>
        
        <div class="device-actions">
          <el-button 
            size="small" 
            type="primary"
            @click="configureDevice(device)"
          >
            配置
          </el-button>
          <el-button 
            size="small"
            @click="syncDevice(device)"
            :loading="device.syncing"
          >
            同步
          </el-button>
          <el-dropdown @command="(command) => handleDeviceAction(device, command)">
            <el-button size="small" type="text">
              更多 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="calibrate">校准设备</el-dropdown-item>
                <el-dropdown-item command="test">测试连接</el-dropdown-item>
                <el-dropdown-item command="logs">查看日志</el-dropdown-item>
                <el-dropdown-item command="remove" divided>移除设备</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 配置对话框 -->
    <el-dialog 
      v-model="configDialogVisible" 
      :title="'配置设备 - ' + selectedDevice?.name"
      width="600px"
      append-to-body
    >
      <div v-if="selectedDevice" class="config-form">
        <el-form :model="deviceConfig" label-width="100px">
          <el-form-item label="设备名称">
            <el-input v-model="deviceConfig.name" />
          </el-form-item>
          
          <el-form-item label="采样频率">
            <el-select v-model="deviceConfig.sampleRate">
              <el-option label="1秒" value="1s" />
              <el-option label="5秒" value="5s" />
              <el-option label="10秒" value="10s" />
              <el-option label="30秒" value="30s" />
              <el-option label="1分钟" value="1m" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="数据精度">
            <el-radio-group v-model="deviceConfig.precision">
              <el-radio label="high">高精度</el-radio>
              <el-radio label="medium">中等精度</el-radio>
              <el-radio label="low">低精度</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="自动同步">
            <el-switch v-model="deviceConfig.autoSync" />
          </el-form-item>
          
          <el-form-item label="预警阈值">
            <div class="threshold-config">
              <div class="threshold-item">
                <span>低电量警告</span>
                <el-input-number 
                  v-model="deviceConfig.thresholds.lowBattery" 
                  :min="10" 
                  :max="50"
                />
                <span>%</span>
              </div>
              <div class="threshold-item">
                <span>离线超时</span>
                <el-input-number 
                  v-model="deviceConfig.thresholds.offlineTimeout" 
                  :min="1" 
                  :max="60"
                />
                <span>分钟</span>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDeviceConfig">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加设备对话框 -->
    <el-dialog 
      v-model="addDialogVisible" 
      title="添加新设备"
      width="500px"
      append-to-body
    >
      <el-form :model="newDevice" label-width="80px">
        <el-form-item label="设备类型">
          <el-select v-model="newDevice.type" @change="onDeviceTypeChange">
            <el-option label="心率监测器" value="heart_rate" />
            <el-option label="血氧监测器" value="blood_oxygen" />
            <el-option label="血压计" value="blood_pressure" />
            <el-option label="体温计" value="thermometer" />
            <el-option label="智能手环" value="smart_band" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="设备名称">
          <el-input v-model="newDevice.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备型号">
          <el-input v-model="newDevice.model" placeholder="请输入设备型号" />
        </el-form-item>
        
        <el-form-item label="连接方式">
          <el-radio-group v-model="newDevice.connectionType">
            <el-radio label="bluetooth">蓝牙</el-radio>
            <el-radio label="wifi">WiFi</el-radio>
            <el-radio label="usb">USB</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNewDevice">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { 
  Monitor, 
  Plus, 
  Refresh, 
  ArrowDown 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Device {
  id: string
  name: string
  type: string
  model: string
  status: 'active' | 'inactive' | 'error'
  battery: number
  lastSync: Date
  dataQuality: number
  syncing?: boolean
}

interface DeviceConfig {
  name: string
  sampleRate: string
  precision: 'high' | 'medium' | 'low'
  autoSync: boolean
  thresholds: {
    lowBattery: number
    offlineTimeout: number
  }
}

// 响应式数据
const isLoading = ref(false)
const configDialogVisible = ref(false)
const addDialogVisible = ref(false)
const selectedDevice = ref<Device | null>(null)

// 设备列表
const devices = ref<Device[]>([
  {
    id: 'device_001',
    name: '心率监测设备',
    type: '心率监测器',
    model: 'HR-Pro-2023',
    status: 'active',
    battery: 85,
    lastSync: new Date(Date.now() - 300000),
    dataQuality: 95
  },
  {
    id: 'device_002',
    name: '血氧监测仪',
    type: '血氧监测器',
    model: 'OX-Smart-V2',
    status: 'active',
    battery: 62,
    lastSync: new Date(Date.now() - 600000),
    dataQuality: 88
  },
  {
    id: 'device_003',
    name: '智能血压计',
    type: '血压计',
    model: 'BP-Digital-X1',
    status: 'inactive',
    battery: 23,
    lastSync: new Date(Date.now() - 3600000),
    dataQuality: 72
  }
])

// 设备配置
const deviceConfig = reactive<DeviceConfig>({
  name: '',
  sampleRate: '5s',
  precision: 'high',
  autoSync: true,
  thresholds: {
    lowBattery: 20,
    offlineTimeout: 5
  }
})

// 新设备
const newDevice = reactive({
  type: '',
  name: '',
  model: '',
  connectionType: 'bluetooth'
})

// 方法
const refreshDevices = async () => {
  isLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('设备列表已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    isLoading.value = false
  }
}

const addDevice = () => {
  Object.assign(newDevice, {
    type: '',
    name: '',
    model: '',
    connectionType: 'bluetooth'
  })
  addDialogVisible.value = true
}

const configureDevice = (device: Device) => {
  selectedDevice.value = device
  deviceConfig.name = device.name
  configDialogVisible.value = true
}

const syncDevice = async (device: Device) => {
  device.syncing = true
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    device.lastSync = new Date()
    device.status = 'active'
    ElMessage.success(`${device.name} 同步完成`)
  } catch (error) {
    ElMessage.error(`${device.name} 同步失败`)
  } finally {
    device.syncing = false
  }
}

const handleDeviceAction = async (device: Device, action: string) => {
  switch (action) {
    case 'calibrate':
      ElMessage.info(`正在校准 ${device.name}...`)
      break
    case 'test':
      ElMessage.success(`${device.name} 连接测试正常`)
      break
    case 'logs':
      ElMessage.info(`查看 ${device.name} 的日志`)
      break
    case 'remove':
      const result = await ElMessageBox.confirm(
        `确认要移除设备 "${device.name}" 吗？`,
        '确认操作',
        { type: 'warning' }
      )
      if (result === 'confirm') {
        const index = devices.value.findIndex(d => d.id === device.id)
        if (index > -1) {
          devices.value.splice(index, 1)
          ElMessage.success('设备已移除')
        }
      }
      break
  }
}

const saveDeviceConfig = () => {
  if (selectedDevice.value) {
    selectedDevice.value.name = deviceConfig.name
    ElMessage.success('设备配置已保存')
  }
  configDialogVisible.value = false
}

const saveNewDevice = () => {
  if (!newDevice.type || !newDevice.name) {
    ElMessage.warning('请填写完整的设备信息')
    return
  }
  
  const device: Device = {
    id: `device_${Date.now()}`,
    name: newDevice.name,
    type: getDeviceTypeLabel(newDevice.type),
    model: newDevice.model || 'Unknown',
    status: 'inactive',
    battery: 100,
    lastSync: new Date(),
    dataQuality: 0
  }
  
  devices.value.push(device)
  addDialogVisible.value = false
  ElMessage.success('设备添加成功')
}

const onDeviceTypeChange = () => {
  // 根据设备类型自动填充一些默认值
  const typeNames = {
    heart_rate: '心率监测设备',
    blood_oxygen: '血氧监测设备',
    blood_pressure: '血压监测设备',
    thermometer: '体温监测设备',
    smart_band: '智能手环'
  }
  
  newDevice.name = typeNames[newDevice.type as keyof typeof typeNames] || ''
}

// 工具方法
const getStatusType = (status: string) => {
  const typeMap = {
    active: 'success',
    inactive: 'warning',
    error: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    active: '在线',
    inactive: '离线',
    error: '异常'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getBatteryClass = (battery: number) => {
  if (battery > 60) return 'high'
  if (battery > 30) return 'medium'
  return 'low'
}

const getQualityClass = (quality: number) => {
  if (quality >= 90) return 'excellent'
  if (quality >= 80) return 'good'
  if (quality >= 70) return 'fair'
  return 'poor'
}

const getDeviceTypeLabel = (type: string) => {
  const labelMap = {
    heart_rate: '心率监测器',
    blood_oxygen: '血氧监测器',
    blood_pressure: '血压计',
    thermometer: '体温计',
    smart_band: '智能手环'
  }
  return labelMap[type as keyof typeof labelMap] || type
}

const formatLastSync = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  return date.toLocaleDateString()
}
</script>

<style lang="scss" scoped>
.device-config-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-header {
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
    
    .panel-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
}

.device-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--spacing-lg);
  
  .device-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
    }
    
    &.active {
      border-color: var(--success-300);
      background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(102, 187, 106, 0.02) 100%);
    }
    
    &.error {
      border-color: var(--error-300);
      background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(255, 107, 107, 0.02) 100%);
    }
  }
  
  .device-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-lg);
    
    .device-info {
      .device-name {
        font-size: var(--font-md);
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
  
  .device-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
    
    .metric-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .metric-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
      
      .metric-value {
        font-size: var(--font-sm);
        color: var(--text-primary);
        font-weight: 500;
      }
      
      .battery-indicator {
        position: relative;
        width: 80px;
        height: 20px;
        background: var(--bg-secondary);
        border-radius: var(--radius-sm);
        overflow: hidden;
        
        .battery-fill {
          height: 100%;
          border-radius: var(--radius-sm);
          transition: width 0.3s ease;
          
          &.high {
            background: linear-gradient(90deg, #66bb6a, #4caf50);
          }
          
          &.medium {
            background: linear-gradient(90deg, #ffa726, #ff9800);
          }
          
          &.low {
            background: linear-gradient(90deg, #ff6b6b, #f44336);
          }
        }
        
        .battery-text {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: var(--font-xs);
          color: var(--text-primary);
          font-weight: 600;
        }
      }
      
      .quality-indicator {
        padding: 2px 8px;
        border-radius: var(--radius-sm);
        font-size: var(--font-xs);
        font-weight: 600;
        
        &.excellent {
          background: rgba(102, 187, 106, 0.2);
          color: var(--success-500);
        }
        
        &.good {
          background: rgba(0, 255, 157, 0.2);
          color: var(--primary-500);
        }
        
        &.fair {
          background: rgba(255, 167, 38, 0.2);
          color: var(--warning-500);
        }
        
        &.poor {
          background: rgba(255, 107, 107, 0.2);
          color: var(--error-500);
        }
      }
    }
  }
  
  .device-actions {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.config-form {
  .threshold-config {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .threshold-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      
      span:first-child {
        width: 100px;
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
      
      span:last-child {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .device-list {
    grid-template-columns: 1fr;
  }
  
  .device-actions {
    flex-wrap: wrap;
  }
}
</style>