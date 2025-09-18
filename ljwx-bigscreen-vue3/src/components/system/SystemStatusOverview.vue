<template>
  <div class="system-status-overview">
    <div class="status-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Monitor />
        </el-icon>
        <h3 class="status-title">{{ title }}</h3>
      </div>
      
      <div class="status-indicator" :class="getOverallStatus()">
        <span class="indicator-dot"></span>
        <span class="status-text">{{ getStatusText() }}</span>
      </div>
    </div>
    
    <!-- 系统状态概览 -->
    <div class="status-overview">
      <div class="overview-card cpu">
        <div class="card-header">
          <el-icon><Cpu /></el-icon>
          <span>CPU使用率</span>
        </div>
        <div class="progress-container">
          <div class="progress-circle">
            <svg viewBox="0 0 42 42" class="progress-svg">
              <circle
                cx="21"
                cy="21"
                r="15.915"
                fill="transparent"
                stroke="var(--bg-secondary)"
                stroke-width="3"
              />
              <circle
                cx="21"
                cy="21"
                r="15.915"
                fill="transparent"
                :stroke="getCpuColor()"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${systemStatus.cpu} 100`"
                transform="rotate(-90 21 21)"
              />
            </svg>
            <div class="progress-text">{{ systemStatus.cpu }}%</div>
          </div>
        </div>
      </div>
      
      <div class="overview-card memory">
        <div class="card-header">
          <el-icon><Files /></el-icon>
          <span>内存使用</span>
        </div>
        <div class="progress-container">
          <div class="progress-circle">
            <svg viewBox="0 0 42 42" class="progress-svg">
              <circle
                cx="21"
                cy="21"
                r="15.915"
                fill="transparent"
                stroke="var(--bg-secondary)"
                stroke-width="3"
              />
              <circle
                cx="21"
                cy="21"
                r="15.915"
                fill="transparent"
                :stroke="getMemoryColor()"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${systemStatus.memory} 100`"
                transform="rotate(-90 21 21)"
              />
            </svg>
            <div class="progress-text">{{ systemStatus.memory }}%</div>
          </div>
        </div>
      </div>
      
      <div class="overview-card network">
        <div class="card-header">
          <el-icon><Connection /></el-icon>
          <span>网络状态</span>
        </div>
        <div class="network-status">
          <div class="network-value">{{ systemStatus.networkLatency }}ms</div>
          <div class="network-label">延迟</div>
          <div class="network-quality" :class="getNetworkQuality()">
            {{ getNetworkQualityText() }}
          </div>
        </div>
      </div>
      
      <div class="overview-card storage">
        <div class="card-header">
          <el-icon><Folder /></el-icon>
          <span>存储空间</span>
        </div>
        <div class="storage-info">
          <div class="storage-used">{{ formatBytes(systemStatus.storageUsed) }}</div>
          <div class="storage-total">/ {{ formatBytes(systemStatus.storageTotal) }}</div>
          <div class="storage-bar">
            <div 
              class="storage-fill" 
              :style="{ width: getStoragePercent() + '%' }"
              :class="getStorageStatus()"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 系统服务状态 -->
    <div class="service-status">
      <div class="service-header">
        <h4>系统服务</h4>
        <el-button size="small" @click="refreshServices">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <div class="service-list">
        <div 
          v-for="service in systemServices" 
          :key="service.name"
          class="service-item"
          :class="service.status"
        >
          <div class="service-info">
            <div class="service-name">{{ service.name }}</div>
            <div class="service-description">{{ service.description }}</div>
          </div>
          <div class="service-metrics">
            <div class="metric-item">
              <span class="metric-label">运行时间</span>
              <span class="metric-value">{{ service.uptime }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">CPU</span>
              <span class="metric-value">{{ service.cpuUsage }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">内存</span>
              <span class="metric-value">{{ service.memoryUsage }}MB</span>
            </div>
          </div>
          <div class="service-status-indicator">
            <el-tag :type="getServiceTagType(service.status)" size="small">
              {{ getServiceStatusText(service.status) }}
            </el-tag>
          </div>
          <div class="service-actions">
            <el-dropdown>
              <el-button size="small" type="text">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="restartService(service)">重启服务</el-dropdown-item>
                  <el-dropdown-item @click="viewLogs(service)">查看日志</el-dropdown-item>
                  <el-dropdown-item @click="serviceDetails(service)">服务详情</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 系统日志 -->
    <div class="system-logs">
      <div class="logs-header">
        <h4>系统日志</h4>
        <div class="logs-controls">
          <el-select v-model="logLevel" size="small" placeholder="日志级别">
            <el-option label="全部" value="all" />
            <el-option label="错误" value="error" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
          <el-button size="small" @click="clearLogs">
            <el-icon><Delete /></el-icon>
            清空日志
          </el-button>
        </div>
      </div>
      
      <div class="logs-container">
        <div 
          v-for="log in filteredLogs" 
          :key="log.id"
          class="log-entry"
          :class="log.level"
        >
          <div class="log-time">{{ formatTime(log.timestamp) }}</div>
          <div class="log-level">{{ log.level.toUpperCase() }}</div>
          <div class="log-service">{{ log.service }}</div>
          <div class="log-message">{{ log.message }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Monitor, 
  Cpu, 
  Files, 
  Connection, 
  Folder, 
  Refresh, 
  MoreFilled, 
  Delete 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '系统状态概览'
})

const logLevel = ref('all')

// 系统状态数据
const systemStatus = reactive({
  cpu: 45,
  memory: 62,
  networkLatency: 23,
  storageUsed: 2.8 * 1024 * 1024 * 1024, // 2.8GB
  storageTotal: 10 * 1024 * 1024 * 1024  // 10GB
})

// 系统服务
const systemServices = ref([
  {
    name: 'Web服务器',
    description: 'Nginx Web服务器',
    status: 'running',
    uptime: '7天12小时',
    cpuUsage: 2.3,
    memoryUsage: 128
  },
  {
    name: '数据库',
    description: 'MySQL数据库服务',
    status: 'running',
    uptime: '7天12小时',
    cpuUsage: 5.8,
    memoryUsage: 512
  },
  {
    name: 'Redis缓存',
    description: 'Redis内存数据库',
    status: 'running',
    uptime: '7天12小时',
    cpuUsage: 1.2,
    memoryUsage: 256
  },
  {
    name: '消息队列',
    description: 'RabbitMQ消息队列',
    status: 'warning',
    uptime: '2天8小时',
    cpuUsage: 3.5,
    memoryUsage: 192
  },
  {
    name: '文件服务',
    description: '文件上传下载服务',
    status: 'stopped',
    uptime: '0',
    cpuUsage: 0,
    memoryUsage: 0
  }
])

// 系统日志
const systemLogs = ref([
  {
    id: 1,
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    level: 'error',
    service: '文件服务',
    message: '文件服务连接失败，正在尝试重新连接'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 10 * 60 * 1000),
    level: 'warning',
    service: '消息队列',
    message: '消息队列连接数接近上限，建议优化连接池配置'
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    level: 'info',
    service: 'Web服务器',
    message: 'Nginx配置重新加载成功'
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    level: 'info',
    service: '数据库',
    message: '数据库备份任务完成'
  },
  {
    id: 5,
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    level: 'warning',
    service: '系统',
    message: 'CPU使用率较高，建议检查运行进程'
  }
])

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return systemLogs.value
  }
  return systemLogs.value.filter(log => log.level === logLevel.value)
})

