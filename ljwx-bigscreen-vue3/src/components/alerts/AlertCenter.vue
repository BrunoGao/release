<template>
  <div class="alert-center">
    <div class="center-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Warning />
        </el-icon>
        <h3 class="center-title">预警中心</h3>
        <el-badge 
          v-if="alertStore.unreadCount > 0" 
          :value="alertStore.unreadCount" 
          class="header-badge"
        />
      </div>
      
      <div class="header-actions">
        <el-button-group>
          <el-button 
            type="primary" 
            size="small"
            @click="refreshAlerts"
            :loading="alertStore.isLoading"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button 
            size="small"
            @click="showFilters = !showFilters"
          >
            <el-icon><Filter /></el-icon>
            筛选
          </el-button>
          <el-button 
            size="small"
            @click="showSettings = !showSettings"
          >
            <el-icon><Setting /></el-icon>
            设置
          </el-button>
        </el-button-group>
        
        <el-dropdown @command="handleBatchAction" class="batch-dropdown">
          <el-button size="small">
            批量操作
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="mark-read">标记为已读</el-dropdown-item>
              <el-dropdown-item command="resolve">解决</el-dropdown-item>
              <el-dropdown-item command="export" divided>导出</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-overview">
      <div class="stat-card critical">
        <div class="stat-icon">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ alertStore.criticalCount }}</div>
          <div class="stat-label">严重预警</div>
        </div>
      </div>
      <div class="stat-card high">
        <div class="stat-icon">
          <el-icon><Bell /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ alertStore.highPriorityCount }}</div>
          <div class="stat-label">高优先级</div>
        </div>
      </div>
      <div class="stat-card unread">
        <div class="stat-icon">
          <el-icon><Message /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ alertStore.unreadCount }}</div>
          <div class="stat-label">未读预警</div>
        </div>
      </div>
      <div class="stat-card total">
        <div class="stat-icon">
          <el-icon><DataLine /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ alertStore.alerts.length }}</div>
          <div class="stat-label">总预警数</div>
        </div>
      </div>
    </div>

    <!-- 筛选面板 -->
    <div v-if="showFilters" class="filters-panel">
      <div class="filter-group">
        <label>严重程度:</label>
        <el-radio-group 
          v-model="alertStore.filters.severity" 
          size="small"
          @change="onFilterChange"
        >
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="critical">严重</el-radio-button>
          <el-radio-button label="high">高</el-radio-button>
          <el-radio-button label="medium">中</el-radio-button>
          <el-radio-button label="low">低</el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="filter-group">
        <label>类型:</label>
        <el-select 
          v-model="alertStore.filters.type" 
          size="small" 
          style="width: 150px"
          @change="onFilterChange"
        >
          <el-option label="全部类型" value="all" />
          <el-option label="生命体征" value="vital_sign" />
          <el-option label="运动健康" value="exercise" />
          <el-option label="睡眠质量" value="sleep" />
          <el-option label="心理健康" value="mental_health" />
          <el-option label="用药提醒" value="medication" />
        </el-select>
      </div>
      
      <div class="filter-group">
        <label>状态:</label>
        <el-select 
          v-model="alertStore.filters.status" 
          size="small" 
          style="width: 120px"
          @change="onFilterChange"
        >
          <el-option label="全部" value="all" />
          <el-option label="未读" value="unread" />
          <el-option label="已读" value="read" />
          <el-option label="已解决" value="resolved" />
        </el-select>
      </div>
      
      <el-button size="small" @click="clearFilters">清除筛选</el-button>
    </div>

    <!-- 预警列表 -->
    <div class="alerts-content">
      <div v-if="alertStore.isLoading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="filteredAlerts.length === 0" class="empty-state">
        <el-empty description="暂无预警信息" />
      </div>
      
      <div v-else class="alerts-list">
        <div 
          v-for="alert in filteredAlerts" 
          :key="alert.id"
          class="alert-item"
          :class="[
            `severity-${alert.severity}`,
            { 
              unread: !alert.isRead,
              resolved: alert.isResolved,
              selected: selectedAlerts.includes(alert.id)
            }
          ]"
          @click="selectAlert(alert)"
        >
          <div class="alert-selection">
            <el-checkbox 
              v-model="selectedAlerts"
              :label="alert.id"
              @click.stop
            />
          </div>
          
          <div class="alert-indicator">
            <div class="severity-badge" :class="alert.severity">
              <el-icon>
                <component :is="getSeverityIcon(alert.severity)" />
              </el-icon>
            </div>
          </div>
          
          <div class="alert-content">
            <div class="alert-header">
              <h4 class="alert-title">{{ alert.title }}</h4>
              <div class="alert-meta">
                <span class="alert-type">{{ getAlertTypeLabel(alert.type) }}</span>
                <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
              </div>
            </div>
            
            <p class="alert-message">{{ alert.message }}</p>
            
            <div class="alert-footer">
              <div class="alert-actions">
                <el-button 
                  v-for="action in alert.actions?.slice(0, 2)" 
                  :key="action.id"
                  size="small"
                  :type="getActionType(action.type)"
                  @click.stop="handleAlertAction(alert, action)"
                >
                  {{ action.label }}
                </el-button>
                
                <el-dropdown 
                  v-if="alert.actions && alert.actions.length > 2"
                  @command="(command) => handleAlertAction(alert, command as any)"
                  @click.stop
                >
                  <el-button size="small" type="text">
                    更多 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item 
                        v-for="action in alert.actions.slice(2)"
                        :key="action.id"
                        :command="action"
                      >
                        {{ action.label }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              
              <div class="alert-status">
                <el-tag v-if="!alert.isRead" type="danger" size="small">未读</el-tag>
                <el-tag v-else-if="alert.isResolved" type="success" size="small">已解决</el-tag>
                <el-tag v-else type="info" size="small">已读</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 紧急模式指示器 -->
    <div v-if="alertStore.emergencyMode" class="emergency-indicator">
      <div class="emergency-content">
        <el-icon class="emergency-icon"><Warning /></el-icon>
        <span class="emergency-text">紧急模式已激活</span>
        <el-button 
          type="danger" 
          size="small" 
          @click="exitEmergencyMode"
        >
          退出紧急模式
        </el-button>
      </div>
    </div>

    <!-- 设置面板 -->
    <el-drawer 
      v-model="showSettings"
      title="预警设置"
      direction="rtl"
      size="400px"
    >
      <div class="settings-content">
        <div class="setting-section">
          <h4>通知设置</h4>
          <div class="setting-item">
            <el-switch 
              v-model="alertStore.notifications.sound"
              @change="updateNotificationSettings"
            />
            <label>声音提醒</label>
          </div>
          <div class="setting-item">
            <el-switch 
              v-model="alertStore.notifications.popup"
              @change="updateNotificationSettings"
            />
            <label>弹窗提醒</label>
          </div>
          <div class="setting-item">
            <el-switch 
              v-model="alertStore.notifications.email"
              @change="updateNotificationSettings"
            />
            <label>邮件通知</label>
          </div>
        </div>
        
        <div class="setting-section">
          <h4>显示设置</h4>
          <div class="setting-item">
            <label>每页显示数量:</label>
            <el-input-number 
              v-model="pageSize" 
              :min="5" 
              :max="50" 
              size="small"
            />
          </div>
          <div class="setting-item">
            <el-switch v-model="autoRefresh" />
            <label>自动刷新</label>
          </div>
        </div>
        
        <div class="setting-section">
          <h4>预警级别</h4>
          <div class="severity-settings">
            <div class="severity-item">
              <span class="severity-label critical">严重</span>
              <el-switch v-model="severityEnabled.critical" />
            </div>
            <div class="severity-item">
              <span class="severity-label high">高</span>
              <el-switch v-model="severityEnabled.high" />
            </div>
            <div class="severity-item">
              <span class="severity-label medium">中</span>
              <el-switch v-model="severityEnabled.medium" />
            </div>
            <div class="severity-item">
              <span class="severity-label low">低</span>
              <el-switch v-model="severityEnabled.low" />
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { 
  Warning, 
  Refresh, 
  Filter, 
  Setting, 
  ArrowDown,
  Bell,
  Message,
  DataLine,
  CircleClose,
  InfoFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAlertStore } from '@/stores/alert'
import type { HealthAlert, AlertAction } from '@/types/health'

// Store
const alertStore = useAlertStore()

// 响应式数据
const showFilters = ref(false)
const showSettings = ref(false)
const selectedAlerts = ref<string[]>([])
const pageSize = ref(20)
const autoRefresh = ref(true)

// 通知设置
const severityEnabled = reactive({
  critical: true,
  high: true,
  medium: true,
  low: true
})

// 计算属性
const filteredAlerts = computed(() => {
  return alertStore.getFilteredAlerts()
})

// 方法
const refreshAlerts = async () => {
  try {
    await alertStore.fetchAlerts()
    ElMessage.success('预警数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  }
}

const selectAlert = (alert: HealthAlert) => {
  if (!alert.isRead) {
    alertStore.handleAlert(alert.id, 'acknowledge')
  }
}

const handleBatchAction = async (command: string) => {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请先选择要操作的预警')
    return
  }

  try {
    switch (command) {
      case 'mark-read':
        await alertStore.batchHandleAlerts(selectedAlerts.value, 'mark_read')
        ElMessage.success('已标记为已读')
        break
      case 'resolve':
        await alertStore.batchHandleAlerts(selectedAlerts.value, 'resolve')
        ElMessage.success('已解决选中的预警')
        break
      case 'export':
        await exportSelectedAlerts()
        break
    }
    selectedAlerts.value = []
  } catch (error) {
    ElMessage.error('批量操作失败')
  }
}

const handleAlertAction = async (alert: HealthAlert, action: AlertAction) => {
  try {
    await alertStore.handleAlert(alert.id, action.type)
    ElMessage.success(`${action.label}操作完成`)
  } catch (error) {
    ElMessage.error(`${action.label}操作失败`)
  }
}

const onFilterChange = () => {
  // 筛选变更时的处理
  selectedAlerts.value = []
}

const clearFilters = () => {
  alertStore.clearFilters()
  selectedAlerts.value = []
}

const exitEmergencyMode = async () => {
  try {
    const result = await ElMessageBox.confirm(
      '确认退出紧急模式吗？',
      '确认操作',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (result === 'confirm') {
      await alertStore.exitEmergencyMode()
      ElMessage.success('已退出紧急模式')
    }
  } catch (error) {
    console.log('取消退出紧急模式')
  }
}

const updateNotificationSettings = () => {
  alertStore.updateNotificationSettings(alertStore.notifications)
}

const exportSelectedAlerts = async () => {
  // 导出选中的预警
  console.log('导出预警:', selectedAlerts.value)
  ElMessage.success('预警数据导出完成')
}

// 工具方法
const getSeverityIcon = (severity: string) => {
  const iconMap = {
    critical: Warning,
    high: Bell,
    medium: InfoFilled,
    low: Message
  }
  return iconMap[severity as keyof typeof iconMap] || InfoFilled
}

const getAlertTypeLabel = (type: string) => {
  const typeMap = {
    vital_sign: '生命体征',
    exercise: '运动健康',
    sleep: '睡眠质量',
    mental_health: '心理健康',
    medication: '用药提醒'
  }
  return typeMap[type as keyof typeof typeMap] || type
}

const getActionType = (actionType: string) => {
  const typeMap = {
    acknowledge: 'primary',
    escalate: 'warning',
    ignore: 'info',
    custom: 'success'
  }
  return typeMap[actionType as keyof typeof typeMap] || 'default'
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return timestamp.toLocaleDateString()
}

// 生命周期
onMounted(() => {
  alertStore.fetchAlerts()
  
  if (autoRefresh.value) {
    alertStore.startAutoRefresh(30000) // 30秒刷新一次
  }
})
</script>

<style lang="scss" scoped>
.alert-center {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

// ========== 头部 ==========
.center-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(255, 107, 107, 0.02) 100%);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--error-500);
      font-size: 20px;
    }
    
    .center-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .header-badge {
      margin-left: var(--spacing-xs);
    }
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }
}

// ========== 统计概览 ==========
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-light);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
    }
    
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }
    
    .stat-content {
      .stat-number {
        font-size: var(--font-xl);
        font-weight: 700;
        font-family: var(--font-tech);
        margin-bottom: var(--spacing-xs);
      }
      
      .stat-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
    
    &.critical {
      .stat-icon {
        background: linear-gradient(135deg, var(--error-500), var(--error-600));
        color: white;
      }
      .stat-number { color: var(--error-500); }
    }
    
    &.high {
      .stat-icon {
        background: linear-gradient(135deg, var(--warning-500), var(--warning-600));
        color: white;
      }
      .stat-number { color: var(--warning-500); }
    }
    
    &.unread {
      .stat-icon {
        background: linear-gradient(135deg, var(--info-500), var(--info-600));
        color: white;
      }
      .stat-number { color: var(--info-500); }
    }
    
    &.total {
      .stat-icon {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        color: white;
      }
      .stat-number { color: var(--primary-500); }
    }
  }
}

// ========== 筛选面板 ==========
.filters-panel {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
  
  .filter-group {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      white-space: nowrap;
    }
  }
}

// ========== 预警列表 ==========
.alerts-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
}

.alerts-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  
  &.unread {
    border-left: 4px solid var(--primary-500);
    background: linear-gradient(90deg, rgba(0, 255, 157, 0.03) 0%, transparent 100%);
  }
  
  &.resolved {
    opacity: 0.7;
    
    .alert-content {
      text-decoration: line-through;
    }
  }
  
  &.selected {
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.05);
  }
  
  &.severity-critical {
    border-left-color: var(--error-500);
    
    .severity-badge {
      background: var(--error-500);
      color: white;
    }
  }
  
  &.severity-high {
    border-left-color: var(--warning-500);
    
    .severity-badge {
      background: var(--warning-500);
      color: white;
    }
  }
  
  &.severity-medium {
    border-left-color: var(--info-500);
    
    .severity-badge {
      background: var(--info-500);
      color: white;
    }
  }
  
  &.severity-low {
    border-left-color: var(--success-500);
    
    .severity-badge {
      background: var(--success-500);
      color: white;
    }
  }
}