// 工具方法
const getOverallStatus = () => {
  if (systemStatus.cpu > 80 || systemStatus.memory > 80) return 'critical'
  if (systemStatus.cpu > 60 || systemStatus.memory > 60) return 'warning'
  return 'normal'
}

const getStatusText = () => {
  const status = getOverallStatus()
  const textMap = {
    normal: '系统正常',
    warning: '需要关注',
    critical: '系统异常'
  }
  return textMap[status]
}

const getCpuColor = () => {
  if (systemStatus.cpu > 80) return 'var(--error-500)'
  if (systemStatus.cpu > 60) return 'var(--warning-500)'
  return 'var(--success-500)'
}

const getMemoryColor = () => {
  if (systemStatus.memory > 80) return 'var(--error-500)'
  if (systemStatus.memory > 60) return 'var(--warning-500)'
  return 'var(--success-500)'
}

const getNetworkQuality = () => {
  if (systemStatus.networkLatency > 100) return 'poor'
  if (systemStatus.networkLatency > 50) return 'fair'
  return 'good'
}

const getNetworkQualityText = () => {
  const quality = getNetworkQuality()
  const textMap = {
    good: '良好',
    fair: '一般',
    poor: '较差'
  }
  return textMap[quality]
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getStoragePercent = () => {
  return Math.round((systemStatus.storageUsed / systemStatus.storageTotal) * 100)
}

const getStorageStatus = () => {
  const percent = getStoragePercent()
  if (percent > 90) return 'critical'
  if (percent > 75) return 'warning'
  return 'normal'
}

const getServiceTagType = (status: string) => {
  const typeMap = {
    running: 'success',
    warning: 'warning',
    stopped: 'danger',
    error: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getServiceStatusText = (status: string) => {
  const textMap = {
    running: '运行中',
    warning: '警告',
    stopped: '已停止',
    error: '错误'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN')
}

// 事件处理
const refreshServices = () => {
  ElMessage.info('刷新系统服务状态')
}

const restartService = (service: any) => {
  ElMessage.info(`重启服务: ${service.name}`)
}

const viewLogs = (service: any) => {
  ElMessage.info(`查看服务日志: ${service.name}`)
}

const serviceDetails = (service: any) => {
  ElMessage.info(`查看服务详情: ${service.name}`)
}

const clearLogs = () => {
  systemLogs.value = []
  ElMessage.success('日志已清空')
}

onMounted(() => {
  console.log('System Status Overview mounted')
})
</script>

<style lang="scss" scoped>
.system-status-overview {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.status-header {
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
    
    .status-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    
    .indicator-dot {
      width: 8px;
      height: 8px;
      border-radius: var(--radius-full);
    }
    
    .status-text {
      font-size: var(--font-sm);
      font-weight: 500;
    }
    
    &.normal {
      background: rgba(102, 187, 106, 0.1);
      color: var(--success-500);
      
      .indicator-dot {
        background: var(--success-500);
      }
    }
    
    &.warning {
      background: rgba(255, 167, 38, 0.1);
      color: var(--warning-500);
      
      .indicator-dot {
        background: var(--warning-500);
      }
    }
    
    &.critical {
      background: rgba(255, 107, 107, 0.1);
      color: var(--error-500);
      
      .indicator-dot {
        background: var(--error-500);
      }
    }
  }
}

.status-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .overview-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    text-align: center;
    
    .card-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-md);
      color: var(--text-secondary);
      font-size: var(--font-sm);
      
      .el-icon {
        font-size: 16px;
      }
    }
    
    .progress-container {
      .progress-circle {
        position: relative;
        width: 80px;
        height: 80px;
        margin: 0 auto;
        
        .progress-svg {
          width: 100%;
          height: 100%;
          transform: rotate(-90deg);
        }
        
        .progress-text {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
      }
    }
    
    .network-status {
      .network-value {
        font-size: var(--font-xl);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
        margin-bottom: var(--spacing-xs);
      }
      
      .network-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-sm);
      }
      
      .network-quality {
        font-size: var(--font-xs);
        padding: 2px 6px;
        border-radius: var(--radius-sm);
        
        &.good {
          background: rgba(102, 187, 106, 0.2);
          color: var(--success-500);
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
    
    .storage-info {
      .storage-used {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-tech);
      }
      
      .storage-total {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-sm);
      }
      
      .storage-bar {
        width: 100%;
        height: 6px;
        background: var(--bg-secondary);
        border-radius: var(--radius-full);
        overflow: hidden;
        
        .storage-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width 0.3s ease;
          
          &.normal {
            background: linear-gradient(90deg, #66bb6a, #4caf50);
          }
          
          &.warning {
            background: linear-gradient(90deg, #ffa726, #ff9800);
          }
          
          &.critical {
            background: linear-gradient(90deg, #ff6b6b, #f44336);
          }
        }
      }
    }
  }
}

.service-status {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .service-header {
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
  
  .service-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    
    .service-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .service-info {
        flex: 1;
        
        .service-name {
          font-size: var(--font-sm);
          font-weight: 500;
          color: var(--text-primary);
          margin-bottom: 2px;
        }
        
        .service-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
      
      .service-metrics {
        display: flex;
        gap: var(--spacing-md);
        
        .metric-item {
          text-align: center;
          
          .metric-label {
            font-size: var(--font-xs);
            color: var(--text-secondary);
            display: block;
            margin-bottom: 2px;
          }
          
          .metric-value {
            font-size: var(--font-xs);
            color: var(--text-primary);
            font-weight: 600;
            font-family: var(--font-tech);
          }
        }
      }
      
      .service-status-indicator {
        .el-tag {
          font-size: var(--font-xs);
        }
      }
      
      &.running {
        border-left: 3px solid var(--success-500);
      }
      
      &.warning {
        border-left: 3px solid var(--warning-500);
      }
      
      &.stopped,
      &.error {
        border-left: 3px solid var(--error-500);
      }
    }
  }
}

.system-logs {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .logs-header {
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
    
    .logs-controls {
      display: flex;
      gap: var(--spacing-sm);
    }
  }
  
  .logs-container {
    max-height: 200px;
    overflow-y: auto;
    
    .log-entry {
      display: grid;
      grid-template-columns: 80px 60px 100px 1fr;
      gap: var(--spacing-sm);
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-sm);
      margin-bottom: var(--spacing-xs);
      font-size: var(--font-xs);
      
      .log-time {
        color: var(--text-secondary);
      }
      
      .log-level {
        font-weight: 600;
      }
      
      .log-service {
        color: var(--text-secondary);
      }
      
      .log-message {
        color: var(--text-primary);
      }
      
      &.error {
        background: rgba(255, 107, 107, 0.1);
        
        .log-level {
          color: var(--error-500);
        }
      }
      
      &.warning {
        background: rgba(255, 167, 38, 0.1);
        
        .log-level {
          color: var(--warning-500);
        }
      }
      
      &.info {
        background: rgba(66, 165, 245, 0.1);
        
        .log-level {
          color: var(--primary-500);
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .status-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .status-overview {
    grid-template-columns: 1fr;
  }
  
  .service-metrics {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .logs-container .log-entry {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
}
</style>