.alert-selection {
  display: flex;
  align-items: center;
  margin-top: var(--spacing-xs);
}

.alert-indicator {
  .severity-badge {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
  }
}

.alert-content {
  flex: 1;
  
  .alert-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-sm);
    
    .alert-title {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
    
    .alert-meta {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      font-size: var(--font-xs);
      color: var(--text-muted);
      
      .alert-type {
        background: var(--bg-secondary);
        padding: 2px 8px;
        border-radius: var(--radius-sm);
      }
    }
  }
  
  .alert-message {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: var(--spacing-md);
  }
  
  .alert-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .alert-actions {
      display: flex;
      gap: var(--spacing-xs);
    }
  }
}

// ========== 紧急模式指示器 ==========
.emergency-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, var(--error-500), var(--error-600));
  color: white;
  padding: var(--spacing-md);
  z-index: 9999;
  animation: emergency-pulse 2s ease-in-out infinite;
  
  .emergency-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    
    .emergency-icon {
      font-size: 20px;
      animation: shake 0.5s ease-in-out infinite;
    }
    
    .emergency-text {
      font-weight: 600;
    }
  }
}

// ========== 设置内容 ==========
.settings-content {
  padding: var(--spacing-md);
  
  .setting-section {
    margin-bottom: var(--spacing-xl);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: var(--spacing-md);
    }
    
    .setting-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: var(--spacing-md);
      
      label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
  }
  
  .severity-settings {
    .severity-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacing-sm);
      margin-bottom: var(--spacing-xs);
      border-radius: var(--radius-sm);
      
      &:hover {
        background: var(--bg-secondary);
      }
      
      .severity-label {
        padding: 2px 8px;
        border-radius: var(--radius-sm);
        font-size: var(--font-xs);
        font-weight: 600;
        
        &.critical { background: var(--error-500); color: white; }
        &.high { background: var(--warning-500); color: white; }
        &.medium { background: var(--info-500); color: white; }
        &.low { background: var(--success-500); color: white; }
      }
    }
  }
}

// ========== 动画 ==========
@keyframes emergency-pulse {
  0%, 100% { 
    background: linear-gradient(135deg, var(--error-500), var(--error-600));
  }
  50% { 
    background: linear-gradient(135deg, var(--error-600), var(--error-700));
  }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filters-panel {
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }
}

@media (max-width: 768px) {
  .center-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .alert-item {
    .alert-header {
      flex-direction: column;
      gap: var(--spacing-xs);
    }
    
    .alert-footer {
      flex-direction: column;
      gap: var(--spacing-sm);
      align-items: flex-start;
    }
  }
}
</style>